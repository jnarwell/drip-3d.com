"""Contact model for team members and external contacts."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


class Contact(Base):
    """
    Contact information for team members and external contacts.

    - Internal contacts (is_internal=True) link to a User record
    - External contacts (is_internal=False) are standalone entries for
      vendors, suppliers, consultants, etc.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    organization = Column(String(200), nullable=True)  # Company/institution
    expertise = Column(JSON, nullable=True)  # ["thermal", "CFD", "manufacturing"]

    # Contact fields (structured instead of JSON)
    email = Column(String(200), nullable=False)  # Primary email - required
    secondary_email = Column(String(200), nullable=True)  # Optional secondary email
    phone = Column(String(50), nullable=True)  # Optional phone

    notes = Column(Text, nullable=True)

    # Internal vs external
    is_internal = Column(Boolean, default=False, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Link to User if internal

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(200), nullable=True)  # User email who added this contact

    # Relationships
    user = relationship("User", backref="contact_profile")

    def __repr__(self):
        contact_type = "Internal" if self.is_internal else "External"
        return f"<Contact {self.id}: {self.name} ({contact_type})>"

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            "id": self.id,
            "name": self.name,
            "organization": self.organization,
            "expertise": self.expertise or [],
            "email": self.email,
            "secondary_email": self.secondary_email,
            "phone": self.phone,
            "notes": self.notes,
            "is_internal": self.is_internal,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
        }
