"""Pydantic schemas for Resources: Property Tables, System Constants, and Calculation Templates"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.models.resources import (
    TableType, InterpolationType, TemplateType,
    ImportMethod, VerificationStatus, SourceType
)


# Variable Definitions
class VariableDefinition(BaseModel):
    """Definition of a table variable (column)"""
    name: str
    symbol: str
    unit: str
    description: Optional[str] = None


# Property Table Templates
class PropertyTableTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    table_type: TableType
    independent_vars: List[VariableDefinition]
    dependent_vars: List[VariableDefinition]
    interpolation_type: InterpolationType = InterpolationType.LINEAR
    extrapolation_allowed: bool = False
    require_monotonic: bool = True
    
    class Config:
        use_enum_values = True


class PropertyTableTemplateCreate(PropertyTableTemplateBase):
    created_from_document: bool = False
    source_document_example: Optional[str] = None
    is_public: bool = False
    workspace_id: Optional[int] = None
    
    @validator('table_type', pre=True)
    def validate_table_type(cls, v):
        if isinstance(v, str):
            # Handle both uppercase (from frontend) and lowercase values
            v_lower = v.lower()
            for member in TableType:
                if member.value == v_lower:
                    return member
            # Also try exact match
            try:
                return TableType(v)
            except ValueError:
                pass
            # Try by name
            try:
                return TableType[v]
            except KeyError:
                pass
        return v
    
    @validator('interpolation_type', pre=True)
    def validate_interpolation_type(cls, v):
        if isinstance(v, str):
            # Handle both uppercase (from frontend) and lowercase values
            v_lower = v.lower()
            for member in InterpolationType:
                if member.value == v_lower:
                    return member
            # Also try exact match
            try:
                return InterpolationType(v)
            except ValueError:
                pass
            # Try by name
            try:
                return InterpolationType[v]
            except KeyError:
                pass
        return v
    
    class Config:
        use_enum_values = True


class PropertyTableTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    interpolation_type: Optional[InterpolationType] = None
    extrapolation_allowed: Optional[bool] = None
    require_monotonic: Optional[bool] = None
    is_public: Optional[bool] = None


class PropertyTableTemplate(PropertyTableTemplateBase):
    id: int
    created_from_document: bool
    source_document_example: Optional[str] = None
    is_public: bool
    workspace_id: Optional[int] = None
    created_by: str
    created_at: datetime
    usage_count: int

    class Config:
        from_attributes = True
        use_enum_values = True


# Property Tables
class PropertyTableBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_id: Optional[int] = None
    material_id: Optional[int] = None
    component_id: Optional[int] = None
    
    # Source information
    source_citation: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_authority: Optional[str] = None
    applicable_conditions: Optional[str] = None
    tags: Optional[List[str]] = None


class PropertyTableCreate(PropertyTableBase):
    data: List[Dict[str, Any]]  # Table data rows
    import_method: ImportMethod
    source_document_path: Optional[str] = None
    source_url: Optional[str] = None
    extracted_via_ocr: bool = False
    data_quality: Optional[str] = None
    is_public: bool = False
    workspace_id: Optional[int] = None
    
    @validator('data')
    def validate_data_not_empty(cls, v):
        if not v:
            raise ValueError("Data cannot be empty")
        return v


class PropertyTableUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    data: Optional[List[Dict[str, Any]]] = None
    source_citation: Optional[str] = None
    source_type: Optional[SourceType] = None
    source_authority: Optional[str] = None
    applicable_conditions: Optional[str] = None
    tags: Optional[List[str]] = None
    data_quality: Optional[str] = None
    is_public: Optional[bool] = None
    manual_corrections: Optional[int] = None


class PropertyTable(PropertyTableBase):
    id: int
    data: List[Dict[str, Any]]
    data_points_count: int
    
    # Import tracking
    import_method: ImportMethod
    source_document_path: Optional[str] = None
    source_document_hash: Optional[str] = None
    source_url: Optional[str] = None
    
    # Verification
    verification_status: VerificationStatus
    verification_method: Optional[str] = None
    last_verified: Optional[datetime] = None
    
    # Quality
    extracted_via_ocr: bool
    manual_corrections: int
    data_quality: Optional[str] = None
    
    # Metadata
    last_updated: datetime
    created_at: datetime
    created_by: str
    is_public: bool
    workspace_id: Optional[int] = None
    
    # Related template
    template: Optional[PropertyTableTemplate] = None

    class Config:
        from_attributes = True
        use_enum_values = True


# Property Table List Response (with verification badges)
class PropertyTableSummary(BaseModel):
    """Summary view for table listing with verification status"""
    id: int
    name: str
    description: Optional[str] = None
    data_points_count: int
    material_name: Optional[str] = None
    
    # Verification info for badge display
    verification_status: VerificationStatus
    import_method: ImportMethod
    source_authority: Optional[str] = None
    source_citation: Optional[str] = None
    
    # Metadata
    created_by: str
    created_at: datetime
    last_updated: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


# System Constants (keep existing)
class SystemConstantBase(BaseModel):
    symbol: str
    name: str
    value: float
    unit: Optional[str] = None
    description: Optional[str] = None
    category: str
    is_editable: bool = False


class SystemConstantCreate(SystemConstantBase):
    pass


class SystemConstantUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class SystemConstant(SystemConstantBase):
    id: int
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True
        use_enum_values = True


# Calculation Templates (keep existing)
class TemplateColumnDefinition(BaseModel):
    name: str
    type: str  # "numeric", "text", "datetime"
    unit: Optional[str] = None
    required: bool = True
    default_value: Optional[Any] = None


class CalculationTemplateBase(BaseModel):
    name: str
    description: Optional[str] = None
    template_type: TemplateType


class CalculationTemplateCreate(CalculationTemplateBase):
    table_structure: Optional[Dict[str, Any]] = None  # For property table templates
    calculation_steps: Optional[List[Dict[str, Any]]] = None  # For workflow templates


class CalculationTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    table_structure: Optional[Dict[str, Any]] = None
    calculation_steps: Optional[List[Dict[str, Any]]] = None
    is_public: Optional[bool] = None


class CalculationTemplate(CalculationTemplateBase):
    id: int
    table_structure: Optional[Dict[str, Any]] = None
    calculation_steps: Optional[List[Dict[str, Any]]] = None
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_public: bool
    usage_count: int

    class Config:
        from_attributes = True
        use_enum_values = True


# Document Import Support
class DocumentAnalysisResult(BaseModel):
    """Result from analyzing a document for tables"""
    table_name: str
    table_type: TableType
    independent_vars: List[VariableDefinition]
    dependent_vars: List[VariableDefinition]
    data_preview: List[Dict[str, Any]]  # First 5-10 rows
    total_rows: int
    source_info: Optional[str] = None
    confidence_score: float  # 0-1, higher is better
    page_number: Optional[int] = None
    extraction_method: str  # "native_pdf", "ocr", "excel"
    
    class Config:
        use_enum_values = True


class TableImportRequest(BaseModel):
    """Request to import data from document"""
    template_id: Optional[int] = None
    document_path: Optional[str] = None
    document_url: Optional[str] = None
    table_index: int = 0  # Which table in document to import
    material_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    tags: Optional[List[str]] = None