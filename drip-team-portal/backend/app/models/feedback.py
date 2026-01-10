"""Feedback submission model for team portal user feedback."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Enum as SQLEnum
from datetime import datetime, timezone
from app.db.database import Base
import enum


class FeedbackType(str, enum.Enum):
    """Type of feedback submission."""
    BUG = "bug"
    FEATURE = "feature"
    QUESTION = "question"


class FeedbackUrgency(str, enum.Enum):
    """Urgency level for feedback."""
    NEED_NOW = "need_now"
    NICE_TO_HAVE = "nice_to_have"


class FeedbackStatus(str, enum.Enum):
    """Status of feedback submission."""
    NEW = "new"
    REVIEWED = "reviewed"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    WONT_FIX = "wont_fix"


class FeedbackSubmission(Base):
    """
    User feedback submissions for bugs, features, and questions.

    Tracks all feedback from team members including browser context
    and resolution workflow.
    """
    __tablename__ = "feedback_submissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(200), nullable=False)  # User email from Auth0
    type = Column(SQLEnum(FeedbackType), nullable=False)
    urgency = Column(SQLEnum(FeedbackUrgency), nullable=False)
    description = Column(Text, nullable=False)
    page_url = Column(String(500), nullable=True)  # Auto-captured from frontend
    browser_info = Column(JSON, nullable=True)  # {userAgent, viewportWidth, viewportHeight}

    # Triage and resolution fields
    status = Column(SQLEnum(FeedbackStatus), nullable=False, default=FeedbackStatus.NEW)
    resolution_notes = Column(Text, nullable=True)
    resolved_by = Column(String(200), nullable=True)  # User email who resolved
    resolved_at = Column(DateTime, nullable=True)

    # Audit timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<FeedbackSubmission {self.id}: {self.type.value} - {self.status.value}>"

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "type": self.type.value if self.type else None,
            "urgency": self.urgency.value if self.urgency else None,
            "description": self.description,
            "page_url": self.page_url,
            "browser_info": self.browser_info or {},
            "status": self.status.value if self.status else None,
            "resolution_notes": self.resolution_notes,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
