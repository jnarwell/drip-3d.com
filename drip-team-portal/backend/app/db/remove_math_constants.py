"""Remove mathematical constants that are already available in programming languages"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.resources import SystemConstant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Math constants to remove
MATH_CONSTANTS_TO_REMOVE = ["PI", "e", "phi", "sqrt2"]

def remove_math_constants(db: Session):
    """Remove mathematical constants from the database"""
    try:
        # Find and delete math constants
        deleted_count = 0
        for symbol in MATH_CONSTANTS_TO_REMOVE:
            constant = db.query(SystemConstant).filter(SystemConstant.symbol == symbol).first()
            if constant:
                db.delete(constant)
                deleted_count += 1
                logger.info(f"Deleted constant: {symbol}")
            else:
                logger.info(f"Constant not found: {symbol}")
        
        db.commit()
        logger.info(f"Successfully removed {deleted_count} mathematical constants")
        return deleted_count
        
    except Exception as e:
        logger.error(f"Error removing constants: {e}")
        db.rollback()
        raise

def main():
    db = SessionLocal()
    try:
        deleted = remove_math_constants(db)
        print(f"\nSuccessfully removed {deleted} mathematical constants")
    except Exception as e:
        print(f"Error: {e}")
        return 1
    finally:
        db.close()
    return 0

if __name__ == "__main__":
    exit(main())