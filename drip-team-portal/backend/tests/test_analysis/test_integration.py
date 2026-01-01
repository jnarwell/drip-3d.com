"""
Analysis Dashboard Integration Tests

End-to-end tests for the Analysis Dashboard feature:
- Full CRUD lifecycle
- Model evaluation integration
- WebSocket + REST API interaction
- Database state verification

NOTE: All tests are SKIPPED until the Analysis REST API is implemented.

To run tests once the endpoint is implemented:
1. Create /api/v1/analyses router
2. Remove the pytestmark skip below
3. Run: pytest tests/test_analysis/test_integration.py -v
"""

import pytest
import time
from app.models.physics_model import ModelInstance, ModelInput
from app.models.values import ValueNode, ComputationStatus


class TestAnalysisFullLifecycle:
    """End-to-end analysis lifecycle tests."""

    def test_create_list_update_evaluate_delete(self, client, db, thermal_model, auth_headers):
        """Complete lifecycle: Create → List → Update → Evaluate → Delete."""

        # 1. CREATE
        create_response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Lifecycle Test",
                "description": "E2E test analysis",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if create_response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        assert create_response.status_code in [200, 201]
        instance_id = create_response.json()['id']
        assert instance_id is not None

        # 2. LIST (should include new analysis)
        list_response = client.get("/api/v1/analyses")
        assert list_response.status_code == 200
        analyses = list_response.json()
        assert any(a['id'] == instance_id for a in analyses)
        assert any(a['name'] == "Lifecycle Test" for a in analyses)

        # 3. GET (single analysis)
        get_response = client.get(f"/api/v1/analyses/{instance_id}")
        assert get_response.status_code == 200
        assert get_response.json()['name'] == "Lifecycle Test"
        assert get_response.json()['description'] == "E2E test analysis"

        # 4. UPDATE name
        update_response = client.patch(
            f"/api/v1/analyses/{instance_id}",
            json={"name": "Lifecycle Test Updated"},
            headers=auth_headers
        )
        assert update_response.status_code == 200
        assert update_response.json()['name'] == "Lifecycle Test Updated"

        # Verify in list
        list_after_update = client.get("/api/v1/analyses")
        assert any(a['name'] == "Lifecycle Test Updated" for a in list_after_update.json())

        # 5. FORCE EVALUATE
        eval_response = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )
        assert eval_response.status_code == 200
        eval_data = eval_response.json()
        assert len(eval_data['output_value_nodes']) > 0
        assert eval_data['computation_status'] == 'valid'

        # Verify output value
        delta_l = next(o for o in eval_data['output_value_nodes'] if o['name'] == 'delta_L')
        expected = 2.3e-5 * 100 * 0.003  # CTE * delta_T * L0
        assert abs(delta_l['computed_value'] - expected) < 1e-12

        # 6. DELETE
        delete_response = client.delete(
            f"/api/v1/analyses/{instance_id}",
            headers=auth_headers
        )
        assert delete_response.status_code == 200

        # 7. VERIFY DELETED
        list_after_delete = client.get("/api/v1/analyses")
        assert not any(a['id'] == instance_id for a in list_after_delete.json())

        # Verify database state
        instance = db.query(ModelInstance).filter(ModelInstance.id == instance_id).first()
        assert instance is None


class TestAnalysisEvaluationIntegration:
    """Tests for model evaluation integration."""

    def test_create_triggers_evaluation(self, client, db, thermal_model, auth_headers):
        """Creating analysis with bindings triggers immediate evaluation."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Auto-Eval Test",
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

        # Should already have output_value_nodes
        assert len(data['output_value_nodes']) > 0
        assert data['computation_status'] == 'valid'

        # Verify output ValueNodes in database
        instance_id = data['id']
        outputs = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
        assert len(outputs) > 0

    def test_update_bindings_triggers_reevaluation(self, client, db, thermal_model, auth_headers):
        """Updating bindings triggers re-evaluation with new values."""
        # Create
        create_response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Reeval Test",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        if create_response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        instance_id = create_response.json()['id']
        original_output = create_response.json()['output_value_nodes'][0]['computed_value']

        # Update with new delta_T (doubled) - must pass ALL bindings as PATCH replaces
        client.patch(
            f"/api/v1/analyses/{instance_id}",
            json={
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "200",  # Double the temperature change
                    "L0": "0.003"
                }
            },
            headers=auth_headers
        )

        # Force re-evaluation after binding update
        eval_response = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        new_output = eval_response.json()['output_value_nodes'][0]['computed_value']

        # Output should be approximately doubled
        assert abs(new_output / original_output - 2.0) < 0.01

    def test_evaluation_preserves_output_relationships(self, client, db, thermal_model, auth_headers):
        """Re-evaluation replaces outputs but maintains proper relationships."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Output Relationship Test",
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

        instance_id = response.json()['id']

        # Get output node IDs
        outputs_1 = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
        ids_1 = {o.id for o in outputs_1}

        # Re-evaluate
        client.post(f"/api/v1/analyses/{instance_id}/evaluate", headers=auth_headers)
        db.expire_all()  # Clear SQLAlchemy cache

        # Get new output nodes
        outputs_2 = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()

        # Should have same count
        assert len(outputs_2) == len(outputs_1)

        # All outputs should reference the instance
        for output in outputs_2:
            assert output.source_model_instance_id == instance_id


class TestMultiOutputAnalysis:
    """Tests for analyses with multiple outputs."""

    def test_rectangle_creates_both_outputs(self, client, db, rectangle_model, auth_headers):
        """Rectangle model creates both area and perimeter outputs."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Rectangle Analysis",
                "model_version_id": rectangle_model.current_version.id,
                "bindings": {
                    "length": "5",
                    "width": "3"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()
        outputs = data['output_value_nodes']

        assert len(outputs) == 2

        output_map = {o['name']: o['computed_value'] for o in outputs}
        assert 'area' in output_map
        assert 'perimeter' in output_map
        assert output_map['area'] == 15.0  # 5 * 3
        assert output_map['perimeter'] == 16.0  # 2 * (5 + 3)

    def test_update_affects_all_outputs(self, client, db, rectangle_model, auth_headers):
        """Updating inputs re-calculates all outputs."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Multi-Output Update Test",
                "model_version_id": rectangle_model.current_version.id,
                "bindings": {
                    "length": "5",
                    "width": "3"
                }
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        instance_id = response.json()['id']

        # Update length - must pass ALL bindings as PATCH replaces
        client.patch(
            f"/api/v1/analyses/{instance_id}",
            json={
                "bindings": {
                    "length": "10",  # Double the length
                    "width": "3"
                }
            },
            headers=auth_headers
        )

        # Force re-evaluation after binding update
        eval_response = client.post(
            f"/api/v1/analyses/{instance_id}/evaluate",
            headers=auth_headers
        )

        outputs = eval_response.json()['output_value_nodes']
        output_map = {o['name']: o['computed_value'] for o in outputs}

        assert output_map['area'] == 30.0  # 10 * 3
        assert output_map['perimeter'] == 26.0  # 2 * (10 + 3)


class TestAnalysisFiltering:
    """Tests for filtering and sorting analyses."""

    @pytest.mark.skip(reason="Filter params not implemented in API")
    def test_filter_by_multiple_criteria(self, client, db, multiple_analyses, thermal_model):
        """Can filter by model and status together."""
        # Set specific status on thermal analyses
        for analysis in multiple_analyses:
            if analysis.model_version.physics_model_id == thermal_model.id:
                analysis.computation_status = ComputationStatus.VALID
            else:
                analysis.computation_status = ComputationStatus.STALE
        db.commit()

        response = client.get(
            f"/api/v1/analyses?model_id={thermal_model.id}&status=valid"
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        data = response.json()

        # Should only return valid thermal analyses
        assert len(data) > 0
        for analysis in data:
            assert analysis['model']['id'] == thermal_model.id
            assert analysis['computation_status'] == 'valid'

    def test_list_is_sorted_by_created_at_desc(self, client, db, multiple_analyses):
        """List returns analyses sorted by created_at descending."""
        response = client.get("/api/v1/analyses")

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        names = [a['name'] for a in response.json()]

        # Should be sorted by created_at DESC (E, D, C, B, A)
        assert names == ['Analysis E', 'Analysis D', 'Analysis C', 'Analysis B', 'Analysis A']


class TestDatabaseStateConsistency:
    """Tests that verify database state consistency."""

    def test_create_creates_all_records(self, client, db, thermal_model, auth_headers):
        """Create properly creates instance, inputs, and outputs."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "State Consistency Test",
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

        instance_id = response.json()['id']

        # Verify instance exists
        instance = db.query(ModelInstance).filter(
            ModelInstance.id == instance_id
        ).first()
        assert instance is not None
        assert instance.name == "State Consistency Test"
        assert instance.component_id is None  # Is analysis

        # Verify inputs exist
        inputs = db.query(ModelInput).filter(
            ModelInput.model_instance_id == instance_id
        ).all()
        assert len(inputs) == 3
        input_names = {i.input_name for i in inputs}
        assert input_names == {'CTE', 'delta_T', 'L0'}

        # Verify outputs exist
        outputs = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
        assert len(outputs) == 1
        assert outputs[0].source_output_name == 'delta_L'

    def test_delete_removes_all_records(self, client, db, thermal_model, auth_headers):
        """Delete removes instance, inputs, and outputs."""
        # Create
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Delete Consistency Test",
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

        instance_id = response.json()['id']

        # Delete
        client.delete(f"/api/v1/analyses/{instance_id}", headers=auth_headers)

        # Verify instance deleted
        instance = db.query(ModelInstance).filter(
            ModelInstance.id == instance_id
        ).first()
        assert instance is None

        # Verify inputs deleted
        inputs = db.query(ModelInput).filter(
            ModelInput.model_instance_id == instance_id
        ).all()
        assert len(inputs) == 0

        # Verify outputs deleted
        outputs = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance_id
        ).all()
        assert len(outputs) == 0

    def test_analysis_does_not_affect_other_analyses(self, client, db, thermal_model, auth_headers):
        """Operations on one analysis don't affect others."""
        # Create two analyses
        response1 = client.post(
            "/api/v1/analyses",
            json={
                "name": "Analysis 1",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {"CTE": "2.3e-5", "delta_T": "100", "L0": "0.003"}
            },
            headers=auth_headers
        )

        if response1.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        response2 = client.post(
            "/api/v1/analyses",
            json={
                "name": "Analysis 2",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {"CTE": "2.3e-5", "delta_T": "200", "L0": "0.003"}
            },
            headers=auth_headers
        )

        id1 = response1.json()['id']
        id2 = response2.json()['id']

        # Delete analysis 1
        client.delete(f"/api/v1/analyses/{id1}", headers=auth_headers)

        # Analysis 2 should still exist
        get_response = client.get(f"/api/v1/analyses/{id2}")
        assert get_response.status_code == 200
        assert get_response.json()['name'] == "Analysis 2"

        # Analysis 2's outputs should still exist
        outputs = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == id2
        ).all()
        assert len(outputs) > 0


class TestConcurrentOperations:
    """Tests for handling concurrent operations."""

    def test_rapid_updates_dont_corrupt_state(self, client, db, thermal_model, auth_headers):
        """Multiple rapid updates don't corrupt analysis state."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Rapid Update Test",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {"CTE": "2.3e-5", "delta_T": "100", "L0": "0.003"}
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        instance_id = response.json()['id']

        # Rapid updates
        for i in range(5):
            client.patch(
                f"/api/v1/analyses/{instance_id}",
                json={"bindings": {"delta_T": str((i + 1) * 100)}},
                headers=auth_headers
            )

        # Final state should be consistent
        final = client.get(f"/api/v1/analyses/{instance_id}").json()

        # Should have exactly one set of output_value_nodes
        assert len(final['output_value_nodes']) == 1

        # Input should be final value
        dt_input = next(i for i in final['inputs'] if i['input_name'] == 'delta_T')
        assert dt_input['literal_value'] == 500.0  # 5 * 100

    def test_rapid_evaluations_produce_correct_results(self, client, db, thermal_model, auth_headers):
        """Multiple rapid evaluations produce correct results."""
        response = client.post(
            "/api/v1/analyses",
            json={
                "name": "Rapid Eval Test",
                "model_version_id": thermal_model.current_version.id,
                "bindings": {"CTE": "2.3e-5", "delta_T": "100", "L0": "0.003"}
            },
            headers=auth_headers
        )

        if response.status_code == 404:
            pytest.skip("Analysis endpoint not implemented yet")

        instance_id = response.json()['id']

        # Rapid evaluations
        for _ in range(3):
            client.post(f"/api/v1/analyses/{instance_id}/evaluate", headers=auth_headers)

        # Final state should be correct
        final = client.get(f"/api/v1/analyses/{instance_id}").json()

        expected = 2.3e-5 * 100 * 0.003
        actual = final['output_value_nodes'][0]['computed_value']
        assert abs(actual - expected) < 1e-12
