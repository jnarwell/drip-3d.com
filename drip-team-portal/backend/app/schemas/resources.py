"""Pydantic schemas for Resources: System Constants"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# System Constants
class SystemConstantBase(BaseModel):
    symbol: str
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    category: str


class SystemConstantCreate(BaseModel):
    symbol: str
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    category: str


class SystemConstantUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class SystemConstant(SystemConstantBase):
    id: int
    is_editable: bool
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
