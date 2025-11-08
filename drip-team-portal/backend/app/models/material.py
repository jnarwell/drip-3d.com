from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, JSON, Boolean, Table
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base

# Association table for component materials (many-to-many)
component_materials = Table(
    'component_materials',
    Base.metadata,
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True),
    Column('material_id', Integer, ForeignKey('materials.id'), primary_key=True),
    Column('percentage', Float, default=100.0),  # For mixed materials
    Column('notes', String)
)


class Material(Base):
    __tablename__ = "materials"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    category = Column(String, nullable=False)  # Metal, Ceramic, Polymer, Composite, etc.
    subcategory = Column(String)  # Aluminum Alloy, Steel Alloy, etc.
    
    # Common identifiers
    uns_number = Column(String)  # Unified Numbering System
    astm_grade = Column(String)
    common_names = Column(JSON)  # List of alternative names
    
    # Source information
    data_source = Column(String)  # NIST, MatWeb, etc.
    source_url = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    property_values = relationship("MaterialProperty", back_populates="material", cascade="all, delete-orphan")
    components = relationship("Component", secondary=component_materials, back_populates="materials")


class MaterialProperty(Base):
    __tablename__ = "material_properties"
    
    id = Column(Integer, primary_key=True)
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=False)
    property_definition_id = Column(Integer, ForeignKey("property_definitions.id"), nullable=False)
    
    # Standard property values with temperature dependence
    value = Column(Float)
    value_min = Column(Float)
    value_max = Column(Float)
    
    # Temperature conditions
    temperature = Column(Float)  # Temperature at which property is measured (°C)
    temperature_range_min = Column(Float)
    temperature_range_max = Column(Float)
    
    # Additional conditions
    conditions = Column(JSON)  # {"pressure": 101325, "strain_rate": 0.001, etc.}
    
    # Source and reliability
    source = Column(String)
    reliability = Column(String)  # "measured", "typical", "estimated"
    notes = Column(String)
    
    # Relationships
    material = relationship("Material", back_populates="property_values")
    property_definition = relationship("PropertyDefinition")


class MaterialPropertyTemplate(Base):
    """Templates defining which properties should be auto-added for each material category"""
    __tablename__ = "material_property_templates"
    
    id = Column(Integer, primary_key=True)
    material_category = Column(String, nullable=False)
    property_definition_id = Column(Integer, ForeignKey("property_definitions.id"), nullable=False)
    is_required = Column(Boolean, default=True)
    
    property_definition = relationship("PropertyDefinition")