from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, DateTime, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class PropertyType(enum.Enum):
    THERMAL = "thermal"
    ELECTRICAL = "electrical"
    MECHANICAL = "mechanical"
    ACOUSTIC = "acoustic"
    MATERIAL = "material"
    DIMENSIONAL = "dimensional"
    OPTICAL = "optical"
    PHYSICAL = "physical"
    OTHER = "other"


class ValueType(enum.Enum):
    SINGLE = "single"  # Single value
    RANGE = "range"    # Min-max range
    AVERAGE = "average"  # Average with tolerance


class PropertyDefinition(Base):
    __tablename__ = "property_definitions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    property_type = Column(SQLEnum(PropertyType), nullable=False)
    unit = Column(String, nullable=False)  # e.g., "W", "°C", "Hz", "m/s²"
    description = Column(String)
    value_type = Column(SQLEnum(ValueType), default=ValueType.SINGLE)
    is_custom = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)
    
    # Relationships
    property_values = relationship("ComponentProperty", back_populates="property_definition")


class ComponentProperty(Base):
    __tablename__ = "component_properties"
    
    id = Column(Integer, primary_key=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=False)
    property_definition_id = Column(Integer, ForeignKey("property_definitions.id"), nullable=False)
    
    # Value storage - flexible for different value types
    single_value = Column(Float)
    min_value = Column(Float)
    max_value = Column(Float)
    average_value = Column(Float)
    tolerance = Column(Float)
    
    # Formula-based calculation fields - STEP 3A: Temporarily disabled for debugging 500 error
    # is_calculated = Column(Boolean, default=False)  # True if value comes from formula
    # formula_id = Column(Integer, nullable=True)  # Removed FK constraint temporarily for safety
    # last_calculated = Column(DateTime, nullable=True)
    # calculation_inputs = Column(JSON, nullable=True)  # Store input values used in calculation
    # calculation_status = Column(String, default="manual")  # "manual", "calculated", "error", "stale"
    
    # Metadata
    notes = Column(String)
    source = Column(String)  # Where this data came from
    conditions = Column(JSON)  # Any conditions this value applies under
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String)
    
    # Material inheritance tracking
    inherited_from_material = Column(Boolean, default=False)  # True if this property came from a material
    source_material_id = Column(Integer, ForeignKey("materials.id"))  # Which material it came from
    
    # Relationships
    component = relationship("Component", back_populates="properties")
    property_definition = relationship("PropertyDefinition", back_populates="property_values")
    source_material = relationship("Material", foreign_keys=[source_material_id])
    # Note: PropertyFormula relationship will be added after import resolution


class UnitSystem(Base):
    __tablename__ = "unit_systems"
    
    id = Column(Integer, primary_key=True)
    base_unit = Column(String, nullable=False)  # e.g., "m", "kg", "s"
    unit_type = Column(String, nullable=False)  # e.g., "length", "mass", "time"
    
    # Conversion factors to base unit
    conversions = Column(JSON)  # {"mm": 0.001, "cm": 0.01, "in": 0.0254}