"""
Test Validation Service

Handles:
- Comparing measured values to model predictions
- Comparing measured values to protocol targets
- Generating validation status (PASS/FAIL/WARNING)
- Aggregating validation statistics
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timezone
import logging

from app.models.test_protocol import (
    TestProtocol, TestRun, TestMeasurement, TestValidation,
    ValidationStatus, TestResultStatus, TestRunStatus
)
from app.models.physics_model import ModelInstance
from app.services.model_evaluation import evaluate_model_instance, get_instance_outputs

logger = logging.getLogger(__name__)


class TestValidationService:
    """Service for validating test measurements against predictions/targets"""

    def __init__(self, db: Session):
        self.db = db

    def validate_run(self, run: TestRun) -> List[TestValidation]:
        """
        Create validations for all measurements in a test run.

        Compares each measurement to:
        1. Model prediction (if analysis_id is set)
        2. Protocol target (from output_schema)

        Returns list of created TestValidation objects.
        """
        validations = []

        if not run.protocol or not run.protocol.output_schema:
            return validations

        # Get predictions from linked analysis
        predictions = self._get_predictions(run)

        # Build measurement lookup
        measurements = {m.parameter_name: m for m in run.measurements}

        # Validate each output parameter
        for output_spec in run.protocol.output_schema:
            param_name = output_spec.get("name")
            if not param_name:
                continue

            measurement = measurements.get(param_name)
            if not measurement:
                continue

            validation = self._create_validation(
                run=run,
                measurement=measurement,
                output_spec=output_spec,
                prediction=predictions.get(param_name)
            )

            if validation:
                self.db.add(validation)
                validations.append(validation)

        return validations

    def _get_predictions(self, run: TestRun) -> Dict[str, float]:
        """Get model predictions for a test run"""
        predictions = {}

        if not run.analysis_id:
            return predictions

        try:
            # Get the model instance
            analysis = self.db.query(ModelInstance).filter(
                ModelInstance.id == run.analysis_id
            ).first()

            if not analysis:
                return predictions

            # Get existing outputs or evaluate the model
            output_nodes = get_instance_outputs(analysis, self.db)

            if not output_nodes:
                # Try to evaluate the model if no outputs exist yet
                try:
                    output_nodes = evaluate_model_instance(analysis, self.db)
                except Exception as eval_error:
                    logger.warning(f"Could not evaluate model instance {analysis.id}: {eval_error}")
                    return predictions

            # Extract values from output nodes
            for node in output_nodes:
                if node.source_output_name and node.computed_value is not None:
                    predictions[node.source_output_name] = float(node.computed_value)

        except Exception as e:
            # Log but don't fail - validation can still use targets
            logger.warning(f"Could not get model predictions: {e}")

        return predictions

    def _create_validation(
        self,
        run: TestRun,
        measurement: TestMeasurement,
        output_spec: dict,
        prediction: Optional[float]
    ) -> Optional[TestValidation]:
        """Create a validation for a single measurement"""

        # Get target value (prediction takes precedence over static target)
        target = prediction if prediction is not None else output_spec.get("target")
        tolerance_pct = output_spec.get("tolerance_pct", 10.0)

        # Also check hard limits
        min_value = output_spec.get("min_value")
        max_value = output_spec.get("max_value")

        measured = measurement.measured_value

        # Determine status
        status = self._determine_status(
            measured=measured,
            target=target,
            tolerance_pct=tolerance_pct,
            min_value=min_value,
            max_value=max_value
        )

        # Calculate error if we have a target
        error_abs = None
        error_pct = None
        if target is not None and target != 0:
            error_abs = measured - target
            error_pct = (error_abs / target) * 100

        return TestValidation(
            run_id=run.id,
            parameter_name=measurement.parameter_name,
            predicted_value=target,
            measured_value=measured,
            unit_id=measurement.unit_id,
            error_absolute=error_abs,
            error_pct=error_pct,
            tolerance_pct=tolerance_pct,
            status=status
        )

    def _determine_status(
        self,
        measured: float,
        target: Optional[float],
        tolerance_pct: float,
        min_value: Optional[float],
        max_value: Optional[float]
    ) -> ValidationStatus:
        """Determine validation status based on measured value"""

        # Check hard limits first
        if min_value is not None and measured < min_value:
            return ValidationStatus.FAIL
        if max_value is not None and measured > max_value:
            return ValidationStatus.FAIL

        # Check against target with tolerance
        if target is not None and target != 0:
            error_pct = abs((measured - target) / target * 100)

            if error_pct <= tolerance_pct:
                return ValidationStatus.PASS
            elif error_pct <= tolerance_pct * 1.5:
                return ValidationStatus.WARNING
            else:
                return ValidationStatus.FAIL

        # No target to compare - assume pass if within hard limits
        return ValidationStatus.PASS

    def determine_run_result(self, run: TestRun) -> TestResultStatus:
        """
        Determine overall test result based on validations.

        Logic:
        - All PASS -> PASS
        - Any FAIL -> FAIL
        - Only WARNING (no FAIL) -> PARTIAL
        """
        validations = self.db.query(TestValidation).filter(
            TestValidation.run_id == run.id
        ).all()

        if not validations:
            return TestResultStatus.PASS  # No validations = assume pass

        statuses = [v.status for v in validations]

        if ValidationStatus.FAIL in statuses:
            return TestResultStatus.FAIL
        elif ValidationStatus.WARNING in statuses:
            return TestResultStatus.PARTIAL
        else:
            return TestResultStatus.PASS

    def get_validation_summary(self, protocol_id: int) -> dict:
        """Get validation statistics for a protocol across all runs"""
        validations = self.db.query(TestValidation).join(TestRun).filter(
            TestRun.protocol_id == protocol_id
        ).all()

        if not validations:
            return {"total": 0, "pass_rate": 0}

        by_parameter = {}
        for v in validations:
            if v.parameter_name not in by_parameter:
                by_parameter[v.parameter_name] = {
                    "total": 0,
                    "passed": 0,
                    "failed": 0,
                    "warning": 0,
                    "errors": []
                }

            stats = by_parameter[v.parameter_name]
            stats["total"] += 1

            if v.status == ValidationStatus.PASS:
                stats["passed"] += 1
            elif v.status == ValidationStatus.FAIL:
                stats["failed"] += 1
            else:
                stats["warning"] += 1

            if v.error_pct is not None:
                stats["errors"].append(v.error_pct)

        # Calculate averages
        for param, stats in by_parameter.items():
            if stats["errors"]:
                stats["avg_error_pct"] = sum(stats["errors"]) / len(stats["errors"])
                stats["max_error_pct"] = max(abs(e) for e in stats["errors"])
            del stats["errors"]  # Don't return raw error list

        total_validations = len(validations)
        total_passed = sum(1 for v in validations if v.status == ValidationStatus.PASS)

        return {
            "total": total_validations,
            "pass_rate": total_passed / total_validations if total_validations > 0 else 0,
            "by_parameter": by_parameter
        }


class TestStatsService:
    """Service for generating test statistics for dashboard"""

    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> dict:
        """Get test statistics for dashboard (only active protocols)"""
        total_protocols = self.db.query(TestProtocol).filter(
            TestProtocol.is_active == True
        ).count()

        # Only count runs from active protocols
        active_runs_query = self.db.query(TestRun).join(TestProtocol).filter(
            TestProtocol.is_active == True
        )

        total_runs = active_runs_query.count()

        completed_runs = active_runs_query.filter(
            TestRun.status == TestRunStatus.COMPLETED
        ).count()

        passed_runs = self.db.query(TestRun).join(TestProtocol).filter(
            TestProtocol.is_active == True,
            TestRun.result == TestResultStatus.PASS
        ).count()

        failed_runs = self.db.query(TestRun).join(TestProtocol).filter(
            TestProtocol.is_active == True,
            TestRun.result == TestResultStatus.FAIL
        ).count()

        in_progress = self.db.query(TestRun).join(TestProtocol).filter(
            TestProtocol.is_active == True,
            TestRun.status == TestRunStatus.IN_PROGRESS
        ).count()

        return {
            "totalProtocols": total_protocols,
            "totalRuns": total_runs,
            "completedRuns": completed_runs,
            "passedRuns": passed_runs,
            "failedRuns": failed_runs,
            "inProgress": in_progress,
            "passRate": passed_runs / completed_runs if completed_runs > 0 else 0
        }

    def get_recent_runs(self, limit: int = 10) -> List[dict]:
        """Get recent test runs for activity feed (only from active protocols)"""
        runs = self.db.query(TestRun).join(TestProtocol).filter(
            TestProtocol.is_active == True
        ).order_by(
            TestRun.created_at.desc()
        ).limit(limit).all()

        return [
            {
                "id": r.id,
                "protocol_id": r.protocol_id,
                "protocol_name": r.protocol.name if r.protocol else None,
                "status": r.status.value,
                "result": r.result.value if r.result else None,
                "operator": r.operator,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in runs
        ]

    def get_protocol_stats(self, protocol_id: int) -> dict:
        """Get statistics for a specific protocol"""
        runs = self.db.query(TestRun).filter(
            TestRun.protocol_id == protocol_id
        ).all()

        if not runs:
            return {
                "total_runs": 0,
                "completed": 0,
                "passed": 0,
                "failed": 0,
                "partial": 0,
                "pass_rate": 0
            }

        completed = [r for r in runs if r.status == TestRunStatus.COMPLETED]
        passed = sum(1 for r in completed if r.result == TestResultStatus.PASS)
        failed = sum(1 for r in completed if r.result == TestResultStatus.FAIL)
        partial = sum(1 for r in completed if r.result == TestResultStatus.PARTIAL)

        return {
            "total_runs": len(runs),
            "completed": len(completed),
            "passed": passed,
            "failed": failed,
            "partial": partial,
            "pass_rate": passed / len(completed) if completed else 0
        }