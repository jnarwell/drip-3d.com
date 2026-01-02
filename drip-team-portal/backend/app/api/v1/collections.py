"""
Collections API - CRUD endpoints for organizing resources into collections.

Collections allow users to group related documents, links, and other resources.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
import os
import logging
import re

from app.db.database import get_db
from app.models.collection import Collection, resource_collections
from app.models.resources import Resource
from app.core.rate_limit import limiter

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

# Input length limits
MAX_NAME_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 2000
HEX_COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')


class CollectionCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    color: Optional[str] = None  # Hex code, e.g., "#FF5733"

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError("Color must be a valid hex code (e.g., '#FF5733')")
        return v.upper()  # Normalize to uppercase


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=MAX_NAME_LENGTH)
    description: Optional[str] = Field(None, max_length=MAX_DESCRIPTION_LENGTH)
    color: Optional[str] = None

    @field_validator('color')
    @classmethod
    def validate_color(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        if not v:
            return None
        if not HEX_COLOR_PATTERN.match(v):
            raise ValueError("Color must be a valid hex code (e.g., '#FF5733')")
        return v.upper()  # Normalize to uppercase


# =============================================================================
# COLLECTION CRUD
# =============================================================================

@router.get("")
async def list_collections(
    include_resources: bool = Query(False, description="Include resource IDs in response"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all collections for the current user.

    Returns collections sorted by name.
    """
    user_email = current_user["email"]

    collections = db.query(Collection).filter(
        Collection.created_by == user_email
    ).order_by(Collection.name).all()

    return {
        "collections": [c.to_dict(include_resources=include_resources) for c in collections],
        "total": len(collections)
    }


@router.post("")
@limiter.limit("20/minute")
async def create_collection(
    request: Request,
    data: CollectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new collection.

    Collection names must be unique per user.
    Rate limited: 20 requests/minute per IP
    """
    user_email = current_user["email"]
    logger.info(f"POST /collections - User: {user_email}, Name: {data.name}")

    # Color validation is handled by Pydantic field_validator
    collection = Collection(
        name=data.name,
        description=data.description,
        color=data.color,
        created_by=user_email
    )

    try:
        db.add(collection)
        db.commit()
        db.refresh(collection)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Collection '{data.name}' already exists"
        )

    logger.info(f"POST /collections - Created collection id={collection.id}")
    return collection.to_dict()


@router.get("/{collection_id}")
async def get_collection(
    collection_id: int,
    include_resources: bool = Query(False, description="Include resource IDs in response"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single collection by ID."""
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    return collection.to_dict(include_resources=include_resources)


@router.patch("/{collection_id}")
async def update_collection(
    collection_id: int,
    data: CollectionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a collection."""
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    if data.name is not None:
        # Check for duplicate name
        existing = db.query(Collection).filter(
            Collection.name == data.name,
            Collection.created_by == user_email,
            Collection.id != collection_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Collection '{data.name}' already exists"
            )
        collection.name = data.name

    if data.description is not None:
        collection.description = data.description

    if data.color is not None:
        # Color validation is handled by Pydantic field_validator
        collection.color = data.color

    db.commit()
    db.refresh(collection)

    return collection.to_dict()


@router.delete("/{collection_id}")
async def delete_collection(
    collection_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a collection.

    This removes the collection but does NOT delete the resources in it.
    """
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    db.delete(collection)
    db.commit()

    return {"deleted": True, "id": collection_id}


# =============================================================================
# COLLECTION RESOURCES
# =============================================================================

@router.get("/{collection_id}/resources")
async def list_collection_resources(
    collection_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all resources in a collection.

    Returns resources sorted by added_at descending.
    """
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get paginated resources
    total = len(collection.resources)
    resources = collection.resources[offset:offset + limit]

    return {
        "resources": [r.to_dict() for r in resources],
        "total": total,
        "limit": limit,
        "offset": offset,
        "collection": collection.to_dict()
    }


@router.post("/{collection_id}/resources/{resource_id}")
async def add_resource_to_collection(
    collection_id: int,
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a resource to a collection."""
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Verify user owns this resource (can only add own resources to collections)
    if resource.added_by != user_email:
        raise HTTPException(
            status_code=403,
            detail="You can only add your own resources to collections"
        )

    # Check if already in collection
    if resource in collection.resources:
        return {"added": False, "message": "Resource already in collection"}

    collection.resources.append(resource)
    db.commit()

    logger.info(f"Added resource {resource_id} to collection {collection_id}")
    return {"added": True, "collection_id": collection_id, "resource_id": resource_id}


@router.delete("/{collection_id}/resources/{resource_id}")
async def remove_resource_from_collection(
    collection_id: int,
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove a resource from a collection."""
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    if resource not in collection.resources:
        return {"removed": False, "message": "Resource not in collection"}

    collection.resources.remove(resource)
    db.commit()

    logger.info(f"Removed resource {resource_id} from collection {collection_id}")
    return {"removed": True, "collection_id": collection_id, "resource_id": resource_id}


class BulkAddRequest(BaseModel):
    resource_ids: List[int] = Field(..., min_length=1, max_length=100)


@router.post("/{collection_id}/resources/bulk")
async def bulk_add_resources_to_collection(
    collection_id: int,
    data: BulkAddRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add multiple resources to a collection at once.

    Only adds resources owned by the current user.
    Skips resources already in the collection.
    """
    user_email = current_user["email"]

    collection = db.query(Collection).filter(
        Collection.id == collection_id,
        Collection.created_by == user_email
    ).first()

    if not collection:
        raise HTTPException(status_code=404, detail="Collection not found")

    # Get all requested resources owned by the user
    resources = db.query(Resource).filter(
        Resource.id.in_(data.resource_ids),
        Resource.added_by == user_email
    ).all()

    if not resources:
        raise HTTPException(
            status_code=400,
            detail="No valid resources found. You can only add your own resources."
        )

    # Add resources not already in collection
    added_count = 0
    for resource in resources:
        if resource not in collection.resources:
            collection.resources.append(resource)
            added_count += 1

    db.commit()

    logger.info(f"Bulk added {added_count} resources to collection {collection_id}")
    return {"added": added_count, "collection_id": collection_id}
