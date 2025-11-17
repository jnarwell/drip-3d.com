"""Seed the database with system constants"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.resources import SystemConstant
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define constants to seed
CONSTANTS = [
    # Physics Constants
    {
        "symbol": "g",
        "name": "Gravitational Acceleration",
        "value": 9.80665,
        "unit": "m/s²",
        "description": "Standard gravity at Earth's surface",
        "category": "Physics"
    },
    {
        "symbol": "c",
        "name": "Speed of Light",
        "value": 299792458,
        "unit": "m/s",
        "description": "Speed of light in vacuum",
        "category": "Physics"
    },
    {
        "symbol": "sigma",
        "name": "Stefan-Boltzmann Constant",
        "value": 5.670374419e-8,
        "unit": "W/(m²·K⁴)",
        "description": "Radiation heat transfer constant",
        "category": "Physics"
    },
    {
        "symbol": "h_planck",
        "name": "Planck Constant",
        "value": 6.62607015e-34,
        "unit": "J·s",
        "description": "Quantum of electromagnetic action",
        "category": "Physics"
    },
    {
        "symbol": "k_B",
        "name": "Boltzmann Constant",
        "value": 1.380649e-23,
        "unit": "J/K",
        "description": "Relates temperature to energy",
        "category": "Physics"
    },
    {
        "symbol": "epsilon_0",
        "name": "Vacuum Permittivity",
        "value": 8.8541878128e-12,
        "unit": "F/m",
        "description": "Electric constant",
        "category": "Physics"
    },
    {
        "symbol": "mu_0",
        "name": "Vacuum Permeability",
        "value": 1.25663706212e-6,
        "unit": "H/m",
        "description": "Magnetic constant",
        "category": "Physics"
    },
    {
        "symbol": "G",
        "name": "Gravitational Constant",
        "value": 6.67430e-11,
        "unit": "m³/(kg·s²)",
        "description": "Universal gravitational constant",
        "category": "Physics"
    },
    
    # Chemistry Constants
    {
        "symbol": "R",
        "name": "Universal Gas Constant",
        "value": 8.314462618,
        "unit": "J/(mol·K)",
        "description": "Gas constant",
        "category": "Chemistry"
    },
    {
        "symbol": "N_A",
        "name": "Avogadro's Number",
        "value": 6.02214076e23,
        "unit": "1/mol",
        "description": "Number of particles per mole",
        "category": "Chemistry"
    },
    {
        "symbol": "F",
        "name": "Faraday Constant",
        "value": 96485.33212,
        "unit": "C/mol",
        "description": "Charge per mole of electrons",
        "category": "Chemistry"
    },
    {
        "symbol": "R_specific_air",
        "name": "Specific Gas Constant (Air)",
        "value": 287.05,
        "unit": "J/(kg·K)",
        "description": "Gas constant for dry air",
        "category": "Chemistry"
    },
    
    # Engineering Constants
    {
        "symbol": "T_stp",
        "name": "STP Temperature",
        "value": 273.15,
        "unit": "K",
        "description": "Standard temperature (0°C)",
        "category": "Engineering"
    },
    {
        "symbol": "P_stp",
        "name": "STP Pressure",
        "value": 101325,
        "unit": "Pa",
        "description": "Standard pressure (1 atm)",
        "category": "Engineering"
    }
]


def seed_constants(db: Session):
    """Seed system constants into the database"""
    logger.info("Starting to seed system constants...")
    
    added = 0
    skipped = 0
    
    for const_data in CONSTANTS:
        # Check if constant already exists
        existing = db.query(SystemConstant).filter(
            SystemConstant.symbol == const_data["symbol"]
        ).first()
        
        if existing:
            logger.info(f"Constant '{const_data['symbol']}' already exists, skipping")
            skipped += 1
            continue
        
        # Create new constant
        constant = SystemConstant(
            **const_data,
            is_editable=False,
            created_by="system"
        )
        db.add(constant)
        added += 1
        logger.info(f"Added constant '{const_data['symbol']}' ({const_data['name']})")
    
    db.commit()
    logger.info(f"Seeding complete! Added: {added}, Skipped: {skipped}")
    return added, skipped


def main():
    """Main function to run the seeding"""
    db = SessionLocal()
    try:
        added, skipped = seed_constants(db)
        print(f"\nSeeding completed successfully!")
        print(f"  - Added: {added} constants")
        print(f"  - Skipped: {skipped} constants (already existed)")
    except Exception as e:
        logger.error(f"Error seeding constants: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()