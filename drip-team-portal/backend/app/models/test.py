from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.db.database import Base

class TestStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    BLOCKED = "BLOCKED"

class TestResultStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"

class Test(Base):
    __tablename__ = "tests"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(String, unique=True, nullable=False, index=True)
    name = Column(String, nullable=False)
    category = Column(String)
    purpose = Column(Text)
    duration_hours = Column(Float)
    
    prerequisites = Column(JSON)
    
    status = Column(Enum(TestStatus), default=TestStatus.NOT_STARTED, index=True)
    executed_date = Column(DateTime)
    engineer = Column(String)
    notes = Column(Text)
    
    linear_issue_id = Column(String)
    linear_sync_status = Column(String)
    
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    test_results = relationship("TestResult", back_populates="test")

class TestResult(Base):
    __tablename__ = "test_results"
    
    id = Column(Integer, primary_key=True, index=True)
    test_id = Column(Integer, ForeignKey("tests.id"))
    component_id = Column(Integer, ForeignKey("components.id"))
    
    result = Column(Enum(TestResultStatus), nullable=False)
    
    steering_force = Column(Float)
    bonding_strength = Column(Float)
    temperature_max = Column(Float)
    drip_number = Column(Float)
    
    physics_validated = Column(Boolean, default=False)
    
    evidence_files = Column(JSON)
    
    executed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    executed_by = Column(String)
    notes = Column(Text)
    
    test = relationship("Test", back_populates="test_results")
    component = relationship("Component", back_populates="test_results")