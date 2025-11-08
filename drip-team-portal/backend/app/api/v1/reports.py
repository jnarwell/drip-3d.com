from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import io

from app.db.database import get_db
import os as os_module
if os_module.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.services.reports import ReportGenerator
from app.models.component import Component, ComponentStatus
from app.models.test import Test, TestResult, TestStatus
from app.models.user import User

router = APIRouter(prefix="/api/v1/reports")

@router.get("/validation-report")
async def generate_validation_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    format: str = Query("pdf", regex="^(pdf|excel)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Generate validation report in PDF or Excel format"""
    # Default date range if not provided
    if not end_date:
        end_date = datetime.utcnow()
    if not start_date:
        start_date = end_date - timedelta(days=30)
    
    report_gen = ReportGenerator(db)
    
    if format == "pdf":
        buffer = report_gen.generate_validation_report(start_date, end_date)
        filename = f"drip_validation_report_{start_date.date()}_{end_date.date()}.pdf"
        media_type = "application/pdf"
    else:
        buffer = report_gen.generate_test_campaign_excel()
        filename = f"drip_test_campaign_{datetime.utcnow().date()}.xlsx"
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    
    return StreamingResponse(
        io.BytesIO(buffer.getvalue()),
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename={filename}"
        }
    )

@router.get("/dashboard-stats")
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get statistics for dashboard display"""
    # Component statistics
    total_components = db.query(Component).count()
    components_verified = db.query(Component).filter(
        Component.status == ComponentStatus.VERIFIED
    ).count()
    components_failed = db.query(Component).filter(
        Component.status == ComponentStatus.FAILED
    ).count()
    
    # Test statistics
    total_tests = db.query(Test).count()
    tests_complete = db.query(Test).filter(
        Test.status == TestStatus.COMPLETED
    ).count()
    tests_in_progress = db.query(Test).filter(
        Test.status == TestStatus.IN_PROGRESS
    ).count()
    
    # Physics validation
    physics_validated = db.query(TestResult).filter(
        TestResult.physics_validated == True
    ).count()
    
    # Component breakdown by category
    components_by_category = db.query(
        Component.category,
        func.count(Component.id).label('count')
    ).group_by(Component.category).all()
    
    # Component breakdown by status
    components_by_status = db.query(
        Component.status,
        func.count(Component.id).label('count')
    ).group_by(Component.status).all()
    
    # Test campaign progress (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    campaign_progress = []
    
    for i in range(30):
        date = thirty_days_ago + timedelta(days=i)
        completed = db.query(Test).filter(
            Test.executed_date <= date,
            Test.status == TestStatus.COMPLETED
        ).count()
        
        campaign_progress.append({
            "date": date.date().isoformat(),
            "completed": completed,
            "planned": total_tests  # Could be more sophisticated
        })
    
    # Critical path items
    critical_path = get_critical_path_items(db)
    
    # Risk assessment
    risks = assess_risks(db)
    
    return {
        "totalComponents": total_components,
        "componentsVerified": components_verified,
        "componentsFailed": components_failed,
        "totalTests": total_tests,
        "testsComplete": tests_complete,
        "testsInProgress": tests_in_progress,
        "physicsValidated": physics_validated > 0,
        "componentsByCategory": [
            {"category": cat, "count": count}
            for cat, count in components_by_category
        ],
        "componentsByStatus": [
            {"status": status, "count": count}
            for status, count in components_by_status
        ],
        "campaignProgress": campaign_progress,
        "criticalPath": critical_path,
        "risks": risks
    }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get recent system activity"""
    from app.models.audit import AuditLog
    
    activities = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    
    return [
        {
            "id": activity.id,
            "type": activity.entity_type,
            "action": activity.action,
            "user": activity.user,
            "timestamp": activity.timestamp,
            "details": activity.details
        }
        for activity in activities
    ]

def get_critical_path_items(db: Session):
    """Identify tests on the critical path"""
    # Get incomplete tests
    incomplete_tests = db.query(Test).filter(
        Test.status != TestStatus.COMPLETED
    ).all()
    
    critical_items = []
    
    for test in incomplete_tests:
        if not test.prerequisites:
            continue
        
        # Check if this test is blocking others
        blocked_count = 0
        for other_test in incomplete_tests:
            if other_test.prerequisites and test.test_id in other_test.prerequisites:
                blocked_count += 1
        
        if blocked_count > 0:
            # Check if prerequisites are met
            prereqs_met = True
            for prereq_id in test.prerequisites:
                prereq = db.query(Test).filter(Test.test_id == prereq_id).first()
                if prereq and prereq.status != TestStatus.COMPLETED:
                    prereqs_met = False
                    break
            
            critical_items.append({
                "id": test.id,
                "test_id": test.test_id,
                "name": test.name,
                "blocked_count": blocked_count,
                "blocked": not prereqs_met,
                "status": test.status
            })
    
    # Sort by number of blocked tests
    critical_items.sort(key=lambda x: x["blocked_count"], reverse=True)
    
    return critical_items[:10]

def assess_risks(db: Session):
    """Assess project risks based on current status"""
    risks = []
    
    # Risk 1: Low component verification rate
    total_components = db.query(Component).count()
    verified_components = db.query(Component).filter(
        Component.status == ComponentStatus.VERIFIED
    ).count()
    
    if total_components > 0:
        verification_rate = verified_components / total_components
        if verification_rate < 0.5:
            risks.append({
                "category": "Component Verification",
                "severity": "high" if verification_rate < 0.3 else "medium",
                "description": f"Only {verification_rate*100:.0f}% of components verified",
                "mitigation": "Prioritize testing of critical components"
            })
    
    # Risk 2: Failed components
    failed_components = db.query(Component).filter(
        Component.status == ComponentStatus.FAILED
    ).count()
    
    if failed_components > 0:
        risks.append({
            "category": "Component Failures",
            "severity": "high",
            "description": f"{failed_components} components have failed verification",
            "mitigation": "Review failed components and identify replacements"
        })
    
    # Risk 3: Test bottlenecks
    blocked_tests = db.query(Test).filter(
        Test.status == TestStatus.BLOCKED
    ).count()
    
    if blocked_tests > 0:
        risks.append({
            "category": "Test Progress",
            "severity": "medium",
            "description": f"{blocked_tests} tests are blocked",
            "mitigation": "Resolve blocking issues to enable test progression"
        })
    
    # Risk 4: Physics validation
    total_results = db.query(TestResult).count()
    physics_validated = db.query(TestResult).filter(
        TestResult.physics_validated == True
    ).count()
    
    if total_results > 0 and physics_validated / total_results < 0.8:
        risks.append({
            "category": "Physics Validation",
            "severity": "medium",
            "description": "Low physics validation rate for test results",
            "mitigation": "Ensure DRIP numbers are calculated for all tests"
        })
    
    return risks