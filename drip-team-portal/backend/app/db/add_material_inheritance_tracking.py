"""Add material inheritance tracking to component properties"""
from sqlalchemy import text
from app.db.database import SessionLocal

def upgrade():
    db = SessionLocal()
    try:
        # Add columns for material inheritance tracking
        db.execute(text("""
            ALTER TABLE component_properties 
            ADD COLUMN IF NOT EXISTS inherited_from_material BOOLEAN DEFAULT FALSE;
        """))
        
        db.execute(text("""
            ALTER TABLE component_properties 
            ADD COLUMN IF NOT EXISTS source_material_id INTEGER REFERENCES materials(id);
        """))
        
        db.commit()
        print("✓ Added material inheritance tracking columns to component_properties table")
        
    except Exception as e:
        print(f"Error adding material inheritance columns: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    upgrade()