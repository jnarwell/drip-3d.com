from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.db.database import get_db
import os
import re

logger = logging.getLogger(__name__)
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

# Import models for variable discovery
from app.models.property import PropertyDefinition, ComponentProperty, UnitSystem
from app.models.component import Component  
from app.models.resources import SystemConstant
from app.models.material import Material, MaterialProperty

router = APIRouter(prefix="/api/v1")

class VariableReference:
    """Data structure for variable references across the system"""
    def __init__(self, 
                 id: str,           # Unique reference ID like "comp_001.prop_thermal_conductivity"
                 display_name: str, # Human readable name
                 value: Any,        # Current value
                 unit: str,         # Unit of measurement
                 type: str,         # "component_property", "system_constant", "material_property" 
                 source: str,       # Source table/location
                 description: Optional[str] = None):
        self.id = id
        self.display_name = display_name  
        self.value = value
        self.unit = unit
        self.type = type
        self.source = source
        self.description = description

    def to_dict(self):
        return {
            "id": self.id,
            "display_name": self.display_name,
            "value": self.value,
            "unit": self.unit,
            "type": self.type,
            "source": self.source,
            "description": self.description
        }

@router.get("/variables/search")
async def search_variables(
    query: Optional[str] = Query(None, description="Search term for filtering variables"),
    type_filter: Optional[str] = Query(None, description="Filter by variable type: component_property, system_constant, material_property"),
    component_id: Optional[str] = Query(None, description="Filter by specific component"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for all available variables across the system.
    This enables the #prefix variable reference system.
    """
    variables = []
    
    try:
        # 1. Component Properties - format: comp_{component_id}.{property_name}
        if not type_filter or type_filter == "component_property":
            component_properties_query = (
                db.query(ComponentProperty, Component, PropertyDefinition)
                .join(Component, ComponentProperty.component_id == Component.id)
                .join(PropertyDefinition, ComponentProperty.property_definition_id == PropertyDefinition.id)
            )
            
            if component_id:
                component_properties_query = component_properties_query.filter(
                    Component.component_id == component_id
                )
                
            component_properties = component_properties_query.all()
            
            for prop, component, prop_def in component_properties:
                # Determine the current value
                current_value = None
                if prop.single_value is not None:
                    current_value = prop.single_value
                elif prop.average_value is not None:
                    current_value = prop.average_value
                elif prop.min_value is not None and prop.max_value is not None:
                    current_value = f"{prop.min_value}-{prop.max_value}"
                
                # Simplify component ID: CMP-001 -> cmp1
                comp_id = component.component_id.lower().replace('cmp-', 'cmp')
                # Convert property name to camelCase: "Young's Modulus" -> "youngsModulus"
                prop_name = ''.join(word.capitalize() if i > 0 else word.lower() 
                                   for i, word in enumerate(prop_def.name.split()))
                variable_id = f"{comp_id}.{prop_name}"
                display_name = f"{component.name} → {prop_def.name}"
                
                # Apply search filter
                if not query or query.lower() in display_name.lower() or query.lower() in variable_id.lower():
                    variables.append(VariableReference(
                        id=variable_id,
                        display_name=display_name,
                        value=current_value,
                        unit=prop_def.unit,
                        type="component_property",
                        source=f"components.{component.component_id}.properties.{prop_def.name}",
                        description=prop_def.description
                    ))
        
        # 2. System Constants - format: const_{symbol}
        if not type_filter or type_filter == "system_constant":
            constants = db.query(SystemConstant).all()
            
            for constant in constants:
                # Simplify constant: const_G -> g
                variable_id = constant.symbol.lower()
                display_name = f"{constant.symbol} ({constant.name})"
                
                # Apply search filter  
                if not query or query.lower() in display_name.lower() or query.lower() in variable_id.lower():
                    variables.append(VariableReference(
                        id=variable_id,
                        display_name=display_name,
                        value=constant.value,
                        unit=constant.unit or "",
                        type="system_constant", 
                        source=f"system_constants.{constant.symbol}",
                        description=constant.description
                    ))
        
        # 3. Material Properties - format: mat_{material_name}.{property_name}
        if not type_filter or type_filter == "material_property":
            material_properties = (
                db.query(MaterialProperty, Material, PropertyDefinition)
                .join(Material, MaterialProperty.material_id == Material.id)
                .join(PropertyDefinition, MaterialProperty.property_definition_id == PropertyDefinition.id)
                .all()
            )
            
            for mat_prop, material, prop_def in material_properties:
                # Determine the current value
                current_value = None
                if mat_prop.value is not None:
                    current_value = mat_prop.value
                elif mat_prop.value_min is not None and mat_prop.value_max is not None:
                    current_value = f"{mat_prop.value_min}-{mat_prop.value_max}"
                
                # Simplify material name and property: mat_steel -> steel, Young's Modulus -> youngsModulus
                mat_name = material.name.lower().replace(' ', '')
                prop_name = ''.join(word.capitalize() if i > 0 else word.lower() 
                                   for i, word in enumerate(prop_def.name.split()))
                variable_id = f"{mat_name}.{prop_name}"
                display_name = f"{material.name} → {prop_def.name}"
                
                # Apply search filter
                if not query or query.lower() in display_name.lower() or query.lower() in variable_id.lower():
                    variables.append(VariableReference(
                        id=variable_id,
                        display_name=display_name,
                        value=current_value,
                        unit=prop_def.unit,
                        type="material_property",
                        source=f"materials.{material.name}.properties.{prop_def.name}",
                        description=prop_def.description
                    ))
        
        # Sort by display name for consistent ordering
        variables.sort(key=lambda x: x.display_name)
        
        return {
            "variables": [var.to_dict() for var in variables],
            "total_count": len(variables),
            "search_query": query,
            "type_filter": type_filter,
            "component_filter": component_id
        }
        
    except Exception as e:
        import logging
        logging.error(f"❌ Error in variable search: {e}")
        raise HTTPException(status_code=500, detail=f"Error searching variables: {str(e)}")


@router.get("/variables/resolve/{variable_id}")
async def resolve_variable(
    variable_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve a specific variable ID to get its current value and metadata.
    Used when evaluating formulas that reference other variables.
    """
    try:
        # Parse the variable ID format
        if variable_id.startswith("cmp"):
            # Component property format: cmp1.length or cmp10.width
            parts = variable_id.split(".", 1)
            if len(parts) != 2:
                raise HTTPException(status_code=400, detail="Invalid component property variable format")
            
            # Extract component number: cmp1 -> CMP-001
            comp_match = re.match(r'cmp(\d+)', parts[0])
            if not comp_match:
                raise HTTPException(status_code=400, detail="Invalid component ID format")
            
            comp_num = comp_match.group(1).zfill(3)
            component_id = f"CMP-{comp_num}"
            
            # Convert camelCase to spaces: youngsModulus -> Young's Modulus
            property_name = parts[1]
            # Add space before capital letters
            property_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', property_name)
            property_name = property_name.capitalize()
            
            # Find the component property
            component_property = (
                db.query(ComponentProperty, Component, PropertyDefinition)
                .join(Component, ComponentProperty.component_id == Component.id)
                .join(PropertyDefinition, ComponentProperty.property_definition_id == PropertyDefinition.id)
                .filter(Component.component_id == component_id)
                .filter(PropertyDefinition.name.ilike(property_name))
                .first()
            )
            
            if not component_property:
                raise HTTPException(status_code=404, detail=f"Component property not found: {variable_id}")
                
            prop, component, prop_def = component_property
            
            # Get current value
            current_value = None
            if prop.single_value is not None:
                current_value = prop.single_value
            elif prop.average_value is not None:
                current_value = prop.average_value
            elif prop.min_value is not None and prop.max_value is not None:
                current_value = f"{prop.min_value}-{prop.max_value}"
            
            return {
                "variable_id": variable_id,
                "value": current_value,
                "unit": prop_def.unit,
                "type": "component_property",
                "source": f"components.{component.component_id}.properties.{prop_def.name}",
                "last_updated": prop.updated_at.isoformat() if prop.updated_at else None,
                "is_calculated": prop.is_calculated,
                "calculation_status": prop.calculation_status
            }
            
        elif variable_id in [const.symbol.lower() for const in db.query(SystemConstant).all()]:
            # System constant format: just the symbol in lowercase (e.g., "g", "pi")
            symbol = variable_id.upper()
            
            constant = db.query(SystemConstant).filter(SystemConstant.symbol == symbol).first()
            if not constant:
                raise HTTPException(status_code=404, detail=f"System constant not found: {symbol}")
            
            return {
                "variable_id": variable_id,
                "value": constant.value,
                "unit": constant.unit or "",
                "type": "system_constant",
                "source": f"system_constants.{constant.symbol}",
                "description": constant.description,
                "category": constant.category
            }
            
        else:
            # Try material property format: materialName.propertyName
            parts = variable_id.split(".", 1)
            if len(parts) == 2:
                material_name = parts[0]
                property_name = parts[1]
                
                # Convert camelCase to spaces
                property_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', property_name)
                property_name = property_name.capitalize()
                
                # Find the material property
                material_property = (
                    db.query(MaterialProperty, Material, PropertyDefinition)
                    .join(Material, MaterialProperty.material_id == Material.id)
                    .join(PropertyDefinition, MaterialProperty.property_definition_id == PropertyDefinition.id)
                    .filter(Material.name.ilike(material_name))
                    .filter(PropertyDefinition.name.ilike(property_name))
                    .first()
                )
                
                if not material_property:
                    raise HTTPException(status_code=404, detail=f"Material property not found: {variable_id}")
                    
                mat_prop, material, prop_def = material_property
                
                # Get current value
                current_value = None
                if mat_prop.value is not None:
                    current_value = mat_prop.value
                elif mat_prop.value_min is not None and mat_prop.value_max is not None:
                    current_value = f"{mat_prop.value_min}-{mat_prop.value_max}"
                
                return {
                    "variable_id": variable_id,
                    "value": current_value,
                    "unit": prop_def.unit,
                    "type": "material_property",
                    "source": f"materials.{material.name}.properties.{prop_def.name}",
                    "last_updated": mat_prop.updated_at.isoformat() if mat_prop.updated_at else None
                }
            else:
                raise HTTPException(status_code=400, detail=f"Unknown variable format: {variable_id}")
            
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"❌ Error resolving variable {variable_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error resolving variable: {str(e)}")


@router.get("/variables/component/{component_id}")
async def get_component_variables(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all variables available for a specific component.
    This includes the component's own properties and all system constants.
    """
    try:
        variables = []
        
        # Get component's own properties
        component = db.query(Component).filter(Component.component_id == component_id).first()
        if not component:
            raise HTTPException(status_code=404, detail=f"Component {component_id} not found")
        
        component_properties = (
            db.query(ComponentProperty, PropertyDefinition)
            .join(PropertyDefinition, ComponentProperty.property_definition_id == PropertyDefinition.id)
            .filter(ComponentProperty.component_id == component.id)
            .all()
        )
        
        for prop, prop_def in component_properties:
            current_value = None
            if prop.single_value is not None:
                current_value = prop.single_value
            elif prop.average_value is not None:
                current_value = prop.average_value
                
            # Simplify component ID: CMP-001 -> cmp1
            comp_id = component.component_id.lower().replace('cmp-', 'cmp')
            # Convert property name to camelCase: "Young's Modulus" -> "youngsModulus"
            prop_name = ''.join(word.capitalize() if i > 0 else word.lower() 
                               for i, word in enumerate(prop_def.name.split()))
            variable_id = f"{comp_id}.{prop_name}"
            variables.append({
                "id": variable_id,
                "display_name": prop_def.name,
                "value": current_value,
                "unit": prop_def.unit,
                "type": "component_property",
                "source": f"components.{component.component_id}.properties.{prop_def.name}",
                "description": prop_def.description,
                "is_calculated": prop.is_calculated,
                "calculation_status": prop.calculation_status
            })
        
        # Add all system constants
        constants = db.query(SystemConstant).all()
        for constant in constants:
            variable_id = f"const_{constant.symbol.lower()}"
            variables.append({
                "id": variable_id,
                "display_name": f"{constant.symbol} ({constant.name})",
                "value": constant.value,
                "unit": constant.unit or "",
                "type": "system_constant",
                "source": f"system_constants.{constant.symbol}",
                "description": constant.description,
                "category": constant.category
            })
        
        # Sort by type then name
        variables.sort(key=lambda x: (x["type"], x["display_name"]))
        
        return {
            "component_id": component_id,
            "variables": variables,
            "total_count": len(variables)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import logging
        logging.error(f"❌ Error getting component variables: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting component variables: {str(e)}")