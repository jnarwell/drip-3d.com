import sys
sys.path.append('/app')

from sqlalchemy.orm import Session
from app.models.material import Material, MaterialProperty, MaterialPropertyTemplate
from app.models.property import PropertyDefinition, PropertyType
from app.db.database import SessionLocal

# Common materials used in DRIP system
MATERIALS_DATA = [
    # Metals
    {
        "name": "Copper C11000 (ETP)",
        "category": "Metal",
        "subcategory": "Pure Metal",
        "uns_number": "C11000",
        "common_names": ["ETP Copper", "Electrolytic Tough Pitch Copper"],
        "data_source": "NIST/MatWeb",
        "properties": {
            "Density": {"value": 8960, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 1084.62, "unit": "°C"},
            "Thermal Conductivity": {"value": 391, "unit": "W/m·K", "temperature": 20},
            "Thermal Expansion Coefficient": {"value": 16.5e-6, "unit": "1/K", "temperature": 20, "temperature_range_max": 100},
            "Specific Heat Capacity": {"value": 385, "unit": "J/kg·K", "temperature": 25},
            "Electrical Resistivity": {"value": 1.72e-8, "unit": "Ω·m", "temperature": 20},
            "Young's Modulus": {"value": 117, "unit": "GPa"},
            "Tensile Strength": {"value": 220, "value_min": 210, "value_max": 365, "unit": "MPa"},
        }
    },
    {
        "name": "Aluminum 6061-T6",
        "category": "Metal",
        "subcategory": "Aluminum Alloy",
        "uns_number": "A96061",
        "astm_grade": "6061-T6",
        "common_names": ["AL 6061-T6", "AA6061-T6"],
        "data_source": "NIST/MatWeb",
        "properties": {
            "Density": {"value": 2700, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 582, "value_min": 582, "value_max": 652, "unit": "°C"},
            "Thermal Conductivity": {"value": 167, "unit": "W/m·K", "temperature": 25},
            "Thermal Expansion Coefficient": {"value": 23.6e-6, "unit": "1/K", "temperature": 20, "temperature_range_max": 100},
            "Specific Heat Capacity": {"value": 896, "unit": "J/kg·K", "temperature": 25},
            "Young's Modulus": {"value": 68.9, "unit": "GPa"},
            "Tensile Strength": {"value": 310, "unit": "MPa"},
            "Yield Strength": {"value": 276, "unit": "MPa"},
        }
    },
    {
        "name": "Steel 316L Stainless",
        "category": "Metal",
        "subcategory": "Stainless Steel",
        "uns_number": "S31603",
        "astm_grade": "316L",
        "common_names": ["316L SS", "Marine Grade Stainless"],
        "data_source": "NIST/MatWeb",
        "properties": {
            "Density": {"value": 8000, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 1375, "value_min": 1375, "value_max": 1400, "unit": "°C"},
            "Thermal Conductivity": {"value": 16.3, "unit": "W/m·K", "temperature": 100},
            "Thermal Expansion Coefficient": {"value": 16.0e-6, "unit": "1/K", "temperature": 20, "temperature_range_max": 100},
            "Young's Modulus": {"value": 193, "unit": "GPa"},
            "Tensile Strength": {"value": 558, "unit": "MPa"},
        }
    },
    {
        "name": "Titanium Grade 2",
        "category": "Metal",
        "subcategory": "Pure Metal",
        "uns_number": "R50400",
        "astm_grade": "Grade 2",
        "common_names": ["CP Titanium Grade 2", "Commercially Pure Titanium"],
        "data_source": "NIST/MatWeb",
        "properties": {
            "Density": {"value": 4507, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 1668, "unit": "°C"},
            "Thermal Conductivity": {"value": 21.9, "unit": "W/m·K", "temperature": 20},
            "Thermal Expansion Coefficient": {"value": 8.6e-6, "unit": "1/K", "temperature": 20, "temperature_range_max": 100},
            "Young's Modulus": {"value": 102.7, "unit": "GPa"},
            "Tensile Strength": {"value": 344, "unit": "MPa"},
        }
    },
    # Ceramics
    {
        "name": "Alumina (Al2O3) 99.5%",
        "category": "Ceramic",
        "subcategory": "Oxide Ceramic",
        "common_names": ["Aluminum Oxide", "Corundum"],
        "data_source": "NIST/MatWeb",
        "properties": {
            "Density": {"value": 3950, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 2054, "unit": "°C"},
            "Thermal Conductivity": {"value": 30, "unit": "W/m·K", "temperature": 20},
            "Thermal Expansion Coefficient": {"value": 8.4e-6, "unit": "1/K", "temperature": 20, "temperature_range_max": 1000},
            "Young's Modulus": {"value": 370, "unit": "GPa"},
            "Hardness": {"value": 1440, "unit": "HV"},
            "Dielectric Constant": {"value": 9.8, "unit": "", "conditions": {"frequency": 1e6}},
        }
    },
    {
        "name": "PZT-4",
        "category": "Ceramic",
        "subcategory": "Piezoelectric",
        "common_names": ["Lead Zirconate Titanate"],
        "data_source": "Manufacturer Data",
        "properties": {
            "Density": {"value": 7500, "unit": "kg/m³", "temperature": 20},
            "Curie Temperature": {"value": 328, "unit": "°C"},
            "Dielectric Constant": {"value": 1300, "unit": "", "conditions": {"frequency": 1000}},
            "Piezoelectric Charge Constant d33": {"value": 289e-12, "unit": "C/N"},
            "Piezoelectric Voltage Constant g33": {"value": 26.1e-3, "unit": "V·m/N"},
            "Young's Modulus": {"value": 81, "unit": "GPa"},
            "Mechanical Q Factor": {"value": 500, "unit": ""},
        }
    },
    # Polymers
    {
        "name": "PTFE (Teflon)",
        "category": "Polymer",
        "subcategory": "Fluoropolymer",
        "common_names": ["Polytetrafluoroethylene", "Teflon"],
        "data_source": "MatWeb",
        "properties": {
            "Density": {"value": 2170, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 327, "unit": "°C"},
            "Thermal Conductivity": {"value": 0.25, "unit": "W/m·K", "temperature": 23},
            "Thermal Expansion Coefficient": {"value": 135e-6, "unit": "1/K", "temperature": 20},
            "Operating Temperature": {"value_min": -200, "value_max": 260, "unit": "°C"},
            "Dielectric Constant": {"value": 2.1, "unit": "", "conditions": {"frequency": 1e6}},
        }
    },
    # Special Materials for DRIP
    {
        "name": "Gallium",
        "category": "Metal",
        "subcategory": "Low Melting Metal",
        "common_names": ["Pure Gallium"],
        "data_source": "NIST",
        "properties": {
            "Density": {"value": 5907, "unit": "kg/m³", "temperature": 29.8},
            "Melting Temperature": {"value": 29.76, "unit": "°C"},
            "Thermal Conductivity": {"value": 40.6, "unit": "W/m·K", "temperature": 30},
            "Viscosity": {"value": 1.98e-3, "unit": "Pa·s", "temperature": 30},
            "Surface Tension": {"value": 0.718, "unit": "N/m", "temperature": 29.8},
        }
    },
    {
        "name": "Indium",
        "category": "Metal",
        "subcategory": "Low Melting Metal",
        "common_names": ["Pure Indium"],
        "data_source": "NIST",
        "properties": {
            "Density": {"value": 7310, "unit": "kg/m³", "temperature": 20},
            "Melting Temperature": {"value": 156.6, "unit": "°C"},
            "Thermal Conductivity": {"value": 81.8, "unit": "W/m·K", "temperature": 25},
            "Young's Modulus": {"value": 11, "unit": "GPa"},
        }
    },
]

# Define which properties to auto-add for each material category
MATERIAL_PROPERTY_TEMPLATES = [
    # Metal properties
    {"category": "Metal", "property_name": "Density", "is_required": True},
    {"category": "Metal", "property_name": "Melting Temperature", "is_required": True},
    {"category": "Metal", "property_name": "Thermal Conductivity", "is_required": True},
    {"category": "Metal", "property_name": "Thermal Expansion Coefficient", "is_required": True},
    {"category": "Metal", "property_name": "Specific Heat Capacity", "is_required": True},
    {"category": "Metal", "property_name": "Young's Modulus", "is_required": True},
    {"category": "Metal", "property_name": "Tensile Strength", "is_required": False},
    {"category": "Metal", "property_name": "Yield Strength", "is_required": False},
    {"category": "Metal", "property_name": "Electrical Resistivity", "is_required": False},
    
    # Ceramic properties
    {"category": "Ceramic", "property_name": "Density", "is_required": True},
    {"category": "Ceramic", "property_name": "Melting Temperature", "is_required": True},
    {"category": "Ceramic", "property_name": "Thermal Conductivity", "is_required": True},
    {"category": "Ceramic", "property_name": "Thermal Expansion Coefficient", "is_required": True},
    {"category": "Ceramic", "property_name": "Young's Modulus", "is_required": True},
    {"category": "Ceramic", "property_name": "Hardness", "is_required": False},
    {"category": "Ceramic", "property_name": "Dielectric Constant", "is_required": False},
    
    # Polymer properties
    {"category": "Polymer", "property_name": "Density", "is_required": True},
    {"category": "Polymer", "property_name": "Melting Temperature", "is_required": True},
    {"category": "Polymer", "property_name": "Glass Transition Temperature", "is_required": False},
    {"category": "Polymer", "property_name": "Thermal Conductivity", "is_required": True},
    {"category": "Polymer", "property_name": "Thermal Expansion Coefficient", "is_required": True},
    {"category": "Polymer", "property_name": "Operating Temperature", "is_required": True},
]


def seed_materials(db: Session):
    """Seed material data and properties"""
    
    # First, ensure property definitions exist
    property_def_map = {}
    all_properties = db.query(PropertyDefinition).all()
    for prop in all_properties:
        property_def_map[prop.name] = prop
    
    # Create material property templates
    for template in MATERIAL_PROPERTY_TEMPLATES:
        if template["property_name"] in property_def_map:
            existing = db.query(MaterialPropertyTemplate).filter(
                MaterialPropertyTemplate.material_category == template["category"],
                MaterialPropertyTemplate.property_definition_id == property_def_map[template["property_name"]].id
            ).first()
            
            if not existing:
                db_template = MaterialPropertyTemplate(
                    material_category=template["category"],
                    property_definition_id=property_def_map[template["property_name"]].id,
                    is_required=template["is_required"]
                )
                db.add(db_template)
    
    db.commit()
    
    # Add materials and their properties
    for material_data in MATERIALS_DATA:
        # Check if material exists
        existing = db.query(Material).filter(Material.name == material_data["name"]).first()
        if existing:
            continue
        
        # Create material
        properties = material_data.pop("properties", {})
        material = Material(**material_data)
        db.add(material)
        db.flush()  # Get the ID
        
        # Add material properties
        for prop_name, prop_data in properties.items():
            if prop_name in property_def_map:
                unit = prop_data.pop("unit", "")
                
                # Create material property
                mat_prop = MaterialProperty(
                    material_id=material.id,
                    property_definition_id=property_def_map[prop_name].id,
                    **prop_data,
                    source=material_data.get("data_source", ""),
                    reliability="typical"
                )
                db.add(mat_prop)
    
    db.commit()
    print(f"Seeded {len(MATERIALS_DATA)} materials with properties")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_materials(db)
    finally:
        db.close()