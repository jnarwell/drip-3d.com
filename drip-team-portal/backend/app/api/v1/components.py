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
from app.services.material_property_manager import MaterialPropertyManager

router = APIRouter(prefix="/api/v1/components")
material_manager = MaterialPropertyManager()

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
    """Delete component"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    # Clean up all foreign key references before deletion (v3 - 2026-01-04)
    from app.models.time_entry import TimeEntry
    from app.models.test import TestResult  # Note: Test model has no component_id
    from app.models.test_protocol import TestRun
    from app.models.physics_model import ModelInstance
    from app.models.material import component_materials
    from app.models.resources import resource_components

    # Set component_id to NULL for related records (preserve data)
    db.query(TimeEntry).filter(TimeEntry.component_id == component.id).update({"component_id": None})
    db.query(TestResult).filter(TestResult.component_id == component.id).update({"component_id": None})
    db.query(TestRun).filter(TestRun.component_id == component.id).update({"component_id": None})
    db.query(ModelInstance).filter(ModelInstance.component_id == component.id).update({"component_id": None})

    # Delete from association tables (many-to-many relationships)
    db.execute(component_materials.delete().where(component_materials.c.component_id == component.id))
    db.execute(resource_components.delete().where(resource_components.c.component_id == component.id))

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

@router.put("/{component_id}/material")
async def change_component_material(
    component_id: str,
    material_id: Optional[int] = Query(None, description="New material ID, or null to clear material"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Change the material of a component and update all inherited properties"""
    # Find component by component_id string
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    try:
        # Use the component's database ID for the material manager
        result = material_manager.change_component_material(
            db=db,
            component_id=component.id,
            new_material_id=material_id,
            user_email=current_user["email"]
        )

        # Create audit log
        audit = AuditLog(
            entity_type="component",
            entity_id=component_id,
            action="material_changed",
            user=current_user["email"],
            details={
                "previous_material_id": result["previous_material_id"],
                "new_material_id": result["new_material_id"],
                "properties_removed": len(result["properties_removed"]),
                "properties_added": len(result["properties_added"])
            }
        )
        db.add(audit)
        db.commit()

        return {
            "status": "success",
            "component_id": component_id,
            "changes": result
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # Catch any other exceptions to ensure proper error response with CORS headers
        import logging
        logging.error(f"Error changing material for component {component_id}: {e}", exc_info=True)
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change material: {str(e)}"
        )