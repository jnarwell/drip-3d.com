"""Isolated formula system models - no foreign key dependencies"""
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean, Text
from datetime import datetime
import enum

from app.db.database import Base


class ReferenceType(enum.Enum):
    """Types of variable references in formulas"""
    COMPONENT_PROPERTY = "component_property"  # Reference to another component's property
    SYSTEM_CONSTANT = "system_constant"        # Reference to system constant (π, g, etc.)
    LITERAL_VALUE = "literal_value"            # Direct numeric value
    FUNCTION_CALL = "function_call"            # Built-in function (sqrt, log, etc.)


class FormulaStatus(enum.Enum):
    """Status of formula evaluation"""
    VALID = "valid"          # Formula evaluates successfully
    ERROR = "error"          # Evaluation error
    CIRCULAR = "circular"    # Circular dependency detected
    MISSING_DEPS = "missing_deps"  # Required dependencies not available
    DISABLED = "disabled"    # Formula temporarily disabled


class PropertyFormula(Base):
    """Formulas that define how property values are calculated - isolated version"""
    __tablename__ = "property_formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What property this formula calculates (stored as ID, no foreign key for now)
    property_definition_id = Column(Integer, nullable=False)
    component_id = Column(Integer, nullable=True)  # NULL = applies to all components
    
    # Formula definition
    name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    formula_expression = Column(Text, nullable=False)  # Mathematical expression
    
    # Example: "sqrt(k * rho * cp) + offset"
    # Variables: k, rho, cp, offset would be defined in PropertyReference
    
    # Validation and metadata
    is_active = Column(Boolean, default=True)
    validation_status = Column(String, default="valid")  # Using string instead of enum for simplicity
    validation_message = Column(String)  # Error details if validation fails
    
    # Dependency management
    calculation_order = Column(Integer, default=0)  # For dependency resolution (lower = calculate first)
    depends_on_formulas = Column(JSON)  # List of formula IDs this depends on
    
    # Audit trail
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String, nullable=False)
    
    # Version control for formulas
    version = Column(Integer, default=1)
    parent_formula_id = Column(Integer, nullable=True)  # Self-reference, no FK constraint


class PropertyReference(Base):
    """Variable references within formulas - isolated version"""
    __tablename__ = "property_references"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, nullable=False)  # Reference to PropertyFormula.id, no FK constraint
    
    # Variable identifier in the formula
    variable_name = Column(String, nullable=False)  # "k", "rho", "temperature", etc.
    reference_type = Column(String, nullable=False)  # Using string instead of enum
    
    # Different reference targets (stored as IDs/symbols, no foreign key constraints)
    # For COMPONENT_PROPERTY
    target_component_id = Column(Integer, nullable=True)
    target_property_definition_id = Column(Integer, nullable=True)
    
    # For SYSTEM_CONSTANT  
    target_constant_symbol = Column(String, nullable=True)
    
    # For LITERAL_VALUE
    literal_value = Column(Float, nullable=True)
    
    # For FUNCTION_CALL
    function_name = Column(String, nullable=True)  # "sqrt", "log", "sin", etc.
    function_args = Column(JSON, nullable=True)    # Arguments for function
    
    # Reference metadata
    description = Column(String)  # Human-readable description of what this variable represents
    units_expected = Column(String)  # Expected units for validation
    default_value = Column(Float, nullable=True)  # Fallback if reference unavailable


class FormulaValidationRule(Base):
    """Rules for validating formula expressions and results - isolated version"""
    __tablename__ = "formula_validation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, nullable=False)  # Reference to PropertyFormula.id, no FK constraint
    
    rule_type = Column(String, nullable=False)  # "range_check", "unit_check", "physics_check"
    rule_expression = Column(String, nullable=False)  # e.g., "result > 0", "result < 1000"
    error_message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)


class CalculationHistory(Base):
    """History of formula calculations for audit and debugging - isolated version"""
    __tablename__ = "calculation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, nullable=False)  # Reference to PropertyFormula.id, no FK constraint
    component_property_id = Column(Integer, nullable=False)  # Reference to ComponentProperty.id, no FK constraint
    
    # Calculation details
    input_values = Column(JSON, nullable=False)  # Variables and their values used
    calculated_value = Column(Float, nullable=False)
    calculation_status = Column(String, nullable=False)  # Using string instead of enum
    error_message = Column(String, nullable=True)
    
    # Performance metrics
    calculation_time_ms = Column(Float, nullable=True)
    dependencies_resolved = Column(Integer, nullable=True)
    
    # Timestamp
    calculated_at = Column(DateTime, default=datetime.utcnow)


class FormulaTemplate(Base):
    """Reusable formula templates for common calculations - isolated version"""
    __tablename__ = "formula_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String, nullable=False)  # "thermal", "mechanical", "electrical", etc.
    
    # Template definition
    template_expression = Column(Text, nullable=False)
    variable_definitions = Column(JSON, nullable=False)  # Variable names, types, descriptions
    
    # Example usage and documentation
    example_usage = Column(Text)
    documentation_url = Column(String)
    reference_paper = Column(String)
    
    # Metadata
    is_public = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)