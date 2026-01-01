"""
Integration Tests: Model Evaluation Service

Tests the model evaluation service that computes outputs.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.physics_model import (
    PhysicsModel,
    PhysicsModelVersion,
    ModelInstance,
    ModelInput
)
from app.models.values import ValueNode, ComputationStatus
from app.services.model_evaluation import (
    evaluate_model_instance,
    resolve_model_input,
    get_instance_outputs,
    invalidate_instance_outputs,
    ModelEvaluationError
)
from app.services.equation_engine import parse_equation


# Test database
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="function")
def db():
    """Create fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def simple_model(db):
    """Create a simple addition model."""
    model = PhysicsModel(name="Addition", category="test")

    # Parse and store AST
    parsed = parse_equation("a + b", allowed_inputs=["a", "b"])

    version = PhysicsModelVersion(
        version=1,
        is_current=True,
        inputs=[
            {"name": "a", "unit": "m", "required": True},
            {"name": "b", "unit": "m", "required": True}
        ],
        outputs=[
            {"name": "sum", "unit": "m"}
        ],
        equations={"sum": "a + b"},
        equation_ast={"sum": parsed["ast"]}
    )

    model.versions.append(version)
    db.add(model)
    db.commit()

    return model, version


@pytest.fixture
def thermal_model(db):
    """Create a thermal expansion model."""
    model = PhysicsModel(name="Thermal Expansion", category="thermal")

    parsed = parse_equation("length * CTE * delta_T", allowed_inputs=["length", "CTE", "delta_T"])

    version = PhysicsModelVersion(
        version=1,
        is_current=True,
        inputs=[
            {"name": "length", "unit": "m", "required": True},
            {"name": "CTE", "unit": "1/K", "required": True},
            {"name": "delta_T", "unit": "K", "required": True}
        ],
        outputs=[
            {"name": "expansion", "unit": "m"}
        ],
        equations={"expansion": "length * CTE * delta_T"},
        equation_ast={"expansion": parsed["ast"]}
    )

    model.versions.append(version)
    db.add(model)
    db.commit()

    return model, version


class TestResolveModelInput:
    """Test input resolution."""

    def test_resolve_literal_value(self, db):
        """Resolve literal value input."""
        model_input = ModelInput(
            input_name="test_input",
            literal_value=42.0
        )

        result = resolve_model_input(model_input, db)
        assert result == 42.0

    def test_resolve_value_node_reference(self, db):
        """Resolve input that references a ValueNode."""
        # Create a ValueNode
        value_node = ValueNode(
            numeric_value=100.0,
            computed_value=100.0,
            computation_status=ComputationStatus.VALID
        )
        db.add(value_node)
        db.flush()

        # Create input that references it
        model_input = ModelInput(
            input_name="test_input",
            source_value_node_id=value_node.id
        )

        result = resolve_model_input(model_input, db)
        assert result == 100.0

    def test_resolve_missing_value_node(self, db):
        """Resolving missing ValueNode should raise error."""
        model_input = ModelInput(
            input_name="test_input",
            source_value_node_id=99999  # Non-existent
        )

        with pytest.raises(ModelEvaluationError):
            resolve_model_input(model_input, db)


class TestEvaluateModelInstance:
    """Test model instance evaluation."""

    def test_evaluate_simple_addition(self, db, simple_model):
        """Evaluate simple addition model."""
        model, version = simple_model

        instance = ModelInstance(
            model_version_id=version.id,
            name="Test Instance"
        )
        db.add(instance)
        db.flush()

        # Add inputs
        input_a = ModelInput(
            model_instance_id=instance.id,
            input_name="a",
            literal_value=2.0
        )
        input_b = ModelInput(
            model_instance_id=instance.id,
            input_name="b",
            literal_value=3.0
        )
        db.add_all([input_a, input_b])
        db.flush()

        # Evaluate
        output_nodes = evaluate_model_instance(instance, db)

        assert len(output_nodes) == 1
        assert output_nodes[0].source_output_name == "sum"
        assert output_nodes[0].computed_value == 5.0  # 2 + 3
        assert output_nodes[0].source_model_instance_id == instance.id

    def test_evaluate_thermal_expansion(self, db, thermal_model):
        """Evaluate thermal expansion model."""
        model, version = thermal_model

        instance = ModelInstance(
            model_version_id=version.id,
            name="Crucible Expansion"
        )
        db.add(instance)
        db.flush()

        # Add inputs
        inputs = [
            ModelInput(model_instance_id=instance.id, input_name="length", literal_value=0.003),      # 3mm
            ModelInput(model_instance_id=instance.id, input_name="CTE", literal_value=8.1e-6),        # 1/K
            ModelInput(model_instance_id=instance.id, input_name="delta_T", literal_value=500),       # K
        ]
        db.add_all(inputs)
        db.flush()

        # Evaluate
        output_nodes = evaluate_model_instance(instance, db)

        assert len(output_nodes) == 1
        assert output_nodes[0].source_output_name == "expansion"

        # Expected: 0.003 * 8.1e-6 * 500 = 0.00001215 m
        expected = 0.003 * 8.1e-6 * 500
        assert abs(output_nodes[0].computed_value - expected) < 1e-15

    def test_evaluate_missing_input(self, db, simple_model):
        """Evaluating with missing required input should fail."""
        model, version = simple_model

        instance = ModelInstance(
            model_version_id=version.id,
            name="Incomplete Instance"
        )
        db.add(instance)
        db.flush()

        # Only add one input (missing "b")
        input_a = ModelInput(
            model_instance_id=instance.id,
            input_name="a",
            literal_value=2.0
        )
        db.add(input_a)
        db.flush()

        with pytest.raises(ModelEvaluationError):
            evaluate_model_instance(instance, db)


class TestGetAndInvalidateOutputs:
    """Test output retrieval and invalidation."""

    def test_get_instance_outputs(self, db, simple_model):
        """Get outputs for an evaluated instance."""
        model, version = simple_model

        instance = ModelInstance(model_version_id=version.id, name="Test")
        db.add(instance)
        db.flush()

        input_a = ModelInput(model_instance_id=instance.id, input_name="a", literal_value=1.0)
        input_b = ModelInput(model_instance_id=instance.id, input_name="b", literal_value=2.0)
        db.add_all([input_a, input_b])
        db.flush()

        # Evaluate
        evaluate_model_instance(instance, db)
        db.commit()

        # Get outputs
        outputs = get_instance_outputs(instance, db)

        assert len(outputs) == 1
        assert outputs[0].source_output_name == "sum"

    def test_invalidate_outputs(self, db, simple_model):
        """Invalidate outputs marks them as stale."""
        model, version = simple_model

        instance = ModelInstance(model_version_id=version.id, name="Test")
        db.add(instance)
        db.flush()

        input_a = ModelInput(model_instance_id=instance.id, input_name="a", literal_value=1.0)
        input_b = ModelInput(model_instance_id=instance.id, input_name="b", literal_value=2.0)
        db.add_all([input_a, input_b])
        db.flush()

        # Evaluate
        output_nodes = evaluate_model_instance(instance, db)
        db.commit()

        # Verify valid status
        assert output_nodes[0].computation_status == ComputationStatus.VALID

        # Invalidate
        count = invalidate_instance_outputs(instance, db)

        assert count == 1
        assert output_nodes[0].computation_status == ComputationStatus.STALE
        assert instance.computation_status == ComputationStatus.STALE
