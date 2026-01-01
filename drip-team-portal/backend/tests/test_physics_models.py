"""
Physics Models Database Tests

Tests for PhysicsModel, PhysicsModelVersion, ModelInstance, ModelInput models.
Note: These tests require a database connection.
"""

import pytest
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError

from app.db.database import Base
from app.models.physics_model import (
    PhysicsModel,
    PhysicsModelVersion,
    ModelInstance,
    ModelInput
)
from app.models.values import ValueNode, ComputationStatus, NodeType


# Use in-memory SQLite for testing (fast, isolated)
TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)


class TestPhysicsModel:
    """Test PhysicsModel creation and properties."""

    def test_create_physics_model(self, db_session):
        """Create a basic physics model."""
        model = PhysicsModel(
            name="Thermal Expansion Calculator",
            category="thermal",
            description="Calculates thermal expansion for materials",
            created_by="test@example.com"
        )
        db_session.add(model)
        db_session.commit()

        assert model.id is not None
        assert model.name == "Thermal Expansion Calculator"
        assert model.category == "thermal"
        assert model.created_at is not None

    def test_model_name_required(self, db_session):
        """Model name is required."""
        model = PhysicsModel(category="thermal")  # No name
        db_session.add(model)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_model_category_optional(self, db_session):
        """Category is optional."""
        model = PhysicsModel(name="Test Model")
        db_session.add(model)
        db_session.commit()

        assert model.id is not None
        assert model.category is None


class TestPhysicsModelVersion:
    """Test PhysicsModelVersion creation and relationships."""

    def test_create_version(self, db_session):
        """Create a model version with inputs/outputs schema."""
        model = PhysicsModel(name="Test Model", category="thermal")
        db_session.add(model)
        db_session.flush()

        version = PhysicsModelVersion(
            physics_model_id=model.id,
            version=1,
            is_current=True,
            inputs=[
                {"name": "length", "unit": "m", "required": True, "description": "Initial length"},
                {"name": "CTE", "unit": "1/K", "required": True, "description": "Coefficient of thermal expansion"},
                {"name": "delta_T", "unit": "K", "required": True, "description": "Temperature change"}
            ],
            outputs=[
                {"name": "expansion", "unit": "m", "description": "Calculated expansion"}
            ],
            equations={
                "expansion": "length * CTE * delta_T"
            },
            created_by="test@example.com"
        )
        db_session.add(version)
        db_session.commit()

        assert version.id is not None
        assert version.version == 1
        assert version.is_current == True
        assert len(version.inputs) == 3
        assert len(version.outputs) == 1
        assert version.equations["expansion"] == "length * CTE * delta_T"

    def test_version_relationship(self, db_session):
        """Test relationship between model and version."""
        model = PhysicsModel(name="Test Model", category="thermal")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)

        db_session.add(model)
        db_session.commit()

        assert len(model.versions) == 1
        assert model.versions[0].physics_model_id == model.id
        assert version.physics_model == model

    def test_unique_version_constraint(self, db_session):
        """Each (physics_model_id, version) pair must be unique."""
        model = PhysicsModel(name="Test Model", category="test")
        db_session.add(model)
        db_session.flush()

        v1 = PhysicsModelVersion(physics_model_id=model.id, version=1)
        db_session.add(v1)
        db_session.flush()

        # Try to add another version with same number
        v2 = PhysicsModelVersion(physics_model_id=model.id, version=1)
        db_session.add(v2)

        with pytest.raises(IntegrityError):
            db_session.flush()

    def test_multiple_versions(self, db_session):
        """Model can have multiple versions."""
        model = PhysicsModel(name="Test Model", category="test")
        db_session.add(model)
        db_session.flush()

        v1 = PhysicsModelVersion(physics_model_id=model.id, version=1, is_current=False)
        v2 = PhysicsModelVersion(physics_model_id=model.id, version=2, is_current=True)

        db_session.add_all([v1, v2])
        db_session.commit()

        assert len(model.versions) == 2


class TestModelInstance:
    """Test ModelInstance creation and bindings."""

    def test_create_instance(self, db_session):
        """Create a model instance."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(
            model_version_id=version.id,
            name="Crucible Expansion Calculator",
            created_by="test@example.com"
        )
        db_session.add(instance)
        db_session.commit()

        assert instance.id is not None
        assert instance.name == "Crucible Expansion Calculator"
        assert instance.model_version_id == version.id

    def test_instance_relationship(self, db_session):
        """Test relationship between version and instance."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.commit()

        assert instance.model_version == version
        assert instance in version.instances


class TestModelInput:
    """Test ModelInput bindings."""

    def test_create_literal_input(self, db_session):
        """Create input bound to literal value."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.flush()

        model_input = ModelInput(
            model_instance_id=instance.id,
            input_name="delta_T",
            literal_value=500.0  # 500 K
        )
        db_session.add(model_input)
        db_session.commit()

        assert model_input.id is not None
        assert model_input.input_name == "delta_T"
        assert model_input.literal_value == 500.0
        assert model_input.source_value_node_id is None
        assert model_input.source_lookup is None

    def test_create_lookup_input(self, db_session):
        """Create input bound to table lookup."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.flush()

        model_input = ModelInput(
            model_instance_id=instance.id,
            input_name="CTE",
            source_lookup={
                "table": "material_properties",
                "column": "CTE",
                "conditions": {"material": "alumina", "temperature": 298}
            }
        )
        db_session.add(model_input)
        db_session.commit()

        assert model_input.source_lookup is not None
        assert model_input.source_lookup["table"] == "material_properties"

    def test_input_relationship(self, db_session):
        """Test relationship between instance and inputs."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.flush()

        input1 = ModelInput(model_instance_id=instance.id, input_name="length", literal_value=0.003)
        input2 = ModelInput(model_instance_id=instance.id, input_name="delta_T", literal_value=500)

        db_session.add_all([input1, input2])
        db_session.commit()

        assert len(instance.inputs) == 2


class TestValueNodeSourceTracking:
    """Test ValueNode source_model_instance_id tracking."""

    def test_create_value_node_with_source(self, db_session):
        """Create ValueNode with source_model_instance_id."""
        # First create the model infrastructure
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.flush()

        # Create ValueNode with source tracking
        value_node = ValueNode(
            node_type=NodeType.LITERAL,
            numeric_value=0.00001215,
            computed_value=0.00001215,
            computed_unit_symbol="m",
            computation_status=ComputationStatus.VALID,
            source_model_instance_id=instance.id,
            source_output_name="thermal_expansion",
            description="#SYSTEM.thermal_expansion"
        )
        db_session.add(value_node)
        db_session.commit()

        assert value_node.id is not None
        assert value_node.source_model_instance_id == instance.id
        assert value_node.source_output_name == "thermal_expansion"

    def test_value_node_source_is_optional(self, db_session):
        """source_model_instance_id should be optional."""
        value_node = ValueNode(
            node_type=NodeType.LITERAL,
            numeric_value=42.0,
            computed_value=42.0,
            computation_status=ComputationStatus.VALID
        )
        db_session.add(value_node)
        db_session.commit()

        assert value_node.id is not None
        assert value_node.source_model_instance_id is None


class TestCascadeDelete:
    """Test cascade delete behavior."""

    def test_delete_model_cascades_to_versions(self, db_session):
        """Deleting model should delete its versions."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.commit()

        version_id = version.id
        db_session.delete(model)
        db_session.commit()

        # Version should be gone
        result = db_session.query(PhysicsModelVersion).filter_by(id=version_id).first()
        assert result is None

    def test_delete_version_cascades_to_instances(self, db_session):
        """Deleting version should delete its instances."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.commit()

        instance_id = instance.id
        db_session.delete(version)
        db_session.commit()

        result = db_session.query(ModelInstance).filter_by(id=instance_id).first()
        assert result is None

    def test_delete_instance_cascades_to_inputs(self, db_session):
        """Deleting instance should delete its inputs."""
        model = PhysicsModel(name="Test Model", category="test")
        version = PhysicsModelVersion(version=1, is_current=True)
        model.versions.append(version)
        db_session.add(model)
        db_session.flush()

        instance = ModelInstance(model_version_id=version.id, name="Test Instance")
        db_session.add(instance)
        db_session.flush()

        model_input = ModelInput(model_instance_id=instance.id, input_name="length", literal_value=0.003)
        db_session.add(model_input)
        db_session.commit()

        input_id = model_input.id
        db_session.delete(instance)
        db_session.commit()

        result = db_session.query(ModelInput).filter_by(id=input_id).first()
        assert result is None
