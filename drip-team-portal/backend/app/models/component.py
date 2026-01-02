from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.db.database import Base

class ComponentStatus(str, enum.Enum):
    NOT_TESTED = "NOT_TESTED"
    IN_TESTING = "IN_TESTING" 
    VERIFIED = "VERIFIED"
    FAILED = "FAILED"

class ComponentCategory(str, enum.Enum):
    ACOUSTIC = "Acoustic"
    THERMAL = "Thermal"
    MECHANICAL = "Mechanical"
    ELECTRICAL = "Electrical"
    MATERIAL = "Material"

class RDPhase(str, enum.Enum):
    PHASE_1 = "PHASE_1"  # Basic acoustic testing w/ styrofoam + gallium indium
    PHASE_2 = "PHASE_2"  # Aluminum testing and production research
    PHASE_3 = "PHASE_3"  # L1 PROTOTYPE

class Component(Base):
    __tablename__ = "components"

    id = Column(Integer, primary_key=True, index=True)
    component_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)

    # Auto-generated unique code for formula references (e.g., "HEATBED_001")
    # Used in expressions like: #HEATBED_001.thermal_conductivity
    code = Column(String, unique=True, index=True)
    part_number = Column(String)
    category = Column(Enum(ComponentCategory), nullable=False)
    status = Column(Enum(ComponentStatus), default=ComponentStatus.NOT_TESTED, index=True)
    phase = Column(Enum(RDPhase), nullable=False, default=RDPhase.PHASE_1)
    unit_cost = Column(Float)
    quantity = Column(Integer, default=1)
    
    tech_specs = Column(JSON)
    
    purchase_order = Column(String)
    supplier = Column(String)
    lead_time_days = Column(Integer)
    order_date = Column(DateTime)
    expected_delivery = Column(DateTime)
    
    notes = Column(Text)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    updated_by = Column(String)
    owner_id = Column(String, nullable=True)  # User email who "owns" this component

    test_results = relationship("TestResult", back_populates="component")
    properties = relationship("ComponentProperty", back_populates="component", cascade="all, delete-orphan")

    # Time tracking and resources
    time_entries = relationship("TimeEntry", back_populates="component")
    from app.models.resources import resource_components
    resources = relationship("Resource", secondary=resource_components, back_populates="components")
    
    # Material relationships
    from app.models.material import component_materials
    materials = relationship("Material", secondary=component_materials, back_populates="components")
    primary_material_id = Column(Integer, ForeignKey("materials.id"))
    primary_material = relationship("Material", foreign_keys=[primary_material_id])