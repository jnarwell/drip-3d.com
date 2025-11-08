import sys
sys.path.append('/app')

from sqlalchemy import create_engine
from app.core.config import settings
from app.models import Base
from app.models.material import Material, MaterialProperty, MaterialPropertyTemplate, component_materials

# Create tables directly
engine = create_engine(settings.DATABASE_URL)

# Create material-related tables
Material.__table__.create(engine, checkfirst=True)
MaterialProperty.__table__.create(engine, checkfirst=True)
MaterialPropertyTemplate.__table__.create(engine, checkfirst=True)
component_materials.create(engine, checkfirst=True)

print("Material tables created successfully")