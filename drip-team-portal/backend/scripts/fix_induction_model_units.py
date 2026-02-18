"""
Fix Induction frequency-thickness model variable units.

Issue #11: The Induction model uses compound units (Ω·m, H/m) that were not
in the dimensional analysis UNIT_DIMENSIONS dict. This script updates the
model's input variable units to use expanded SI base-unit notation that the
dimensional analysis system can validate.

Usage:
    python -m scripts.fix_induction_model_units
"""

import sys
import os

# Add backend directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.physics_model import PhysicsModel, PhysicsModelVersion


def fix_induction_model_units():
    """Update resistivity and permeability units in the Induction frequency-thickness model."""
    with Session(engine) as session:
        # Find model with name containing "Induction frequency-thickness"
        model = session.query(PhysicsModel).filter(
            PhysicsModel.name.contains("Induction frequency-thickness")
        ).first()

        if not model:
            print("ERROR: Could not find model with name containing 'Induction frequency-thickness'")
            sys.exit(1)

        print(f"Found model: id={model.id}, name='{model.name}'")

        # Get current version
        version = session.query(PhysicsModelVersion).filter(
            PhysicsModelVersion.physics_model_id == model.id,
            PhysicsModelVersion.is_current == True,
        ).first()

        if not version:
            print("ERROR: No current version found for this model")
            sys.exit(1)

        print(f"Current version: id={version.id}, version={version.version}")

        inputs = version.inputs
        if not inputs:
            print("ERROR: Version has no inputs defined")
            sys.exit(1)

        changes = []

        for inp in inputs:
            if inp.get("name") == "resistivity":
                old_unit = inp.get("unit")
                inp["unit"] = "kg*m^3/(A^2*s^3)"
                changes.append(f"  resistivity: '{old_unit}' -> 'kg*m^3/(A^2*s^3)'")

            elif inp.get("name") == "permeability":
                old_unit = inp.get("unit")
                inp["unit"] = "kg*m/(A^2*s^2)"
                changes.append(f"  permeability: '{old_unit}' -> 'kg*m/(A^2*s^2)'")

        if not changes:
            print("WARNING: No 'resistivity' or 'permeability' variables found in model inputs")
            sys.exit(1)

        # Write back the modified inputs
        version.inputs = inputs
        session.commit()

        print("Updated units:")
        for change in changes:
            print(change)
        print("Done.")


if __name__ == "__main__":
    fix_induction_model_units()
