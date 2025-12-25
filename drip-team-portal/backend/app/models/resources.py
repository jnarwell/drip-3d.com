"""Models for Resources: System Constants"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime
from datetime import datetime

from app.db.database import Base


class SystemConstant(Base):
    """Physical and mathematical constants used in expressions.

    Constants can be referenced in expressions as:
    - $g (gravitational acceleration)
    - $PI (pi)
    - $R (universal gas constant)
    """
    __tablename__ = "system_constants"

    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, nullable=False, index=True)  # "g", "PI", "R"
    name = Column(String(100), nullable=False)  # "Gravitational Acceleration"
    value = Column(Float, nullable=False)  # 9.80665
    unit = Column(String(20))  # "m/s²"
    description = Column(String(500))  # "Standard acceleration due to gravity"
    category = Column(String(50), nullable=False)  # "Physics", "Mathematics", "Chemistry"
    is_editable = Column(Boolean, default=True)  # Can users modify this?
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

    def __repr__(self):
        return f"<SystemConstant ${self.symbol} = {self.value} {self.unit or ''}>"


