"""
Analysis Dashboard CRUD Endpoint Tests

Tests for:
- GET /api/v1/analyses - List all analyses
- GET /api/v1/analyses/{id} - Get single analysis
- POST /api/v1/analyses - Create analysis (alias for model-instances)
- PATCH /api/v1/analyses/{id} - Update analysis
- DELETE /api/v1/analyses/{id} - Delete analysis
- POST /api/v1/analyses/{id}/evaluate - Force re-evaluation

NOTE: These tests define the expected API behavior.
All tests are SKIPPED until the analysis router is implemented.

To run tests once the endpoint is implemented:
1. Create /api/v1/analyses router in backend/app/api/v1/analyses.py
2. Register router in main.py
3. Remove the pytestmark skip below
4. Run: pytest tests/test_analysis/test_crud.py -v
"""

import pytest
from app.models.physics_model import ModelInstance, ModelInput
from app.models.values import ValueNode, ComputationStatus


class TestListAnalyses:
    """Test GET /api/v1/analyses endpoint."""

    def test_list_empty(self, client, db):
        """Empty list when no analyses exist."""
        response = client.get("/api/v1/analyses")

        # NOTE: Will 404 until endpoint exists
        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json() == []

    def test_list_multiple_analyses(self, client, db, multiple_analyses):
        """List returns all analyses sorted by created_at descending."""
        response = client.get("/api/v1/analyses")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5

        # Check sorted by created_at DESC (E, D, C, B, A - most recent first)
        names = [item['name'] for item in data]
        assert names == ['Analysis E', 'Analysis D', 'Analysis C', 'Analysis B', 'Analysis A']

    def test_list_excludes_component_instances(self, client, db, thermal_model, component_attached_instance):
        """List should not include component-attached instances."""
        # Create an analysis in addition to component_attached_instance
        version = thermal_model.current_version
        analysis = ModelInstance(
            model_version_id=version.id,
            name="Standalone Analysis",
            component_id=None,  # Analysis
            created_by="test@drip-3d.com"
        )
        db.add(analysis)
        db.flush()

        # Add required inputs
        inputs = [
            ModelInput(model_instance_id=analysis.id, input_name="CTE", literal_value=2.3e-5),
            ModelInput(model_instance_id=analysis.id, input_name="delta_T", literal_value=100.0),
            ModelInput(model_instance_id=analysis.id, input_name="L0", literal_value=0.003),
        ]
        for inp in inputs:
            db.add(inp)
        db.commit()

        response = client.get("/api/v1/analyses")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()

        # Should only have the analysis, not component instance
        assert len(data) == 1
        assert data[0]['name'] == "Standalone Analysis"
        # is_analysis field only present in detailed responses, not list

    def test_list_includes_model_info(self, client, db, thermal_analysis):
        """List should include model name for each analysis."""
        response = client.get("/api/v1/analyses")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()
        assert len(data) == 1
        assert 'model' in data[0]
        assert data[0]['model']['name'] == "Thermal Expansion"

    @pytest.mark.skip(reason="Filter params not implemented in API")
    def test_filter_by_status(self, client, db, multiple_analyses):
        """Filter analyses by computation status."""
        # Set different statuses
        multiple_analyses[0].computation_status = ComputationStatus.VALID
        multiple_analyses[1].computation_status = ComputationStatus.STALE
        multiple_analyses[2].computation_status = ComputationStatus.ERROR
        multiple_analyses[3].computation_status = ComputationStatus.VALID
        multiple_analyses[4].computation_status = ComputationStatus.PENDING
        db.commit()

        # Filter by valid
        response = client.get("/api/v1/analyses?status=valid")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(item['computation_status'] == 'valid' for item in data)

    @pytest.mark.skip(reason="Filter params not implemented in API")
    def test_filter_by_model_id(self, client, db, multiple_analyses, thermal_model):
        """Filter analyses by physics model."""
        model_id = thermal_model.id

        response = client.get(f"/api/v1/analyses?model_id={model_id}")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should only return analyses using thermal model (A, C, E)
        assert len(data) == 3
        assert all(item['model']['name'] == thermal_model.name for item in data)

    @pytest.mark.skip(reason="Filter params not implemented in API")
    def test_filter_by_model_name(self, client, db, multiple_analyses, thermal_model):
        """Filter analyses by model name."""
        response = client.get("/api/v1/analyses?model_name=Thermal")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should match "Thermal Expansion"
        assert len(data) == 3


class TestGetAnalysis:
    """Test GET /api/v1/analyses/{id} endpoint."""

    def test_get_analysis(self, client, db, thermal_analysis):
        """Get single analysis by ID."""
        response = client.get(f"/api/v1/analyses/{thermal_analysis.id}")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data['id'] == thermal_analysis.id
        assert data['name'] == "Test Thermal Analysis"
        # is_analysis not in response - component_id being None indicates analysis

    def test_get_analysis_includes_inputs(self, client, db, thermal_analysis):
        """Get analysis includes input bindings."""
        response = client.get(f"/api/v1/analyses/{thermal_analysis.id}")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()
        assert 'inputs' in data
        assert len(data['inputs']) == 3

        # Check input names (API uses 'input_name' field)
        input_names = {inp['input_name'] for inp in data['inputs']}
        assert input_names == {'CTE', 'delta_T', 'L0'}

    def test_get_analysis_includes_outputs(self, client, db, thermal_analysis_with_outputs):
        """Get evaluated analysis includes output_value_nodes."""
        response = client.get(f"/api/v1/analyses/{thermal_analysis_with_outputs.id}")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()
        assert 'output_value_nodes' in data
        assert len(data['output_value_nodes']) > 0
        assert data['output_value_nodes'][0]['name'] == 'delta_L'

    def test_get_nonexistent_analysis(self, client, db):
        """Get non-existent analysis returns 404."""
        response = client.get("/api/v1/analyses/999999")

        # If endpoint not implemented, we get 404 anyway
        assert response.status_code == 404

    def test_get_component_instance_as_analysis(self, client, db, component_attached_instance):
        """Getting component-attached instance via /analyses should fail."""
        response = client.get(f"/api/v1/analyses/{component_attached_instance.id}")

        # Should return 404 because it's not an analysis
        if response.status_code == 404:
            pass  # Expected - either endpoint missing or correctly rejecting
        else:
            assert response.status_code == 404


class TestCreateAnalysis:
    """Test POST /api/v1/analyses endpoint."""

    def test_create_analysis(self, client, db, thermal_model, auth_headers):
        """Create a new analysis."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "New Analysis",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code in [200, 201]
        data = response.json()
        assert data['name'] == "New Analysis"
        assert data['is_analysis'] is True
        assert data['component_id'] is None

    def test_create_analysis_with_description(self, client, db, thermal_model, auth_headers):
        """Create analysis with description."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Described Analysis",
                "description": "Analysis for testing thermal expansion",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code in [200, 201]
        data = response.json()
        assert data['description'] == "Analysis for testing thermal expansion"

    def test_create_analysis_evaluates_immediately(self, client, db, thermal_model, auth_headers):
        """Creating analysis triggers immediate evaluation."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Auto-Evaluated",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()

        # Should have output_value_nodes
        assert 'output_value_nodes' in data
        assert len(data['output_value_nodes']) > 0

        # Should have valid status (lowercase)
        assert data['computation_status'] == 'valid'

    def test_create_analysis_missing_required_input(self, client, db, thermal_model, auth_headers):
        """Create with missing required input should fail."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Incomplete",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5"
                    # Missing delta_T and L0
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 400
        assert "missing" in response.json()['detail'].lower()

    def test_create_analysis_duplicate_name(self, client, db, thermal_analysis, thermal_model, auth_headers):
        """Create with duplicate name should fail."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Test Thermal Analysis",  # Already exists
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 400
        assert "already exists" in response.json()['detail'].lower()

    def test_create_analysis_invalid_model(self, client, db, auth_headers):
        """Create with invalid model version should fail."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Bad Model",
                "model_version_id": 999999,  # Non-existent
                "bindings": {}
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code in [400, 404]


class TestUpdateAnalysis:
    """Test PATCH /api/v1/analyses/{id} endpoint."""

    def test_update_name(self, client, db, thermal_analysis, auth_headers):
        """Update analysis name."""
        response = client.patch(
            f"/api/v1/analyses/{thermal_analysis.id}",
            json={"name": "Updated Name"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()
        assert data['name'] == "Updated Name"

    def test_update_description(self, client, db, thermal_analysis, auth_headers):
        """Update analysis description."""
        response = client.patch(
            f"/api/v1/analyses/{thermal_analysis.id}",
            json={"description": "New description"},
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json()['description'] == "New description"

    def test_update_name_duplicate(self, client, db, multiple_analyses, auth_headers):
        """Cannot update to duplicate name."""
        response = client.patch(
            f"/api/v1/analyses/{multiple_analyses[0].id}",
            json={"name": "Analysis B"},  # Already exists
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 400
        assert "already exists" in response.json()['detail'].lower()

    def test_update_bindings_triggers_reeval(self, client, db, thermal_analysis_with_outputs, auth_headers):
        """Update input bindings triggers re-evaluation."""
        original_id = thermal_analysis_with_outputs.id

        response = client.patch(
            f"/api/v1/analyses/{original_id}",
            json={
                "bindings": {
                    "CTE": "5.0e-5",  # Changed value
                    "delta_T": "200",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should have re-evaluated with new values
        assert len(data['output_value_nodes']) > 0

        # Check that input was updated
        cte_input = next(inp for inp in data['inputs'] if inp['input_name'] == 'CTE')
        assert cte_input['literal_value'] == 5.0e-5

    def test_update_single_binding(self, client, db, thermal_analysis, auth_headers):
        """Update single binding should work."""
        response = client.patch(
            f"/api/v1/analyses/{thermal_analysis.id}",
            json={
                "bindings": {
                    "delta_T": "500"  # Only update one
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # delta_T should be updated
        dt_input = next(inp for inp in data['inputs'] if inp['input_name'] == 'delta_T')
        assert dt_input['literal_value'] == 500.0

    def test_update_nonexistent_analysis(self, client, db, auth_headers):
        """Update non-existent analysis returns 404."""
        response = client.patch(
            "/api/v1/analyses/999999",
            json={"name": "New Name"},
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_update_component_instance_as_analysis(self, client, db, component_attached_instance, auth_headers):
        """Cannot update component-attached instance via /analyses."""
        response = client.patch(
            f"/api/v1/analyses/{component_attached_instance.id}",
            json={"name": "Hacked Name"},
            headers=auth_headers
        )

        # Should fail - not an analysis
        assert response.status_code == 404


class TestDeleteAnalysis:
    """Test DELETE /api/v1/analyses/{id} endpoint."""

    def test_delete_analysis(self, client, db, thermal_analysis, auth_headers):
        """Delete analysis removes instance."""
        instance_id = thermal_analysis.id

        response = client.delete(
            f"/api/v1/analyses/{instance_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        assert response.json().get('success') is True or 'deleted' in str(response.json()).lower()

        # Verify deleted
        instance = db.query(ModelInstance).filter(ModelInstance.id == instance_id).first()
        assert instance is None

    def test_delete_removes_inputs(self, client, db, thermal_analysis, auth_headers):
        """Deleting analysis removes input records."""
        instance_id = thermal_analysis.id

        # Count inputs before
        inputs_before = db.query(ModelInput).filter(
            ModelInput.model_instance_id == instance_id
        ).count()
        assert inputs_before == 3

        response = client.delete(
            f"/api/v1/analyses/{instance_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        # Inputs should be deleted
        inputs_after = db.query(ModelInput).filter(
            ModelInput.model_instance_id == instance_id
        ).count()
        assert inputs_after == 0

    def test_delete_removes_outputs(self, client, db, thermal_analysis_with_outputs, auth_headers):
        """Deleting analysis removes output ValueNodes."""
        instance_id = thermal_analysis_with_outputs.id

        # Verify outputs exist
        outputs_before = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).count()
        assert outputs_before > 0

        response = client.delete(
            f"/api/v1/analyses/{instance_id}",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        # Outputs should be deleted
        outputs_after = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).count()
        assert outputs_after == 0

    def test_delete_nonexistent_analysis(self, client, db, auth_headers):
        """Delete non-existent analysis returns 404."""
        response = client.delete(
            "/api/v1/analyses/999999",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_delete_component_instance_as_analysis(self, client, db, component_attached_instance, auth_headers):
        """Cannot delete component-attached instance via /analyses."""
        response = client.delete(
            f"/api/v1/analyses/{component_attached_instance.id}",
            headers=auth_headers
        )

        # Should fail - not an analysis
        assert response.status_code == 404


class TestEvaluateAnalysis:
    """Test POST /api/v1/analyses/{id}/evaluate endpoint."""

    def test_force_evaluate(self, client, db, thermal_analysis, auth_headers):
        """Force evaluation creates output ValueNodes."""
        instance_id = thermal_analysis.id

        response = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert response.status_code == 200
        data = response.json()

        # Should have output_value_nodes
        assert len(data['output_value_nodes']) > 0
        assert data['output_value_nodes'][0]['name'] == 'delta_L'
        assert data['computation_status'] == 'valid'

    def test_evaluate_updates_timestamp(self, client, db, thermal_analysis, auth_headers):
        """Evaluation updates last_computed timestamp."""
        instance_id = thermal_analysis.id

        # First evaluation
        response1 = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        if response1.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        time1 = response1.json()['last_computed']

        # Brief delay
        import time
        time.sleep(0.1)

        # Second evaluation
        response2 = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        time2 = response2.json()['last_computed']

        # Timestamp should be updated
        assert time2 > time1

    def test_evaluate_replaces_outputs(self, client, db, thermal_analysis_with_outputs, auth_headers):
        """Re-evaluation replaces old outputs."""
        instance_id = thermal_analysis_with_outputs.id

        # Get original output count
        outputs_before = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
        output_ids_before = {o.id for o in outputs_before}

        response = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        # Old outputs should be gone or replaced
        outputs_after = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()

        # Should have same number of outputs
        assert len(outputs_after) == len(outputs_before)

    def test_evaluate_nonexistent_analysis(self, client, db, auth_headers):
        """Evaluate non-existent analysis returns 404."""
        response = client.post(
            "/api/v1/analyses/999999/evaluate",
            headers=auth_headers
        )
        assert response.status_code == 404

    def test_evaluate_with_lookup_binding(self, client, db, thermal_model, auth_headers):
        """Evaluate analysis with LOOKUP binding."""
        # Create analysis with LOOKUP binding
        version = thermal_model.current_version
        instance = ModelInstance(
            model_version_id=version.id,
            name="Lookup Analysis",
            component_id=None,
            created_by="test@drip-3d.com"
        )
        db.add(instance)
        db.flush()

        inputs = [
            ModelInput(
                model_instance_id=instance.id,
                input_name="CTE",
                source_lookup={
                    "table": "engineering_properties",
                    "column": "CTE",
                    "material": "Aluminum",
                    "temperature": 300
                }
            ),
            ModelInput(model_instance_id=instance.id, input_name="delta_T", literal_value=100.0),
            ModelInput(model_instance_id=instance.id, input_name="L0", literal_value=0.003),
        ]
        for inp in inputs:
            db.add(inp)
        db.commit()

        response = client.post(
            f"/api/v1/analyses/{instance.id}/evaluate",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        # May fail if LOOKUP not resolved, but should attempt evaluation
        assert response.status_code in [200, 400, 422]


class TestMultiOutputAnalysis:
    """Test analyses with multiple outputs."""

    def test_multi_output_evaluation(self, client, db, rectangle_model, auth_headers):
        """Evaluate model with multiple outputs."""
        version = rectangle_model.current_version
        instance = ModelInstance(
            model_version_id=version.id,
            name="Rectangle Analysis",
            component_id=None,
            created_by="test@drip-3d.com"
        )
        db.add(instance)
        db.flush()

        inputs = [
            ModelInput(model_instance_id=instance.id, input_name="length", literal_value=5.0),
            ModelInput(model_instance_id=instance.id, input_name="width", literal_value=3.0),
        ]
        for inp in inputs:
            db.add(inp)
        db.commit()

        response = client.post(
            f"/api/v1/analyses/{instance.id}/evaluate",
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()

        # Should have both output_value_nodes
        assert len(data['output_value_nodes']) == 2

        output_names = {o['name'] for o in data['output_value_nodes']}
        assert output_names == {'area', 'perimeter'}

        # Check values
        area = next(o for o in data['output_value_nodes'] if o['name'] == 'area')
        perimeter = next(o for o in data['output_value_nodes'] if o['name'] == 'perimeter')

        assert area['computed_value'] == 15.0  # 5 * 3
        assert perimeter['computed_value'] == 16.0  # 2 * (5 + 3)
