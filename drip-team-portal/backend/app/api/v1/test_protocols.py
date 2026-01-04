"""
Test Protocols API - CRUD endpoints for the new testing system.

Provides:
- Protocol CRUD (reusable test templates)
- Test Run lifecycle management (create, start, complete, abort)
- Measurements recording (single and bulk)
- Validation triggers and results
- Protocol statistics
"""

from fastapi import APIRouter, Depends, Query, HTTPException, status, Body
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, timezone
import os

from app.db.database import get_db
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

from app.models.test_protocol import (
    TestProtocol, TestRun, TestMeasurement, TestValidation,
    TestRunStatus, TestResultStatus, ValidationStatus
)
from app.models.component import Component
from app.models.physics_model import ModelInstance
from app.models.audit import AuditLog
from app.schemas.test_protocol import (
    TestProtocolCreate, TestProtocolUpdate, TestProtocolResponse, TestProtocolDetail,
    TestRunCreate, TestRunUpdate, TestRunStart, TestRunComplete,
    TestRunResponse, TestRunDetail, TestRunSummary,
    TestMeasurementCreate, TestMeasurementBulkCreate, TestMeasurementResponse,
    TestValidationResponse,
    ProtocolStats
)

router = APIRouter(prefix="/api/v1/test-protocols", tags=["Test Protocols"])


# ============== PROTOCOL CRUD ==============

@router.get("/", response_model=List[TestProtocolResponse])
async def list_protocols(
    category: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all test protocols with optional filters"""
    query = db.query(TestProtocol)

    if category:
        query = query.filter(TestProtocol.category == category)
    if is_active is not None:
        query = query.filter(TestProtocol.is_active == is_active)
    if search:
        query = query.filter(
            TestProtocol.name.ilike(f"%{search}%") |
            TestProtocol.description.ilike(f"%{search}%")
        )

    protocols = query.order_by(TestProtocol.name).offset(skip).limit(limit).all()

    # Add run counts
    result = []
    for p in protocols:
        resp = TestProtocolResponse.model_validate(p)
        resp.run_count = db.query(TestRun).filter(TestRun.protocol_id == p.id).count()
        result.append(resp)

    return result


@router.get("/categories")
async def list_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get list of all protocol categories"""
    categories = db.query(TestProtocol.category).distinct().filter(
        TestProtocol.category.isnot(None)
    ).all()
    return [c[0] for c in categories]


@router.get("/{protocol_id}", response_model=TestProtocolDetail)
async def get_protocol(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get protocol details with recent runs"""
    protocol = db.query(TestProtocol).filter(TestProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    # Get recent runs
    recent_runs = db.query(TestRun).filter(
        TestRun.protocol_id == protocol_id
    ).order_by(TestRun.created_at.desc()).limit(10).all()

    resp = TestProtocolDetail.model_validate(protocol)
    resp.run_count = db.query(TestRun).filter(TestRun.protocol_id == protocol_id).count()
    resp.recent_runs = [TestRunSummary.model_validate(r) for r in recent_runs]

    if protocol.model:
        resp.model_name = protocol.model.name

    return resp


@router.post("/", response_model=TestProtocolResponse, status_code=status.HTTP_201_CREATED)
async def create_protocol(
    protocol: TestProtocolCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new test protocol"""
    # Convert Pydantic schemas to dicts for JSON columns
    protocol_data = protocol.model_dump()
    if protocol_data.get("input_schema"):
        protocol_data["input_schema"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in protocol_data["input_schema"]]
    if protocol_data.get("output_schema"):
        protocol_data["output_schema"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in protocol_data["output_schema"]]

    db_protocol = TestProtocol(
        **protocol_data,
        created_by=current_user["email"]
    )
    db.add(db_protocol)
    db.flush()  # Get the ID before committing

    # Audit log
    audit = AuditLog(
        entity_type="test_protocol",
        entity_id=str(db_protocol.id),
        action="created",
        user=current_user["email"],
        details=protocol_data
    )
    db.add(audit)

    db.commit()
    db.refresh(db_protocol)
    return db_protocol


@router.patch("/{protocol_id}", response_model=TestProtocolResponse)
async def update_protocol(
    protocol_id: int,
    updates: TestProtocolUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a test protocol"""
    protocol = db.query(TestProtocol).filter(TestProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    update_data = updates.model_dump(exclude_unset=True)

    # Convert nested Pydantic models to dicts
    if "input_schema" in update_data and update_data["input_schema"]:
        update_data["input_schema"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["input_schema"]]
    if "output_schema" in update_data and update_data["output_schema"]:
        update_data["output_schema"] = [item.model_dump() if hasattr(item, 'model_dump') else item for item in update_data["output_schema"]]

    for key, value in update_data.items():
        setattr(protocol, key, value)

    # Audit log
    audit = AuditLog(
        entity_type="test_protocol",
        entity_id=str(protocol_id),
        action="updated",
        user=current_user["email"],
        details=update_data
    )
    db.add(audit)

    db.commit()
    db.refresh(protocol)
    return protocol


@router.delete("/{protocol_id}")
async def delete_protocol(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a test protocol (soft delete by setting is_active=False)"""
    protocol = db.query(TestProtocol).filter(TestProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    # Soft delete
    protocol.is_active = False

    audit = AuditLog(
        entity_type="test_protocol",
        entity_id=str(protocol_id),
        action="deactivated",
        user=current_user["email"],
        details={"protocol_name": protocol.name}
    )
    db.add(audit)

    db.commit()
    return {"status": "success", "message": f"Protocol {protocol_id} deactivated"}


# ============== TEST RUN CRUD ==============

@router.post("/{protocol_id}/runs", response_model=TestRunResponse, status_code=status.HTTP_201_CREATED)
async def create_run(
    protocol_id: int,
    run: TestRunCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new test run for a protocol"""
    protocol = db.query(TestProtocol).filter(TestProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    # Calculate run number
    max_run = db.query(func.max(TestRun.run_number)).filter(
        TestRun.protocol_id == protocol_id
    ).scalar() or 0

    db_run = TestRun(
        protocol_id=protocol_id,
        component_id=run.component_id,
        analysis_id=run.analysis_id,
        run_number=max_run + 1,
        operator=run.operator or current_user["email"],
        configuration=run.configuration,
        notes=run.notes,
        status=TestRunStatus.SETUP
    )
    db.add(db_run)
    db.flush()

    audit = AuditLog(
        entity_type="test_run",
        entity_id=str(db_run.id),
        action="created",
        user=current_user["email"],
        details={"protocol_id": protocol_id, "run_number": max_run + 1}
    )
    db.add(audit)

    db.commit()
    db.refresh(db_run)
    return db_run


@router.get("/{protocol_id}/runs", response_model=List[TestRunSummary])
async def list_runs(
    protocol_id: int,
    status: Optional[TestRunStatus] = Query(None),
    result: Optional[TestResultStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all runs for a protocol"""
    query = db.query(TestRun).filter(TestRun.protocol_id == protocol_id)

    if status:
        query = query.filter(TestRun.status == status)
    if result:
        query = query.filter(TestRun.result == result)

    runs = query.order_by(TestRun.created_at.desc()).offset(skip).limit(limit).all()
    return runs


@router.get("/runs/{run_id}", response_model=TestRunDetail)
async def get_run(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed run info including measurements and validations"""
    run = db.query(TestRun).options(
        selectinload(TestRun.measurements),
        selectinload(TestRun.validations),
        selectinload(TestRun.protocol),
        selectinload(TestRun.component)
    ).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    resp = TestRunDetail.model_validate(run)
    resp.protocol_name = run.protocol.name if run.protocol else None
    resp.component_name = run.component.name if run.component else None
    resp.measurements = [TestMeasurementResponse.model_validate(m) for m in run.measurements]
    resp.validations = [TestValidationResponse.model_validate(v) for v in run.validations]

    return resp


@router.post("/runs/{run_id}/start", response_model=TestRunResponse)
async def start_run(
    run_id: int,
    start_data: TestRunStart = Body(default=None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Start a test run (transition from SETUP to IN_PROGRESS)"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status != TestRunStatus.SETUP:
        raise HTTPException(status_code=400, detail=f"Cannot start run in {run.status} status")

    run.status = TestRunStatus.IN_PROGRESS
    run.started_at = datetime.now(timezone.utc)
    if start_data:
        if start_data.configuration:
            run.configuration = start_data.configuration
        if start_data.operator:
            run.operator = start_data.operator

    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/complete", response_model=TestRunResponse)
async def complete_run(
    run_id: int,
    complete_data: TestRunComplete,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Complete a test run and trigger validation"""
    run = db.query(TestRun).options(
        selectinload(TestRun.measurements),
        selectinload(TestRun.protocol)
    ).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status not in [TestRunStatus.IN_PROGRESS, TestRunStatus.SETUP]:
        raise HTTPException(status_code=400, detail=f"Cannot complete run in {run.status} status")

    run.status = TestRunStatus.COMPLETED
    run.completed_at = datetime.now(timezone.utc)
    run.result = complete_data.result
    if complete_data.notes:
        run.notes = complete_data.notes

    # Trigger validation if we have measurements and protocol has output schema
    if run.measurements and run.protocol.output_schema:
        await _create_validations(db, run)

    audit = AuditLog(
        entity_type="test_run",
        entity_id=str(run_id),
        action="completed",
        user=current_user["email"],
        details={"result": complete_data.result.value}
    )
    db.add(audit)

    db.commit()
    db.refresh(run)
    return run


@router.post("/runs/{run_id}/abort", response_model=TestRunResponse)
async def abort_run(
    run_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Abort a test run"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    run.status = TestRunStatus.ABORTED
    run.completed_at = datetime.now(timezone.utc)
    if notes:
        run.notes = notes

    db.commit()
    db.refresh(run)
    return run


# ============== MEASUREMENTS ==============

@router.post("/runs/{run_id}/measurements", response_model=TestMeasurementResponse)
async def add_measurement(
    run_id: int,
    measurement: TestMeasurementCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add a single measurement to a run"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status == TestRunStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot add measurements to completed run")

    db_measurement = TestMeasurement(
        run_id=run_id,
        **measurement.model_dump()
    )
    db.add(db_measurement)
    db.commit()
    db.refresh(db_measurement)
    return db_measurement


@router.post("/runs/{run_id}/measurements/bulk", response_model=List[TestMeasurementResponse])
async def add_measurements_bulk(
    run_id: int,
    bulk: TestMeasurementBulkCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Add multiple measurements at once"""
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    if run.status == TestRunStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot add measurements to completed run")

    db_measurements = []
    for m in bulk.measurements:
        db_m = TestMeasurement(run_id=run_id, **m.model_dump())
        db.add(db_m)
        db_measurements.append(db_m)

    db.commit()
    for m in db_measurements:
        db.refresh(m)

    return db_measurements


@router.get("/runs/{run_id}/measurements", response_model=List[TestMeasurementResponse])
async def get_measurements(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all measurements for a run"""
    measurements = db.query(TestMeasurement).filter(
        TestMeasurement.run_id == run_id
    ).order_by(TestMeasurement.timestamp).all()
    return measurements


# ============== VALIDATIONS ==============

@router.get("/runs/{run_id}/validations", response_model=List[TestValidationResponse])
async def get_validations(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all validations for a run"""
    validations = db.query(TestValidation).filter(
        TestValidation.run_id == run_id
    ).all()
    return validations


@router.post("/runs/{run_id}/validate")
async def trigger_validation(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually trigger validation for a run"""
    run = db.query(TestRun).options(
        selectinload(TestRun.measurements),
        selectinload(TestRun.protocol)
    ).filter(TestRun.id == run_id).first()

    if not run:
        raise HTTPException(status_code=404, detail="Run not found")

    # Clear existing validations
    db.query(TestValidation).filter(TestValidation.run_id == run_id).delete()

    # Create new validations
    validations = await _create_validations(db, run)

    db.commit()
    return {"status": "success", "validations_created": len(validations)}


# ============== STATS ==============

@router.get("/{protocol_id}/stats", response_model=ProtocolStats)
async def get_protocol_stats(
    protocol_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for a protocol"""
    protocol = db.query(TestProtocol).filter(TestProtocol.id == protocol_id).first()
    if not protocol:
        raise HTTPException(status_code=404, detail="Protocol not found")

    runs = db.query(TestRun).filter(TestRun.protocol_id == protocol_id).all()

    completed_runs = [r for r in runs if r.status == TestRunStatus.COMPLETED]
    passed = sum(1 for r in completed_runs if r.result == TestResultStatus.PASS)
    failed = sum(1 for r in completed_runs if r.result == TestResultStatus.FAIL)
    partial = sum(1 for r in completed_runs if r.result == TestResultStatus.PARTIAL)

    # Calculate average duration
    durations = []
    for r in completed_runs:
        if r.started_at and r.completed_at:
            duration = (r.completed_at - r.started_at).total_seconds() / 60
            durations.append(duration)

    return ProtocolStats(
        protocol_id=protocol_id,
        protocol_name=protocol.name,
        total_runs=len(runs),
        passed=passed,
        failed=failed,
        partial=partial,
        pass_rate=passed / len(completed_runs) if completed_runs else 0,
        avg_duration_minutes=sum(durations) / len(durations) if durations else None
    )


# ============== HELPER FUNCTIONS ==============

async def _create_validations(db: Session, run: TestRun) -> List[TestValidation]:
    """Create validation records comparing measurements to targets/predictions"""
    validations = []

    if not run.protocol.output_schema:
        return validations

    # Build measurement lookup
    measurements = {m.parameter_name: m for m in run.measurements}

    # TODO: Get predictions from analysis if linked
    predictions = {}
    if run.analysis_id:
        # Instance D will implement model evaluation
        # For now, use target values from output_schema
        pass

    for output in run.protocol.output_schema:
        param_name = output.get("name")
        if not param_name or param_name not in measurements:
            continue

        measurement = measurements[param_name]
        target = output.get("target")
        tolerance_pct = output.get("tolerance_pct", 10.0)

        # Get predicted value (from analysis or target)
        predicted = predictions.get(param_name, target)

        if predicted is None:
            continue

        # Calculate error
        error_abs = measurement.measured_value - predicted
        error_pct = (error_abs / predicted * 100) if predicted != 0 else 0

        # Determine status
        if abs(error_pct) <= tolerance_pct:
            val_status = ValidationStatus.PASS
        elif abs(error_pct) <= tolerance_pct * 1.5:
            val_status = ValidationStatus.WARNING
        else:
            val_status = ValidationStatus.FAIL

        validation = TestValidation(
            run_id=run.id,
            parameter_name=param_name,
            predicted_value=predicted,
            measured_value=measurement.measured_value,
            unit_id=measurement.unit_id,
            error_absolute=error_abs,
            error_pct=error_pct,
            tolerance_pct=tolerance_pct,
            status=val_status
        )
        db.add(validation)
        validations.append(validation)

    return validations
