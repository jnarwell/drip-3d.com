"""
Integration Tests: End-to-End Flows

Tests complete user flows from model creation to instance evaluation.
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
from app.models.values import ValueNode


# Create test database
TEST_DATABASE_URL = "sqlite:///./test_e2e.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="module")
def client():
    """Create test client with fresh database."""
    Base.metadata.create_all(bind=engine)
    yield TestClient(app)
    Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test_e2e.db"):
        os.remove("./test_e2e.db")


class TestCompleteModelFlow:
    """Test complete model creation → validation → save flow."""

    def test_complete_thermal_expansion_flow(self, client):
        """
        End-to-end test:
        1. Validate model equations
        2. Create model
        3. Verify model stored correctly
        4. Create instance
        5. (Future: Verify outputs computed)
        """
        # Step 1: Validate
        validate_response = client.post("/api/v1/physics-models/validate", json={
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

        assert validate_response.status_code == 200
        validate_data = validate_response.json()
        assert validate_data["valid"] == True
        assert "expansion" in validate_data["dimensional_analysis"]
        assert "expansion" in validate_data["latex_preview"]

        # Step 2: Create model
        create_response = client.post("/api/v1/physics-models", json={
            "name": "E2E Thermal Expansion",
            "category": "thermal",
            "description": "End-to-end test model",
            "inputs": [
                {"name": "length", "unit": "m", "description": "Initial length"},
                {"name": "CTE", "unit": "1/K", "description": "CTE"},
                {"name": "delta_T", "unit": "K", "description": "Temperature change"}
            ],
            "outputs": [
                {"name": "expansion", "unit": "m", "description": "Calculated expansion"}
            ],
            "equations": {
                "expansion": "length * CTE * delta_T"
            }
        })

        assert create_response.status_code == 200
        model = create_response.json()
        model_id = model["id"]
        version_id = model["current_version"]["id"]

        assert model["name"] == "E2E Thermal Expansion"
        assert model["current_version"]["equation_latex"] is not None

        # Step 3: Verify stored
        get_response = client.get(f"/api/v1/physics-models/{model_id}")
        assert get_response.status_code == 200
        stored_model = get_response.json()

        assert stored_model["id"] == model_id
        assert len(stored_model["versions"]) == 1
        assert stored_model["current_version"]["id"] == version_id

        # Step 4: Create instance
        instance_response = client.post("/api/v1/model-instances", json={
            "name": "Crucible Expansion Test",
            "model_version_id": version_id,
            "bindings": {
                "length": "0.003",      # 3mm
                "CTE": "0.0000081",     # 8.1e-6
                "delta_T": "500"        # 500K
            }
        })

        assert instance_response.status_code == 200
        instance = instance_response.json()

        assert instance["id"] is not None
        assert instance["name"] == "Crucible Expansion Test"
        assert instance["model_version_id"] == version_id

        # Step 5: Verify instance stored
        get_instance_response = client.get(f"/api/v1/model-instances/{instance['id']}")
        assert get_instance_response.status_code == 200
        stored_instance = get_instance_response.json()

        assert stored_instance["id"] == instance["id"]
        assert len(stored_instance["inputs"]) == 3


class TestMultipleOutputsFlow:
    """Test models with multiple outputs."""

    def test_multi_output_model(self, client):
        """Create and instantiate model with multiple outputs."""
        # Create model with area and perimeter
        create_response = client.post("/api/v1/physics-models", json={
            "name": "Rectangle Properties",
            "category": "mechanical",
            "inputs": [
                {"name": "length", "unit": "m"},
                {"name": "width", "unit": "m"}
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

        assert create_response.status_code == 200
        model = create_response.json()

        # Validate it has LaTeX for both outputs
        assert "area" in model["current_version"]["equation_latex"]
        assert "perimeter" in model["current_version"]["equation_latex"]

        # Create instance
        instance_response = client.post("/api/v1/model-instances", json={
            "name": "Room Dimensions",
            "model_version_id": model["current_version"]["id"],
            "bindings": {
                "length": "5.0",
                "width": "3.0"
            }
        })

        assert instance_response.status_code == 200
        instance = instance_response.json()

        # Expected results (not yet computed by current API)
        # area = 5 * 3 = 15 m²
        # perimeter = 2 * (5 + 3) = 16 m


class TestModelListingFlow:
    """Test model listing and filtering."""

    def test_list_and_filter_models(self, client):
        """Create models in different categories and filter."""
        # Create thermal model
        client.post("/api/v1/physics-models", json={
            "name": "Heat Transfer",
            "category": "thermal",
            "inputs": [{"name": "Q", "unit": "W"}],
            "outputs": [{"name": "T", "unit": "K"}],
            "equations": {"T": "Q"}
        })

        # Create mechanical model
        client.post("/api/v1/physics-models", json={
            "name": "Stress Calculation",
            "category": "mechanical",
            "inputs": [{"name": "F", "unit": "N"}],
            "outputs": [{"name": "sigma", "unit": "Pa"}],
            "equations": {"sigma": "F"}
        })

        # List all
        all_response = client.get("/api/v1/physics-models")
        all_models = all_response.json()

        # Filter by thermal
        thermal_response = client.get("/api/v1/physics-models?category=thermal")
        thermal_models = thermal_response.json()

        # Filter by mechanical
        mech_response = client.get("/api/v1/physics-models?category=mechanical")
        mech_models = mech_response.json()

        # Verify filtering works
        assert len(all_models) >= len(thermal_models) + len(mech_models)
        assert all(m["category"] == "thermal" for m in thermal_models)
        assert all(m["category"] == "mechanical" for m in mech_models)
