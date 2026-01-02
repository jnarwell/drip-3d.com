from sqlalchemy import Column, Integer, String, JSON, DateTime
from datetime import datetime, timezone
from app.db.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, nullable=False)
    entity_id = Column(String, nullable=False)
    action = Column(String, nullable=False)
    user = Column(String, nullable=False)
    details = Column(JSON)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)