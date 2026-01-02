"""
Value System - Universal Value Nodes with Expressions

Every value in the system (property, table cell, test result) is a ValueNode that can be:
- A literal number with units
- A reference to another ValueNode
- A mathematical expression combining ValueNodes

Features:
- Reactive dependency tracking
- Stale detection and recalculation
- Circular dependency prevention
- Unit propagation through expressions
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSON
from datetime import datetime, timezone
import enum

from app.db.database import Base


class NodeType(enum.Enum):
    """Types of value nodes."""
    LITERAL = "literal"           # Direct numeric value with unit
    REFERENCE = "reference"       # Points to another ValueNode
    EXPRESSION = "expression"     # Mathematical expression
    TABLE_LOOKUP = "table_lookup" # Table lookup (Phase 4)


class ComputationStatus(enum.Enum):
    """Status of computed value."""
    VALID = "valid"           # Computed value is current
    STALE = "stale"           # Dependencies changed, needs recalculation
    ERROR = "error"           # Computation failed
    PENDING = "pending"       # Not yet computed
    CIRCULAR = "circular"     # Circular dependency detected


class ValueNode(Base):
    """
    Universal value container - the core of the value system.

    Can represent:
    - Literal: value=10, unit_id=<meter>
    - Reference: references another ValueNode
    - Expression: expression_string="sqrt(#cmp001.length * #cmp001.width)"

    The computed_value and computed_unit_id store the cached result.
    """
    __tablename__ = "value_nodes"

    id = Column(Integer, primary_key=True)

    # Type of node
    node_type = Column(SQLEnum(NodeType), nullable=False, default=NodeType.LITERAL)

    # For LITERAL nodes: direct numeric value
    numeric_value = Column(Float, nullable=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # For EXPRESSION nodes: the expression string and parsed AST
    expression_string = Column(Text, nullable=True)  # Original user input: "sqrt(#cmp001.length * 2)"
    parsed_expression = Column(JSON, nullable=True)  # Parsed AST for evaluation

    # For REFERENCE nodes: points to another ValueNode
    reference_node_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=True)

    # Computed/cached result (for expressions and references)
    computed_value = Column(Float, nullable=True)
    computed_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)
    computed_unit_symbol = Column(String, nullable=True)  # SI unit symbol for display (e.g., "m", "Pa")
    computation_status = Column(SQLEnum(ComputationStatus), default=ComputationStatus.PENDING)
    computation_error = Column(Text, nullable=True)
    last_computed = Column(DateTime, nullable=True)

    # Metadata
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    created_by = Column(String, nullable=True)

    # Description/name for debugging and display
    description = Column(String, nullable=True)

    # Physics Model output tracking
    # When a ModelInstance computes, it creates ValueNodes with these set
    source_model_instance_id = Column(Integer, ForeignKey("model_instances.id"), nullable=True)
    source_output_name = Column(String(100), nullable=True)  # Which output this represents

    # Relationships
    unit = relationship("Unit", foreign_keys=[unit_id])
    computed_unit = relationship("Unit", foreign_keys=[computed_unit_id])
    reference_node = relationship("ValueNode", remote_side=[id], foreign_keys=[reference_node_id])

    # Dependencies (what this node depends on)
    dependencies = relationship(
        "ValueDependency",
        foreign_keys="ValueDependency.dependent_id",
        back_populates="dependent_node",
        cascade="all, delete-orphan"
    )

    # Dependents (what depends on this node)
    dependents = relationship(
        "ValueDependency",
        foreign_keys="ValueDependency.source_id",
        back_populates="source_node"
    )

    def __repr__(self):
        if self.node_type == NodeType.LITERAL:
            return f"<ValueNode {self.id}: {self.numeric_value} (literal)>"
        elif self.node_type == NodeType.EXPRESSION:
            return f"<ValueNode {self.id}: {self.expression_string[:30]}... (expression)>"
        elif self.node_type == NodeType.REFERENCE:
            return f"<ValueNode {self.id}: -> {self.reference_node_id} (reference)>"
        return f"<ValueNode {self.id}: {self.node_type}>"

    def get_effective_value(self) -> tuple:
        """
        Get the effective value and unit_id for this node.

        Returns: (value, unit_id, is_valid)
        """
        if self.node_type == NodeType.LITERAL:
            return (self.numeric_value, self.unit_id, True)
        elif self.computation_status == ComputationStatus.VALID:
            return (self.computed_value, self.computed_unit_id, True)
        else:
            return (self.computed_value, self.computed_unit_id, False)

    def mark_stale(self):
        """Mark this node as needing recalculation."""
        if self.node_type != NodeType.LITERAL:
            self.computation_status = ComputationStatus.STALE

    def is_stale(self) -> bool:
        """Check if this node needs recalculation."""
        return self.computation_status in (ComputationStatus.STALE, ComputationStatus.PENDING)


class ValueDependency(Base):
    """
    Tracks dependencies between ValueNodes.

    When source_node changes, dependent_node needs to be recalculated.

    Example:
        If ValueNode A has expression "#B + #C", then:
        - A is dependent on B: ValueDependency(dependent_id=A, source_id=B, variable_name="B")
        - A is dependent on C: ValueDependency(dependent_id=A, source_id=C, variable_name="C")
    """
    __tablename__ = "value_dependencies"

    id = Column(Integer, primary_key=True)

    # The node that uses another value (the dependent)
    dependent_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=False)

    # The node being used (the source/dependency)
    source_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=False)

    # How it's referenced in the expression (e.g., "cmp001.length")
    variable_name = Column(String, nullable=True)

    # Relationships
    dependent_node = relationship(
        "ValueNode",
        foreign_keys=[dependent_id],
        back_populates="dependencies"
    )
    source_node = relationship(
        "ValueNode",
        foreign_keys=[source_id],
        back_populates="dependents"
    )

    def __repr__(self):
        return f"<ValueDependency {self.dependent_id} depends on {self.source_id} as '{self.variable_name}'>"


class PropertyValueLink(Base):
    """
    Links ComponentProperty to ValueNode.

    This allows any property to either:
    - Have a direct value (value_node points to a LITERAL)
    - Be computed (value_node points to an EXPRESSION)
    - Reference another property (value_node points to a REFERENCE)
    """
    __tablename__ = "property_value_links"

    id = Column(Integer, primary_key=True)

    # The component property
    component_property_id = Column(Integer, ForeignKey("component_properties.id"), nullable=False, unique=True)

    # The value node
    value_node_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=False)

    # Relationships
    value_node = relationship("ValueNode")

    def __repr__(self):
        return f"<PropertyValueLink property={self.component_property_id} -> node={self.value_node_id}>"


class MaterialPropertyValueLink(Base):
    """
    Links MaterialProperty to ValueNode for material-level expressions.
    """
    __tablename__ = "material_property_value_links"

    id = Column(Integer, primary_key=True)

    # The material property
    material_property_id = Column(Integer, ForeignKey("material_properties.id"), nullable=False, unique=True)

    # The value node
    value_node_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=False)

    # Relationships
    value_node = relationship("ValueNode")

    def __repr__(self):
        return f"<MaterialPropertyValueLink material_prop={self.material_property_id} -> node={self.value_node_id}>"
