"""
MODEL() Function Tests - Shared Fixtures and Stubs

Phase 1: Stubs return hardcoded values for TDD
Phase 2: Replace stubs with real imports from app.services.*

PHASE 2 ACTIVE: Using real evaluate_inline_model implementation
"""

import pytest
import sys
import os
import re
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.db.database import Base
from app.models.physics_model import PhysicsModel, PhysicsModelVersion, ModelInstance, ModelInput
from app.models.values import ValueNode, NodeType, ComputationStatus
from app.services.equation_engine import parse_equation

# Phase 2: Import real evaluate_inline_model
from app.services.model_evaluation import evaluate_inline_model, ModelEvaluationError


# ==================== DATABASE FIXTURES ====================

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db():
    """Create a fresh in-memory database for each test."""
    engine = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()
    Base.metadata.drop_all(engine)


# ==================== REAL IMPLEMENTATIONS (from value_engine.py) ====================

# Import real pattern from value_engine.py
try:
    from app.services.value_engine import MODEL_PATTERN, _split_model_params, _parse_model_binding
    REAL_MODEL_PATTERN = MODEL_PATTERN
    REAL_SPLIT_PARAMS = _split_model_params
    REAL_PARSE_BINDING = _parse_model_binding
except ImportError:
    # Fallback stubs if not yet implemented
    REAL_MODEL_PATTERN = re.compile(
        r'MODEL\s*\(\s*"([^"]+)"(?:\s*,\s*([^)]+))?\s*\)',
        re.UNICODE
    )

    def REAL_SPLIT_PARAMS(params_str):
        """Stub for _split_model_params."""
        raise NotImplementedError("_split_model_params not yet imported")

    def REAL_PARSE_BINDING(binding_str):
        """Stub for _parse_model_binding."""
        raise NotImplementedError("_parse_model_binding not yet imported")


@pytest.fixture
def model_pattern():
    """Real MODEL() regex pattern from value_engine.py."""
    return REAL_MODEL_PATTERN


@pytest.fixture
def split_model_params():
    """Real _split_model_params function."""
    return REAL_SPLIT_PARAMS


@pytest.fixture
def parse_model_binding():
    """Real _parse_model_binding function."""
    return REAL_PARSE_BINDING


# ==================== STUB IMPLEMENTATIONS ====================

@pytest.fixture
def stub_evaluate_inline_model():
    """
    Stub for evaluate_inline_model() that returns hardcoded values.

    Replace this with real implementation in Phase 2.
    """
    def evaluate(model_name: str, bindings: dict, output_name: str = None, db=None):
        # Hardcoded responses for known test models
        if model_name == "Simple" and "x" in bindings:
            return bindings["x"] * 2

        if model_name == "Thermal Expansion":
            cte = bindings.get("CTE", 2.3e-5)
            delta_t = bindings.get("delta_T", 100)
            l0 = bindings.get("L0", 1.0)
            return cte * delta_t * l0

        if model_name == "Rectangle":
            length = bindings["length"]
            width = bindings["width"]

            if output_name == "area":
                return length * width
            elif output_name == "perimeter":
                return 2 * (length + width)
            else:
                # Default to first output (area)
                return length * width

        if model_name == "Constant":
            # Model with no inputs, returns pi
            return 3.14159

        if model_name == "NonExistent":
            raise ValueError(f"Model '{model_name}' not found")

        raise NotImplementedError(f"Stub doesn't handle model '{model_name}'")

    return evaluate


# ==================== PHASE 2: REAL IMPLEMENTATION ====================

@pytest.fixture
def real_evaluate_inline_model():
    """
    Real evaluate_inline_model() from app.services.model_evaluation.

    Phase 2: Use this instead of stub_evaluate_inline_model for tests
    against the actual implementation.
    """
    return evaluate_inline_model


@pytest.fixture
def evaluate_model(db):
    """
    Convenience fixture that wraps evaluate_inline_model with db session.

    Usage in tests:
        result = evaluate_model("Simple", {"x": 5})
    """
    def _evaluate(model_name: str, bindings: dict, output_name: str = None):
        return evaluate_inline_model(
            model_name=model_name,
            bindings=bindings,
            output_name=output_name,
            db=db
        )
    return _evaluate


@pytest.fixture
def stub_resolve_binding():
    """
    Stub for binding resolution that handles different binding types.
    """
    def resolve(binding_value: str, db=None, context: dict = None):
        context = context or {}
        binding_value = binding_value.strip()

        # Literal number
        try:
            return float(binding_value)
        except ValueError:
            pass

        # Number with unit (e.g., "1m", "5mm", "100K")
        unit_match = re.match(r'^(-?\d+\.?\d*)\s*([a-zA-Z°]+)$', binding_value)
        if unit_match:
            value = float(unit_match.group(1))
            unit = unit_match.group(2)
            # Return tuple of (value, unit) for unit-aware resolution
            return (value, unit)

        # Property reference (e.g., "#FRAME.length")
        if binding_value.startswith('#'):
            ref = binding_value[1:]  # Remove #
            if ref in context:
                return context[ref]
            raise ValueError(f"Reference '{binding_value}' not found in context")

        # Quoted string (for output name)
        if binding_value.startswith('"') and binding_value.endswith('"'):
            return binding_value[1:-1]

        # Expression - return as-is for now
        return binding_value

    return resolve


# ==================== MODEL FIXTURES ====================

@pytest.fixture
def simple_model(db):
    """Model: y = x * 2"""
    model = PhysicsModel(
        name="Simple",
        description="Simple doubling model",
        category="test"
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
        equation_ast={"y": parsed["ast"]}
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def thermal_model(db):
    """Model: delta_L = CTE * delta_T * L0"""
    model = PhysicsModel(
        name="Thermal Expansion",
        description="Calculates thermal expansion",
        category="thermal"
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
        equation_ast={"delta_L": parsed["ast"]}
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def rectangle_model(db):
    """Multi-output model: area = L*W, perimeter = 2*(L+W)"""
    model = PhysicsModel(
        name="Rectangle",
        description="Rectangle calculations",
        category="geometry"
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
        }
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def constant_model(db):
    """Model with no inputs - returns constant."""
    model = PhysicsModel(
        name="Constant",
        description="Returns pi",
        category="test"
    )
    db.add(model)
    db.flush()

    parsed = parse_equation("pi", allowed_inputs=[])

    version = PhysicsModelVersion(
        physics_model_id=model.id,
        version=1,
        is_current=True,
        inputs=[],
        outputs=[{"name": "value", "unit": "1"}],
        equations={"value": "pi"},
        equation_ast={"value": parsed["ast"]}
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


@pytest.fixture
def complex_model(db):
    """Complex model with 5 inputs and nested functions."""
    model = PhysicsModel(
        name="Complex",
        description="Complex calculation",
        category="test"
    )
    db.add(model)
    db.flush()

    # result = sqrt(a**2 + b**2) * sin(c) + d / e
    parsed = parse_equation("sqrt(a**2 + b**2) * sin(c) + d / e",
                           allowed_inputs=["a", "b", "c", "d", "e"])

    version = PhysicsModelVersion(
        physics_model_id=model.id,
        version=1,
        is_current=True,
        inputs=[
            {"name": "a", "unit": "m", "required": True},
            {"name": "b", "unit": "m", "required": True},
            {"name": "c", "unit": "rad", "required": True},
            {"name": "d", "unit": "m", "required": True},
            {"name": "e", "unit": "1", "required": True}
        ],
        outputs=[{"name": "result", "unit": "m"}],
        equations={"result": "sqrt(a**2 + b**2) * sin(c) + d / e"},
        equation_ast={"result": parsed["ast"]}
    )
    db.add(version)
    db.commit()
    db.refresh(model)

    return model


# ==================== COMPONENT FIXTURES ====================

@pytest.fixture
def component_with_properties(db):
    """
    Create a mock component with properties for reference testing.

    Returns dict simulating #FRAME.length, #FRAME.width, etc.
    """
    return {
        "FRAME.length": 0.003,      # 3mm
        "FRAME.width": 0.002,       # 2mm
        "FRAME.height": 0.001,      # 1mm
        "SENSOR.temp": 373.15,      # 100°C in K
        "SENSOR.delta_T": 100,      # 100K change
        "MATERIAL.CTE": 2.3e-5,     # Aluminum-like CTE
    }


@pytest.fixture
def component_chain(db):
    """
    Two components with dependency chain for testing.

    A.x = 10
    B.y = A.x * 2 (depends on A)
    """
    return {
        "A.x": 10,
        "B.y": 20,  # Computed from A.x * 2
        "_dependencies": {
            "B.y": ["A.x"]
        }
    }
