"""API endpoints for Calculation Templates"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.resources import CalculationTemplate, TemplateType
from app.schemas.resources import (
    CalculationTemplate as CalculationTemplateSchema,
    CalculationTemplateCreate,
    CalculationTemplateUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/templates")


@router.get("/", response_model=List[CalculationTemplateSchema])
async def list_templates(
    template_type: Optional[TemplateType] = Query(None, description="Filter by template type"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    my_templates_only: bool = Query(False, description="Show only templates created by current user"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all calculation templates with optional filtering"""
    query = db.query(CalculationTemplate)
    
    if template_type:
        query = query.filter(CalculationTemplate.template_type == template_type)
    
    if my_templates_only:
        query = query.filter(CalculationTemplate.created_by == current_user["email"])
    else:
        # Show public templates or user's own templates
        query = query.filter(
            (CalculationTemplate.is_public == True) |
            (CalculationTemplate.created_by == current_user["email"])
        )
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (CalculationTemplate.name.ilike(search_pattern)) |
            (CalculationTemplate.description.ilike(search_pattern))
        )
    
    # Order by created_at descending
    query = query.order_by(CalculationTemplate.created_at.desc())
    
    total = query.count()
    templates = query.offset(skip).limit(limit).all()
    
    logger.info(f"User {current_user['email']} listed {len(templates)} templates (total: {total})")
    return templates


@router.get("/{template_id}", response_model=CalculationTemplateSchema)
async def get_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific template by ID"""
    template = db.query(CalculationTemplate).filter(CalculationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )
    
    # Check permissions
    if not template.is_public and template.created_by != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this template"
        )
    
    # Increment usage count
    template.usage_count = (template.usage_count or 0) + 1
    db.commit()
    
    return template


@router.post("/", response_model=CalculationTemplateSchema)
async def create_template(
    template_data: CalculationTemplateCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new calculation template"""
    # Validate template type
    if template_data.template_type == TemplateType.WORKFLOW:
        # For now, workflow templates are not supported
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Workflow templates are coming soon. Please create a property table template instead."
        )
    
    # Create template
    template = CalculationTemplate(
        **template_data.dict(exclude_unset=True),
        created_by=current_user["email"]
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    logger.info(f"User {current_user['email']} created template '{template.name}'")
    return template


@router.patch("/{template_id}", response_model=CalculationTemplateSchema)
async def update_template(
    template_id: int,
    template_update: CalculationTemplateUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a template (only by creator)"""
    template = db.query(CalculationTemplate).filter(CalculationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )
    
    # Check permissions
    if template.created_by != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can modify this template"
        )
    
    # Update fields
    update_data = template_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(template, field, value)
    
    db.commit()
    db.refresh(template)
    
    logger.info(f"User {current_user['email']} updated template '{template.name}'")
    return template


@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a template (only by creator)"""
    template = db.query(CalculationTemplate).filter(CalculationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )
    
    # Check permissions
    if template.created_by != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the creator can delete this template"
        )
    
    name = template.name
    db.delete(template)
    db.commit()
    
    logger.info(f"User {current_user['email']} deleted template '{name}'")
    return {"message": f"Template '{name}' deleted successfully"}


@router.post("/{template_id}/duplicate", response_model=CalculationTemplateSchema)
async def duplicate_template(
    template_id: int,
    new_name: str = Query(..., description="Name for the duplicated template"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Duplicate an existing template"""
    template = db.query(CalculationTemplate).filter(CalculationTemplate.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Template with id {template_id} not found"
        )
    
    # Check permissions
    if not template.is_public and template.created_by != current_user["email"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to duplicate this template"
        )
    
    # Create duplicate
    new_template = CalculationTemplate(
        name=new_name,
        description=f"Copy of: {template.description}" if template.description else None,
        template_type=template.template_type,
        table_structure=template.table_structure,
        calculation_steps=template.calculation_steps,
        created_by=current_user["email"],
        is_public=False  # Duplicates start as private
    )
    
    db.add(new_template)
    db.commit()
    db.refresh(new_template)
    
    logger.info(f"User {current_user['email']} duplicated template '{template.name}' as '{new_name}'")
    return new_template