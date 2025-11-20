"""Formula system models for property calculations and inter-component dependencies"""
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SQLEnum, DateTime, JSON, Boolean, Text
from sqlalchemy.orm import relationship
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
    """Formulas that define how property values are calculated"""
    __tablename__ = "property_formulas"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # What property this formula calculates
    property_definition_id = Column(Integer, ForeignKey("property_definitions.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True)  # NULL = applies to all components
    
    # Formula definition
    name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    formula_expression = Column(Text, nullable=False)  # Mathematical expression
    
    # Example: "sqrt(k * rho * cp) + offset"
    # Variables: k, rho, cp, offset would be defined in PropertyReference
    
    # Validation and metadata
    is_active = Column(Boolean, default=True)
    validation_status = Column(SQLEnum(FormulaStatus), default=FormulaStatus.VALID)
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
    parent_formula_id = Column(Integer, ForeignKey("property_formulas.id"), nullable=True)
    
    # Relationships
    property_definition = relationship("PropertyDefinition")
    component = relationship("Component")
    parent_formula = relationship("PropertyFormula", remote_side=[id])
    child_formulas = relationship("PropertyFormula", remote_side=[parent_formula_id])
    references = relationship("PropertyReference", back_populates="formula", cascade="all, delete-orphan")
    calculated_properties = relationship("ComponentProperty", back_populates="formula")


class PropertyReference(Base):
    """Variable references within formulas"""
    __tablename__ = "property_references"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, ForeignKey("property_formulas.id"), nullable=False)
    
    # Variable identifier in the formula
    variable_name = Column(String, nullable=False)  # "k", "rho", "temperature", etc.
    reference_type = Column(SQLEnum(ReferenceType), nullable=False)
    
    # Different reference targets
    # For COMPONENT_PROPERTY
    target_component_id = Column(Integer, ForeignKey("components.id"), nullable=True)
    target_property_definition_id = Column(Integer, ForeignKey("property_definitions.id"), nullable=True)
    
    # For SYSTEM_CONSTANT  
    target_constant_symbol = Column(String, ForeignKey("system_constants.symbol"), nullable=True)
    
    # For LITERAL_VALUE
    literal_value = Column(Float, nullable=True)
    
    # For FUNCTION_CALL
    function_name = Column(String, nullable=True)  # "sqrt", "log", "sin", etc.
    function_args = Column(JSON, nullable=True)    # Arguments for function
    
    # Reference metadata
    description = Column(String)  # Human-readable description of what this variable represents
    units_expected = Column(String)  # Expected units for validation
    default_value = Column(Float, nullable=True)  # Fallback if reference unavailable
    
    # Relationships
    formula = relationship("PropertyFormula", back_populates="references")
    target_component = relationship("Component", foreign_keys=[target_component_id])
    target_property_definition = relationship("PropertyDefinition", foreign_keys=[target_property_definition_id])
    target_constant = relationship("SystemConstant", foreign_keys=[target_constant_symbol])


class FormulaValidationRule(Base):
    """Rules for validating formula expressions and results"""
    __tablename__ = "formula_validation_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, ForeignKey("property_formulas.id"), nullable=False)
    
    rule_type = Column(String, nullable=False)  # "range_check", "unit_check", "physics_check"
    rule_expression = Column(String, nullable=False)  # e.g., "result > 0", "result < 1000"
    error_message = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    formula = relationship("PropertyFormula")


class CalculationHistory(Base):
    """History of formula calculations for audit and debugging"""
    __tablename__ = "calculation_history"
    
    id = Column(Integer, primary_key=True, index=True)
    formula_id = Column(Integer, ForeignKey("property_formulas.id"), nullable=False)
    component_property_id = Column(Integer, ForeignKey("component_properties.id"), nullable=False)
    
    # Calculation details
    input_values = Column(JSON, nullable=False)  # Variables and their values used
    calculated_value = Column(Float, nullable=False)
    calculation_status = Column(SQLEnum(FormulaStatus), nullable=False)
    error_message = Column(String, nullable=True)
    
    # Performance metrics
    calculation_time_ms = Column(Float, nullable=True)
    dependencies_resolved = Column(Integer, nullable=True)
    
    # Timestamp
    calculated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    formula = relationship("PropertyFormula")
    component_property = relationship("ComponentProperty")


class FormulaTemplate(Base):
    """Reusable formula templates for common calculations"""
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