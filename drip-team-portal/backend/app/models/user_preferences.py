"""
User Unit Preferences

Stores per-user, per-quantity-type preferred display units.
For example, a user can prefer:
- length: mm (instead of default m)
- pressure: psi (instead of default Pa)
- temperature: °F (instead of default K)
"""

from sqlalchemy import Column, Integer, String, Float, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base


class UserUnitPreference(Base):
    """
    User's preferred display unit for each quantity type.

    When displaying values of a given quantity type (e.g., length, pressure),
    the system will convert from SI base units to the user's preferred unit.

    When the user enters a value without specifying a unit, the system
    assumes the value is in the user's preferred unit for that quantity type.
    """
    __tablename__ = "user_unit_preferences"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # The quantity type this preference applies to
    # e.g., "length", "mass", "pressure", "temperature", "thermalConductivity"
    quantity_type = Column(String(50), nullable=False)

    # The preferred unit for this quantity type
    preferred_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    # Display precision (e.g., 0.01 = 2 decimal places, 0.001 = 3 decimal places)
    precision = Column(Float, default=0.01)

    # Ensure one preference per user per quantity type
    __table_args__ = (
        UniqueConstraint('user_id', 'quantity_type', name='unique_user_quantity_preference'),
    )

    # Relationships
    user = relationship("User", back_populates="unit_preferences")
    preferred_unit = relationship("Unit")

    def __repr__(self):
        return f"<UserUnitPreference user={self.user_id} {self.quantity_type}={self.preferred_unit_id}>"
