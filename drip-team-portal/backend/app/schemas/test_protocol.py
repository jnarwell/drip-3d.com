from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.test_protocol import TestRunStatus, TestResultStatus, ValidationStatus


# === TestProtocol Schemas ===

class InputSchemaItem(BaseModel):
    """Schema for a single input parameter"""
    name: str
    unit_id: Optional[int] = None
    required: bool = True
    description: Optional[str] = None
    default_value: Optional[float] = None


class OutputSchemaItem(BaseModel):
    """Schema for a single output/measurement parameter"""
    name: str
    unit_id: Optional[int] = None
    target: Optional[float] = None        # Expected value from model
    tolerance_pct: Optional[float] = None  # Acceptable deviation %
    min_value: Optional[float] = None      # Hard minimum
    max_value: Optional[float] = None      # Hard maximum
    description: Optional[str] = None


class TestProtocolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    input_schema: Optional[List[InputSchemaItem]] = None
    output_schema: Optional[List[OutputSchemaItem]] = None
    procedure: Optional[str] = None
    equipment: Optional[List[str]] = None
    setup_checklist: Optional[List[str]] = None
    model_id: Optional[int] = None


class TestProtocolCreate(TestProtocolBase):
    pass


class TestProtocolUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    input_schema: Optional[List[InputSchemaItem]] = None
    output_schema: Optional[List[OutputSchemaItem]] = None
    procedure: Optional[str] = None
    equipment: Optional[List[str]] = None
    setup_checklist: Optional[List[str]] = None
    model_id: Optional[int] = None
    is_active: Optional[bool] = None


class TestProtocolResponse(TestProtocolBase):
    id: int
    version: int
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Include run count for list views
    run_count: Optional[int] = None

    class Config:
        from_attributes = True


class TestProtocolDetail(TestProtocolResponse):
    """Extended response with recent runs"""
    recent_runs: Optional[List['TestRunSummary']] = None
    model_name: Optional[str] = None  # Denormalized for display


# === TestRun Schemas ===

class TestRunBase(BaseModel):
    protocol_id: int
    component_id: Optional[int] = None
    analysis_id: Optional[int] = None
    operator: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    notes: Optional[str] = None


class TestRunCreate(TestRunBase):
    pass


class TestRunUpdate(BaseModel):
    status: Optional[TestRunStatus] = None
    operator: Optional[str] = None
    configuration: Optional[Dict[str, Any]] = None
    result: Optional[TestResultStatus] = None
    notes: Optional[str] = None


class TestRunStart(BaseModel):
    """Schema for starting a test run"""
    configuration: Optional[Dict[str, Any]] = None
    operator: Optional[str] = None


class TestRunComplete(BaseModel):
    """Schema for completing a test run"""
    result: TestResultStatus
    notes: Optional[str] = None


class TestRunSummary(BaseModel):
    """Minimal run info for lists"""
    id: int
    run_number: Optional[int] = None
    status: TestRunStatus
    result: Optional[TestResultStatus] = None
    operator: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestRunResponse(TestRunBase):
    id: int
    run_number: Optional[int] = None
    status: TestRunStatus
    result: Optional[TestResultStatus] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TestRunDetail(TestRunResponse):
    """Extended response with measurements and validations"""
    protocol_name: Optional[str] = None
    component_name: Optional[str] = None
    measurements: List['TestMeasurementResponse'] = []
    validations: List['TestValidationResponse'] = []


# === TestMeasurement Schemas ===

class TestMeasurementBase(BaseModel):
    parameter_name: str
    measured_value: float
    unit_id: Optional[int] = None
    notes: Optional[str] = None


class TestMeasurementCreate(TestMeasurementBase):
    pass


class TestMeasurementBulkCreate(BaseModel):
    """Create multiple measurements at once"""
    measurements: List[TestMeasurementCreate]


class TestMeasurementResponse(TestMeasurementBase):
    id: int
    run_id: int
    timestamp: datetime
    unit_symbol: Optional[str] = None  # Denormalized for display

    class Config:
        from_attributes = True


# === TestValidation Schemas ===

class TestValidationResponse(BaseModel):
    id: int
    run_id: int
    parameter_name: str
    predicted_value: Optional[float] = None
    measured_value: Optional[float] = None
    unit_id: Optional[int] = None
    unit_symbol: Optional[str] = None
    error_absolute: Optional[float] = None
    error_pct: Optional[float] = None
    tolerance_pct: Optional[float] = None
    status: Optional[ValidationStatus] = None
    created_at: datetime

    class Config:
        from_attributes = True


# === Query/Filter Schemas ===

class TestProtocolFilter(BaseModel):
    category: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None
    model_id: Optional[int] = None


class TestRunFilter(BaseModel):
    protocol_id: Optional[int] = None
    component_id: Optional[int] = None
    status: Optional[TestRunStatus] = None
    result: Optional[TestResultStatus] = None
    operator: Optional[str] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None


# === Stats/Aggregation Schemas ===

class ProtocolStats(BaseModel):
    """Statistics for a single protocol"""
    protocol_id: int
    protocol_name: str
    total_runs: int
    passed: int
    failed: int
    partial: int
    pass_rate: float
    avg_duration_minutes: Optional[float] = None


class ValidationSummary(BaseModel):
    """Summary of validation results across runs"""
    parameter_name: str
    run_count: int
    avg_error_pct: float
    max_error_pct: float
    pass_count: int
    fail_count: int


# Forward references for nested models
TestProtocolDetail.model_rebuild()
TestRunDetail.model_rebuild()