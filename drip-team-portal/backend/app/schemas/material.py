from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime


class MaterialBase(BaseModel):
    name: str
    category: str
    subcategory: Optional[str] = None
    uns_number: Optional[str] = None
    astm_grade: Optional[str] = None
    common_names: Optional[List[str]] = None
    data_source: Optional[str] = None
    source_url: Optional[str] = None


class MaterialCreate(MaterialBase):
    pass


class MaterialPropertyValue(BaseModel):
    property_name: str
    value: Optional[float] = None
    value_min: Optional[float] = None
    value_max: Optional[float] = None
    unit: str
    temperature: Optional[float] = None
    conditions: Optional[Dict[str, Any]] = None


class MaterialResponse(MaterialBase):
    id: int
    created_at: datetime
    updated_at: datetime
    properties: Optional[List[MaterialPropertyValue]] = None
    
    class Config:
        from_attributes = True


class ComponentMaterialAdd(BaseModel):
    material_id: int
    percentage: Optional[float] = 100.0
    notes: Optional[str] = None


class ComponentMaterialResponse(BaseModel):
    material: MaterialResponse
    percentage: float
    notes: Optional[str] = None
    inherited_properties: List[MaterialPropertyValue]
    
    class Config:
        from_attributes = True