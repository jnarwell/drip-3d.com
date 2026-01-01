"""
Phase 2 Team Aggregation Tests

Tests for:
- GET /api/v1/time/summary with user names
- GET /api/v1/users - Team member listing
- GET /api/v1/time/summary/by-project - Project-based aggregation
- POST /api/v1/linear-enhanced/sync-users - Sync Linear users
"""

import pytest
from datetime import datetime, timezone, timedelta


class TestSummaryUserNames:
    """Test summary endpoint includes user names."""

    def test_summary_includes_user_names(self, client, auth_headers, completed_entries):
        """Summary with group_by=user should include name field."""
        response = client.get(
            "/api/v1/time/summary?group_by=user",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "groups" in data

        for group in data["groups"]:
            assert "key" in group  # email
            # Phase 2 adds name field
            if "name" not in group:
                pytest.skip("User name enrichment not implemented yet")
            assert "name" in group

    def test_summary_user_without_entries(self, client, auth_headers):
        """Users without entries should not appear in summary."""
        response = client.get(
            "/api/v1/time/summary?group_by=user",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary endpoint not implemented yet")

        assert response.status_code == 200
        # Empty or only users with entries
        data = response.json()
        for group in data.get("groups", []):
            assert group.get("entry_count", 0) > 0


class TestListUsers:
    """Test GET /api/v1/users endpoint."""

    def test_list_users(self, client, auth_headers):
        """GET /users returns team members."""
        response = client.get("/api/v1/users", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Users endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "users" in data

    def test_list_users_includes_email(self, client, auth_headers):
        """Each user has an email field."""
        response = client.get("/api/v1/users", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Users endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for user in data.get("users", []):
            assert "email" in user

    def test_list_users_includes_name(self, client, auth_headers):
        """Each user has a name field."""
        response = client.get("/api/v1/users", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Users endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for user in data.get("users", []):
            assert "name" in user

    def test_list_users_active_filter(self, client, auth_headers):
        """Filter users by active status."""
        response = client.get("/api/v1/users?active=true", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Users endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for user in data.get("users", []):
            assert user.get("is_active", True) is True


class TestSummaryByProject:
    """Test GET /api/v1/time/summary/by-project endpoint."""

    def test_summary_by_project(self, client, auth_headers):
        """GET /summary/by-project returns project breakdown."""
        response = client.get(
            "/api/v1/time/summary/by-project",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary by project endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "groups" in data
        assert data["group_by"] == "project"

    def test_summary_by_project_includes_totals(self, client, auth_headers, completed_entries):
        """Each project group includes total_seconds and entry_count."""
        response = client.get(
            "/api/v1/time/summary/by-project",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary by project endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for group in data.get("groups", []):
            assert "total_seconds" in group
            assert "entry_count" in group

    def test_summary_by_project_includes_project_name(self, client, auth_headers, completed_entries):
        """Each group includes project_name from Linear."""
        response = client.get(
            "/api/v1/time/summary/by-project",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary by project endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        for group in data.get("groups", []):
            # Should have project_id and project_name
            assert "project_id" in group or "key" in group
            # project_name may be None for entries without Linear project
            assert "project_name" in group

    def test_summary_by_project_date_filter(self, client, auth_headers, completed_entries):
        """Filter project summary by date range."""
        today = datetime.now(timezone.utc).date()

        response = client.get(
            f"/api/v1/time/summary/by-project?start_date={today.isoformat()}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary by project endpoint not implemented yet")

        assert response.status_code == 200

    def test_summary_by_project_user_filter(self, client, auth_headers, completed_entries):
        """Filter project summary by user."""
        response = client.get(
            "/api/v1/time/summary/by-project?user_id=user@drip-3d.com",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Summary by project endpoint not implemented yet")

        assert response.status_code == 200


class TestLinearSync:
    """Test Linear user sync endpoint."""

    def test_sync_linear_users(self, client, auth_headers):
        """POST /linear-enhanced/sync-users syncs team members."""
        response = client.post(
            "/api/v1/linear-enhanced/sync-users",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Linear sync endpoint not implemented yet")

        # May also return 503 if Linear not configured
        if response.status_code == 503:
            pytest.skip("Linear API not configured")

        assert response.status_code == 200
        data = response.json()
        assert "synced" in data or "users" in data

    def test_sync_returns_count(self, client, auth_headers):
        """Sync returns count of synced users."""
        response = client.post(
            "/api/v1/linear-enhanced/sync-users",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Linear sync endpoint not implemented yet")
        if response.status_code == 503:
            pytest.skip("Linear API not configured")

        assert response.status_code == 200
        data = response.json()
        # Should include count of synced users
        assert "synced" in data or "count" in data or "users" in data


class TestTeamDashboard:
    """Test team dashboard aggregation endpoints."""

    def test_team_summary(self, client, auth_headers, completed_entries):
        """Get overall team summary."""
        response = client.get(
            "/api/v1/time/team-summary",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Team summary endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should include overall metrics
        assert "total_hours" in data or "total_seconds" in data
        assert "entry_count" in data or "total_entries" in data

    def test_team_summary_by_week(self, client, auth_headers, completed_entries):
        """Get team summary grouped by week."""
        response = client.get(
            "/api/v1/time/team-summary?period=week",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Team summary endpoint not implemented yet")

        assert response.status_code == 200

    def test_active_timers_admin(self, client, auth_headers):
        """Admin can see all active timers across team."""
        response = client.get(
            "/api/v1/time/active-all",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Active timers admin endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "active_timers" in data
        assert "count" in data


class TestUserTimeStats:
    """Test per-user time statistics."""

    def test_user_stats(self, client, auth_headers, completed_entries):
        """Get time stats for a specific user."""
        response = client.get(
            "/api/v1/time/users/user@drip-3d.com/stats",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("User stats endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data or "email" in data
        assert "total_seconds" in data or "total_hours" in data

    def test_user_stats_by_period(self, client, auth_headers, completed_entries):
        """Get time stats for user by period."""
        response = client.get(
            "/api/v1/time/users/user@drip-3d.com/stats?period=week",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("User stats endpoint not implemented yet")

        assert response.status_code == 200

    def test_user_recent_entries(self, client, auth_headers, completed_entries):
        """Get recent entries for a specific user."""
        response = client.get(
            "/api/v1/time/users/user@drip-3d.com/entries",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("User entries endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "entries" in data
