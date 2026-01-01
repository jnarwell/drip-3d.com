"""
Time Tracking API - Endpoints for tracking work sessions.

Provides:
- Start/stop timers with auto-stop of previous
- Active timer retrieval
- Time entry CRUD with filters
- Summary aggregation by user/component
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime, timezone, date
import os

from app.db.database import get_db
from app.models.time_entry import TimeEntry
from app.models.resources import Resource
from app.models.component import Component

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/time", tags=["time"])


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class TimerStartRequest(BaseModel):
    linear_issue_id: Optional[str] = None
    component_id: Optional[int] = None


class TimerStopRequest(BaseModel):
    linear_issue_id: Optional[str] = None
    linear_issue_title: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    is_uncategorized: bool = False
    component_id: Optional[int] = None


class TimeEntryCreateRequest(BaseModel):
    """For manual time entry creation."""
    started_at: datetime
    stopped_at: datetime
    linear_issue_id: Optional[str] = None
    linear_issue_title: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    is_uncategorized: bool = False
    component_id: Optional[int] = None


class TimeEntryUpdateRequest(BaseModel):
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    linear_issue_id: Optional[str] = None
    linear_issue_title: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    is_uncategorized: Optional[bool] = None
    component_id: Optional[int] = None


# =============================================================================
# TIMER ENDPOINTS
# =============================================================================

@router.post("/start")
async def start_timer(
    data: TimerStartRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Start a new timer.

    Automatically stops any running timer for this user first.
    Returns the newly created entry.
    """
    user_id = current_user["email"]

    # Handle empty body
    if data is None:
        data = TimerStartRequest()

    # Auto-stop any running timer
    running_entry = db.query(TimeEntry).filter(
        TimeEntry.user_id == user_id,
        TimeEntry.stopped_at.is_(None)
    ).first()

    stopped_entry = None
    if running_entry:
        running_entry.stop()
        # Mark as uncategorized if no categorization was provided
        if not any([
            running_entry.linear_issue_id,
            running_entry.resource_id,
            running_entry.description,
            running_entry.is_uncategorized
        ]):
            running_entry.is_uncategorized = True
        stopped_entry = running_entry.to_dict()

    # Create new entry
    new_entry = TimeEntry(
        user_id=user_id,
        started_at=datetime.now(timezone.utc),
        linear_issue_id=data.linear_issue_id,
        component_id=data.component_id
    )
    db.add(new_entry)
    db.commit()
    db.refresh(new_entry)

    response = {
        "id": new_entry.id,
        "started_at": new_entry.started_at.isoformat(),
        "user_id": new_entry.user_id,
        "linear_issue_id": new_entry.linear_issue_id,
        "component_id": new_entry.component_id,
    }

    if stopped_entry:
        response["stopped_previous"] = stopped_entry

    return response


@router.post("/stop")
async def stop_timer(
    data: TimerStopRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Stop the current running timer.

    Requires categorization: at least one of linear_issue_id, resource_id,
    description, or is_uncategorized=true must be provided.
    """
    user_id = current_user["email"]

    # Validate categorization
    has_categorization = any([
        data.linear_issue_id,
        data.resource_id,
        data.description,
        data.is_uncategorized
    ])
    if not has_categorization:
        raise HTTPException(
            status_code=400,
            detail="Categorization required: provide linear_issue_id, resource_id, description, or set is_uncategorized=true"
        )

    # Find running timer
    running_entry = db.query(TimeEntry).filter(
        TimeEntry.user_id == user_id,
        TimeEntry.stopped_at.is_(None)
    ).first()

    if not running_entry:
        raise HTTPException(status_code=404, detail="No running timer found")

    # Stop and categorize
    running_entry.stop()
    running_entry.linear_issue_id = data.linear_issue_id
    running_entry.linear_issue_title = data.linear_issue_title
    running_entry.resource_id = data.resource_id
    running_entry.description = data.description
    running_entry.is_uncategorized = data.is_uncategorized

    # Update component if provided
    if data.component_id is not None:
        running_entry.component_id = data.component_id

    db.commit()
    db.refresh(running_entry)

    return running_entry.to_dict()


@router.get("/active")
async def get_active_timer(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get the current user's running timer, or null if none.
    """
    user_id = current_user["email"]

    running_entry = db.query(TimeEntry).filter(
        TimeEntry.user_id == user_id,
        TimeEntry.stopped_at.is_(None)
    ).first()

    if not running_entry:
        return None

    return running_entry.to_dict()


# =============================================================================
# ENTRIES CRUD
# =============================================================================

@router.get("/entries")
async def list_entries(
    start_date: Optional[date] = Query(None, description="Filter entries starting from this date"),
    end_date: Optional[date] = Query(None, description="Filter entries up to this date"),
    user_id: Optional[str] = Query(None, description="Filter by user email"),
    component_id: Optional[int] = Query(None, description="Filter by component ID"),
    linear_issue_id: Optional[str] = Query(None, description="Filter by Linear issue ID"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List time entries with optional filters.

    Returns entries sorted by started_at descending (most recent first).
    """
    query = db.query(TimeEntry)

    # Apply filters
    # Note: Use naive datetimes for SQLite compatibility (SQLite stores naive)
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeEntry.started_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeEntry.started_at <= end_datetime)

    if user_id:
        query = query.filter(TimeEntry.user_id == user_id)

    if component_id:
        query = query.filter(TimeEntry.component_id == component_id)

    if linear_issue_id:
        query = query.filter(TimeEntry.linear_issue_id == linear_issue_id)

    # Get total count
    total = query.count()

    # Get paginated results
    entries = query.order_by(TimeEntry.started_at.desc()).offset(offset).limit(limit).all()

    return {
        "entries": [e.to_dict() for e in entries],
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.post("/entries")
async def create_entry(
    data: TimeEntryCreateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a manual time entry (already completed).

    Useful for logging time after the fact.
    """
    user_id = current_user["email"]

    # Validate categorization
    has_categorization = any([
        data.linear_issue_id,
        data.resource_id,
        data.description,
        data.is_uncategorized
    ])
    if not has_categorization:
        raise HTTPException(
            status_code=400,
            detail="Categorization required"
        )

    # Calculate duration
    duration = int((data.stopped_at - data.started_at).total_seconds())
    if duration < 0:
        raise HTTPException(status_code=400, detail="stopped_at must be after started_at")

    entry = TimeEntry(
        user_id=user_id,
        started_at=data.started_at,
        stopped_at=data.stopped_at,
        duration_seconds=duration,
        linear_issue_id=data.linear_issue_id,
        linear_issue_title=data.linear_issue_title,
        resource_id=data.resource_id,
        description=data.description,
        is_uncategorized=data.is_uncategorized,
        component_id=data.component_id
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)

    return entry.to_dict()


@router.get("/entries/{entry_id}")
async def get_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a single time entry by ID."""
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()

    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    return entry.to_dict()


@router.patch("/entries/{entry_id}")
async def update_entry(
    entry_id: int,
    data: TimeEntryUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a time entry.

    Only the entry owner can update their entries.
    """
    user_id = current_user["email"]

    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    # Check ownership
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own entries")

    # Update fields
    if data.started_at is not None:
        entry.started_at = data.started_at
    if data.stopped_at is not None:
        entry.stopped_at = data.stopped_at
    if data.linear_issue_id is not None:
        entry.linear_issue_id = data.linear_issue_id
    if data.linear_issue_title is not None:
        entry.linear_issue_title = data.linear_issue_title
    if data.resource_id is not None:
        entry.resource_id = data.resource_id
    if data.description is not None:
        entry.description = data.description
    if data.is_uncategorized is not None:
        entry.is_uncategorized = data.is_uncategorized
    if data.component_id is not None:
        entry.component_id = data.component_id

    # Recalculate duration if both times are set
    if entry.started_at and entry.stopped_at:
        entry.duration_seconds = entry.compute_duration()

    db.commit()
    db.refresh(entry)

    return entry.to_dict()


@router.delete("/entries/{entry_id}")
async def delete_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a time entry.

    Only the entry owner can delete their entries.
    """
    user_id = current_user["email"]

    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    # Check ownership
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only delete your own entries")

    db.delete(entry)
    db.commit()

    return {"deleted": True, "id": entry_id}


# =============================================================================
# SUMMARY / AGGREGATION
# =============================================================================

@router.get("/summary")
async def get_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    group_by: str = Query("user", regex="^(user|component|linear_issue)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated time summary.

    Groups by: user, component, or linear_issue
    Returns total_seconds and entry_count per group.
    """
    # Build base query for completed entries only
    query = db.query(TimeEntry).filter(TimeEntry.stopped_at.isnot(None))

    # Apply date filters
    # Note: Use naive datetimes for SQLite compatibility (SQLite stores naive)
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeEntry.started_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeEntry.started_at <= end_datetime)

    # Group by logic
    if group_by == "user":
        results = db.query(
            TimeEntry.user_id.label("key"),
            func.sum(TimeEntry.duration_seconds).label("total_seconds"),
            func.count(TimeEntry.id).label("entry_count")
        ).filter(
            TimeEntry.stopped_at.isnot(None)
        )

        if start_date:
            results = results.filter(TimeEntry.started_at >= start_datetime)
        if end_date:
            results = results.filter(TimeEntry.started_at <= end_datetime)

        results = results.group_by(TimeEntry.user_id).all()

        groups = [
            {"key": r.key, "total_seconds": r.total_seconds or 0, "entry_count": r.entry_count}
            for r in results
        ]

    elif group_by == "component":
        results = db.query(
            TimeEntry.component_id.label("key"),
            func.sum(TimeEntry.duration_seconds).label("total_seconds"),
            func.count(TimeEntry.id).label("entry_count")
        ).filter(
            TimeEntry.stopped_at.isnot(None),
            TimeEntry.component_id.isnot(None)
        )

        if start_date:
            results = results.filter(TimeEntry.started_at >= start_datetime)
        if end_date:
            results = results.filter(TimeEntry.started_at <= end_datetime)

        results = results.group_by(TimeEntry.component_id).all()

        # Enrich with component names
        component_ids = [r.key for r in results]
        components = {c.id: c.name for c in db.query(Component).filter(Component.id.in_(component_ids)).all()}

        groups = [
            {
                "key": r.key,
                "component_name": components.get(r.key),
                "total_seconds": r.total_seconds or 0,
                "entry_count": r.entry_count
            }
            for r in results
        ]

    elif group_by == "linear_issue":
        results = db.query(
            TimeEntry.linear_issue_id.label("key"),
            TimeEntry.linear_issue_title.label("title"),
            func.sum(TimeEntry.duration_seconds).label("total_seconds"),
            func.count(TimeEntry.id).label("entry_count")
        ).filter(
            TimeEntry.stopped_at.isnot(None),
            TimeEntry.linear_issue_id.isnot(None)
        )

        if start_date:
            results = results.filter(TimeEntry.started_at >= start_datetime)
        if end_date:
            results = results.filter(TimeEntry.started_at <= end_datetime)

        results = results.group_by(TimeEntry.linear_issue_id, TimeEntry.linear_issue_title).all()

        groups = [
            {
                "key": r.key,
                "linear_issue_title": r.title,
                "total_seconds": r.total_seconds or 0,
                "entry_count": r.entry_count
            }
            for r in results
        ]

    return {
        "group_by": group_by,
        "groups": groups,
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    }


# =============================================================================
# TEAM VIEW (All active timers)
# =============================================================================

@router.get("/team/active")
async def get_team_active_timers(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all currently running timers across the team.

    Useful for showing who's working on what.
    """
    running_entries = db.query(TimeEntry).filter(
        TimeEntry.stopped_at.is_(None)
    ).order_by(TimeEntry.started_at.asc()).all()

    return {
        "active_timers": [e.to_dict() for e in running_entries],
        "count": len(running_entries)
    }
