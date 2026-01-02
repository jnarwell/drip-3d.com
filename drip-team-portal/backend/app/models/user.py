from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, nullable=False, index=True)
    name = Column(String)
    auth0_id = Column(String, unique=True, nullable=False)

    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)

    last_login = Column(DateTime)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # User's preferred display units per quantity type
    unit_preferences = relationship(
        "UserUnitPreference",
        back_populates="user",
        cascade="all, delete-orphan"
    )