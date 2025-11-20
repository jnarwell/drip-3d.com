from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.property import PropertyDefinition, ComponentProperty, PropertyType
from app.models.component import Component
from app.models.formula_isolated import PropertyFormula
from app.services.formula_engine import FormulaEngine
from app.schemas.property import (
    PropertyDefinitionCreate,
    PropertyDefinitionResponse,
    ComponentPropertyCreate,
    ComponentPropertyUpdate,
    ComponentPropertyResponse
)

router = APIRouter(prefix="/api/v1")

# Property Definitions endpoints
@router.get("/property-definitions", response_model=List[PropertyDefinitionResponse])
async def get_property_definitions(
    property_type: PropertyType = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all property definitions, optionally filtered by type"""
    query = db.query(PropertyDefinition)
    if property_type:
        query = query.filter(PropertyDefinition.property_type == property_type)
    return query.all()


@router.post("/property-definitions", response_model=PropertyDefinitionResponse)
async def create_property_definition(
    property_def: PropertyDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom property definition"""
    db_property_def = PropertyDefinition(
        **property_def.dict(),
        created_by=current_user["email"]
    )
    db.add(db_property_def)
    db.commit()
    db.refresh(db_property_def)
    return db_property_def


# Component Properties endpoints
@router.get("/components/{component_id}/properties", response_model=List[ComponentPropertyResponse])
async def get_component_properties(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all properties for a specific component"""
    import logging
    logger = logging.getLogger(__name__)
    
    logger.info(f"🔍 Getting properties for component: {component_id}")
    
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    logger.info(f"📋 Component found: DB ID {component.id}, current material: {component.primary_material_id}")
    
    properties = db.query(ComponentProperty).filter(
        ComponentProperty.component_id == component.id
    ).all()
    
    logger.info(f"📊 Found {len(properties)} properties")
    # STEP 3A DEBUG: Temporarily removed detailed logging to fix 500 error
    
    return properties


@router.post("/components/{component_id}/properties", response_model=ComponentPropertyResponse)
async def add_component_property(
    component_id: str,
    property_data: ComponentPropertyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a property to a component"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    # Check if property definition exists
    property_def = db.query(PropertyDefinition).filter(
        PropertyDefinition.id == property_data.property_definition_id
    ).first()
    if not property_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property definition not found"
        )
    
    # Check if this property already exists for the component
    existing = db.query(ComponentProperty).filter(
        ComponentProperty.component_id == component.id,
        ComponentProperty.property_definition_id == property_data.property_definition_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property already exists for the component"
        )
    
    db_property = ComponentProperty(
        component_id=component.id,
        **property_data.dict(),
        updated_by=current_user["email"]
    )
    
    db.add(db_property)
    db.commit()
    db.refresh(db_property)
    return db_property


@router.patch("/components/{component_id}/properties/{property_id}", response_model=ComponentPropertyResponse)
async def update_component_property(
    component_id: str,
    property_id: int,
    property_update: ComponentPropertyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a component property value"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    update_data = property_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_value, field, value)
    
    property_value.updated_at = datetime.utcnow()
    property_value.updated_by = current_user["email"]
    
    db.commit()
    db.refresh(property_value)
    return property_value


@router.delete("/components/{component_id}/properties/{property_id}")
async def delete_component_property(
    component_id: str,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a component property"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    db.delete(property_value)
    db.commit()
    
    return {"status": "success", "message": "Property deleted"}


@router.post("/components/{component_id}/properties/{property_id}/calculate")
async def calculate_property_value(
    component_id: str,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate a property value using its formula"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    if not property_value.is_calculated or not property_value.formula_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property is not formula-based"
        )
    
    # Use formula engine to calculate
    engine = FormulaEngine(db)
    result = engine.calculate_property(property_value)
    
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Formula calculation failed: {result.error_message}"
        )
    
    # Update the property with calculated value
    engine._update_property_value(property_value, result)
    property_value.updated_by = current_user["email"]
    db.commit()
    db.refresh(property_value)
    
    return {
        "status": "success",
        "calculated_value": result.value,
        "input_values": result.input_values,
        "property": ComponentPropertyResponse.from_orm(property_value)
    }


@router.post("/components/{component_id}/properties/calculate-all")
async def calculate_all_properties(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate all formula-based properties for a component"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    # Get all formula-based properties
    formula_properties = db.query(ComponentProperty).filter(
        ComponentProperty.component_id == component.id,
        ComponentProperty.is_calculated == True,
        ComponentProperty.formula_id.isnot(None)
    ).all()
    
    if not formula_properties:
        return {"status": "success", "message": "No formula-based properties found", "calculated": 0}
    
    engine = FormulaEngine(db)
    results = []
    errors = []
    
    for prop in formula_properties:
        result = engine.calculate_property(prop)
        if result.success:
            engine._update_property_value(prop, result)
            prop.updated_by = current_user["email"]
            results.append({
                "property_id": prop.id,
                "property_name": prop.property_definition.name,
                "calculated_value": result.value
            })
        else:
            errors.append({
                "property_id": prop.id,
                "property_name": prop.property_definition.name,
                "error": result.error_message
            })
    
    db.commit()
    
    return {
        "status": "success",
        "calculated": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }