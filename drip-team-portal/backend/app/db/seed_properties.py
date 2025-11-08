import sys
sys.path.append('/app')

from sqlalchemy.orm import Session
from app.models.property import PropertyDefinition, PropertyType, ValueType
from app.db.database import SessionLocal

# Default property definitions
DEFAULT_PROPERTIES = [
    # Electrical Properties
    {
        "name": "Power Consumption",
        "property_type": PropertyType.ELECTRICAL,
        "unit": "W",
        "description": "Power consumption during operation",
        "value_type": ValueType.RANGE,
        "is_custom": False
    },
    {
        "name": "Voltage",
        "property_type": PropertyType.ELECTRICAL,
        "unit": "V",
        "description": "Operating voltage",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Current",
        "property_type": PropertyType.ELECTRICAL,
        "unit": "A",
        "description": "Operating current",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Frequency Response",
        "property_type": PropertyType.ELECTRICAL,
        "unit": "Hz",
        "description": "Frequency response range",
        "value_type": ValueType.RANGE,
        "is_custom": False
    },
    
    # Thermal Properties
    {
        "name": "Operating Temperature",
        "property_type": PropertyType.THERMAL,
        "unit": "°C",
        "description": "Operating temperature range",
        "value_type": ValueType.RANGE,
        "is_custom": False
    },
    {
        "name": "Melting Temperature",
        "property_type": PropertyType.THERMAL,
        "unit": "°C",
        "description": "Material melting temperature",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Thermal Conductivity",
        "property_type": PropertyType.THERMAL,
        "unit": "W/m·K",
        "description": "Thermal conductivity coefficient",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Heat Generation Rate",
        "property_type": PropertyType.THERMAL,
        "unit": "W/W",
        "description": "Heat generated per watt of power",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Thermal Expansion Coefficient",
        "property_type": PropertyType.THERMAL,
        "unit": "1/K",
        "description": "Linear thermal expansion coefficient",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    
    # Mechanical Properties
    {
        "name": "Tensile Strength",
        "property_type": PropertyType.MECHANICAL,
        "unit": "MPa",
        "description": "Ultimate tensile strength",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Young's Modulus",
        "property_type": PropertyType.MECHANICAL,
        "unit": "GPa",
        "description": "Elastic modulus",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Density",
        "property_type": PropertyType.MECHANICAL,
        "unit": "kg/m³",
        "description": "Material density",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Hardness",
        "property_type": PropertyType.MECHANICAL,
        "unit": "HV",
        "description": "Vickers hardness",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    
    # Acoustic Properties
    {
        "name": "Resonance Frequency",
        "property_type": PropertyType.ACOUSTIC,
        "unit": "kHz",
        "description": "Primary resonance frequency",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Acoustic Power",
        "property_type": PropertyType.ACOUSTIC,
        "unit": "W",
        "description": "Acoustic power output",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Q Factor",
        "property_type": PropertyType.ACOUSTIC,
        "unit": "",
        "description": "Quality factor (dimensionless)",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Amplitude per Energy",
        "property_type": PropertyType.ACOUSTIC,
        "unit": "µm/W",
        "description": "Displacement amplitude per watt",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Half-Wave Frequency",
        "property_type": PropertyType.ACOUSTIC,
        "unit": "kHz",
        "description": "Half-wave resonance frequency",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    
    # Dimensional Properties
    {
        "name": "Length",
        "property_type": PropertyType.DIMENSIONAL,
        "unit": "mm",
        "description": "Component length",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Width",
        "property_type": PropertyType.DIMENSIONAL,
        "unit": "mm",
        "description": "Component width",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Height",
        "property_type": PropertyType.DIMENSIONAL,
        "unit": "mm",
        "description": "Component height",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    },
    {
        "name": "Weight",
        "property_type": PropertyType.DIMENSIONAL,
        "unit": "kg",
        "description": "Component weight",
        "value_type": ValueType.SINGLE,
        "is_custom": False
    }
]


def seed_properties(db: Session):
    """Seed default property definitions"""
    for prop_data in DEFAULT_PROPERTIES:
        existing = db.query(PropertyDefinition).filter(
            PropertyDefinition.name == prop_data["name"],
            PropertyDefinition.property_type == prop_data["property_type"]
        ).first()
        
        if not existing:
            prop_def = PropertyDefinition(**prop_data)
            db.add(prop_def)
    
    db.commit()
    print(f"Seeded {len(DEFAULT_PROPERTIES)} property definitions")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_properties(db)
    finally:
        db.close()