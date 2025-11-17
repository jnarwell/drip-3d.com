"""Models for Resources: Property Tables, System Constants, and Calculation Templates"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Enum, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base


class TableType(str, enum.Enum):
    """Types of property tables"""
    SINGLE_VAR_LOOKUP = "single_var_lookup"  # e.g., properties vs temperature
    RANGE_BASED_LOOKUP = "range_based_lookup"  # e.g., correlation coefficients
    MULTI_VAR_LOOKUP = "multi_var_lookup"  # e.g., 2D matrix (P vs T)
    REFERENCE_ONLY = "reference_only"  # e.g., composition tables


class InterpolationType(str, enum.Enum):
    """Types of interpolation methods"""
    LINEAR = "linear"
    LOGARITHMIC = "logarithmic"
    POLYNOMIAL = "polynomial"
    RANGE_LOOKUP = "range_lookup"
    NONE = "none"


class ImportMethod(str, enum.Enum):
    """Methods used to import table data"""
    DOCUMENT_IMPORT = "document_import"  # Imported from PDF/Excel
    API_IMPORT = "api_import"  # Imported from API (NIST, etc.)
    MANUAL_ENTRY = "manual_entry"  # Typed in by user
    COPIED = "copied"  # Copied from another table


class VerificationStatus(str, enum.Enum):
    """Verification status of table data"""
    VERIFIED = "verified"  # Green - Imported from authoritative source
    CITED = "cited"  # Yellow - Manual with source attribution  
    UNVERIFIED = "unverified"  # Red - No source documentation


class SourceType(str, enum.Enum):
    """Types of data sources"""
    STANDARD = "standard"  # e.g., IAPWS, ISO
    PAPER = "paper"  # Peer-reviewed publication
    HANDBOOK = "handbook"  # Engineering handbook
    REPORT = "report"  # Technical report
    EXPERIMENTAL = "experimental"  # Lab data
    OTHER = "other"


class TemplateType(str, enum.Enum):
    """Types of calculation templates"""
    PROPERTY_TABLE = "property_table"
    WORKFLOW = "workflow"


class PropertyTableTemplate(Base):
    """Template for property table structure (no data)"""
    __tablename__ = "property_table_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Structure definition
    table_type = Column(Enum(TableType), nullable=False)
    
    # Independent variables (e.g., [{"name": "Temperature", "symbol": "T", "unit": "K"}])
    independent_vars = Column(JSON, nullable=False)
    
    # Dependent variables (e.g., [{"name": "Pressure", "symbol": "P", "unit": "Pa"}, ...])
    dependent_vars = Column(JSON, nullable=False)
    
    # Interpolation settings
    interpolation_type = Column(Enum(InterpolationType), default=InterpolationType.LINEAR)
    extrapolation_allowed = Column(Boolean, default=False)
    require_monotonic = Column(Boolean, default=True)
    
    # Template metadata
    created_from_document = Column(Boolean, default=False)
    source_document_example = Column(String)  # Path/name of document used to create template
    
    # Sharing and usage
    is_public = Column(Boolean, default=False)
    workspace_id = Column(Integer, nullable=True)  # NULL = private to user
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    usage_count = Column(Integer, default=0)
    
    # Relationships
    tables = relationship("PropertyTable", back_populates="template")


class PropertyTable(Base):
    """Property lookup tables for temperature-dependent and correlation-based calculations"""
    __tablename__ = "property_tables"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    
    # Link to template (new)
    template_id = Column(Integer, ForeignKey("property_table_templates.id"), nullable=True)
    
    # Scope - table can be global, material-specific, or component-specific
    material_id = Column(Integer, ForeignKey("materials.id"), nullable=True)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    
    # Table data
    data = Column(JSON, nullable=False)  # Array of row objects
    data_points_count = Column(Integer)  # Number of data rows
    
    # Import tracking (new)
    import_method = Column(Enum(ImportMethod), nullable=False)
    source_document_path = Column(String)  # Path to uploaded PDF/Excel
    source_document_hash = Column(String)  # For duplicate detection
    source_url = Column(String)  # If imported from URL
    
    # Source attribution (enhanced)
    source_citation = Column(String)  # Full citation text
    source_type = Column(Enum(SourceType))
    source_authority = Column(String)  # e.g., "IAPWS", "NIST"
    
    # Verification (new)
    verification_status = Column(Enum(VerificationStatus), nullable=False)
    verification_method = Column(String)  # How it was verified
    last_verified = Column(DateTime)
    
    # Quality metadata (new)
    extracted_via_ocr = Column(Boolean, default=False)
    manual_corrections = Column(Integer, default=0)
    data_quality = Column(String)  # "High", "Medium", "Low"
    
    # Metadata
    applicable_conditions = Column(String)  # e.g., "Saturation conditions"
    tags = Column(JSON)  # ["water", "steam", "IAPWS"]
    last_updated = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, nullable=False)
    is_public = Column(Boolean, default=False)
    workspace_id = Column(Integer, nullable=True)
    
    # Relationships
    template = relationship("PropertyTableTemplate", back_populates="tables")
    material = relationship("Material", back_populates="property_tables")
    component = relationship("Component", back_populates="property_tables")


class SystemConstant(Base):
    """Physical and mathematical constants used throughout the system"""
    __tablename__ = "system_constants"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String, unique=True, nullable=False, index=True)  # "g", "PI", "sigma"
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String)
    description = Column(String)
    category = Column(String, nullable=False)  # "Physics", "Mathematics", "Chemistry", "Engineering"
    is_editable = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)


class CalculationTemplate(Base):
    """Templates for property tables and calculation workflows"""
    __tablename__ = "calculation_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String)
    template_type = Column(Enum(TemplateType), nullable=False)
    
    # For property table templates
    table_structure = Column(JSON)  # Defines columns, types, units
    # Example: {
    #   "columns": [
    #     {"name": "temperature", "type": "numeric", "unit": "K", "required": true},
    #     {"name": "density", "type": "numeric", "unit": "kg/m³", "required": true}
    #   ]
    # }
    
    # For workflow templates (future implementation)
    calculation_steps = Column(JSON)  # Ordered list of calculations
    
    # Metadata
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_public = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)