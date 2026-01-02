"""Collection model for organizing resources."""
from sqlalchemy import Column, Integer, String, DateTime, Text, Table, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.database import Base


# =============================================================================
# ASSOCIATION TABLE
# =============================================================================

# Many-to-many: Resources <-> Collections
resource_collections = Table(
    'resource_collections',
    Base.metadata,
    Column('resource_id', Integer, ForeignKey('resources.id', ondelete='CASCADE'), primary_key=True),
    Column('collection_id', Integer, ForeignKey('collections.id', ondelete='CASCADE'), primary_key=True),
)


# =============================================================================
# COLLECTION MODEL
# =============================================================================

class Collection(Base):
    """
    Collections for organizing resources.

    Each user can create collections to group related documents, links, etc.
    Collection names are unique per user (not globally).
    """
    __tablename__ = "collections"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    color = Column(String(7), nullable=True)  # Hex code, e.g., "#FF5733"

    # Ownership
    created_by = Column(String(200), nullable=False)  # User email
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint: name + created_by
    __table_args__ = (
        UniqueConstraint('name', 'created_by', name='uq_collection_name_per_user'),
    )

    # Relationships
    resources = relationship(
        "Resource",
        secondary=resource_collections,
        back_populates="collections"
    )

    def __repr__(self):
        return f"<Collection {self.id}: {self.name} ({self.created_by})>"

    def to_dict(self, include_resources: bool = False) -> dict:
        """Return dictionary representation for API responses."""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "color": self.color,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "resource_count": len(self.resources) if self.resources else 0,
        }
        if include_resources:
            result["resource_ids"] = [r.id for r in self.resources] if self.resources else []
        return result
