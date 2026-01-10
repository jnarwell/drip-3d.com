"""
Feedback API - CRUD endpoints for user feedback submissions.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timezone
import os
import io
import csv

from app.db.database import get_db
from app.models.feedback import FeedbackSubmission, FeedbackType, FeedbackUrgency, FeedbackStatus
from app.schemas.feedback import FeedbackCreate, FeedbackUpdate

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/feedback", tags=["feedback"])


# =============================================================================
# CRUD ENDPOINTS
# =============================================================================

@router.post("")
async def create_feedback(
    data: FeedbackCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new feedback submission.

    Captures user feedback with browser context and auto-sets the submitter.
    """
    user_email = current_user["email"]

    # Validate type and urgency
    try:
        feedback_type = FeedbackType(data.type)
        feedback_urgency = FeedbackUrgency(data.urgency)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid type or urgency value: {str(e)}"
        )

    # Create feedback submission
    feedback = FeedbackSubmission(
        user_id=user_email,
        type=feedback_type,
        urgency=feedback_urgency,
        description=data.description,
        page_url=data.page_url,
        browser_info=data.browser_info,
        status=FeedbackStatus.NEW
    )

    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    return feedback.to_dict()


@router.get("")
async def list_feedback(
    status: Optional[str] = Query(None, description="Filter by status (new, reviewed, in_progress, resolved, wont_fix)"),
    type: Optional[str] = Query(None, description="Filter by type (bug, feature, question)"),
    urgency: Optional[str] = Query(None, description="Filter by urgency (need_now, nice_to_have)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List feedback submissions with optional filters and pagination.

    Returns submissions sorted by creation date (newest first).
    """
    query = db.query(FeedbackSubmission)

    # Apply filters
    if status:
        try:
            status_enum = FeedbackStatus(status)
            query = query.filter(FeedbackSubmission.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")

    if type:
        try:
            type_enum = FeedbackType(type)
            query = query.filter(FeedbackSubmission.type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type value: {type}")

    if urgency:
        try:
            urgency_enum = FeedbackUrgency(urgency)
            query = query.filter(FeedbackSubmission.urgency == urgency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid urgency value: {urgency}")

    # Get total count
    total = query.count()

    # Get paginated results (newest first)
    submissions = query.order_by(FeedbackSubmission.created_at.desc()).offset(offset).limit(limit).all()

    return {
        "feedback": [s.to_dict() for s in submissions],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/export")
async def export_feedback(
    status: Optional[str] = Query(None, description="Filter by status"),
    type: Optional[str] = Query(None, description="Filter by type"),
    urgency: Optional[str] = Query(None, description="Filter by urgency"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Export filtered feedback submissions as CSV.

    Applies the same filters as the list endpoint.
    """
    query = db.query(FeedbackSubmission)

    # Apply same filters as list endpoint
    if status:
        try:
            status_enum = FeedbackStatus(status)
            query = query.filter(FeedbackSubmission.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {status}")

    if type:
        try:
            type_enum = FeedbackType(type)
            query = query.filter(FeedbackSubmission.type == type_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid type value: {type}")

    if urgency:
        try:
            urgency_enum = FeedbackUrgency(urgency)
            query = query.filter(FeedbackSubmission.urgency == urgency_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid urgency value: {urgency}")

    # Get all matching submissions
    submissions = query.order_by(FeedbackSubmission.created_at.desc()).all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        "ID",
        "User ID",
        "Type",
        "Urgency",
        "Description",
        "Page URL",
        "Browser Agent",
        "Viewport Width",
        "Viewport Height",
        "Status",
        "Resolution Notes",
        "Resolved By",
        "Resolved At",
        "Created At",
        "Updated At"
    ])

    # Write data rows
    for submission in submissions:
        browser_info = submission.browser_info or {}
        writer.writerow([
            submission.id,
            submission.user_id,
            submission.type.value if submission.type else "",
            submission.urgency.value if submission.urgency else "",
            submission.description,
            submission.page_url or "",
            browser_info.get("userAgent", ""),
            browser_info.get("viewportWidth", ""),
            browser_info.get("viewportHeight", ""),
            submission.status.value if submission.status else "",
            submission.resolution_notes or "",
            submission.resolved_by or "",
            submission.resolved_at.isoformat() if submission.resolved_at else "",
            submission.created_at.isoformat() if submission.created_at else "",
            submission.updated_at.isoformat() if submission.updated_at else "",
        ])

    # Prepare response
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=feedback_export_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )


@router.get("/{feedback_id}")
async def get_feedback(
    feedback_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single feedback submission by ID."""
    feedback = db.query(FeedbackSubmission).filter(FeedbackSubmission.id == feedback_id).first()

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback submission not found")

    return feedback.to_dict()


@router.patch("/{feedback_id}")
async def update_feedback(
    feedback_id: int,
    data: FeedbackUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update feedback submission status and resolution.

    When marking as resolved or wont_fix, resolution_notes is required.
    Automatically sets resolved_by and resolved_at when transitioning to resolved/wont_fix.
    """
    feedback = db.query(FeedbackSubmission).filter(FeedbackSubmission.id == feedback_id).first()

    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback submission not found")

    user_email = current_user["email"]

    # Update status if provided
    if data.status is not None:
        try:
            new_status = FeedbackStatus(data.status)

            # Require resolution_notes for resolved/wont_fix
            if new_status in [FeedbackStatus.RESOLVED, FeedbackStatus.WONT_FIX]:
                if not data.resolution_notes and not feedback.resolution_notes:
                    raise HTTPException(
                        status_code=400,
                        detail=f"resolution_notes is required when status is '{new_status.value}'"
                    )

                # Set resolution metadata
                feedback.resolved_by = user_email
                feedback.resolved_at = datetime.now(timezone.utc)

            feedback.status = new_status
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status value: {data.status}")

    # Update resolution_notes if provided
    if data.resolution_notes is not None:
        feedback.resolution_notes = data.resolution_notes

    db.commit()
    db.refresh(feedback)

    return feedback.to_dict()
