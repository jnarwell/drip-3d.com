"""Google OAuth tokens for Drive access."""
from sqlalchemy import Column, Integer, String, DateTime, Text
from datetime import datetime, timezone

from app.db.database import Base


class GoogleToken(Base):
    """
    Stores Google OAuth tokens for users who have connected Google Drive.

    Tokens are stored per user email and include both access and refresh tokens
    to allow automatic refresh when the access token expires.
    """
    __tablename__ = "google_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String(200), unique=True, nullable=False, index=True)

    # OAuth tokens (stored encrypted in production via application-level encryption)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)  # May not always be provided

    # Token expiration
    expires_at = Column(DateTime, nullable=True)

    # Audit fields
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<GoogleToken {self.id}: {self.user_email}>"

    def is_expired(self) -> bool:
        """Check if the access token has expired."""
        if not self.expires_at:
            return True
        return datetime.now(timezone.utc) >= self.expires_at

    def to_dict(self) -> dict:
        """Return dictionary representation (without sensitive tokens)."""
        return {
            "id": self.id,
            "user_email": self.user_email,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "is_expired": self.is_expired(),
        }
