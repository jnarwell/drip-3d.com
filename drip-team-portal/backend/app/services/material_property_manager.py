"""Service for managing material property inheritance on components"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging

from app.models.component import Component
from app.models.material import Material, MaterialProperty
from app.models.property import ComponentProperty, PropertyDefinition, PropertyType
from app.services.alloy_standards import AlloyStandardsService

logger = logging.getLogger(__name__)

class MaterialPropertyManager:
    """Manages the inheritance of material properties to components"""
    
    def __init__(self):
        self.standards_service = AlloyStandardsService()
    
    def change_component_material(
        self, 
        db: Session, 
        component_id: int, 
        new_material_id: Optional[int],
        user_email: str
    ) -> Dict[str, Any]:
        """
        Changes a component's material and updates all inherited properties
        
        Process:
        1. Find all properties that were inherited from the previous material
        2. Delete those properties
        3. If a new material is selected, add its properties to the component
        """
        logger.info(f"🔄 Starting material change for component {component_id}: {new_material_id}")
        
        # Get the component
        component = db.query(Component).filter(Component.id == component_id).first()
        if not component:
            raise ValueError(f"Component {component_id} not found")
        
        logger.info(f"📋 Component found: {component.component_id}, current material: {component.primary_material_id}")
        
        # Track changes for response
        changes = {
            "component_id": component_id,
            "previous_material_id": component.primary_material_id,
            "new_material_id": new_material_id,
            "properties_removed": [],
            "properties_added": []
        }
        
        # Step 1: Remove all properties inherited from any previous material
        logger.info("🗑️  Looking for properties to remove...")
        
        # Remove properly tracked inherited properties
        inherited_props = db.query(ComponentProperty).filter(
            and_(
                ComponentProperty.component_id == component_id,
                ComponentProperty.inherited_from_material == True
            )
        ).all()
        logger.info(f"📊 Found {len(inherited_props)} properly tracked inherited properties")
        
        # Also remove ANY legacy properties that have "From material:" or "Inherited from material:" in notes
        # This handles old properties that weren't properly marked as inherited
        legacy_inherited_props = db.query(ComponentProperty).filter(
            and_(
                ComponentProperty.component_id == component_id,
                ComponentProperty.notes.ilike("%From material:%").self_group() |
                ComponentProperty.notes.ilike("%Inherited from material:%").self_group()
            )
        ).all()
        logger.info(f"📊 Found {len(legacy_inherited_props)} legacy inherited properties")
        
        # Combine both lists and remove duplicates
        all_props_to_remove = {prop.id: prop for prop in inherited_props + legacy_inherited_props}.values()
        logger.info(f"🗑️  Total properties to remove: {len(list(all_props_to_remove))}")
        
        for prop in all_props_to_remove:
            prop_def = prop.property_definition
            notes_preview = (prop.notes[:50] + "...") if prop.notes else "None"
            logger.info(f"❌ Removing property: {prop_def.name} = {prop.single_value} {prop_def.unit} (ID: {prop.id}, inherited: {prop.inherited_from_material}, notes: '{notes_preview}')")
            changes["properties_removed"].append({
                "name": prop_def.name,
                "value": prop.single_value,
                "unit": prop_def.unit
            })
            db.delete(prop)
        
        # Step 2: Update the component's material
        logger.info(f"🔄 Updating component material from {component.primary_material_id} to {new_material_id}")
        component.primary_material_id = new_material_id
        
        # Step 3: If new material is set, inherit its properties
        if new_material_id:
            new_material = db.query(Material).filter(Material.id == new_material_id).first()
            if not new_material:
                raise ValueError(f"Material {new_material_id} not found")
            
            logger.info(f"➕ Adding properties from material: {new_material.name}")
            # Add properties from the material
            changes["properties_added"] = self._add_material_properties_to_component(
                db, component, new_material, user_email
            )
            logger.info(f"✅ Added {len(changes['properties_added'])} new properties")
        
        # Commit changes
        logger.info("💾 Committing database changes...")
        db.commit()
        logger.info("✅ Database commit completed")
        
        logger.info(f"🎉 Material change completed! Removed: {len(changes['properties_removed'])}, Added: {len(changes['properties_added'])}")
        return changes
    
    def _add_material_properties_to_component(
        self, 
        db: Session, 
        component: Component, 
        material: Material,
        user_email: str
    ) -> List[Dict[str, Any]]:
        """Add material properties to a component"""
        properties_added = []
        
        # Get material properties from database
        material_props = db.query(MaterialProperty).filter(
            MaterialProperty.material_id == material.id
        ).all()
        
        for mat_prop in material_props:
            prop_def = mat_prop.property_definition
            
            # Check if component already has this property (user-defined)
            existing = db.query(ComponentProperty).filter(
                and_(
                    ComponentProperty.component_id == component.id,
                    ComponentProperty.property_definition_id == prop_def.id,
                    ComponentProperty.inherited_from_material == False
                )
            ).first()
            
            if not existing:
                # Add the property to the component
                comp_prop = ComponentProperty(
                    component_id=component.id,
                    property_definition_id=prop_def.id,
                    single_value=mat_prop.value,
                    min_value=mat_prop.value_min,
                    max_value=mat_prop.value_max,
                    notes=f"Inherited from material: {material.name}",
                    source=mat_prop.source or "Material Database",
                    conditions=mat_prop.conditions,
                    updated_by=user_email,
                    inherited_from_material=True,
                    source_material_id=material.id
                )
                db.add(comp_prop)
                
                properties_added.append({
                    "name": prop_def.name,
                    "value": mat_prop.value,
                    "unit": prop_def.unit
                })
        
        # Also check if material has standard properties from alloy database
        # Only add from standards if the material doesn't already have MaterialProperty records
        if material.mp_id and material.mp_id.startswith("std-") and not material_props:
            mp_id_part = material.mp_id.replace("std-", "")
            
            # Handle specific category-code format (e.g., "stainless_steel-304")
            if "-" in mp_id_part and not mp_id_part.replace("-", "").isdigit():
                category, alloy_code = mp_id_part.split("-", 1)
                # Get the specific variant from the category
                if category in self.standards_service.standards_data:
                    if alloy_code in self.standards_service.standards_data[category]:
                        standard_data = self.standards_service.standards_data[category][alloy_code]
                    else:
                        standard_data = None
                else:
                    standard_data = None
            else:
                # Fallback to general lookup for simple codes
                alloy_code = mp_id_part
                standard_data = self.standards_service.get_alloy_standard(alloy_code)
            
            if standard_data:
                # Add thermal properties
                if standard_data.get("thermal"):
                    properties_added.extend(
                        self._add_standard_thermal_properties(
                            db, component, material, standard_data["thermal"], user_email
                        )
                    )
                
                # Add mechanical properties
                if standard_data.get("mechanical"):
                    properties_added.extend(
                        self._add_standard_mechanical_properties(
                            db, component, material, standard_data["mechanical"], user_email
                        )
                    )
                
                # Add acoustic properties
                if standard_data.get("acoustic"):
                    properties_added.extend(
                        self._add_standard_acoustic_properties(
                            db, component, material, standard_data["acoustic"], user_email
                        )
                    )
        
        return properties_added
    
    def _add_standard_thermal_properties(
        self, db: Session, component: Component, material: Material, 
        thermal_data: Dict[str, Any], user_email: str
    ) -> List[Dict[str, Any]]:
        """Add thermal properties from standards database"""
        properties_added = []
        
        property_mapping = {
            "melting_point": ("Melting Point", "°C", PropertyType.THERMAL),
            "thermal_conductivity": ("Thermal Conductivity", "W/m·K", PropertyType.THERMAL),
            "specific_heat": ("Specific Heat Capacity", "J/kg·K", PropertyType.THERMAL),
            "solidus": ("Solidus Temperature", "°C", PropertyType.THERMAL),
            "liquidus": ("Liquidus Temperature", "°C", PropertyType.THERMAL),
            "thermal_expansion": ("Thermal Expansion Coefficient", "1/K", PropertyType.THERMAL)
        }
        
        for key, (prop_name, unit, prop_type) in property_mapping.items():
            if key in thermal_data:
                # Get or create property definition
                prop_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == prop_name
                ).first()
                
                if not prop_def:
                    prop_def = PropertyDefinition(
                        name=prop_name,
                        property_type=prop_type,
                        unit=unit,
                        description=f"{prop_name} of the material",
                        created_by=user_email
                    )
                    db.add(prop_def)
                    db.flush()
                
                # Check if property already exists
                existing = db.query(ComponentProperty).filter(
                    and_(
                        ComponentProperty.component_id == component.id,
                        ComponentProperty.property_definition_id == prop_def.id
                    )
                ).first()
                
                if not existing:
                    comp_prop = ComponentProperty(
                        component_id=component.id,
                        property_definition_id=prop_def.id,
                        single_value=thermal_data[key],
                        notes=f"From standard: {material.name}",
                        source="Alloy Standards Database",
                        updated_by=user_email,
                        inherited_from_material=True,
                        source_material_id=material.id
                    )
                    db.add(comp_prop)
                    
                    properties_added.append({
                        "name": prop_name,
                        "value": thermal_data[key],
                        "unit": unit
                    })
        
        return properties_added
    
    def _add_standard_mechanical_properties(
        self, db: Session, component: Component, material: Material, 
        mechanical_data: Dict[str, Any], user_email: str
    ) -> List[Dict[str, Any]]:
        """Add mechanical properties from standards database"""
        properties_added = []
        
        property_mapping = {
            "density": ("Density", "g/cm³", PropertyType.PHYSICAL),
            "yield_strength": ("Yield Strength", "MPa", PropertyType.MECHANICAL),
            "ultimate_tensile_strength": ("Ultimate Tensile Strength", "MPa", PropertyType.MECHANICAL),
            "elongation": ("Elongation at Break", "%", PropertyType.MECHANICAL),
            "youngs_modulus": ("Young's Modulus", "GPa", PropertyType.MECHANICAL),
            "shear_modulus": ("Shear Modulus", "GPa", PropertyType.MECHANICAL),
            "poisson_ratio": ("Poisson's Ratio", "", PropertyType.MECHANICAL),
            "brinell_hardness": ("Brinell Hardness", "HB", PropertyType.MECHANICAL)
        }
        
        for key, (prop_name, unit, prop_type) in property_mapping.items():
            if key in mechanical_data:
                # Get or create property definition
                prop_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == prop_name
                ).first()
                
                if not prop_def:
                    prop_def = PropertyDefinition(
                        name=prop_name,
                        property_type=prop_type,
                        unit=unit,
                        description=f"{prop_name} of the material",
                        created_by=user_email
                    )
                    db.add(prop_def)
                    db.flush()
                
                # Check if property already exists
                existing = db.query(ComponentProperty).filter(
                    and_(
                        ComponentProperty.component_id == component.id,
                        ComponentProperty.property_definition_id == prop_def.id
                    )
                ).first()
                
                if not existing:
                    comp_prop = ComponentProperty(
                        component_id=component.id,
                        property_definition_id=prop_def.id,
                        single_value=mechanical_data[key],
                        notes=f"From standard: {material.name}",
                        source="Alloy Standards Database",
                        updated_by=user_email,
                        inherited_from_material=True,
                        source_material_id=material.id
                    )
                    db.add(comp_prop)
                    
                    properties_added.append({
                        "name": prop_name,
                        "value": mechanical_data[key],
                        "unit": unit
                    })
        
        return properties_added
    
    def _add_standard_acoustic_properties(
        self, db: Session, component: Component, material: Material, 
        acoustic_data: Dict[str, Any], user_email: str
    ) -> List[Dict[str, Any]]:
        """Add acoustic properties from standards database"""
        properties_added = []
        
        property_mapping = {
            "longitudinal_velocity": ("Longitudinal Wave Velocity", "m/s", PropertyType.ACOUSTIC),
            "shear_velocity": ("Shear Wave Velocity", "m/s", PropertyType.ACOUSTIC),
            "acoustic_impedance": ("Acoustic Impedance", "MRayl", PropertyType.ACOUSTIC),
            "longitudinal_impedance": ("Longitudinal Acoustic Impedance", "Rayl", PropertyType.ACOUSTIC),
            "shear_impedance": ("Shear Acoustic Impedance", "Rayl", PropertyType.ACOUSTIC)
        }
        
        for key, (prop_name, unit, prop_type) in property_mapping.items():
            if key in acoustic_data:
                # Get or create property definition
                prop_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == prop_name
                ).first()
                
                if not prop_def:
                    prop_def = PropertyDefinition(
                        name=prop_name,
                        property_type=prop_type,
                        unit=unit,
                        description=f"{prop_name} of the material",
                        created_by=user_email
                    )
                    db.add(prop_def)
                    db.flush()
                
                # Check if property already exists
                existing = db.query(ComponentProperty).filter(
                    and_(
                        ComponentProperty.component_id == component.id,
                        ComponentProperty.property_definition_id == prop_def.id
                    )
                ).first()
                
                if not existing:
                    comp_prop = ComponentProperty(
                        component_id=component.id,
                        property_definition_id=prop_def.id,
                        single_value=acoustic_data[key],
                        notes=f"From standard: {material.name}",
                        source="Alloy Standards Database",
                        updated_by=user_email,
                        inherited_from_material=True,
                        source_material_id=material.id
                    )
                    db.add(comp_prop)
                    
                    properties_added.append({
                        "name": prop_name,
                        "value": acoustic_data[key],
                        "unit": unit
                    })
        
        return properties_added
    
    def get_inherited_properties(self, db: Session, component_id: int) -> List[ComponentProperty]:
        """Get all properties that were inherited from a material"""
        return db.query(ComponentProperty).filter(
            and_(
                ComponentProperty.component_id == component_id,
                ComponentProperty.inherited_from_material == True
            )
        ).all()
    
    def get_user_defined_properties(self, db: Session, component_id: int) -> List[ComponentProperty]:
        """Get all properties that were manually added by users"""
        return db.query(ComponentProperty).filter(
            and_(
                ComponentProperty.component_id == component_id,
                ComponentProperty.inherited_from_material == False
            )
        ).all()