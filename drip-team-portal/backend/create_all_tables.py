"""Create all database tables for the DRIP Team Portal"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import engine, SessionLocal
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_all_tables():
    """Create all tables in the database"""
    try:
        # Import all models to register them with Base
        from app.models.audit import AuditLog
        from app.models.component import Component
        from app.models.material import Material, MaterialProperty, MaterialPropertyTemplate
        from app.models.resources import PropertyTableTemplate, PropertyTable, SystemConstant, CalculationTemplate
        from app.models.user import User
        from app.models.test import Test, TestResult
        from app.models.property import PropertyDefinition, ComponentProperty, UnitSystem
        
        # Import Base after all models are imported
        from app.models import Base
        
        # Create all tables
        logger.info("Creating all database tables...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("All tables created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False


def main():
    """Main function to create all tables"""
    try:
        # Test database connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
        
        # Create tables
        if not create_all_tables():
            print("Failed to create tables")
            return 1
        
        print("Database initialization completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error during database initialization: {e}")
        return 1


if __name__ == "__main__":
    exit(main())