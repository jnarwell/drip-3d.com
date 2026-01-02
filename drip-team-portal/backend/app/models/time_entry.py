"""
Time Entry Model for tracking work sessions.

Time entries track work sessions with:
- Start/stop timestamps and computed duration
- Categorization via Linear issues, resources, or descriptions
- Optional component context
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey,
    Index, func, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.db.database import Base


class TimeEntry(Base):
    """
    Tracks a work session with timing and categorization.

    Entries can be:
    - Running (stopped_at is NULL)
    - Completed (stopped_at and duration_seconds populated)

    Categorization (at least one should be populated, or is_uncategorized=True):
    - linear_issue_id: Link to Linear issue (e.g., "DRP-156")
    - resource_id: Link to a Resource record
    - description: Free-text description
    """
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True)
    user_id = Column(String(200), nullable=False, index=True)  # User email (e.g., "jamie@drip-3d.com")

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    stopped_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # Categorization (at least one should be populated, or is_uncategorized=True)
    linear_issue_id = Column(String(50), nullable=True, index=True)  # "DRP-156"
    linear_issue_title = Column(String(500), nullable=True)  # Cache for display
    resource_id = Column(Integer, ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    is_uncategorized = Column(Boolean, default=False)  # N/A flag

    # Optional context
    component_id = Column(Integer, ForeignKey("components.id"), nullable=True, index=True)

    # Meta
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Edit history: [{field, old_value, new_value, reason, edited_at, edited_by}, ...]
    edit_history = Column(JSON, default=list)

    # Relationships
    component = relationship("Component", back_populates="time_entries")
    resource = relationship("Resource", back_populates="time_entries")
    breaks = relationship("TimeBreak", back_populates="time_entry", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_time_entries_user_started", "user_id", "started_at"),
        Index("ix_time_entries_active", "user_id", "stopped_at"),
    )

    def __repr__(self):
        status = "running" if self.stopped_at is None else f"{self.duration_seconds}s"
        return f"<TimeEntry {self.id}: {self.user_id} ({status})>"

    @property
    def is_running(self) -> bool:
        """True if this timer is still running."""
        return self.stopped_at is None

    @property
    def total_break_seconds(self) -> int:
        """Total seconds spent on breaks."""
        return sum(b.duration_seconds for b in (self.breaks or []))

    @property
    def net_duration_seconds(self) -> int:
        """Duration minus break time."""
        gross = self.duration_seconds or 0
        return max(0, gross - self.total_break_seconds)

    @property
    def was_edited(self) -> bool:
        """True if this entry has edit history."""
        return len(self.edit_history or []) > 0

    @property
    def on_break(self) -> bool:
        """True if there's an active break (no stopped_at)."""
        return any(b.stopped_at is None for b in (self.breaks or []))

    def compute_duration(self) -> int:
        """
        Compute duration in seconds from started_at to stopped_at.

        Returns 0 if stopped_at is not set.
        Handles timezone-naive datetimes from SQLite by assuming UTC.
        """
        if self.stopped_at is None:
            return 0

        # Normalize both to UTC-aware (SQLite loses tzinfo)
        started = self.started_at.replace(tzinfo=timezone.utc) if self.started_at.tzinfo is None else self.started_at
        stopped = self.stopped_at.replace(tzinfo=timezone.utc) if self.stopped_at.tzinfo is None else self.stopped_at
        delta = stopped - started
        return int(delta.total_seconds())

    def stop(self, stop_time: datetime = None) -> int:
        """
        Stop this timer and compute duration.

        Args:
            stop_time: When to stop (defaults to now)

        Returns:
            Duration in seconds
        """
        if stop_time is None:
            stop_time = datetime.now(timezone.utc)

        self.stopped_at = stop_time
        self.duration_seconds = self.compute_duration()
        return self.duration_seconds

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "stopped_at": self.stopped_at.isoformat() if self.stopped_at else None,
            "duration_seconds": self.duration_seconds,
            "linear_issue_id": self.linear_issue_id,
            "linear_issue_title": self.linear_issue_title,
            "resource_id": self.resource_id,
            "description": self.description,
            "is_uncategorized": self.is_uncategorized,
            "component_id": self.component_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            # Break tracking
            "breaks": [b.to_dict() for b in (self.breaks or [])],
            "total_break_seconds": self.total_break_seconds,
            "net_duration_seconds": self.net_duration_seconds,
            "on_break": self.on_break,
            # Edit history
            "edit_history": self.edit_history or [],
            "was_edited": self.was_edited,
        }
