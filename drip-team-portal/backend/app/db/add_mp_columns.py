import sys
sys.path.append('/app')

from sqlalchemy import create_engine, text
from app.core.config import settings

# Add missing columns
engine = create_engine(settings.DATABASE_URL)

with engine.connect() as conn:
    # Add mp_id column to materials table
    try:
        conn.execute(text("ALTER TABLE materials ADD COLUMN mp_id VARCHAR UNIQUE"))
        conn.commit()
        print("Added mp_id column to materials table")
    except Exception as e:
        print(f"mp_id column might already exist or error: {e}")
        conn.rollback()
    
    # Add created_by column to materials table
    try:
        conn.execute(text("ALTER TABLE materials ADD COLUMN created_by VARCHAR"))
        conn.commit()
        print("Added created_by column to materials table")
    except Exception as e:
        print(f"created_by column might already exist or error: {e}")
        conn.rollback()
    
    # Add created_by column to material_properties table
    try:
        conn.execute(text("ALTER TABLE material_properties ADD COLUMN created_by VARCHAR"))
        conn.commit()
        print("Added created_by column to material_properties table")
    except Exception as e:
        print(f"created_by column might already exist or error: {e}")
        conn.rollback()

print("Database update completed")