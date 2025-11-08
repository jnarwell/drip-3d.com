from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.test import TestStatus, TestResultStatus

class TestBase(BaseModel):
    test_id: str = Field(..., description="Unique test identifier")
    name: str = Field(..., description="Test name")
    category: Optional[str] = None
    purpose: Optional[str] = None
    duration_hours: Optional[float] = None
    prerequisites: Optional[List[str]] = None

class TestCreate(TestBase):
    pass

class TestUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    purpose: Optional[str] = None
    duration_hours: Optional[float] = None
    prerequisites: Optional[List[str]] = None
    status: Optional[TestStatus] = None
    notes: Optional[str] = None

class TestResponse(TestBase):
    id: int
    status: TestStatus
    executed_date: Optional[datetime] = None
    engineer: Optional[str] = None
    notes: Optional[str] = None
    linear_issue_id: Optional[str] = None
    linear_sync_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class TestResultBase(BaseModel):
    result: TestResultStatus
    component_id: Optional[str] = None
    steering_force: Optional[float] = None
    bonding_strength: Optional[float] = None
    temperature_max: Optional[float] = None
    drip_number: Optional[float] = None
    notes: Optional[str] = None

class TestResultCreate(TestResultBase):
    evidence_files: Optional[List[str]] = None
    drip_validation_params: Optional[Dict[str, float]] = None

class TestResultResponse(TestResultBase):
    id: int
    test_id: int
    physics_validated: bool = False
    executed_at: datetime
    executed_by: str
    
    class Config:
        from_attributes = True