from fastapi import APIRouter, Depends, Query, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.test import Test, TestResult, TestStatus, TestResultStatus
from app.models.component import Component
from app.models.audit import AuditLog
from app.schemas.test import TestCreate, TestUpdate, TestResponse, TestResultCreate, TestResultResponse
from app.services.physics import DRIPValidation

router = APIRouter(prefix="/api/v1/tests")

@router.get("/", response_model=List[TestResponse])
async def get_tests(
    category: Optional[str] = Query(None),
    status: Optional[TestStatus] = Query(None),
    search: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get filtered list of tests"""
    query = db.query(Test)
    
    if category:
        query = query.filter(Test.category == category)
    if status:
        query = query.filter(Test.status == status)
    if search:
        query = query.filter(
            Test.name.ilike(f"%{search}%") | 
            Test.test_id.ilike(f"%{search}%")
        )
    
    tests = query.offset(skip).limit(limit).all()
    return tests

@router.get("/critical-path")
async def get_critical_path(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get tests on critical path (blocking other tests)"""
    try:
        print(f"🔧 Critical path requested by user: {current_user}")
        print(f"🔧 DEV_MODE environment: {os.getenv('DEV_MODE')}")
        
        # Test database connection first
        try:
            db_test = db.execute("SELECT 1").fetchone()
            print(f"🔧 Database connection successful: {db_test}")
        except Exception as db_error:
            print(f"❌ Database connection failed: {db_error}")
            raise db_error
        
        # Get all tests with their prerequisites
        tests = db.query(Test).filter(Test.status != TestStatus.COMPLETED).all()
        print(f"🔧 Found {len(tests)} incomplete tests")
        
        critical_tests = []
        for test in tests:
            if test.prerequisites:
                # Check if this test is blocking others
                blocked_tests = []
                for other_test in tests:
                    if other_test.prerequisites and test.test_id in other_test.prerequisites:
                        blocked_tests.append(other_test.test_id)
                
                if blocked_tests:
                    critical_tests.append({
                        "id": test.id,
                        "test_id": test.test_id,
                        "name": test.name,
                        "status": test.status,
                        "blocking": blocked_tests,
                        "blocked": test.status != TestStatus.NOT_STARTED
                    })
        
        # Sort by number of blocked tests
        critical_tests.sort(key=lambda x: len(x["blocking"]), reverse=True)
        print(f"🔧 Returning {len(critical_tests)} critical tests")
        
        return critical_tests[:10]  # Top 10 critical path items
        
    except Exception as e:
        print(f"❌ Error in critical_path: {str(e)}")
        print(f"❌ Error type: {type(e)}")
        import traceback
        print(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/{test_id}", response_model=TestResponse)
async def get_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get specific test by ID"""
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    return test

@router.post("/", response_model=TestResponse)
async def create_test(
    test: TestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create new test"""
    existing = db.query(Test).filter(Test.test_id == test.test_id).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Test {test.test_id} already exists"
        )
    
    db_test = Test(**test.dict())
    db.add(db_test)
    
    audit = AuditLog(
        entity_type="test",
        entity_id=test.test_id,
        action="created",
        user=current_user["email"],
        details=test.dict()
    )
    db.add(audit)
    
    db.commit()
    db.refresh(db_test)
    
    return db_test

@router.post("/{test_id}/results", response_model=TestResultResponse)
async def create_test_result(
    test_id: str,
    result: TestResultCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Submit test result"""
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Get component if specified
    component = None
    if result.component_id:
        component = db.query(Component).filter(Component.component_id == result.component_id).first()
        if not component:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Component {result.component_id} not found"
            )
    
    # Create test result
    db_result = TestResult(
        test_id=test.id,
        component_id=component.id if component else None,
        result=result.result,
        steering_force=result.steering_force,
        bonding_strength=result.bonding_strength,
        temperature_max=result.temperature_max,
        drip_number=result.drip_number,
        executed_by=current_user["email"],
        notes=result.notes
    )
    
    # Validate physics if DRIP number provided
    if result.drip_number and result.drip_validation_params:
        validation = DRIPValidation(**result.drip_validation_params)
        calculated_drip = validation.calculate_drip_number()
        db_result.physics_validated = validation.validate_scaling(result.drip_number)
    
    db.add(db_result)
    
    # Update test status
    test.status = TestStatus.COMPLETED
    test.executed_date = datetime.utcnow()
    test.engineer = current_user["email"]
    
    # Update component status if applicable
    if component and result.result == TestResultStatus.PASS:
        component.status = ComponentStatus.VERIFIED
        component.updated_by = current_user["email"]
    
    # Audit log
    audit = AuditLog(
        entity_type="test_result",
        entity_id=f"{test_id}_result_{datetime.utcnow().isoformat()}",
        action="Test result submitted",
        user=current_user["email"],
        details={
            "test_id": test_id,
            "result": result.result,
            "component_id": result.component_id
        }
    )
    db.add(audit)
    
    db.commit()
    db.refresh(db_result)
    
    return db_result

@router.get("/{test_id}/results", response_model=List[TestResultResponse])
async def get_test_results(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all results for a test"""
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    return test.test_results

@router.post("/physics/drip-validation")
async def validate_drip_number(
    validation_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate and validate DRIP number"""
    try:
        validator = DRIPValidation(**validation_data)
        drip_number = validator.calculate_drip_number()
        
        result = {
            "drip_number": drip_number,
            "parameters": validation_data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if "target_drip" in validation_data:
            passed = validator.validate_scaling(validation_data["target_drip"])
            result["passed"] = passed
            result["deviation"] = abs(drip_number - validation_data["target_drip"])
        
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error calculating DRIP number: {str(e)}"
        )


@router.patch("/{test_id}", response_model=TestResponse)
async def update_test(
    test_id: str,
    test_update: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update test details"""
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Update fields
    for key, value in test_update.items():
        if hasattr(test, key) and key not in ["id", "test_id", "created_at"]:
            setattr(test, key, value)
    
    # Create audit log
    audit = AuditLog(
        entity_type="test",
        entity_id=test_id,
        action="updated",
        user=current_user["email"],
        details=test_update
    )
    db.add(audit)
    
    db.commit()
    db.refresh(test)
    
    return test

@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete test"""
    # In dev mode, allow deletion
    if os.getenv("DEV_MODE") != "true":
        user = db.query(User).filter(User.email == current_user["email"]).first()
        if not user or not user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete tests"
            )
    
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )
    
    # Create audit log before deletion
    audit = AuditLog(
        entity_type="test",
        entity_id=test_id,
        action="deleted",
        user=current_user["email"],
        details={"test_name": test.name}
    )
    db.add(audit)
    
    # Delete related test results first
    db.query(TestResult).filter(TestResult.test_id == test.id).delete()
    
    db.delete(test)
    db.commit()
    
    return {"status": "success", "message": f"Test {test_id} deleted"}