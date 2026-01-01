"""
Analysis Dashboard Tests - Shared Fixtures

Provides:
- Database fixtures (in-memory SQLite)
- Model fixtures (thermal, simple, rectangle models)
- Analysis fixtures (pre-created instances)
- Client fixtures (FastAPI test client with auth)
"""

import pytest
import sys
import os
from datetime import datetime

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.physics_model import PhysicsModel, PhysicsModelVersion, ModelInstance, ModelInput
from app.models.values import ValueNode, ComputationStatus, NodeType
from app.services.equation_engine import parse_equation


# ==================== DATABASE FIXTURES ====================

import tempfile

# Use file-based SQLite with check_same_thread=False for cross-thread access
# This allows FastAPI TestClient (which runs in a different thread) to share the DB
TEST_DB_FILE = tempfile.mktemp(suffix=".db")
TEST_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"


@pytest.fixture(scope="function")
def db():
    """Create a fresh file-based database for each test with cross-thread access."""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        echo=False
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)

    # Clean up temp file
    if os.path.exists(TEST_DB_FILE):
        os.remove(TEST_DB_FILE)


# ==================== MODEL FIXTURES ====================

@pytest.fixture
def thermal_model(db):
    """Create thermal expansion model: delta_L = CTE * delta_T * L0"""
    model = PhysicsModel(
        name="Thermal Expansion",
        description="Calculates thermal expansion",
        category="thermal",
        created_by="test@drip-3d.com"
    )
    db.add(model)
    db.flush()

    parsed = parse_equation("CTE * delta_T * L0", allowed_inputs=["CTE", "delta_T", "L0"])

    version = PhysicsModelVersion(
        physics_model_id=model.id,
        version=1,
        is_current=True,
        inputs=[
            {"name": "L0", "unit": "m", "required": True, "description": "Initial length"},
            {"name": "CTE", "unit": "1/K", "required": True, "description": "Coefficient of thermal expansion"},
            {"name": "delta_T", "unit": "K", "required": True, "description": "Temperature change"}
        ],
        outputs=[
            {"name": "delta_L", "unit": "m", "description": "Change in length"}
        ],
        equations={"delta_L": "CTE * delta_T * L0"},
        equation_ast={"delta_L": parsed["ast"]},
        created_by="test@drip-3d.com"
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def simple_model(db):
    """Create simple doubling model: y = x * 2"""
    model = PhysicsModel(
        name="Simple",
        description="Simple doubling model",
        category="test",
        created_by="test@drip-3d.com"
    )
    db.add(model)
    db.flush()

    parsed = parse_equation("x * 2", allowed_inputs=["x"])

    version = PhysicsModelVersion(
        physics_model_id=model.id,
        version=1,
        is_current=True,
        inputs=[{"name": "x", "unit": "m", "required": True}],
        outputs=[{"name": "y", "unit": "m"}],
        equations={"y": "x * 2"},
        equation_ast={"y": parsed["ast"]},
        created_by="test@drip-3d.com"
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def rectangle_model(db):
    """Create multi-output rectangle model: area = L*W, perimeter = 2*(L+W)"""
    model = PhysicsModel(
        name="Rectangle",
        description="Rectangle calculations",
        category="geometry",
        created_by="test@drip-3d.com"
    )
    db.add(model)
    db.flush()

    parsed_area = parse_equation("length * width", allowed_inputs=["length", "width"])
    parsed_perimeter = parse_equation("2 * (length + width)", allowed_inputs=["length", "width"])

    version = PhysicsModelVersion(
        physics_model_id=model.id,
        version=1,
        is_current=True,
        inputs=[
            {"name": "length", "unit": "m", "required": True},
            {"name": "width", "unit": "m", "required": True}
        ],
        outputs=[
            {"name": "area", "unit": "m2"},
            {"name": "perimeter", "unit": "m"}
        ],
        equations={
            "area": "length * width",
            "perimeter": "2 * (length + width)"
        },
        equation_ast={
            "area": parsed_area["ast"],
            "perimeter": parsed_perimeter["ast"]
        },
        created_by="test@drip-3d.com"
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


# ==================== ANALYSIS FIXTURES ====================

@pytest.fixture
def thermal_analysis(db, thermal_model):
    """Pre-created thermal expansion analysis with literal bindings."""
    version = thermal_model.current_version

    instance = ModelInstance(
        model_version_id=version.id,
        name="Test Thermal Analysis",
        component_id=None,  # Analysis, not component-attached
        created_by="test@drip-3d.com",
        computation_status=ComputationStatus.PENDING
    )
    db.add(instance)
    db.flush()

    # Add inputs
    inputs = [
        ModelInput(
            model_instance_id=instance.id,
            input_name="CTE",
            literal_value=2.3e-5
        ),
        ModelInput(
            model_instance_id=instance.id,
            input_name="delta_T",
            literal_value=100.0
        ),
        ModelInput(
            model_instance_id=instance.id,
            input_name="L0",
            literal_value=0.003
        ),
    ]
    for inp in inputs:
        db.add(inp)

    db.commit()
    db.refresh(instance)
    return instance


@pytest.fixture
def thermal_analysis_with_outputs(db, thermal_analysis):
    """Thermal analysis with computed output ValueNodes."""
    from app.services.model_evaluation import evaluate_and_attach
    evaluate_and_attach(thermal_analysis, db)
    db.commit()
    db.refresh(thermal_analysis)
    return thermal_analysis


@pytest.fixture
def simple_analysis(db, simple_model):
    """Pre-created simple analysis."""
    version = simple_model.current_version

    instance = ModelInstance(
        model_version_id=version.id,
        name="Simple Analysis",
        component_id=None,
        created_by="test@drip-3d.com",
        computation_status=ComputationStatus.PENDING
    )
    db.add(instance)
    db.flush()

    inp = ModelInput(
        model_instance_id=instance.id,
        input_name="x",
        literal_value=5.0
    )
    db.add(inp)
    db.commit()
    db.refresh(instance)

    return instance


@pytest.fixture
def multiple_analyses(db, thermal_model, simple_model):
    """Create 5 analyses for list testing (A, B, C, D, E)."""
    analyses = []

    for i in range(5):
        model = thermal_model if i % 2 == 0 else simple_model
        version = model.current_version

        instance = ModelInstance(
            model_version_id=version.id,
            name=f"Analysis {chr(65 + i)}",  # A, B, C, D, E
            component_id=None,
            created_by="test@drip-3d.com",
            computation_status=ComputationStatus.VALID
        )
        db.add(instance)
        db.flush()

        # Add minimal inputs based on model type
        if model.name == "Thermal Expansion":
            inputs = [
                ModelInput(model_instance_id=instance.id, input_name="CTE", literal_value=2.3e-5),
                ModelInput(model_instance_id=instance.id, input_name="delta_T", literal_value=100.0),
                ModelInput(model_instance_id=instance.id, input_name="L0", literal_value=0.003),
            ]
        else:
            inputs = [
                ModelInput(model_instance_id=instance.id, input_name="x", literal_value=5.0)
            ]

        for inp in inputs:
            db.add(inp)

        analyses.append(instance)

    db.commit()
    return analyses


@pytest.fixture
def component_attached_instance(db, thermal_model):
    """Create a component-attached instance (NOT an analysis)."""
    version = thermal_model.current_version

    instance = ModelInstance(
        model_version_id=version.id,
        name="Component Instance",
        component_id=1,  # Attached to component - NOT an analysis
        created_by="test@drip-3d.com",
        computation_status=ComputationStatus.VALID
    )
    db.add(instance)
    db.flush()

    inputs = [
        ModelInput(model_instance_id=instance.id, input_name="CTE", literal_value=2.3e-5),
        ModelInput(model_instance_id=instance.id, input_name="delta_T", literal_value=100.0),
        ModelInput(model_instance_id=instance.id, input_name="L0", literal_value=0.003),
    ]
    for inp in inputs:
        db.add(inp)

    db.commit()
    db.refresh(instance)
    return instance


# ==================== CLIENT FIXTURES ====================

@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app, db):
    """
    Create FastAPI test client with database override.

    NOTE: This requires the analysis router to be registered in main.py.
    Until implementation exists, API tests will fail with 404.
    """
    from fastapi.testclient import TestClient
    from app.db.database import get_db

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    """
    Generate mock auth headers for testing.

    In dev mode, these will be accepted.
    In production tests, would need proper Auth0 mock.
    """
    return {
        "Authorization": "Bearer mock-dev-token"
    }


@pytest.fixture
def mock_token():
    """
    Generate mock JWT token for WebSocket testing.

    NOTE: This is a simplified token for dev testing.
    Production would use proper Auth0 tokens.
    """
    return "mock-dev-token"


# ==================== HELPER FIXTURES ====================

@pytest.fixture
def get_analysis_outputs(db):
    """Helper to get output ValueNodes for an analysis."""
    def _get_outputs(instance_id: int):
        return db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
    return _get_outputs


@pytest.fixture
def evaluate_analysis(db):
    """Helper to evaluate an analysis and return outputs."""
    def _evaluate(instance):
        from app.services.model_evaluation import evaluate_and_attach
        result = evaluate_and_attach(instance, db)
        db.commit()
        db.refresh(instance)
        return result
    return _evaluate
