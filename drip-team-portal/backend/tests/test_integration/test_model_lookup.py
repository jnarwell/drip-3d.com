"""
Integration Tests: Model Lookup API

Tests the /physics-models/by-name/{name} endpoint and PhysicsModel.find_by_name()
class method used by MODEL() function evaluation.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.db.database import Base, get_db


# Create test database
TEST_DATABASE_URL = "sqlite:///./test_model_lookup.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override the database dependency for testing."""
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Override the dependency
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
    # Clean up test database file
    if os.path.exists("./test_model_lookup.db"):
        os.remove("./test_model_lookup.db")


@pytest.fixture(scope="module")
def thermal_model(client):
    """Create a thermal expansion model for testing."""
    response = client.post("/api/v1/physics-models", json={
        "name": "Thermal Expansion",
        "category": "thermal",
        "description": "Calculates linear thermal expansion: ΔL = α × ΔT × L₀",
        "inputs": [
            {"name": "CTE", "unit": "1/K", "dimension": "thermal_expansion", "required": True},
            {"name": "delta_T", "unit": "K", "dimension": "temperature_difference", "required": True},
            {"name": "L0", "unit": "m", "dimension": "length", "required": True}
        ],
        "outputs": [
            {"name": "delta_L", "unit": "m", "dimension": "length"}
        ],
        "equations": {
            "delta_L": "CTE * delta_T * L0"
        }
    })
    assert response.status_code == 200
    return response.json()


@pytest.fixture(scope="module")
def rectangle_model(client):
    """Create a multi-output rectangle model for testing."""
    response = client.post("/api/v1/physics-models", json={
        "name": "Rectangle Calculator",
        "category": "mechanical",
        "description": "Calculates area and perimeter of a rectangle",
        "inputs": [
            {"name": "length", "unit": "m", "required": True},
            {"name": "width", "unit": "m", "required": True}
        ],
        "outputs": [
            {"name": "area", "unit": "m2"},
            {"name": "perimeter", "unit": "m"}
        ],
        "equations": {
            "area": "length * width",
            "perimeter": "2 * (length + width)"
        }
    })
    assert response.status_code == 200
    return response.json()


class TestGetModelByName:
    """Test the /physics-models/by-name/{name} endpoint."""

    def test_get_model_by_exact_name(self, client, thermal_model):
        """GET /physics-models/by-name/{name} with exact name."""
        response = client.get("/api/v1/physics-models/by-name/Thermal Expansion")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thermal Expansion"
        assert data["category"] == "thermal"
        assert "current_version" in data
        assert data["current_version"]["equations"] is not None

    def test_get_model_by_name_case_insensitive_lower(self, client, thermal_model):
        """Model lookup should be case-insensitive (lowercase)."""
        response = client.get("/api/v1/physics-models/by-name/thermal expansion")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thermal Expansion"

    def test_get_model_by_name_case_insensitive_upper(self, client, thermal_model):
        """Model lookup should be case-insensitive (uppercase)."""
        response = client.get("/api/v1/physics-models/by-name/THERMAL EXPANSION")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thermal Expansion"

    def test_get_model_by_name_case_insensitive_mixed(self, client, thermal_model):
        """Model lookup should be case-insensitive (mixed case)."""
        response = client.get("/api/v1/physics-models/by-name/ThErMaL eXpAnSiOn")

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thermal Expansion"

    def test_get_model_by_name_not_found(self, client):
        """GET /physics-models/by-name/{name} with non-existent model."""
        response = client.get("/api/v1/physics-models/by-name/NonExistent Model")

        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()

    def test_get_model_by_name_includes_inputs(self, client, thermal_model):
        """Response should include input schema."""
        response = client.get("/api/v1/physics-models/by-name/Thermal Expansion")

        assert response.status_code == 200
        data = response.json()
        inputs = data["current_version"]["inputs"]

        assert len(inputs) == 3
        input_names = [i["name"] for i in inputs]
        assert "CTE" in input_names
        assert "delta_T" in input_names
        assert "L0" in input_names

    def test_get_model_by_name_includes_outputs(self, client, thermal_model):
        """Response should include output schema."""
        response = client.get("/api/v1/physics-models/by-name/Thermal Expansion")

        assert response.status_code == 200
        data = response.json()
        outputs = data["current_version"]["outputs"]

        assert len(outputs) == 1
        assert outputs[0]["name"] == "delta_L"
        assert outputs[0]["unit"] == "m"

    def test_get_model_by_name_includes_equations(self, client, thermal_model):
        """Response should include equations."""
        response = client.get("/api/v1/physics-models/by-name/Thermal Expansion")

        assert response.status_code == 200
        data = response.json()
        equations = data["current_version"]["equations"]

        assert "delta_L" in equations
        assert equations["delta_L"] == "CTE * delta_T * L0"

    def test_get_model_by_name_includes_equation_ast(self, client, thermal_model):
        """Response should include pre-parsed equation AST."""
        response = client.get("/api/v1/physics-models/by-name/Thermal Expansion")

        assert response.status_code == 200
        data = response.json()
        equation_ast = data["current_version"]["equation_ast"]

        assert equation_ast is not None
        assert "delta_L" in equation_ast

    def test_get_multi_output_model_by_name(self, client, rectangle_model):
        """Multi-output model should include all outputs."""
        response = client.get("/api/v1/physics-models/by-name/Rectangle Calculator")

        assert response.status_code == 200
        data = response.json()

        outputs = data["current_version"]["outputs"]
        assert len(outputs) == 2

        output_names = [o["name"] for o in outputs]
        assert "area" in output_names
        assert "perimeter" in output_names

        equations = data["current_version"]["equations"]
        assert "area" in equations
        assert "perimeter" in equations


class TestFindByNameClassMethod:
    """Test the PhysicsModel.find_by_name() class method directly."""

    def test_find_by_name_returns_model(self, client, thermal_model):
        """find_by_name should return the model when found."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")

            assert model is not None
            assert model.name == "Thermal Expansion"
            assert model.category == "thermal"
        finally:
            db.close()

    def test_find_by_name_case_insensitive(self, client, thermal_model):
        """find_by_name should be case-insensitive."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "thermal expansion")
            assert model is not None
            assert model.name == "Thermal Expansion"
        finally:
            db.close()

    def test_find_by_name_returns_none_when_not_found(self, client):
        """find_by_name should return None when model not found."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "NonExistent Model")
            assert model is None
        finally:
            db.close()

    def test_find_by_name_eager_loads_versions(self, client, thermal_model):
        """find_by_name should eager-load versions."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")

            # Versions should be accessible without additional query
            assert len(model.versions) >= 1
            assert model.versions[0].version == 1
        finally:
            db.close()

    def test_current_version_property(self, client, thermal_model):
        """current_version property should return the current version."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")

            current = model.current_version
            assert current is not None
            assert current.is_current == True
            assert current.version == 1
        finally:
            db.close()


class TestModelLookupForMODELFunction:
    """
    Tests verifying that the lookup infrastructure supports MODEL() evaluation.
    These tests simulate what evaluate_inline_model() will do.
    """

    def test_lookup_provides_equations_for_evaluation(self, client, thermal_model):
        """Lookup should provide everything needed for equation evaluation."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")
            version = model.current_version

            # Should have equations dict
            assert version.equations is not None
            assert "delta_L" in version.equations

            # Should have inputs schema for validation
            assert version.inputs is not None
            required_inputs = {
                inp.get('name') for inp in version.inputs
                if inp.get('required', True)
            }
            assert required_inputs == {"CTE", "delta_T", "L0"}
        finally:
            db.close()

    def test_lookup_provides_ast_for_fast_evaluation(self, client, thermal_model):
        """Lookup should provide pre-parsed AST when available."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Thermal Expansion")
            version = model.current_version

            # AST should be available for fast evaluation
            if version.equation_ast:
                assert "delta_L" in version.equation_ast
        finally:
            db.close()

    def test_multi_output_model_has_all_equations(self, client, rectangle_model):
        """Multi-output models should have equations for each output."""
        from app.models.physics_model import PhysicsModel

        db = TestingSessionLocal()
        try:
            model = PhysicsModel.find_by_name(db, "Rectangle Calculator")
            version = model.current_version

            equations = version.equations
            assert len(equations) == 2
            assert "area" in equations
            assert "perimeter" in equations

            # Verify equation content
            assert "length * width" in equations["area"]
            assert "length + width" in equations["perimeter"]
        finally:
            db.close()
