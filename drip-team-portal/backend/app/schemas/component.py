from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.component import ComponentStatus, ComponentCategory, RDPhase

class ComponentBase(BaseModel):
    component_id: str = Field(..., description="Unique component identifier")
    name: str = Field(..., description="Component name")
    part_number: Optional[str] = None
    category: ComponentCategory
    phase: RDPhase = RDPhase.PHASE_1
    unit_cost: Optional[float] = None
    quantity: int = 1
    tech_specs: Optional[Dict[str, Any]] = None
    purchase_order: Optional[str] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None
    order_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None

class ComponentCreate(BaseModel):
    name: str = Field(..., description="Component name")
    part_number: Optional[str] = None
    category: ComponentCategory
    phase: RDPhase = RDPhase.PHASE_1
    unit_cost: Optional[float] = None
    quantity: int = 1
    tech_specs: Optional[Dict[str, Any]] = None
    purchase_order: Optional[str] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None
    order_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None

class ComponentUpdate(BaseModel):
    name: Optional[str] = None
    part_number: Optional[str] = None
    category: Optional[ComponentCategory] = None
    phase: Optional[RDPhase] = None
    unit_cost: Optional[float] = None
    quantity: Optional[int] = None
    tech_specs: Optional[Dict[str, Any]] = None
    purchase_order: Optional[str] = None
    supplier: Optional[str] = None
    lead_time_days: Optional[int] = None
    order_date: Optional[datetime] = None
    expected_delivery: Optional[datetime] = None
    notes: Optional[str] = None

class ComponentStatusUpdate(BaseModel):
    status: ComponentStatus
    notes: Optional[str] = None
    sync_to_linear: bool = False

class ComponentResponse(ComponentBase):
    id: int
    status: ComponentStatus
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[str] = None
    
    class Config:
        from_attributes = True