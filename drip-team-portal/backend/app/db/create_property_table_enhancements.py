"""Create enhanced property table schema with templates and verification"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.models import Base, PropertyTable, PropertyTableTemplate
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_enhanced_tables():
    """Create the enhanced property table schema"""
    try:
        # Import all models to ensure they're registered
        from app.models import (
            PropertyTable, PropertyTableTemplate, SystemConstant, 
            CalculationTemplate, Material, Component
        )
        
        # Create new tables
        logger.info("Creating enhanced property table schema...")
        
        # Create property_table_templates first
        PropertyTableTemplate.__table__.create(bind=engine, checkfirst=True)
        logger.info("Created property_table_templates table")
        
        # Drop existing property_tables if exists and recreate with new schema
        with engine.connect() as conn:
            # Check if table exists
            result = conn.execute(text(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = 'public' AND table_name = 'property_tables')"
            ))
            table_exists = result.scalar()
            
            if table_exists:
                logger.info("Dropping existing property_tables...")
                conn.execute(text("DROP TABLE IF EXISTS property_tables CASCADE"))
                conn.commit()
        
        # Create new property_tables with enhanced schema
        PropertyTable.__table__.create(bind=engine, checkfirst=True)
        logger.info("Created enhanced property_tables table")
        
        logger.info("Enhanced property table schema created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating enhanced tables: {e}")
        return False


def main():
    """Main function to create enhanced tables"""
    if not create_enhanced_tables():
        print("Failed to create enhanced property table schema")
        return 1
    
    print("\nEnhanced property table schema created successfully!")
    print("New features added:")
    print("- Property table templates for reusable structures")
    print("- Import method tracking (document, API, manual)")
    print("- Verification status (verified, cited, unverified)")
    print("- Source attribution and citation tracking")
    print("- Document hash for duplicate detection")
    print("- OCR and quality metadata")
    
    return 0


if __name__ == "__main__":
    exit(main())