"""
Integration Tests: Model Creation Flow

Tests the complete flow of creating physics models through the API.
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
TEST_DATABASE_URL = "sqlite:///./test_integration.db"
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
    if os.path.exists("./test_integration.db"):
        os.remove("./test_integration.db")


class TestValidateEndpoint:
    """Test the /physics-models/validate endpoint."""

    def test_validate_simple_equation(self, client):
        """Validate a simple addition equation."""
        response = client.post("/api/v1/physics-models/validate", json={
            "inputs": [
                {"name": "a", "unit": "m"},
                {"name": "b", "unit": "m"}
            ],
            "outputs": [
                {"name": "sum", "unit": "m"}
            ],
            "equations": {
                "sum": "a + b"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert len(data["errors"]) == 0
        assert "sum" in data["latex_preview"]

    def test_validate_thermal_expansion(self, client):
        """Validate thermal expansion equation."""
        response = client.post("/api/v1/physics-models/validate", json={
            "inputs": [
                {"name": "length", "unit": "m"},
                {"name": "CTE", "unit": "1/K"},
                {"name": "delta_T", "unit": "K"}
            ],
            "outputs": [
                {"name": "expansion", "unit": "m"}
            ],
            "equations": {
                "expansion": "length * CTE * delta_T"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True

    def test_validate_missing_equation(self, client):
        """Validate should fail if equation is missing for output."""
        response = client.post("/api/v1/physics-models/validate", json={
            "inputs": [
                {"name": "a", "unit": "m"}
            ],
            "outputs": [
                {"name": "result", "unit": "m"}
            ],
            "equations": {}  # Missing equation
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert any("Missing equation" in e for e in data["errors"])

    def test_validate_unknown_input_reference(self, client):
        """Validate should fail if equation references undefined input."""
        response = client.post("/api/v1/physics-models/validate", json={
            "inputs": [
                {"name": "a", "unit": "m"}
            ],
            "outputs": [
                {"name": "result", "unit": "m"}
            ],
            "equations": {
                "result": "a + unknown_var"  # unknown_var not in inputs
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert any("unknown" in e.lower() for e in data["errors"])

    def test_validate_syntax_error(self, client):
        """Validate should fail on syntax error."""
        response = client.post("/api/v1/physics-models/validate", json={
            "inputs": [
                {"name": "a", "unit": "m"}
            ],
            "outputs": [
                {"name": "result", "unit": "m"}
            ],
            "equations": {
                "result": "a + * b"  # Syntax error
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False


class TestCreateModel:
    """Test the /physics-models POST endpoint."""

    def test_create_simple_model(self, client):
        """Create a simple physics model."""
        response = client.post("/api/v1/physics-models", json={
            "name": "Simple Addition",
            "category": "test",
            "description": "Adds two numbers",
            "inputs": [
                {"name": "a", "unit": "m"},
                {"name": "b", "unit": "m"}
            ],
            "outputs": [
                {"name": "sum", "unit": "m"}
            ],
            "equations": {
                "sum": "a + b"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == "Simple Addition"
        assert data["current_version"] is not None
        assert data["current_version"]["version"] == 1

    def test_create_thermal_expansion_model(self, client):
        """Create a thermal expansion model."""
        response = client.post("/api/v1/physics-models", json={
            "name": "Thermal Expansion",
            "category": "thermal",
            "description": "Calculates thermal expansion",
            "inputs": [
                {"name": "length", "unit": "m", "description": "Initial length"},
                {"name": "CTE", "unit": "1/K", "description": "Coefficient of thermal expansion"},
                {"name": "delta_T", "unit": "K", "description": "Temperature change"}
            ],
            "outputs": [
                {"name": "expansion", "unit": "m", "description": "Calculated expansion"}
            ],
            "equations": {
                "expansion": "length * CTE * delta_T"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Thermal Expansion"
        assert data["category"] == "thermal"
        assert "equation_latex" in data["current_version"]

    def test_create_model_with_functions(self, client):
        """Create a model using mathematical functions."""
        response = client.post("/api/v1/physics-models", json={
            "name": "Circle Area",
            "category": "mechanical",
            "inputs": [
                {"name": "radius", "unit": "m"}
            ],
            "outputs": [
                {"name": "area", "unit": "m2"}
            ],
            "equations": {
                "area": "pi * radius**2"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Circle Area"

    def test_create_model_missing_equation(self, client):
        """Creating model without equation should fail."""
        response = client.post("/api/v1/physics-models", json={
            "name": "Incomplete Model",
            "category": "test",
            "inputs": [{"name": "x", "unit": "m"}],
            "outputs": [{"name": "y", "unit": "m"}],
            "equations": {}  # Missing
        })

        assert response.status_code == 400


class TestListAndGetModels:
    """Test listing and getting physics models."""

    def test_list_models(self, client):
        """List all physics models."""
        response = client.get("/api/v1/physics-models")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should have models from previous tests
        assert len(data) >= 2

    def test_list_models_by_category(self, client):
        """Filter models by category."""
        response = client.get("/api/v1/physics-models?category=thermal")

        assert response.status_code == 200
        data = response.json()
        assert all(m["category"] == "thermal" for m in data)

    def test_get_model_by_id(self, client):
        """Get a specific model by ID."""
        # First list to get an ID
        list_response = client.get("/api/v1/physics-models")
        models = list_response.json()
        model_id = models[0]["id"]

        # Get by ID
        response = client.get(f"/api/v1/physics-models/{model_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == model_id
        assert "versions" in data
        assert "current_version" in data

    def test_get_nonexistent_model(self, client):
        """Getting non-existent model should return 404."""
        response = client.get("/api/v1/physics-models/99999")

        assert response.status_code == 404


class TestCategories:
    """Test the categories endpoint."""

    def test_list_categories(self, client):
        """List available categories."""
        response = client.get("/api/v1/physics-models/categories")

        assert response.status_code == 200
        data = response.json()
        assert "categories" in data
        assert len(data["categories"]) >= 4
        assert any(c["id"] == "thermal" for c in data["categories"])
