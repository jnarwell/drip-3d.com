"""
Integration Tests: Instance Creation Flow

Tests the complete flow of creating model instances through the API.
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
TEST_DATABASE_URL = "sqlite:///./test_instance.db"
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
    if os.path.exists("./test_instance.db"):
        os.remove("./test_instance.db")


@pytest.fixture(scope="module")
def model_data(client):
    """Create a test model and return its data."""
    response = client.post("/api/v1/physics-models", json={
        "name": "Test Addition Model",
        "category": "test",
        "inputs": [
            {"name": "a", "unit": "m", "required": True},
            {"name": "b", "unit": "m", "required": True}
        ],
        "outputs": [
            {"name": "sum", "unit": "m"}
        ],
        "equations": {
            "sum": "a + b"
        }
    })
    return response.json()


class TestInstanceCreation:
    """Test the /model-instances POST endpoint."""

    def test_create_instance_with_literal_bindings(self, client, model_data):
        """Create instance with literal value bindings."""
        response = client.post("/api/v1/model-instances", json={
            "name": "Test Instance",
            "model_version_id": model_data["current_version"]["id"],
            "bindings": {
                "a": "2.0",
                "b": "3.0"
            }
        })

        assert response.status_code == 200
        data = response.json()
        assert data["id"] is not None
        assert data["name"] == "Test Instance"
        assert data["model_version_id"] == model_data["current_version"]["id"]
        assert "bindings" in data

    def test_create_instance_missing_required_input(self, client, model_data):
        """Create instance missing required input should fail."""
        response = client.post("/api/v1/model-instances", json={
            "name": "Incomplete Instance",
            "model_version_id": model_data["current_version"]["id"],
            "bindings": {
                "a": "2.0"
                # Missing "b"
            }
        })

        assert response.status_code == 400
        assert "missing" in response.json()["detail"].lower()

    def test_create_instance_invalid_version(self, client):
        """Create instance with invalid version ID should fail."""
        response = client.post("/api/v1/model-instances", json={
            "name": "Invalid Instance",
            "model_version_id": 99999,
            "bindings": {"a": "1.0", "b": "2.0"}
        })

        assert response.status_code == 404


class TestGetInstance:
    """Test getting model instances."""

    def test_get_instance_by_id(self, client, model_data):
        """Get a specific instance by ID."""
        # First create an instance
        create_response = client.post("/api/v1/model-instances", json={
            "name": "Instance for Get Test",
            "model_version_id": model_data["current_version"]["id"],
            "bindings": {"a": "5.0", "b": "6.0"}
        })
        instance_id = create_response.json()["id"]

        # Then get it
        response = client.get(f"/api/v1/model-instances/{instance_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == instance_id
        assert data["name"] == "Instance for Get Test"
        assert "inputs" in data

    def test_get_nonexistent_instance(self, client):
        """Getting non-existent instance should return 404."""
        response = client.get("/api/v1/model-instances/99999")

        assert response.status_code == 404
