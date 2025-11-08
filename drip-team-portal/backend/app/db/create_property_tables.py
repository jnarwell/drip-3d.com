import sys
sys.path.append('/app')

from sqlalchemy import create_engine
from app.core.config import settings
from app.models import Base
from app.models.property import PropertyDefinition, ComponentProperty, UnitSystem

# Create tables directly
engine = create_engine(settings.DATABASE_URL)

# Create only the property-related tables
PropertyDefinition.__table__.create(engine, checkfirst=True)
ComponentProperty.__table__.create(engine, checkfirst=True)
UnitSystem.__table__.create(engine, checkfirst=True)

print("Property tables created successfully")