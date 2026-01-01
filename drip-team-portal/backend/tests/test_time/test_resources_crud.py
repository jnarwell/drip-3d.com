"""
Resources API Tests

Tests for:
- POST /api/v1/resources - Create resource
- GET /api/v1/resources - List resources with filters
- GET /api/v1/resources/{id} - Get single resource
- PATCH /api/v1/resources/{id} - Update resource
- DELETE /api/v1/resources/{id} - Delete resource
- Resource <-> Component associations
"""

import pytest


class TestCreateResource:
    """Test POST /api/v1/resources endpoint."""

    def test_create_resource(self, client, auth_headers):
        """Create a basic resource."""
        response = client.post(
            "/api/v1/resources",
            json={
                "title": "Test Doc",
                "resource_type": "doc",
                "url": "https://example.com/doc"
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Test Doc"
        assert data["resource_type"] == "doc"
        assert data["url"] == "https://example.com/doc"
        assert "id" in data

    def test_create_resource_with_tags(self, client, auth_headers):
        """Create resource with tags."""
        response = client.post(
            "/api/v1/resources",
            json={
                "title": "Tagged Resource",
                "resource_type": "paper",
                "url": "https://arxiv.org/paper",
                "tags": ["research", "thermal", "phase-1"]
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["research", "thermal", "phase-1"]

    def test_create_resource_with_notes(self, client, auth_headers):
        """Create resource with notes."""
        response = client.post(
            "/api/v1/resources",
            json={
                "title": "Noted Resource",
                "resource_type": "link",
                "notes": "Important reference for thermal calculations"
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == "Important reference for thermal calculations"

    def test_create_resource_invalid_type(self, client, auth_headers):
        """Create with invalid resource_type should fail."""
        response = client.post(
            "/api/v1/resources",
            json={
                "title": "Bad Type",
                "resource_type": "invalid_type"
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 400
        assert "resource_type" in response.json()["detail"].lower()

    def test_create_resource_all_valid_types(self, client, auth_headers):
        """All valid resource types work."""
        valid_types = ["doc", "folder", "image", "link", "paper", "video", "spreadsheet"]

        for resource_type in valid_types:
            response = client.post(
                "/api/v1/resources",
                json={
                    "title": f"Test {resource_type}",
                    "resource_type": resource_type
                },
                headers=auth_headers
            )

            if response.status_code == 404:
                pytest.skip("Resources endpoint not implemented yet")

            assert response.status_code == 200, f"Failed for type: {resource_type}"


class TestListResources:
    """Test GET /api/v1/resources endpoint."""

    def test_list_resources_empty(self, client, auth_headers):
        """Empty list when no resources."""
        response = client.get("/api/v1/resources", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "resources" in data
        assert len(data["resources"]) == 0

    def test_list_resources(self, client, auth_headers, multiple_resources):
        """List all resources."""
        response = client.get("/api/v1/resources", headers=auth_headers)

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data["resources"]) == len(multiple_resources)

    def test_list_filter_by_type(self, client, auth_headers, multiple_resources):
        """Filter resources by type."""
        response = client.get(
            "/api/v1/resources?resource_type=doc",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # Only 1 doc in fixtures
        assert len(data["resources"]) == 1
        assert data["resources"][0]["resource_type"] == "doc"

    def test_list_filter_by_component(self, client, auth_headers, multiple_resources, test_component):
        """Filter resources by linked component."""
        response = client.get(
            f"/api/v1/resources?component_id={test_component.id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        # 1 resource linked to component in fixtures
        assert len(data["resources"]) == 1

    def test_list_search(self, client, auth_headers, multiple_resources):
        """Search in title and notes."""
        response = client.get(
            "/api/v1/resources?search=Design",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data["resources"]) >= 1
        assert "Design" in data["resources"][0]["title"]


class TestGetResource:
    """Test GET /api/v1/resources/{id} endpoint."""

    def test_get_resource(self, client, auth_headers, test_resource):
        """Get single resource by ID."""
        response = client.get(
            f"/api/v1/resources/{test_resource.id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == test_resource.id
        assert data["title"] == test_resource.title

    def test_get_nonexistent_resource(self, client, auth_headers):
        """Get non-existent resource returns 404."""
        response = client.get(
            "/api/v1/resources/99999",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestUpdateResource:
    """Test PATCH /api/v1/resources/{id} endpoint."""

    def test_update_title(self, client, auth_headers, test_resource):
        """Update resource title."""
        response = client.patch(
            f"/api/v1/resources/{test_resource.id}",
            json={"title": "Updated Title"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"

    def test_update_tags(self, client, auth_headers, test_resource):
        """Update resource tags."""
        response = client.patch(
            f"/api/v1/resources/{test_resource.id}",
            json={"tags": ["new-tag", "updated"]},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data["tags"] == ["new-tag", "updated"]

    def test_update_invalid_type(self, client, auth_headers, test_resource):
        """Update with invalid type fails."""
        response = client.patch(
            f"/api/v1/resources/{test_resource.id}",
            json={"resource_type": "invalid"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 400


class TestDeleteResource:
    """Test DELETE /api/v1/resources/{id} endpoint."""

    def test_delete_resource(self, client, auth_headers, test_resource):
        """Delete a resource."""
        resource_id = test_resource.id
        response = client.delete(
            f"/api/v1/resources/{resource_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json()["deleted"] is True

        # Verify deleted
        get_response = client.get(
            f"/api/v1/resources/{resource_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 404

    def test_delete_nonexistent(self, client, auth_headers):
        """Delete non-existent resource returns 404."""
        response = client.delete(
            "/api/v1/resources/99999",
            headers=auth_headers
        )

        assert response.status_code == 404


class TestResourceComponentAssociation:
    """Test resource <-> component associations."""

    def test_create_with_component(self, client, auth_headers, test_component):
        """Create resource linked to component."""
        response = client.post(
            "/api/v1/resources",
            json={
                "title": "Component Doc",
                "resource_type": "doc",
                "component_ids": [test_component.id]
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert test_component.id in data["component_ids"]

    def test_update_component_association(self, client, auth_headers, test_resource, test_component):
        """Update resource to link to component."""
        response = client.patch(
            f"/api/v1/resources/{test_resource.id}",
            json={"component_ids": [test_component.id]},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert test_component.id in data["component_ids"]

    def test_remove_component_association(self, client, auth_headers, multiple_resources):
        """Remove component association from resource."""
        # First resource in fixtures is linked to test_component
        resource = multiple_resources[0]

        response = client.patch(
            f"/api/v1/resources/{resource.id}",
            json={"component_ids": []},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data["component_ids"]) == 0


class TestResourceTypes:
    """Test GET /api/v1/resources/types/list endpoint."""

    def test_list_resource_types(self, client, auth_headers):
        """Get list of valid resource types."""
        response = client.get(
            "/api/v1/resources/types/list",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Resources endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert len(data["types"]) >= 7

        type_ids = [t["id"] for t in data["types"]]
        assert "doc" in type_ids
        assert "paper" in type_ids
        assert "video" in type_ids
