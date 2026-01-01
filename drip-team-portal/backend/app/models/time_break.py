"""
TimeBreak Model - Tracks breaks within time entries.

Breaks allow pausing work sessions without stopping the timer.
Each break has start/stop times and an optional note.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.database import Base


class TimeBreak(Base):
    """
    A break within a time entry.

    When stopped_at is NULL, the break is currently active.
    Duration is computed from start to stop times.
    """
    __tablename__ = "time_breaks"

    id = Column(Integer, primary_key=True)
    time_entry_id = Column(Integer, ForeignKey("time_entries.id", ondelete="CASCADE"), nullable=False)

    started_at = Column(DateTime(timezone=True), nullable=False)
    stopped_at = Column(DateTime(timezone=True), nullable=True)  # null = currently on break
    note = Column(String(200), nullable=True)  # "lunch", "coffee", etc.

    # Relationship
    time_entry = relationship("TimeEntry", back_populates="breaks")

    def __repr__(self):
        status = "active" if self.stopped_at is None else f"{self.duration_seconds}s"
        return f"<TimeBreak {self.id}: {status}>"

    @property
    def is_active(self) -> bool:
        """True if this break is still active (not stopped)."""
        return self.stopped_at is None

    @property
    def duration_seconds(self) -> int:
        """
        Compute break duration in seconds.

        Returns 0 if break is still active.
        Handles timezone-naive datetimes from SQLite by assuming UTC.
        """
        if not self.stopped_at or not self.started_at:
            return 0
        # Normalize both to UTC-aware (SQLite loses tzinfo)
        started = self.started_at.replace(tzinfo=timezone.utc) if self.started_at.tzinfo is None else self.started_at
        stopped = self.stopped_at.replace(tzinfo=timezone.utc) if self.stopped_at.tzinfo is None else self.stopped_at
        return int((stopped - started).total_seconds())

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            "id": self.id,
            "time_entry_id": self.time_entry_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "note": self.note,
            "duration_seconds": self.duration_seconds,
            "is_active": self.is_active,
        }
