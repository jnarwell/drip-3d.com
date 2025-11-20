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
from app.models.formula import PropertyFormula
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
    
    logger.info(f"📊 Found {len(properties)} properties:")
    for prop in properties:
        notes_preview = (prop.notes[:50] + "...") if prop.notes else "None"
        logger.info(f"  - {prop.property_definition.name}: {prop.single_value} (ID: {prop.id}, inherited: {prop.inherited_from_material}, notes: '{notes_preview}')")
    
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


@router.post("/components/{component_id}/properties/{property_id}/set-formula")
async def set_property_formula(
    component_id: str,
    property_id: int,
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Set a property to use formula-based calculation"""
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
    
    formula = db.query(PropertyFormula).get(formula_id)
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Formula not found"
        )
    
    # Verify formula is for the same property definition
    if formula.property_definition_id != property_value.property_definition_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formula is not for this property type"
        )
    
    try:
        # Set property to use formula
        property_value.is_calculated = True
        property_value.formula_id = formula_id
        property_value.calculation_status = "pending"
        property_value.updated_by = current_user["email"]
        
        # Calculate initial value
        engine = FormulaEngine(db)
        calc_result = engine.calculate_property(property_value)
        
        if calc_result.success:
            # Update property with calculated value
            engine._update_property_value(property_value, calc_result)
            property_value.calculation_status = "calculated"
        else:
            property_value.calculation_status = "error"
            property_value.notes = f"Calculation error: {calc_result.error_message}"
        
        db.commit()
        db.refresh(property_value)
        
        return {
            "status": "success", 
            "message": "Formula set and calculated",
            "calculation_result": {
                "success": calc_result.success,
                "value": calc_result.value,
                "error": calc_result.error_message
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error setting formula: {str(e)}"
        )


@router.post("/components/{component_id}/properties/{property_id}/calculate")
async def calculate_property_value(
    component_id: str,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger calculation for a formula-based property"""
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
    
    try:
        engine = FormulaEngine(db)
        calc_result = engine.calculate_property(property_value)
        
        if calc_result.success:
            # Update property with calculated value
            engine._update_property_value(property_value, calc_result)
            property_value.calculation_status = "calculated"
        else:
            property_value.calculation_status = "error"
            property_value.notes = f"Calculation error: {calc_result.error_message}"
        
        property_value.updated_by = current_user["email"]
        db.commit()
        db.refresh(property_value)
        
        return {
            "status": "success",
            "calculation_result": {
                "success": calc_result.success,
                "value": calc_result.value,
                "error_message": calc_result.error_message,
                "input_values": calc_result.input_values,
                "calculation_time_ms": calc_result.calculation_time_ms
            }
        }
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating property: {str(e)}"
        )


@router.post("/components/{component_id}/properties/{property_id}/remove-formula")
async def remove_property_formula(
    component_id: str,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove formula from property and make it manually editable"""
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
    
    # Remove formula association
    property_value.is_calculated = False
    property_value.formula_id = None
    property_value.calculation_status = "manual"
    property_value.calculation_inputs = None
    property_value.last_calculated = None
    property_value.updated_by = current_user["email"]
    
    db.commit()
    
    return {"status": "success", "message": "Formula removed, property is now manually editable"}