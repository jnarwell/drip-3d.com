from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.component import Component, ComponentStatus, ComponentCategory
from app.models.audit import AuditLog
from app.models.user import User
from app.schemas.component import ComponentCreate, ComponentUpdate, ComponentResponse, ComponentStatusUpdate
from app.services.linear import LinearService

router = APIRouter(prefix="/api/v1/components")

@router.get("/", response_model=List[ComponentResponse])
async def get_components(
    category: Optional[ComponentCategory] = Query(None),
    status: Optional[ComponentStatus] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get filtered list of components"""
    query = db.query(Component)
    
    if category:
        query = query.filter(Component.category == category)
    if status:
        query = query.filter(Component.status == status)
    if search:
        query = query.filter(
            Component.name.ilike(f"%{search}%") | 
            Component.component_id.ilike(f"%{search}%") |
            Component.part_number.ilike(f"%{search}%")
        )
    
    total = query.count()
    components = query.offset(skip).limit(limit).all()
    
    return components

@router.get("/{component_id}", response_model=ComponentResponse)
async def get_component(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific component by ID"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    return component

@router.post("/", response_model=ComponentResponse)
async def create_component(
    component: ComponentCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new component"""
    # Generate component ID
    count = db.query(Component).count()
    component_id = f"CMP-{str(count + 1).zfill(3)}"
    
    # Check if component_id already exists (in case of race condition)
    while db.query(Component).filter(Component.component_id == component_id).first():
        count += 1
        component_id = f"CMP-{str(count + 1).zfill(3)}"
    
    db_component = Component(
        component_id=component_id,
        **component.dict(),
        updated_by=current_user["email"]
    )
    db.add(db_component)
    
    # Create audit log
    audit = AuditLog(
        entity_type="component",
        entity_id=component_id,
        action="created",
        user=current_user["email"],
        details=component.dict()
    )
    db.add(audit)
    
    db.commit()
    db.refresh(db_component)
    
    return db_component

@router.patch("/{component_id}", response_model=ComponentResponse)
async def update_component(
    component_id: str,
    component_update: ComponentUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update component"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    update_data = component_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(component, field, value)
    
    component.updated_at = datetime.utcnow()
    component.updated_by = current_user["email"]
    
    # Create audit log
    audit = AuditLog(
        entity_type="component",
        entity_id=component_id,
        action="updated",
        user=current_user["email"],
        details=update_data
    )
    db.add(audit)
    
    db.commit()
    db.refresh(component)
    
    return component

@router.patch("/{component_id}/status")
async def update_component_status(
    component_id: str,
    status_update: ComponentStatusUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update component verification status"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    old_status = component.status
    component.status = status_update.status
    component.updated_by = current_user["email"]
    component.updated_at = datetime.utcnow()
    
    # Create audit log
    audit = AuditLog(
        entity_type="component",
        entity_id=component_id,
        action=f"Status changed from {old_status} to {status_update.status}",
        user=current_user["email"],
        details={
            "old_status": old_status,
            "new_status": status_update.status,
            "notes": status_update.notes
        }
    )
    db.add(audit)
    
    # Sync to Linear if requested
    if status_update.sync_to_linear:
        from app.core.config import settings
        linear = LinearService(settings.LINEAR_API_KEY)
        # This would be implemented based on Linear API integration
        # await linear.sync_component_status(component)
    
    db.commit()
    
    return {"status": "success", "component_id": component_id, "new_status": component.status}

@router.delete("/{component_id}")
async def delete_component(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete component (admin only)"""
    # Check if user is admin (skip in dev mode)
    if os.getenv("DEV_MODE") != "true":
        user = db.query(User).filter(User.email == current_user["email"]).first()
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete components"
            )
    
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    # Create audit log before deletion
    audit = AuditLog(
        entity_type="component",
        entity_id=component_id,
        action="deleted",
        user=current_user["email"],
        details={"component_name": component.name}
    )
    db.add(audit)
    
    db.delete(component)
    db.commit()
    
    return {"status": "success", "message": f"Component {component_id} deleted"}