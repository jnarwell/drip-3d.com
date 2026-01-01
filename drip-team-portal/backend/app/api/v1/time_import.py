"""
One-time CSV import endpoint for historical timesheet data.

Supports filtering, exclusions, and meeting duplication rules.
"""

from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
import csv
from io import StringIO
from datetime import datetime, timedelta
import logging
import os

from app.db.database import get_db
from app.models.time_entry import TimeEntry

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/time", tags=["time-import"])

# =============================================================================
# CONFIGURATION
# =============================================================================

NAME_TO_EMAIL = {
    "James Marwell": "jamie@drip-3d.com",
    "Emma Blemaster": "emma@drip-3d.com",
    "Pierce Thompson": "pierce@drip-3d.com",
    "Ryota Sato": "ryota@drip-3d.com",
    "Addison Prairie": "addy@drip-3d.com",
    "Molly Chen": "molly@drip-3d.com",
}

# Patterns to exclude entirely (case-insensitive match in Notes)
EXCLUDE_PATTERNS = [
    "Coaching Meeting",
    "ME103",
    "ENGR15",
    "CME102",
    "House Clean",
    "Health Meeting",
    "Weston",
]

# Meeting patterns → list of participants who get entries
MEETING_RULES = [
    ("Emma / Jamie", ["jamie@drip-3d.com", "emma@drip-3d.com"]),
    ("Jamie / Emma", ["jamie@drip-3d.com", "emma@drip-3d.com"]),
    ("Ryota / Jamie", ["jamie@drip-3d.com", "ryota@drip-3d.com"]),
    ("Jamie / Ryota", ["jamie@drip-3d.com", "ryota@drip-3d.com"]),
    ("Addison / Jamie", ["jamie@drip-3d.com", "addy@drip-3d.com"]),
    ("Jamie / Addison", ["jamie@drip-3d.com", "addy@drip-3d.com"]),
    ("Wendy Gu", ["jamie@drip-3d.com", "emma@drip-3d.com"]),
    ("Brutus Khuri", ["jamie@drip-3d.com", "ryota@drip-3d.com"]),
    ("Pierce Thompson Meeting", ["jamie@drip-3d.com", "pierce@drip-3d.com"]),
    ("Intellectual Property", ["jamie@drip-3d.com", "emma@drip-3d.com"]),
    ("Weld", ["jamie@drip-3d.com", "emma@drip-3d.com"]),
]

# =============================================================================
# HELPERS
# =============================================================================

def should_exclude(notes: str) -> bool:
    """Check if entry should be excluded entirely."""
    if not notes:
        return False
    notes_lower = notes.lower()
    for pattern in EXCLUDE_PATTERNS:
        if pattern.lower() in notes_lower:
            return True
    return False


def get_participants(notes: str, default_email: str) -> List[str]:
    """Get list of emails who should have entries for this row."""
    if not notes:
        return [default_email]

    notes_lower = notes.lower()
    for pattern, participants in MEETING_RULES:
        if pattern.lower() in notes_lower:
            return participants

    return [default_email]


def parse_duration(duration_str: str) -> int:
    """Parse 'H:MM:SS' or 'H:MM' to seconds."""
    if not duration_str:
        return 0

    parts = duration_str.strip().split(":")
    try:
        hours = int(parts[0]) if parts[0] else 0
        minutes = int(parts[1]) if len(parts) > 1 else 0
        seconds = int(parts[2]) if len(parts) > 2 else 0
        return hours * 3600 + minutes * 60 + seconds
    except (ValueError, IndexError):
        return 0


def parse_datetime(date_str: str, time_str: str) -> datetime:
    """Parse date and time into datetime."""
    if not date_str:
        raise ValueError("Missing date")

    # Clean up time string
    time_str = (time_str or "9:00 am").strip().lower()

    # Normalize time format
    time_str = time_str.replace(".", "").replace("  ", " ")

    dt_str = f"{date_str.strip()} {time_str}"

    # Try various formats
    formats = [
        "%m/%d/%Y %I:%M %p",
        "%m/%d/%Y %I:%M%p",
        "%m/%d/%Y %H:%M",
        "%m/%d/%Y %I %p",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(dt_str, fmt)
        except ValueError:
            continue

    # Fallback: just parse date, use 9am
    try:
        return datetime.strptime(date_str.strip(), "%m/%d/%Y").replace(hour=9)
    except ValueError:
        raise ValueError(f"Cannot parse date: {date_str}")


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.post("/import-csv/preview")
async def preview_csv_import(
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """
    Preview CSV import without creating entries.

    Returns breakdown of what will be imported, excluded, and skipped.
    """
    content = await file.read()
    text = content.decode('utf-8-sig')  # Handle BOM
    reader = csv.DictReader(StringIO(text))

    will_import = []
    excluded = []
    skipped = []

    for i, row in enumerate(reader, start=2):
        user_name = row.get("User", "").strip()
        notes = row.get("Notes", "").strip() or row.get("Task", "").strip()
        date_str = row.get("Date", "").strip()
        duration_str = row.get("Duration", "0:00:00").strip()
        hours = row.get("Hours", "0")
        time_str = row.get("From", "").strip()

        # Unknown user → skip
        if user_name not in NAME_TO_EMAIL:
            skipped.append({
                "row": i,
                "reason": f"Unknown user: {user_name}",
                "date": date_str,
                "notes": notes[:50] if notes else "(empty)"
            })
            continue

        default_email = NAME_TO_EMAIL[user_name]

        # Excluded patterns
        if should_exclude(notes):
            excluded.append({
                "row": i,
                "reason": "Matches exclude pattern",
                "date": date_str,
                "notes": notes[:50],
                "user": user_name
            })
            continue

        # Get participants for this entry
        participants = get_participants(notes, default_email)
        is_meeting = len(participants) > 1

        for email in participants:
            will_import.append({
                "row": i,
                "user": email,
                "date": date_str,
                "time": time_str,
                "hours": hours,
                "notes": notes[:50] if notes else "(empty)",
                "is_meeting": is_meeting
            })

    # Summary stats
    meeting_entries = sum(1 for e in will_import if e.get("is_meeting"))

    return {
        "summary": {
            "will_import": len(will_import),
            "excluded": len(excluded),
            "skipped": len(skipped),
            "meeting_duplicates": meeting_entries
        },
        "preview": {
            "import_sample": will_import[:25],
            "excluded": excluded,
            "skipped": skipped
        }
    }


@router.post("/import-csv/execute")
async def execute_csv_import(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Execute CSV import and create TimeEntry records.

    Run preview first to verify what will be imported.
    """
    content = await file.read()
    text = content.decode('utf-8-sig')
    reader = csv.DictReader(StringIO(text))

    imported = []
    errors = []

    for i, row in enumerate(reader, start=2):
        try:
            user_name = row.get("User", "").strip()
            notes = row.get("Notes", "").strip() or row.get("Task", "").strip()
            date_str = row.get("Date", "").strip()
            time_str = row.get("From", "").strip()
            duration_str = row.get("Duration", "0:00:00").strip()

            # Skip unknown users
            if user_name not in NAME_TO_EMAIL:
                continue

            default_email = NAME_TO_EMAIL[user_name]

            # Skip excluded
            if should_exclude(notes):
                continue

            # Parse times
            started_at = parse_datetime(date_str, time_str)
            duration_seconds = parse_duration(duration_str)
            stopped_at = started_at + timedelta(seconds=duration_seconds)

            # Get participants
            participants = get_participants(notes, default_email)

            # Create entry for each participant
            for email in participants:
                entry = TimeEntry(
                    user_id=email,
                    started_at=started_at,
                    stopped_at=stopped_at,
                    duration_seconds=duration_seconds,
                    description=notes or "Imported from timesheet",
                    linear_issue_id=None,
                    linear_issue_title=None,
                    resource_id=None,
                    component_id=None,
                    is_uncategorized=False
                )
                db.add(entry)
                imported.append({
                    "user": email,
                    "date": date_str,
                    "hours": round(duration_seconds / 3600, 2),
                    "notes": notes[:40] if notes else "(imported)"
                })

        except Exception as e:
            errors.append({
                "row": i,
                "error": str(e),
                "user": row.get("User", ""),
                "date": row.get("Date", "")
            })

    # Commit all entries
    db.commit()

    logger.info(f"[CSV-IMPORT] Imported {len(imported)} time entries, {len(errors)} errors")

    return {
        "imported": len(imported),
        "errors": len(errors),
        "error_details": errors[:10] if errors else [],
        "sample": imported[:15]
    }
