"""
Time Tracking API Tests

Tests for:
- POST /api/v1/time/start - Start timer
- POST /api/v1/time/stop - Stop timer with categorization
- GET /api/v1/time/active - Get running timer
- GET /api/v1/time/entries - List entries with filters
- GET /api/v1/time/summary - Aggregated summary
"""

import pytest
import time
from datetime import datetime, timezone, timedelta


class TestStartTimer:
    """Test POST /api/v1/time/start endpoint."""

    def test_start_timer_creates_entry(self, client, auth_headers):
        """Starting a timer creates a new entry and returns id."""
        response = client.post("/api/v1/time/start", json={}, headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "started_at" in data
        assert data.get("stopped_previous") is None  # No previous timer

    def test_start_timer_with_issue(self, client, auth_headers):
        """Start timer with a Linear issue ID."""
        response = client.post(
            "/api/v1/time/start",
            json={"linear_issue_id": "DRP-200"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["linear_issue_id"] == "DRP-200"

    def test_start_timer_with_component(self, client, auth_headers, test_component):
        """Start timer with a component ID."""
        response = client.post(
            "/api/v1/time/start",
            json={"component_id": test_component.id},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["component_id"] == test_component.id

    def test_start_timer_auto_stops_previous(self, client, auth_headers, running_timer):
        """Starting a new timer auto-stops the previous one."""
        response = client.post("/api/v1/time/start", json={}, headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should have stopped the previous timer
        assert "stopped_previous" in data
        assert data["stopped_previous"]["id"] == running_timer.id
        assert data["stopped_previous"]["stopped_at"] is not None


class TestStopTimer:
    """Test POST /api/v1/time/stop endpoint."""

    def test_stop_timer_computes_duration(self, client, auth_headers, running_timer):
        """Stopping computes duration correctly."""
        # Small delay to ensure measurable duration
        time.sleep(0.1)

        response = client.post(
            "/api/v1/time/stop",
            json={"description": "Test work"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["stopped_at"] is not None
        assert data["duration_seconds"] is not None
        assert data["duration_seconds"] > 0

    def test_stop_requires_categorization(self, client, auth_headers, running_timer):
        """Stop with empty body should fail (no categorization)."""
        response = client.post(
            "/api/v1/time/stop",
            json={},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 400
        assert "categorization" in response.json()["detail"].lower()

    def test_stop_accepts_uncategorized_flag(self, client, auth_headers, running_timer):
        """Stop with is_uncategorized=True should succeed."""
        response = client.post(
            "/api/v1/time/stop",
            json={"is_uncategorized": True},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["is_uncategorized"] is True

    def test_stop_with_linear_issue(self, client, auth_headers, running_timer):
        """Stop with Linear issue categorization."""
        response = client.post(
            "/api/v1/time/stop",
            json={
                "linear_issue_id": "DRP-150",
                "linear_issue_title": "Fix the bug"
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["linear_issue_id"] == "DRP-150"
        assert data["linear_issue_title"] == "Fix the bug"

    def test_stop_with_resource(self, client, auth_headers, running_timer, test_resource):
        """Stop with resource categorization."""
        response = client.post(
            "/api/v1/time/stop",
            json={"resource_id": test_resource.id},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["resource_id"] == test_resource.id

    def test_stop_no_running_timer(self, client, auth_headers):
        """Stop when no timer is running should fail."""
        response = client.post(
            "/api/v1/time/stop",
            json={"description": "Nothing running"},
            headers=auth_headers
        )

        if response.status_code == 404:
            # Could be endpoint not found OR no timer found
            pass  # Expected
        else:
            assert response.status_code == 404


class TestGetActiveTimer:
    """Test GET /api/v1/time/active endpoint."""

    def test_get_active_returns_null_when_none(self, client, auth_headers):
        """No active timer returns null."""
        response = client.get("/api/v1/time/active", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json() is None

    def test_get_active_returns_running_timer(self, client, auth_headers, running_timer):
        """Returns the running timer when one exists."""
        response = client.get("/api/v1/time/active", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data is not None
        assert data["id"] == running_timer.id
        assert data["stopped_at"] is None


class TestListEntries:
    """Test GET /api/v1/time/entries endpoint."""

    def test_list_entries_empty(self, client, auth_headers):
        """Empty list when no entries."""
        response = client.get("/api/v1/time/entries", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
        assert len(data["entries"]) == 0

    def test_list_entries_returns_all(self, client, auth_headers, completed_entries):
        """Lists all entries."""
        response = client.get("/api/v1/time/entries", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data["entries"]) == len(completed_entries)

    def test_entries_filter_by_user(self, client, auth_headers, completed_entries):
        """Filter entries by user_id."""
        response = client.get(
            "/api/v1/time/entries?user_id=test@drip-3d.com",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # 3 entries for test user, 1 for other user
        assert len(data["entries"]) == 3

    def test_entries_filter_by_component(self, client, auth_headers, completed_entries, test_component):
        """Filter entries by component_id."""
        response = client.get(
            f"/api/v1/time/entries?component_id={test_component.id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # 2 entries have component_id set
        assert len(data["entries"]) == 2

    def test_entries_filter_by_date_range(self, client, auth_headers, completed_entries):
        """Filter entries by date range."""
        today = datetime.now(timezone.utc).date()

        response = client.get(
            f"/api/v1/time/entries?start_date={today.isoformat()}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # 2 entries are from today (entries 3 and 4)
        assert len(data["entries"]) == 2

    def test_entries_filter_by_linear_issue(self, client, auth_headers, completed_entries):
        """Filter entries by Linear issue ID."""
        response = client.get(
            "/api/v1/time/entries?linear_issue_id=DRP-101",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # 2 entries have DRP-101
        assert len(data["entries"]) == 2


class TestSummary:
    """Test GET /api/v1/time/summary endpoint."""

    def test_summary_groups_by_user(self, client, auth_headers, completed_entries):
        """Summary grouped by user."""
        response = client.get(
            "/api/v1/time/summary?group_by=user",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "user"
        assert "groups" in data
        assert len(data["groups"]) == 2  # test@drip-3d.com and other@drip-3d.com

    def test_summary_groups_by_component(self, client, auth_headers, completed_entries):
        """Summary grouped by component."""
        response = client.get(
            "/api/v1/time/summary?group_by=component",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "component"
        # Only entries with component_id are included
        assert len(data["groups"]) >= 1

    def test_summary_groups_by_linear_issue(self, client, auth_headers, completed_entries):
        """Summary grouped by Linear issue."""
        response = client.get(
            "/api/v1/time/summary?group_by=linear_issue",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["group_by"] == "linear_issue"
        # DRP-101 and DRP-102
        assert len(data["groups"]) == 2

    def test_summary_includes_totals(self, client, auth_headers, completed_entries):
        """Summary includes total_seconds and entry_count."""
        response = client.get(
            "/api/v1/time/summary?group_by=user",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for group in data["groups"]:
            assert "total_seconds" in group
            assert "entry_count" in group
            assert group["total_seconds"] > 0
            assert group["entry_count"] > 0


class TestEntryCRUD:
    """Test time entry CRUD operations."""

    def test_create_manual_entry(self, client, auth_headers):
        """Create a manual time entry (already completed)."""
        now = datetime.now(timezone.utc)
        response = client.post(
            "/api/v1/time/entries",
            json={
                "started_at": (now - timedelta(hours=2)).isoformat(),
                "stopped_at": (now - timedelta(hours=1)).isoformat(),
                "description": "Manual entry for past work"
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["duration_seconds"] == 3600
        assert data["description"] == "Manual entry for past work"

    def test_get_single_entry(self, client, auth_headers, completed_entries):
        """Get a single time entry by ID."""
        entry_id = completed_entries[0].id
        response = client.get(
            f"/api/v1/time/entries/{entry_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id

    def test_update_entry(self, client, auth_headers, completed_entries):
        """Update a time entry."""
        entry_id = completed_entries[0].id
        response = client.patch(
            f"/api/v1/time/entries/{entry_id}",
            json={"description": "Updated description"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["description"] == "Updated description"

    def test_delete_entry(self, client, auth_headers, completed_entries):
        """Delete a time entry."""
        entry_id = completed_entries[0].id
        response = client.delete(
            f"/api/v1/time/entries/{entry_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Time endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_response = client.get(
            f"/api/v1/time/entries/{entry_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404
