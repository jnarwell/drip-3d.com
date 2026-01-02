"""Models for Resources: System Constants and Project Resources"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey, Table, func
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.database import Base


# =============================================================================
# ASSOCIATION TABLES
# =============================================================================

# Many-to-many: Resources <-> Components
resource_components = Table(
    'resource_components',
    Base.metadata,
    Column('resource_id', Integer, ForeignKey('resources.id'), primary_key=True),
    Column('component_id', Integer, ForeignKey('components.id'), primary_key=True),
)

# Many-to-many: Resources <-> PhysicsModels
resource_physics_models = Table(
    'resource_physics_models',
    Base.metadata,
    Column('resource_id', Integer, ForeignKey('resources.id'), primary_key=True),
    Column('physics_model_id', Integer, ForeignKey('physics_models.id'), primary_key=True),
)


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


# =============================================================================
# RESOURCE MODEL
# =============================================================================

class Resource(Base):
    """
    Project resources: documents, links, papers, images, etc.

    Resources can be linked to:
    - Components (via resource_components)
    - PhysicsModels (via resource_physics_models)
    - TimeEntries (via time_entries.resource_id)

    Types: doc, folder, image, link, paper, video, spreadsheet
    """
    __tablename__ = "resources"

    id = Column(Integer, primary_key=True)
    title = Column(String(300), nullable=False)
    resource_type = Column(String(50), nullable=False)  # doc, folder, image, link, paper, video, spreadsheet
    url = Column(String(2000), nullable=True)

    # Ownership
    added_by = Column(String(200), nullable=False)  # User email
    added_at = Column(DateTime(timezone=True), server_default=func.now())

    # Metadata
    tags = Column(JSON, nullable=True)  # ["research", "thermal", "phase-1"]
    notes = Column(Text, nullable=True)

    # Google Drive integration
    google_drive_file_id = Column(String(100), nullable=True, index=True)  # Drive file ID for linked docs

    # Relationships
    components = relationship(
        "Component",
        secondary=resource_components,
        back_populates="resources"
    )
    physics_models = relationship(
        "PhysicsModel",
        secondary=resource_physics_models,
        back_populates="resources"
    )
    time_entries = relationship("TimeEntry", back_populates="resource")
    collections = relationship(
        "Collection",
        secondary="resource_collections",
        back_populates="resources"
    )

    def __repr__(self):
        return f"<Resource {self.id}: {self.title} ({self.resource_type})>"

    def to_dict(self) -> dict:
        """Return dictionary representation for API responses."""
        return {
            "id": self.id,
            "title": self.title,
            "resource_type": self.resource_type,
            "url": self.url,
            "google_drive_file_id": self.google_drive_file_id,
            "added_by": self.added_by,
            "added_at": self.added_at.isoformat() if self.added_at else None,
            "tags": self.tags,
            "notes": self.notes,
            "component_ids": [c.id for c in self.components] if self.components else [],
            "physics_model_ids": [p.id for p in self.physics_models] if self.physics_models else [],
            "collection_ids": [c.id for c in self.collections] if self.collections else [],
        }
