from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.material import Material, MaterialProperty, component_materials
from app.models.component import Component
from app.models.property import ComponentProperty, PropertyDefinition
from app.schemas.material import MaterialResponse, MaterialPropertyValue, ComponentMaterialAdd, ComponentMaterialResponse

router = APIRouter(prefix="/api/v1")

# Material endpoints
@router.get("/materials", response_model=List[MaterialResponse])
async def get_materials(
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all materials, optionally filtered"""
    query = db.query(Material)
    
    if category:
        query = query.filter(Material.category == category)
    
    if search:
        query = query.filter(
            Material.name.ilike(f"%{search}%") |
            Material.uns_number.ilike(f"%{search}%") |
            Material.astm_grade.ilike(f"%{search}%")
        )
    
    # Use eager loading to avoid N+1 query problem
    from sqlalchemy.orm import joinedload
    materials = query.options(
        joinedload(Material.property_values).joinedload(MaterialProperty.property_definition)
    ).all()
    
    # Add property values (now efficiently loaded)
    for material in materials:
        material.properties = []
        for mat_prop in material.property_values:
            prop_def = mat_prop.property_definition
            material.properties.append(MaterialPropertyValue(
                property_name=prop_def.name,
                value=mat_prop.value,
                value_min=mat_prop.value_min,
                value_max=mat_prop.value_max,
                unit=prop_def.unit,
                temperature=mat_prop.temperature,
                conditions=mat_prop.conditions
            ))
    
    return materials


@router.get("/materials/{material_id}", response_model=MaterialResponse)
async def get_material(
    material_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific material with all properties"""
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Add property values
    material.properties = []
    for mat_prop in material.property_values:
        prop_def = mat_prop.property_definition
        material.properties.append(MaterialPropertyValue(
            property_name=prop_def.name,
            value=mat_prop.value,
            value_min=mat_prop.value_min,
            value_max=mat_prop.value_max,
            unit=prop_def.unit,
            temperature=mat_prop.temperature,
            conditions=mat_prop.conditions
        ))
    
    return material


# Component material endpoints
@router.post("/components/{component_id}/material")
async def set_component_material(
    component_id: str,
    material_data: ComponentMaterialAdd,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Set primary material for a component and auto-add material properties"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    material = db.query(Material).filter(Material.id == material_data.material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    # Set as primary material
    component.primary_material_id = material.id
    
    # Add to materials relationship if not already there
    if material not in component.materials:
        component.materials.append(material)
    
    # Auto-add material properties to component
    added_properties = []
    for mat_prop in material.property_values:
        # Check if this property already exists for the component
        existing = db.query(ComponentProperty).filter(
            ComponentProperty.component_id == component.id,
            ComponentProperty.property_definition_id == mat_prop.property_definition_id
        ).first()
        
        if not existing:
            # Create component property from material property
            comp_prop = ComponentProperty(
                component_id=component.id,
                property_definition_id=mat_prop.property_definition_id,
                single_value=mat_prop.value,
                min_value=mat_prop.value_min,
                max_value=mat_prop.value_max,
                notes=f"From material: {material.name}",
                source=mat_prop.source or material.data_source,
                conditions=mat_prop.conditions,
                updated_by=current_user["email"]
            )
            db.add(comp_prop)
            added_properties.append(mat_prop.property_definition.name)
    
    db.commit()
    
    return {
        "status": "success",
        "material": material.name,
        "properties_added": added_properties
    }


@router.get("/components/{component_id}/materials", response_model=List[ComponentMaterialResponse])
async def get_component_materials(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all materials for a component with inherited properties"""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    result = []
    
    # Include primary material
    if component.primary_material:
        material = component.primary_material
        
        # Get inherited properties
        inherited_props = []
        for mat_prop in material.property_values:
            # Check if this property is overridden at component level
            comp_prop = db.query(ComponentProperty).filter(
                ComponentProperty.component_id == component.id,
                ComponentProperty.property_definition_id == mat_prop.property_definition_id
            ).first()
            
            if comp_prop and comp_prop.notes and "From material:" not in comp_prop.notes:
                # Property has been manually overridden
                continue
            
            prop_def = mat_prop.property_definition
            inherited_props.append(MaterialPropertyValue(
                property_name=prop_def.name,
                value=mat_prop.value,
                value_min=mat_prop.value_min,
                value_max=mat_prop.value_max,
                unit=prop_def.unit,
                temperature=mat_prop.temperature,
                conditions=mat_prop.conditions
            ))
        
        # Prepare material response
        material.properties = []
        for mat_prop in material.property_values:
            prop_def = mat_prop.property_definition
            material.properties.append(MaterialPropertyValue(
                property_name=prop_def.name,
                value=mat_prop.value,
                value_min=mat_prop.value_min,
                value_max=mat_prop.value_max,
                unit=prop_def.unit,
                temperature=mat_prop.temperature,
                conditions=mat_prop.conditions
            ))
        
        result.append(ComponentMaterialResponse(
            material=material,
            percentage=100.0,
            notes="Primary material",
            inherited_properties=inherited_props
        ))
    
    return result


@router.delete("/components/{component_id}/material/{material_id}")
async def remove_component_material(
    component_id: str,
    material_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Remove material from component and its auto-generated properties"""
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"🗑️ Removing material {material_id} from component {component_id}")
    
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )
    
    material = db.query(Material).filter(Material.id == material_id).first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found"
        )
    
    logger.info(f"📋 Component: {component.component_id}, Material: {material.name}, Current properties: {len(component.properties)}")
    
    # Remove all inherited properties (both old and new patterns)
    removed_properties = []
    
    # Get properties that are properly marked as inherited
    inherited_props = [prop for prop in component.properties if prop.inherited_from_material]
    
    # Also get legacy properties with old patterns
    legacy_props = [prop for prop in component.properties 
                   if prop.notes and (
                       "From material:" in prop.notes or 
                       "Inherited from material:" in prop.notes
                   )]
    
    # Combine and remove duplicates
    all_props_to_remove = {prop.id: prop for prop in inherited_props + legacy_props}.values()
    logger.info(f"🔍 Found {len(inherited_props)} properly tracked + {len(legacy_props)} legacy inherited properties = {len(list(all_props_to_remove))} total to remove")
    
    for prop in all_props_to_remove:
        notes_preview = (prop.notes[:50] + "...") if prop.notes else "None"
        logger.info(f"❌ Removing property: {prop.property_definition.name} = {prop.single_value} (ID: {prop.id}, inherited: {prop.inherited_from_material}, notes: '{notes_preview}')")
        removed_properties.append(prop.property_definition.name)
        db.delete(prop)
    
    # Remove primary material reference if it matches
    if component.primary_material_id == material_id:
        component.primary_material_id = None
    
    # Remove from materials relationship
    if material in component.materials:
        component.materials.remove(material)
    
    logger.info("💾 Committing material removal changes...")
    db.commit()
    logger.info(f"✅ Material removal completed! Removed {len(removed_properties)} properties: {removed_properties}")
    
    return {
        "status": "success",
        "message": "Material removed from component",
        "properties_removed": removed_properties
    }