"""
Collections API - CRUD endpoints for organizing resources into collections.

Collections allow users to group related documents, links, and other resources.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from pydantic import BaseModel
import os
import logging

from app.db.database import get_db
from app.models.collection import Collection, resource_collections
from app.models.resources import Resource

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/collections", tags=["collections"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class CollectionCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    color: Optional[str] = None  # Hex code, e.g., "#FF5733"


class CollectionUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None


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
async def create_collection(
    data: CollectionCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new collection.

    Collection names must be unique per user.
    """
    user_email = current_user["email"]
    logger.info(f"POST /collections - User: {user_email}, Name: {data.name}")

    # Validate color format if provided
    if data.color and not data.color.startswith("#"):
        raise HTTPException(
            status_code=400,
            detail="Color must be a hex code starting with '#' (e.g., '#FF5733')"
        )

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
        if data.color and not data.color.startswith("#"):
            raise HTTPException(
                status_code=400,
                detail="Color must be a hex code starting with '#' (e.g., '#FF5733')"
            )
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
