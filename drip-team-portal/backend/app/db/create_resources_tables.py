"""Create tables for the Resources module"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.models.resources import PropertyTable, SystemConstant, CalculationTemplate
from app.db.seed_constants import seed_constants
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_resources_tables():
    """Create the resources tables in the database"""
    try:
        # Import Base after all models are imported
        from app.models import Base
        
        # Create tables
        logger.info("Creating resources tables...")
        Base.metadata.create_all(bind=engine, tables=[
            PropertyTable.__table__,
            SystemConstant.__table__,
            CalculationTemplate.__table__
        ])
        
        logger.info("Resources tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating resources tables: {e}")
        return False


def main():
    """Main function to create tables and seed data"""
    # Create tables
    if not create_resources_tables():
        print("Failed to create tables")
        return 1
    
    # Seed constants
    print("\nSeeding system constants...")
    db = SessionLocal()
    try:
        added, skipped = seed_constants(db)
        print(f"Seeding completed! Added: {added}, Skipped: {skipped}")
    except Exception as e:
        print(f"Error seeding constants: {e}")
        db.rollback()
        return 1
    finally:
        db.close()
    
    return 0


if __name__ == "__main__":
    exit(main())