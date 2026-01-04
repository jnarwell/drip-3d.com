"""
Test Protocol System

Architecture:
    TestProtocol (1) ──< TestRun (N)
                            │
                            ├──< TestMeasurement (N)
                            └──< TestValidation (N)

    TestProtocol can optionally link to PhysicsModel for predictions.
    TestRun can optionally link to ModelInstance for specific predictions.
    TestRun can optionally link to Component being tested.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, JSON, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.db.database import Base


class TestRunStatus(str, enum.Enum):
    SETUP = "SETUP"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    ABORTED = "ABORTED"


class TestResultStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    PARTIAL = "PARTIAL"


class ValidationStatus(str, enum.Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"


class TestProtocol(Base):
    """
    Reusable test template defining WHAT to test and HOW.

    input_schema example:
    [
        {"name": "voltage", "unit_id": 5, "required": true, "description": "Drive voltage"},
        {"name": "frequency", "unit_id": 8, "required": true, "description": "Operating frequency"}
    ]

    output_schema example:
    [
        {"name": "power", "unit_id": 12, "target": 12.0, "tolerance_pct": 10.0, "description": "Measured power"},
        {"name": "temperature", "unit_id": 3, "max": 100.0, "description": "Max temperature observed"}
    ]
    """
    __tablename__ = "test_protocols"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)  # Acoustic, Thermal, Mechanical, etc.

    # Schema definitions
    input_schema = Column(JSON)   # Expected test configuration inputs
    output_schema = Column(JSON)  # Expected measurements with targets/tolerances
    procedure = Column(Text)      # Step-by-step instructions (markdown)
    equipment = Column(JSON)      # List of required equipment
    setup_checklist = Column(JSON)  # Pre-test setup steps checklist

    # Optional model linkage for automatic predictions
    model_id = Column(Integer, ForeignKey("physics_models.id"), nullable=True)

    # Versioning & status
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)

    # Audit
    created_by = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    runs = relationship("TestRun", back_populates="protocol", cascade="all, delete-orphan")
    model = relationship("PhysicsModel")

    def __repr__(self):
        return f"<TestProtocol {self.id}: {self.name}>"


class TestRun(Base):
    """
    Single execution of a protocol - records WHEN, WHO, and WHAT HAPPENED.

    configuration example:
    {"voltage": 24.1, "frequency": 40020, "ambient_temp": 22.5}
    """
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    protocol_id = Column(Integer, ForeignKey("test_protocols.id"), nullable=False, index=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True, index=True)
    analysis_id = Column(Integer, ForeignKey("model_instances.id"), nullable=True)

    # Execution context
    run_number = Column(Integer)  # Auto-increment per protocol
    status = Column(Enum(TestRunStatus), default=TestRunStatus.SETUP, index=True)
    operator = Column(String(100))

    # Timing
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

    # Configuration (actual test conditions - matches protocol input_schema)
    configuration = Column(JSON)

    # Overall result
    result = Column(Enum(TestResultStatus), nullable=True)
    notes = Column(Text)

    # Audit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    protocol = relationship("TestProtocol", back_populates="runs")
    component = relationship("Component", back_populates="test_runs")
    analysis = relationship("ModelInstance")
    measurements = relationship("TestMeasurement", back_populates="run", cascade="all, delete-orphan")
    validations = relationship("TestValidation", back_populates="run", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<TestRun {self.id}: Protocol {self.protocol_id} #{self.run_number}>"


class TestMeasurement(Base):
    """
    Individual measured value from a test run.
    Flexible key-value storage for any measurement type.
    """
    __tablename__ = "test_measurements"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)

    parameter_name = Column(String(100), nullable=False)  # Must match output_schema name
    measured_value = Column(Float, nullable=False)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text)

    # Relationships
    run = relationship("TestRun", back_populates="measurements")
    unit = relationship("Unit")

    def __repr__(self):
        return f"<TestMeasurement {self.parameter_name}: {self.measured_value}>"


class TestValidation(Base):
    """
    Comparison of predicted vs measured values.
    Created when a TestRun has both measurements and model predictions.
    """
    __tablename__ = "test_validations"

    id = Column(Integer, primary_key=True, index=True)
    run_id = Column(Integer, ForeignKey("test_runs.id"), nullable=False, index=True)

    parameter_name = Column(String(100), nullable=False)
    predicted_value = Column(Float)
    measured_value = Column(Float)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Validation results
    error_absolute = Column(Float)      # measured - predicted
    error_pct = Column(Float)           # (measured - predicted) / predicted * 100
    tolerance_pct = Column(Float)       # From protocol output_schema
    status = Column(Enum(ValidationStatus))

    # Audit
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    run = relationship("TestRun", back_populates="validations")
    unit = relationship("Unit")

    def __repr__(self):
        return f"<TestValidation {self.parameter_name}: {self.status}>"
