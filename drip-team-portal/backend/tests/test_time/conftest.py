"""
Time Tracking Tests - Shared Fixtures

Provides:
- Database fixtures (file-based SQLite with cross-thread access)
- TimeEntry and Resource model fixtures
- Client fixtures (FastAPI test client with auth)
"""

import pytest
import sys
import os
import tempfile
from datetime import datetime, timezone, timedelta

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.models.time_entry import TimeEntry
from app.models.resources import Resource
from app.models.component import Component, ComponentCategory, ComponentStatus


# =============================================================================
# DATABASE FIXTURES
# =============================================================================

# Use file-based SQLite with check_same_thread=False for cross-thread access
TEST_DB_FILE = tempfile.mktemp(suffix="_time_test.db")
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


# =============================================================================
# CLIENT FIXTURES
# =============================================================================

@pytest.fixture
def app():
    """Create FastAPI app for testing."""
    from app.main import app as fastapi_app
    return fastapi_app


@pytest.fixture
def client(app, db):
    """Create FastAPI test client with database override."""
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
    """Mock auth headers. In DEV_MODE, auth is bypassed via security_dev.py."""
    return {"Authorization": "Bearer mock-dev-token"}


# =============================================================================
# MODEL FIXTURES
# =============================================================================

@pytest.fixture
def test_component(db):
    """Create a test component for association tests."""
    component = Component(
        component_id="CMP-TEST-001",
        name="Test Component",
        category=ComponentCategory.MECHANICAL,
        status=ComponentStatus.NOT_TESTED,
        notes="Test component for time tracking tests"
    )
    db.add(component)
    db.commit()
    db.refresh(component)
    return component


@pytest.fixture
def test_resource(db):
    """Create a test resource."""
    resource = Resource(
        title="Test Document",
        resource_type="doc",
        url="https://example.com/test-doc",
        added_by="test@drip-3d.com",
        tags=["test", "documentation"],
        notes="A test resource for time tracking tests"
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@pytest.fixture
def running_timer(db):
    """Create a running timer (no stopped_at) for the test user."""
    entry = TimeEntry(
        user_id="test@drip-3d.com",
        started_at=datetime.now(timezone.utc) - timedelta(minutes=30),
        stopped_at=None,
        linear_issue_id="DRP-100"
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


@pytest.fixture
def completed_entries(db, test_component):
    """Create multiple completed time entries for filter/summary tests."""
    now = datetime.now(timezone.utc)
    entries = []

    entry1 = TimeEntry(
        user_id="test@drip-3d.com",
        started_at=now - timedelta(days=1, hours=2),
        stopped_at=now - timedelta(days=1, hours=1),
        duration_seconds=3600,
        linear_issue_id="DRP-101",
        linear_issue_title="Fix thermal bug",
        component_id=test_component.id,
        description="Worked on thermal calculations"
    )
    entries.append(entry1)

    entry2 = TimeEntry(
        user_id="test@drip-3d.com",
        started_at=now - timedelta(days=1, hours=5),
        stopped_at=now - timedelta(days=1, hours=3),
        duration_seconds=7200,
        linear_issue_id="DRP-102",
        linear_issue_title="Add new feature"
    )
    entries.append(entry2)

    entry3 = TimeEntry(
        user_id="test@drip-3d.com",
        started_at=now - timedelta(hours=3),
        stopped_at=now - timedelta(hours=2),
        duration_seconds=3600,
        linear_issue_id="DRP-101",
        linear_issue_title="Fix thermal bug",
        component_id=test_component.id
    )
    entries.append(entry3)

    entry4 = TimeEntry(
        user_id="other@drip-3d.com",
        started_at=now - timedelta(hours=4),
        stopped_at=now - timedelta(hours=3),
        duration_seconds=3600,
        is_uncategorized=True
    )
    entries.append(entry4)

    for entry in entries:
        db.add(entry)
    db.commit()
    for entry in entries:
        db.refresh(entry)

    return entries


@pytest.fixture
def multiple_resources(db, test_component):
    """Create multiple resources for list/filter tests."""
    resources = []

    resource1 = Resource(
        title="Design Document",
        resource_type="doc",
        url="https://example.com/design",
        added_by="test@drip-3d.com",
        tags=["design", "phase-1"]
    )
    resources.append(resource1)

    resource2 = Resource(
        title="Research Paper",
        resource_type="paper",
        url="https://arxiv.org/paper",
        added_by="test@drip-3d.com",
        tags=["research", "thermal"]
    )
    resources.append(resource2)

    resource3 = Resource(
        title="Tutorial Video",
        resource_type="video",
        url="https://youtube.com/watch",
        added_by="other@drip-3d.com"
    )
    resources.append(resource3)

    for resource in resources:
        db.add(resource)
    db.commit()

    # Link first resource to component
    resource1.components.append(test_component)
    db.commit()

    for resource in resources:
        db.refresh(resource)

    return resources
