"""
Resources API - CRUD endpoints for project resources.

Resources are documents, links, papers, images, etc. that can be
linked to components and physics models.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import or_, String
from typing import Optional, List
from pydantic import BaseModel
import os
import logging

logger = logging.getLogger(__name__)

from app.db.database import get_db
from app.models.resources import Resource, resource_components, resource_physics_models
from app.models.component import Component
from app.models.physics_model import PhysicsModel

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/resources", tags=["resources"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class ResourceCreateRequest(BaseModel):
    title: str
    resource_type: str  # doc, folder, image, link, paper, video, spreadsheet
    url: Optional[str] = None
    google_drive_file_id: Optional[str] = None  # Google Drive file ID
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    component_ids: Optional[List[int]] = None
    physics_model_ids: Optional[List[int]] = None


class ResourceUpdateRequest(BaseModel):
    title: Optional[str] = None
    resource_type: Optional[str] = None
    url: Optional[str] = None
    google_drive_file_id: Optional[str] = None  # Google Drive file ID
    tags: Optional[List[str]] = None
    notes: Optional[str] = None
    component_ids: Optional[List[int]] = None
    physics_model_ids: Optional[List[int]] = None


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================

@router.get("")
async def list_resources(
    resource_type: Optional[str] = Query(None, description="Filter by type (doc, link, paper, etc.)"),
    type: Optional[str] = Query(None, description="Alias for resource_type, supports comma-separated"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    component_id: Optional[int] = Query(None, description="Filter by linked component"),
    physics_model_id: Optional[int] = Query(None, description="Filter by linked physics model"),
    search: Optional[str] = Query(None, description="Search in title, notes, and tags"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List resources with optional filters.

    Returns resources sorted by added_at descending (most recent first).
    """
    # Use selectinload to prevent N+1 queries when calling to_dict()
    query = db.query(Resource).options(
        selectinload(Resource.components),
        selectinload(Resource.physics_models),
        selectinload(Resource.collections)
    )

    # Apply filters - support both 'type' and 'resource_type', with comma-separated values
    type_filter = type or resource_type
    if type_filter:
        types = [t.strip() for t in type_filter.split(",")]
        if len(types) == 1:
            query = query.filter(Resource.resource_type == types[0])
        else:
            query = query.filter(Resource.resource_type.in_(types))

    if component_id:
        query = query.join(resource_components).filter(
            resource_components.c.component_id == component_id
        )

    if physics_model_id:
        query = query.join(resource_physics_models).filter(
            resource_physics_models.c.physics_model_id == physics_model_id
        )

    # Filter by tag (check if tag exists in JSON array)
    if tag:
        # Cast JSON array to text and check for tag value
        query = query.filter(Resource.tags.cast(String).ilike(f'%"{tag}"%'))

    if search:
        search_pattern = f"%{search}%"
        logger.info(f"GET /resources - Search: '{search}' -> pattern: '{search_pattern}'")
        query = query.filter(
            or_(
                Resource.title.ilike(search_pattern),
                Resource.notes.ilike(search_pattern),
                # Also search in tags (cast JSON to string)
                Resource.tags.cast(String).ilike(search_pattern)
            )
        )

    # Get total count
    total = query.count()

    # Get paginated results
    resources = query.order_by(Resource.added_at.desc()).offset(offset).limit(limit).all()

    # Debug logging
    logger.info(f"GET /resources - type={type_filter}, tag={tag}, search={search}, total={total}")

    return {
        "resources": [r.to_dict() for r in resources],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("")
async def create_resource(
    data: ResourceCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new resource.

    Can optionally link to components and physics models during creation.
    """
    # Log received payload for debugging
    logger.info(f"POST /resources - Received payload: {data.model_dump()}")
    logger.info(f"POST /resources - User: {current_user.get('email', 'unknown')}")

    user_id = current_user["email"]

    # Validate resource_type
    valid_types = {"doc", "folder", "image", "link", "paper", "pdf", "slides", "spreadsheet", "video"}
    if data.resource_type not in valid_types:
        logger.warning(f"POST /resources - Invalid resource_type: '{data.resource_type}' (valid: {valid_types})")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid resource_type '{data.resource_type}'. Must be one of: {', '.join(sorted(valid_types))}"
        )

    # Create resource
    resource = Resource(
        title=data.title,
        resource_type=data.resource_type,
        url=data.url,
        google_drive_file_id=data.google_drive_file_id,
        tags=data.tags,
        notes=data.notes,
        added_by=user_id
    )

    # Link to components if provided
    if data.component_ids:
        components = db.query(Component).filter(Component.id.in_(data.component_ids)).all()
        found_ids = [c.id for c in components]
        if len(components) != len(data.component_ids):
            missing = set(data.component_ids) - set(found_ids)
            logger.warning(f"POST /resources - Component IDs not found: {missing} (requested: {data.component_ids}, found: {found_ids})")
            raise HTTPException(status_code=400, detail=f"Component IDs not found: {list(missing)}")
        resource.components = components

    # Link to physics models if provided
    if data.physics_model_ids:
        models = db.query(PhysicsModel).filter(PhysicsModel.id.in_(data.physics_model_ids)).all()
        found_ids = [m.id for m in models]
        if len(models) != len(data.physics_model_ids):
            missing = set(data.physics_model_ids) - set(found_ids)
            logger.warning(f"POST /resources - PhysicsModel IDs not found: {missing} (requested: {data.physics_model_ids}, found: {found_ids})")
            raise HTTPException(status_code=400, detail=f"PhysicsModel IDs not found: {list(missing)}")
        resource.physics_models = models

    db.add(resource)
    db.commit()
    db.refresh(resource)

    logger.info(f"POST /resources - Created resource id={resource.id}")
    return resource.to_dict()


@router.get("/{resource_id}")
async def get_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single resource by ID."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    return resource.to_dict()


@router.patch("/{resource_id}")
async def update_resource(
    resource_id: int,
    data: ResourceUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a resource.

    Can update associations with components and physics models.
    """
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    # Update fields
    if data.title is not None:
        resource.title = data.title

    if data.resource_type is not None:
        valid_types = {"doc", "folder", "image", "link", "paper", "pdf", "slides", "spreadsheet", "video"}
        if data.resource_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid resource_type. Must be one of: {', '.join(valid_types)}"
            )
        resource.resource_type = data.resource_type

    if data.url is not None:
        resource.url = data.url

    if data.google_drive_file_id is not None:
        resource.google_drive_file_id = data.google_drive_file_id

    if data.tags is not None:
        resource.tags = data.tags

    if data.notes is not None:
        resource.notes = data.notes

    # Update component associations
    if data.component_ids is not None:
        if data.component_ids:
            components = db.query(Component).filter(Component.id.in_(data.component_ids)).all()
            if len(components) != len(data.component_ids):
                raise HTTPException(status_code=400, detail="One or more component IDs not found")
            resource.components = components
        else:
            resource.components = []

    # Update physics model associations
    if data.physics_model_ids is not None:
        if data.physics_model_ids:
            models = db.query(PhysicsModel).filter(PhysicsModel.id.in_(data.physics_model_ids)).all()
            if len(models) != len(data.physics_model_ids):
                raise HTTPException(status_code=400, detail="One or more physics model IDs not found")
            resource.physics_models = models
        else:
            resource.physics_models = []

    db.commit()
    db.refresh(resource)

    return resource.to_dict()


@router.delete("/{resource_id}")
async def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a resource."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()

    if not resource:
        raise HTTPException(status_code=404, detail="Resource not found")

    db.delete(resource)
    db.commit()

    return {"deleted": True, "id": resource_id}


# =============================================================================
# RESOURCE TYPES
# =============================================================================

@router.get("/types/list")
async def list_resource_types(
    current_user: dict = Depends(get_current_user)
):
    """
    Get list of valid resource types.
    """
    return {
        "types": [
            {"id": "doc", "name": "Document", "icon": "FileText"},
            {"id": "folder", "name": "Folder", "icon": "Folder"},
            {"id": "image", "name": "Image", "icon": "Image"},
            {"id": "link", "name": "Link", "icon": "Link"},
            {"id": "paper", "name": "Research Paper", "icon": "BookOpen"},
            {"id": "pdf", "name": "PDF", "icon": "FileText"},
            {"id": "slides", "name": "Slides", "icon": "Presentation"},
            {"id": "spreadsheet", "name": "Spreadsheet", "icon": "Table"},
            {"id": "video", "name": "Video", "icon": "Video"},
        ]
    }
