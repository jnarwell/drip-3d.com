from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
from app.models.property import PropertyType, ValueType


class PropertyDefinitionBase(BaseModel):
    name: str
    property_type: PropertyType
    unit: str
    description: Optional[str] = None
    value_type: ValueType = ValueType.SINGLE
    

class PropertyDefinitionCreate(PropertyDefinitionBase):
    is_custom: bool = True


class PropertyDefinitionResponse(PropertyDefinitionBase):
    id: int
    is_custom: bool
    created_at: datetime
    created_by: Optional[str] = None
    
    class Config:
        from_attributes = True


class ComponentPropertyBase(BaseModel):
    property_definition_id: int
    single_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    average_value: Optional[float] = None
    tolerance: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None


class ComponentPropertyCreate(ComponentPropertyBase):
    # Expression support - if provided, creates an expression ValueNode
    expression: Optional[str] = None
    unit_id: Optional[int] = None


class ComponentPropertyUpdate(BaseModel):
    single_value: Optional[float] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    average_value: Optional[float] = None
    tolerance: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    # Expression support
    expression: Optional[str] = None
    unit_id: Optional[int] = None


class ValueNodeBrief(BaseModel):
    """Brief info about a value node."""
    id: int
    node_type: str
    expression_string: Optional[str] = None
    computed_value: Optional[float] = None
    computed_unit_symbol: Optional[str] = None
    computation_status: str

    class Config:
        from_attributes = True


class ComponentPropertyResponse(ComponentPropertyBase):
    id: int
    component_id: int
    property_definition: PropertyDefinitionResponse
    updated_at: datetime
    updated_by: Optional[str] = None
    # Value system integration
    value_node_id: Optional[int] = None
    value_node: Optional[ValueNodeBrief] = None

    class Config:
        from_attributes = True


class UnitSystemBase(BaseModel):
    base_unit: str
    unit_type: str
    conversions: Dict[str, float]


class UnitSystemResponse(UnitSystemBase):
    id: int
    
    class Config:
        from_attributes = True