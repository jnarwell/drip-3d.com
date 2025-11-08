import sys
sys.path.append('/app')

from sqlalchemy import create_engine, text
from app.core.config import settings

# Add missing columns
engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Add primary_material_id column to components table
    try:
        conn.execute(text("ALTER TABLE components ADD COLUMN primary_material_id INTEGER REFERENCES materials(id)"))
        conn.commit()
        print("Added primary_material_id column")
    except Exception as e:
        print(f"Column might already exist or error: {e}")
        conn.rollback()

print("Database update completed")