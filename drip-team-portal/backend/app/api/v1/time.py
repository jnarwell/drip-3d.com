"""
Time Tracking API - Endpoints for tracking work sessions.

Provides:
- Start/stop timers with auto-stop of previous
- Active timer retrieval
- Time entry CRUD with filters
- Summary aggregation by user/component
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import func, and_, or_
from typing import Optional, List
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
from datetime import datetime, timezone, date
import os

from app.db.database import get_db
from app.models.time_entry import TimeEntry
from app.models.time_break import TimeBreak
from app.models.resources import Resource
from app.models.component import Component
from app.models.user import User

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


class ManualBreakInput(BaseModel):
    """Break for manual entry creation."""
    started_at: datetime
    stopped_at: datetime
    note: Optional[str] = None


class TimeEntryCreateRequest(BaseModel):
    """For manual time entry creation."""
    started_at: datetime
    stopped_at: datetime
    breaks: Optional[List[ManualBreakInput]] = None
    linear_issue_id: Optional[str] = None
    linear_issue_title: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    is_uncategorized: bool = False
    component_id: Optional[int] = None


class BreakUpdateInput(BaseModel):
    """Break for updating - includes optional id for existing breaks."""
    id: Optional[int] = None  # If provided, updates existing; if None, creates new
    started_at: datetime
    stopped_at: datetime
    note: Optional[str] = None


class TimeEntryUpdateRequest(BaseModel):
    """Update request with required edit_reason for audit trail."""
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    breaks: Optional[List[BreakUpdateInput]] = None  # If provided, replaces all breaks
    linear_issue_id: Optional[str] = None
    linear_issue_title: Optional[str] = None
    resource_id: Optional[int] = None
    description: Optional[str] = None
    is_uncategorized: Optional[bool] = None
    component_id: Optional[int] = None
    edit_reason: str  # REQUIRED - why was this entry edited?


class BreakStartRequest(BaseModel):
    """Optional note when starting a break."""
    note: Optional[str] = None


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
    print(f"🕐 [TIME] START: user_id={user_id}")

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
    Users can only view their own entries (user_id filter is ignored for security).
    """
    current_user_email = current_user.get('email')
    logger.info(f"GET /entries - user={current_user_email}, requested_filter={user_id}")

    # Use selectinload to prevent N+1 queries when calling to_dict()
    query = db.query(TimeEntry).options(selectinload(TimeEntry.breaks))

    # SECURITY: Always filter by current user - users can only see their own entries
    # The user_id parameter is accepted but ignored to prevent cross-user access
    query = query.filter(TimeEntry.user_id == current_user_email)

    # Apply date filters
    # Note: Use naive datetimes for SQLite compatibility (SQLite stores naive)
    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeEntry.started_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeEntry.started_at <= end_datetime)

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
    Supports optional breaks array for break periods.
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

    # Create breaks if provided
    if data.breaks:
        for break_input in data.breaks:
            # Validate break is within entry time range
            if break_input.started_at < data.started_at or break_input.stopped_at > data.stopped_at:
                raise HTTPException(
                    status_code=400,
                    detail="Break times must be within entry time range"
                )

            break_entry = TimeBreak(
                time_entry_id=entry.id,
                started_at=break_input.started_at,
                stopped_at=break_input.stopped_at,
                note=break_input.note
            )
            db.add(break_entry)

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
    Update a time entry with edit tracking.

    Requires edit_reason for audit trail.
    Only the entry owner can update their entries.
    """
    user_id = current_user["email"]

    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Time entry not found")

    # Check ownership
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Can only update your own entries")

    # Track changes for edit history
    changes = []
    editable_fields = [
        "started_at", "stopped_at", "linear_issue_id", "linear_issue_title",
        "resource_id", "description", "is_uncategorized", "component_id"
    ]

    for field in editable_fields:
        new_value = getattr(data, field)
        if new_value is not None:
            old_value = getattr(entry, field)
            # Compare values (handle datetime serialization)
            old_str = old_value.isoformat() if hasattr(old_value, 'isoformat') else str(old_value) if old_value is not None else None
            new_str = new_value.isoformat() if hasattr(new_value, 'isoformat') else str(new_value) if new_value is not None else None

            if old_str != new_str:
                changes.append({
                    "field": field,
                    "old_value": old_str,
                    "new_value": new_str,
                    "reason": data.edit_reason,
                    "edited_at": datetime.now(timezone.utc).isoformat(),
                    "edited_by": user_id
                })
                setattr(entry, field, new_value)

    # Handle breaks if provided (replaces all existing breaks)
    if data.breaks is not None:
        # Get current breaks for history
        current_breaks = db.query(TimeBreak).filter(TimeBreak.time_entry_id == entry_id).all()
        old_breaks_str = str([{"started_at": b.started_at.isoformat(), "stopped_at": b.stopped_at.isoformat(), "note": b.note} for b in current_breaks])
        new_breaks_str = str([{"started_at": b.started_at.isoformat(), "stopped_at": b.stopped_at.isoformat(), "note": b.note} for b in data.breaks])

        if old_breaks_str != new_breaks_str:
            changes.append({
                "field": "breaks",
                "old_value": old_breaks_str,
                "new_value": new_breaks_str,
                "reason": data.edit_reason,
                "edited_at": datetime.now(timezone.utc).isoformat(),
                "edited_by": user_id
            })

            # Delete existing breaks
            for b in current_breaks:
                db.delete(b)

            # Create new breaks
            for break_input in data.breaks:
                break_entry = TimeBreak(
                    time_entry_id=entry_id,
                    started_at=break_input.started_at,
                    stopped_at=break_input.stopped_at,
                    note=break_input.note
                )
                db.add(break_entry)

    # Append changes to edit history
    if changes:
        history = entry.edit_history or []
        history.extend(changes)
        entry.edit_history = history

        # Recalculate duration if times changed
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
# BREAK ENDPOINTS
# =============================================================================

@router.post("/entries/{entry_id}/breaks")
async def start_break(
    entry_id: int,
    data: BreakStartRequest = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Start a break on a running time entry.

    Only works on entries that are still running (no stopped_at).
    Cannot start a break if already on break.
    """
    user_id = current_user["email"]

    # Handle empty body
    if data is None:
        data = BreakStartRequest()

    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your entry")
    if entry.stopped_at:
        raise HTTPException(status_code=400, detail="Cannot break on stopped entry")
    if entry.on_break:
        raise HTTPException(status_code=400, detail="Already on break")

    break_entry = TimeBreak(
        time_entry_id=entry_id,
        started_at=datetime.now(timezone.utc),
        note=data.note
    )
    db.add(break_entry)
    db.commit()
    db.refresh(break_entry)

    return break_entry.to_dict()


@router.post("/entries/{entry_id}/breaks/{break_id}/stop")
async def stop_break(
    entry_id: int,
    break_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    End an active break.

    Returns the completed break with duration.
    """
    user_id = current_user["email"]

    # Verify entry ownership
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your entry")

    break_entry = db.query(TimeBreak).filter(
        TimeBreak.id == break_id,
        TimeBreak.time_entry_id == entry_id
    ).first()
    if not break_entry:
        raise HTTPException(status_code=404, detail="Break not found")
    if break_entry.stopped_at:
        raise HTTPException(status_code=400, detail="Break already stopped")

    break_entry.stopped_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(break_entry)

    return break_entry.to_dict()


@router.get("/entries/{entry_id}/breaks")
async def list_breaks(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List all breaks for a time entry.
    """
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")

    breaks = db.query(TimeBreak).filter(
        TimeBreak.time_entry_id == entry_id
    ).order_by(TimeBreak.started_at.asc()).all()

    return {
        "breaks": [b.to_dict() for b in breaks],
        "total_break_seconds": sum(b.duration_seconds for b in breaks),
        "active_break": next((b.to_dict() for b in breaks if b.stopped_at is None), None)
    }


@router.delete("/entries/{entry_id}/breaks/{break_id}")
async def delete_break(
    entry_id: int,
    break_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a break from a time entry.

    Only the entry owner can delete breaks.
    """
    user_id = current_user["email"]

    # Verify entry ownership
    entry = db.query(TimeEntry).filter(TimeEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    if entry.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not your entry")

    break_entry = db.query(TimeBreak).filter(
        TimeBreak.id == break_id,
        TimeBreak.time_entry_id == entry_id
    ).first()
    if not break_entry:
        raise HTTPException(status_code=404, detail="Break not found")

    db.delete(break_entry)
    db.commit()

    return {"deleted": True, "id": break_id}


# =============================================================================
# SUMMARY / AGGREGATION
# =============================================================================

@router.get("/summary")
async def get_summary(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user_id: Optional[str] = Query(None, description="Filter by user email"),
    group_by: str = Query("user", regex="^(user|component|linear_issue)$"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get aggregated time summary.

    Groups by: user, component, or linear_issue
    Returns total_seconds and entry_count per group.
    Optionally filter by user_id (email) to get individual user summary.
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
        # Join User table to get names
        results = db.query(
            TimeEntry.user_id.label("key"),
            User.name.label("user_name"),
            func.sum(TimeEntry.duration_seconds).label("total_seconds"),
            func.count(TimeEntry.id).label("entry_count")
        ).outerjoin(
            User, TimeEntry.user_id == User.email
        ).filter(
            TimeEntry.stopped_at.isnot(None)
        )

        if start_date:
            results = results.filter(TimeEntry.started_at >= start_datetime)
        if end_date:
            results = results.filter(TimeEntry.started_at <= end_datetime)
        if user_id:
            results = results.filter(TimeEntry.user_id == user_id)

        results = results.group_by(TimeEntry.user_id, User.name).all()

        groups = [
            {
                "key": r.key,
                "name": r.user_name or r.key.split("@")[0].replace(".", " ").title(),
                "total_seconds": r.total_seconds or 0,
                "entry_count": r.entry_count
            }
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
        if user_id:
            results = results.filter(TimeEntry.user_id == user_id)

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
        if user_id:
            results = results.filter(TimeEntry.user_id == user_id)

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


@router.get("/summary/by-project")
async def get_summary_by_project(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    user_id: Optional[str] = Query(None, description="Filter by user email"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get time summary grouped by Linear project.

    Fetches project info from Linear API for issues in the time entries.
    Returns total time per project with issue counts.
    """
    import httpx

    # Build query for entries with linear_issue_id
    query = db.query(TimeEntry).filter(
        TimeEntry.stopped_at.isnot(None),
        TimeEntry.linear_issue_id.isnot(None)
    )

    if start_date:
        start_datetime = datetime.combine(start_date, datetime.min.time())
        query = query.filter(TimeEntry.started_at >= start_datetime)

    if end_date:
        end_datetime = datetime.combine(end_date, datetime.max.time())
        query = query.filter(TimeEntry.started_at <= end_datetime)

    if user_id:
        query = query.filter(TimeEntry.user_id == user_id)

    entries = query.all()

    if not entries:
        return {
            "group_by": "project",
            "groups": [],
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }

    # Collect unique issue identifiers
    issue_ids = list(set(e.linear_issue_id for e in entries if e.linear_issue_id))
    logger.info(f"[BY-PROJECT] Time entries with Linear issues: {issue_ids}")

    # Fetch issue->project mapping from Linear
    issue_to_project = {}
    LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")

    logger.info(f"[BY-PROJECT] LINEAR_API_KEY configured: {bool(LINEAR_API_KEY)}")
    if LINEAR_API_KEY and issue_ids:
        try:
            # Use aliased queries to fetch each issue by identifier
            # Linear's issue(id:) query accepts both UUIDs and identifiers like "SYS-15"
            alias_queries = []
            for i, identifier in enumerate(issue_ids):
                alias = f"issue_{i}"
                alias_queries.append(f'{alias}: issue(id: "{identifier}") {{ identifier project {{ id name }} }}')

            graphql_query = "query { " + " ".join(alias_queries) + " }"
            logger.info(f"[BY-PROJECT] Querying {len(issue_ids)} issues from Linear")

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    "https://api.linear.app/graphql",
                    json={"query": graphql_query},
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": LINEAR_API_KEY
                    }
                )
                logger.info(f"[BY-PROJECT] Linear API response status: {response.status_code}")
                if response.status_code == 200:
                    data = response.json()

                    # Check for GraphQL errors
                    if "errors" in data:
                        logger.error(f"[BY-PROJECT] GraphQL errors: {data['errors']}")

                    # Parse aliased response - each key is like "issue_0", "issue_1", etc.
                    response_data = data.get("data", {})
                    issues_found = 0
                    for key, issue in response_data.items():
                        if issue:  # issue might be null if not found
                            issues_found += 1
                            project = issue.get("project")
                            identifier = issue.get("identifier")
                            if identifier:
                                issue_to_project[identifier] = {
                                    "project_id": project.get("id") if project else None,
                                    "project_name": project.get("name") if project else "No Project"
                                }

                    logger.info(f"[BY-PROJECT] Linear returned {issues_found} issues")
                    logger.info(f"[BY-PROJECT] Issue to project mapping: {issue_to_project}")
                else:
                    logger.warning(f"[BY-PROJECT] Linear API error: {response.text}")
        except Exception as e:
            logger.warning(f"Failed to fetch Linear project info: {e}", exc_info=True)

    # Aggregate by project
    project_totals = {}
    for entry in entries:
        project_info = issue_to_project.get(
            entry.linear_issue_id,
            {"project_id": None, "project_name": "No Project"}
        )
        project_key = project_info["project_id"] or "none"

        if project_key not in project_totals:
            project_totals[project_key] = {
                "project_id": project_info["project_id"],
                "project_name": project_info["project_name"],
                "total_seconds": 0,
                "entry_count": 0,
                "issues": set()
            }

        project_totals[project_key]["total_seconds"] += entry.duration_seconds or 0
        project_totals[project_key]["entry_count"] += 1
        if entry.linear_issue_id:
            project_totals[project_key]["issues"].add(entry.linear_issue_id)

    # Build response groups (convert sets to counts)
    groups = []
    for key, data in project_totals.items():
        groups.append({
            "project_id": data["project_id"],
            "project_name": data["project_name"],
            "total_seconds": data["total_seconds"],
            "entry_count": data["entry_count"],
            "issue_count": len(data["issues"])
        })

    # Sort by total time descending
    groups.sort(key=lambda x: x["total_seconds"], reverse=True)

    return {
        "group_by": "project",
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
