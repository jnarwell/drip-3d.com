"""
Physics Models System

Provides reusable physics/engineering calculation templates that can be:
- Versioned (with full history)
- Instantiated with specific input bindings
- Connected to the ValueNode system for reactive computation

Architecture:
    PhysicsModel (1) ──< PhysicsModelVersion (N)
                               │
                               └──< ModelInstance (N)
                                        │
                                        ├──< ModelInput (N)
                                        └──> ValueNode (N) [outputs via source_model_instance_id]
"""

from sqlalchemy import Column, Integer, String, Text, Boolean, Float, DateTime, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship, selectinload, Session
from sqlalchemy import Enum as SQLEnum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    pass  # Avoid circular imports
from datetime import datetime, timezone

from app.db.database import Base
from app.models.values import ComputationStatus


class PhysicsModel(Base):
    """
    Template identity for a physics model (survives version changes).

    Examples:
    - "Thermal Resistance Calculator"
    - "Beam Deflection Model"
    - "Fluid Flow Analysis"
    """
    __tablename__ = "physics_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    category = Column(String(50), index=True)  # "thermal", "mechanical", "fluid", "electrical"
    created_by = Column(String(100))  # Email of creator
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    versions = relationship(
        "PhysicsModelVersion",
        back_populates="physics_model",
        cascade="all, delete-orphan"
    )

    # Resources relationship (via association table)
    from app.models.resources import resource_physics_models
    resources = relationship(
        "Resource",
        secondary=resource_physics_models,
        back_populates="physics_models"
    )

    def __repr__(self):
        return f"<PhysicsModel {self.id}: {self.name}>"

    @classmethod
    def find_by_name(cls, db: Session, name: str) -> Optional['PhysicsModel']:
        """
        Find a physics model by name (case-insensitive).

        Returns the model with current_version eager-loaded for fast access,
        or None if not found.

        This is the preferred method for MODEL() function lookups as it:
        - Performs case-insensitive matching
        - Eager-loads versions to avoid N+1 queries
        - Returns None instead of raising exceptions

        Args:
            db: Database session
            name: Model name to search for (case-insensitive)

        Returns:
            PhysicsModel with versions loaded, or None if not found

        Example:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")
            if model:
                current = next((v for v in model.versions if v.is_current), None)
                print(current.equations)
        """
        return db.query(cls).options(
            selectinload(cls.versions)
        ).filter(
            func.lower(cls.name) == name.lower()
        ).first()

    @property
    def current_version(self) -> Optional['PhysicsModelVersion']:
        """
        Get the current (active) version of this model.

        Returns None if no version is marked as current.
        """
        return next((v for v in self.versions if v.is_current), None)


class PhysicsModelVersion(Base):
    """
    Specific version of a physics model with equations and schemas.

    Contains:
    - Input schema: what inputs are required and their units
    - Output schema: what outputs are produced and their units
    - Equations: mathematical relationships between inputs and outputs

    Example inputs schema:
    [
        {"name": "length", "unit_id": 5, "required": True, "description": "Beam length"},
        {"name": "width", "unit_id": 5, "required": True, "description": "Beam width"}
    ]

    Example outputs schema:
    [
        {"name": "area", "unit_id": 6, "expression": "length * width"},
        {"name": "perimeter", "unit_id": 5, "expression": "2 * (length + width)"}
    ]
    """
    __tablename__ = "physics_model_versions"

    id = Column(Integer, primary_key=True)
    physics_model_id = Column(Integer, ForeignKey("physics_models.id"), nullable=False)
    version = Column(Integer, nullable=False, default=1)
    is_current = Column(Boolean, default=True, index=True)
    changelog = Column(Text)  # What changed in this version

    # Schema definitions (JSONB)
    inputs = Column(JSON)   # [{"name": "...", "unit_id": ..., "required": ..., "description": ...}]
    outputs = Column(JSON)  # [{"name": "...", "expression": "...", "unit_id": ..., "description": ...}]
    equations = Column(JSON)  # {"output_name": "expression", ...} - alternative compact format

    # Cached representations
    equation_ast = Column(JSON)  # Pre-parsed AST for fast evaluation
    equation_latex = Column(Text)  # LaTeX rendering for display

    created_by = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    physics_model = relationship("PhysicsModel", back_populates="versions")
    instances = relationship(
        "ModelInstance",
        back_populates="model_version",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint('physics_model_id', 'version', name='uq_model_version'),
    )

    def __repr__(self):
        return f"<PhysicsModelVersion {self.id}: v{self.version} of model {self.physics_model_id}>"


class ModelInstance(Base):
    """
    Specific binding of a physics model version to concrete inputs.

    Can optionally be attached to a Component for contextual computation.
    When component_id is NULL, this is a standalone "Analysis" that can be
    referenced by name from expressions.

    When computed:
    - Reads input values from bound sources (ValueNodes, lookups, literals)
    - Evaluates equations
    - Creates/updates output ValueNodes with source_model_instance_id set
    """
    __tablename__ = "model_instances"

    id = Column(Integer, primary_key=True)
    model_version_id = Column(Integer, ForeignKey("physics_model_versions.id"), nullable=False)
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True, index=True)
    name = Column(String(200))  # Optional friendly name for this instance
    description = Column(Text)  # Optional description for analyses

    created_by = Column(String(100))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_computed = Column(DateTime)  # When outputs were last calculated
    computation_status = Column(SQLEnum(ComputationStatus))  # Reuse from values.py
    error_message = Column(Text, nullable=True)  # Detailed error message when computation_status is ERROR

    # Relationships
    model_version = relationship("PhysicsModelVersion", back_populates="instances")
    component = relationship("Component")
    inputs = relationship(
        "ModelInput",
        back_populates="model_instance",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<ModelInstance {self.id}: {self.name or 'unnamed'} (version {self.model_version_id})>"

    @property
    def is_analysis(self) -> bool:
        """True if this is a standalone analysis (not attached to a component)."""
        return self.component_id is None

    @property
    def is_component_instance(self) -> bool:
        """True if this is attached to a component."""
        return self.component_id is not None

    def to_dict_full(self) -> dict:
        """
        Return a full dictionary representation for API responses.

        Includes model info, inputs, and computed outputs.
        """
        from app.models.values import ValueNode

        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "model_version_id": self.model_version_id,
            "component_id": self.component_id,
            "is_analysis": self.is_analysis,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_computed": self.last_computed.isoformat() if self.last_computed else None,
            "computation_status": self.computation_status.value if self.computation_status else None,
            "inputs": [],
            "outputs": [],
        }

        # Add model info if loaded
        if self.model_version:
            result["model"] = {
                "id": self.model_version.physics_model_id,
                "name": self.model_version.physics_model.name if self.model_version.physics_model else None,
                "version": self.model_version.version,
            }

        # Add inputs
        for inp in self.inputs:
            input_dict = {
                "name": inp.input_name,
                "source_type": None,
                "value": None,
            }
            if inp.source_value_node_id:
                input_dict["source_type"] = "value_node"
                input_dict["source_value_node_id"] = inp.source_value_node_id
                if inp.source_value_node:
                    val, unit_id, valid = inp.source_value_node.get_effective_value()
                    input_dict["value"] = val
                    input_dict["unit_id"] = unit_id
            elif inp.source_lookup:
                input_dict["source_type"] = "lookup"
                input_dict["lookup"] = inp.source_lookup
            elif inp.literal_value is not None:
                input_dict["source_type"] = "literal"
                input_dict["value"] = inp.literal_value
                input_dict["unit_id"] = inp.literal_unit_id
            result["inputs"].append(input_dict)

        return result


class ModelInput(Base):
    """
    Binds an input name to a concrete source for a ModelInstance.

    Source can be one of:
    - source_value_node_id: Reference to a ValueNode
    - source_lookup: LOOKUP expression {"table": "...", "key": "...", "conditions": {...}}
    - literal_value + literal_unit_id: Direct constant value

    Only one source type should be populated per input.
    """
    __tablename__ = "model_inputs"

    id = Column(Integer, primary_key=True)
    model_instance_id = Column(Integer, ForeignKey("model_instances.id"), nullable=False)
    input_name = Column(String(100), nullable=False)  # Must match an input name in version schema

    # Source binding - ONE of these should be set
    source_value_node_id = Column(Integer, ForeignKey("value_nodes.id"), nullable=True)
    source_lookup = Column(JSON, nullable=True)  # {"table": "...", "key": "...", "conditions": {...}}
    literal_value = Column(Float, nullable=True)
    literal_unit_id = Column(Integer, ForeignKey("units.id"), nullable=True)

    # Relationships
    model_instance = relationship("ModelInstance", back_populates="inputs")
    source_value_node = relationship("ValueNode")
    literal_unit = relationship("Unit")

    def __repr__(self):
        if self.source_value_node_id:
            return f"<ModelInput {self.input_name}: -> ValueNode {self.source_value_node_id}>"
        elif self.source_lookup:
            return f"<ModelInput {self.input_name}: LOOKUP>"
        elif self.literal_value is not None:
            return f"<ModelInput {self.input_name}: {self.literal_value}>"
        return f"<ModelInput {self.input_name}: unbound>"
