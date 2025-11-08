from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import hmac
import hashlib
import json
from datetime import datetime

from app.db.database import get_db
from app.models.test import Test, TestStatus
from app.core.config import settings

router = APIRouter(prefix="/api/v1/webhooks")

def verify_linear_signature(payload: bytes, signature: str) -> bool:
    """Verify Linear webhook signature"""
    expected_signature = hmac.new(
        settings.LINEAR_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

@router.post("/linear")
async def handle_linear_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Handle Linear webhook events"""
    # Get signature from headers
    signature = request.headers.get("Linear-Signature", "")
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    # Get raw body
    body = await request.body()
    
    # Verify signature
    if not verify_linear_signature(body, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Parse JSON
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    
    # Handle different event types
    event_type = data.get("type")
    action = data.get("action")
    
    if event_type == "Issue":
        if action in ["create", "update"]:
            issue_data = data.get("data", {})
            
            # Check if this is a test-related issue
            if has_test_labels(issue_data):
                background_tasks.add_task(
                    process_linear_test_update,
                    issue_data,
                    db
                )
        elif action == "remove":
            # Handle issue deletion if needed
            pass
    
    elif event_type == "Comment":
        if action == "create":
            comment_data = data.get("data", {})
            background_tasks.add_task(
                process_linear_comment,
                comment_data,
                db
            )
    
    return {"status": "ok", "received": event_type}

def has_test_labels(issue: dict) -> bool:
    """Check if Linear issue has test-related labels"""
    test_labels = {"DRIP-TEST", "STEERING-RESULTS", "BONDING-RESULTS", "THERMAL-TEST"}
    
    labels = issue.get("labels", {}).get("nodes", [])
    issue_labels = {label.get("name", "") for label in labels}
    
    return bool(issue_labels.intersection(test_labels))

async def process_linear_test_update(issue: dict, db: Session):
    """Process Linear issue update for test results"""
    # Extract test ID from issue
    test_id = extract_test_id(issue)
    if not test_id:
        return
    
    # Find test in database
    test = db.query(Test).filter(Test.test_id == test_id).first()
    if not test:
        # Could create a new test here if desired
        return
    
    # Update test with Linear data
    test.linear_issue_id = issue.get("id")
    test.linear_sync_status = "synced"
    
    # Map Linear state to test status
    state_name = issue.get("state", {}).get("name", "")
    status_map = {
        "Todo": TestStatus.NOT_STARTED,
        "In Progress": TestStatus.IN_PROGRESS,
        "Done": TestStatus.COMPLETED,
        "Canceled": TestStatus.BLOCKED
    }
    
    if state_name in status_map:
        test.status = status_map[state_name]
    
    # Extract custom fields if available
    custom_fields = issue.get("customFieldValues", [])
    for field in custom_fields:
        field_name = field.get("customField", {}).get("name", "")
        field_value = field.get("value")
        
        if field_name == "DRIP Number" and field_value:
            # Store in test results or test metadata
            pass
        elif field_name == "Test Result" and field_value:
            # Update test result
            pass
    
    db.commit()

async def process_linear_comment(comment: dict, db: Session):
    """Process Linear comment for test updates"""
    # Extract issue ID from comment
    issue_id = comment.get("issue", {}).get("id")
    if not issue_id:
        return
    
    # Find test with this Linear issue ID
    test = db.query(Test).filter(Test.linear_issue_id == issue_id).first()
    if not test:
        return
    
    # Could parse comment for specific commands or updates
    comment_body = comment.get("body", "")
    
    # Example: Look for test result updates in comments
    if "RESULT:" in comment_body:
        # Parse and update test result
        pass
    
    # Store comment in audit log or test notes
    if test.notes:
        test.notes += f"\n\n[Linear Comment {datetime.utcnow().isoformat()}]: {comment_body}"
    else:
        test.notes = f"[Linear Comment {datetime.utcnow().isoformat()}]: {comment_body}"
    
    db.commit()

def extract_test_id(issue: dict) -> str:
    """Extract test ID from Linear issue"""
    import re
    
    # Try title first
    title = issue.get("title", "")
    match = re.search(r'Test\s+([A-Z]{2}-\d{3})', title)
    if match:
        return match.group(1)
    
    # Try description
    description = issue.get("description", "")
    match = re.search(r'\*\*Test ID\*\*:\s*([A-Z]{2}-\d{3})', description)
    if match:
        return match.group(1)
    
    return ""

def map_linear_state_to_status(state_name: str) -> str:
    """Map Linear issue state to test status"""
    mapping = {
        "Todo": "NOT_STARTED",
        "In Progress": "IN_PROGRESS",
        "In Review": "IN_PROGRESS",
        "Done": "COMPLETED",
        "Canceled": "BLOCKED",
        "Duplicate": "BLOCKED",
        "Backlog": "NOT_STARTED"
    }
    
    return mapping.get(state_name, "NOT_STARTED")