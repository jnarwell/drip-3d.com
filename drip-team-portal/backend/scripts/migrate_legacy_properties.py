"""Migrate legacy ComponentProperty fields to ValueNodes.

This script creates ValueNodes for properties that have legacy values
(single_value, average_value, min_value) but no value_node_id.

Run with:
    PYTHONPATH=. python scripts/migrate_legacy_properties.py           # Dry run
    PYTHONPATH=. python scripts/migrate_legacy_properties.py --execute # Actually migrate
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime
from app.db.database import SessionLocal
# Import all models to ensure relationships are configured
from app.models.values import ValueNode, ValueDependency, NodeType, ComputationStatus
from app.models.units import Unit
from app.models.property import ComponentProperty, PropertyDefinition
from app.models.component import Component
from app.models.material import Material, MaterialProperty


# SI base units for common dimensions
DIMENSION_SI_UNITS = {
    'length': 'm',
    'mass': 'kg',
    'time': 's',
    'pressure': 'Pa',
    'temperature': 'K',
    'force': 'N',
    'energy': 'J',
    'power': 'W',
    'velocity': 'm/s',
    'acceleration': 'm/s²',
    'area': 'm²',
    'volume': 'm³',
    'density': 'kg/m³',
}

# Unit to SI conversion factors
UNIT_TO_SI = {
    # Length
    'nm': 1e-9, 'μm': 1e-6, 'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
    'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.344,
    # Pressure
    'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9,
    'bar': 1e5, 'mbar': 100, 'psi': 6894.76, 'ksi': 6.895e6,
    # Temperature (note: these are scaling factors for differences, not absolute)
    'K': 1, '°C': 1, 'degC': 1,  # Same scale, different offset
    '°F': 5/9, 'degF': 5/9,
    # Energy
    'J': 1, 'kJ': 1000, 'MJ': 1e6, 'cal': 4.184, 'BTU': 1055.06,
    # Power
    'W': 1, 'kW': 1000, 'MW': 1e6, 'hp': 745.7,
    # Force
    'N': 1, 'kN': 1000, 'MN': 1e6, 'lbf': 4.44822,
    # Mass
    'g': 0.001, 'kg': 1, 'mg': 1e-6, 'lb': 0.453592, 'oz': 0.0283495,
}

# Unit to dimension mapping
UNIT_TO_DIMENSION = {
    # Length
    'nm': 'length', 'μm': 'length', 'mm': 'length', 'cm': 'length', 'm': 'length', 'km': 'length',
    'in': 'length', 'ft': 'length', 'yd': 'length', 'mi': 'length',
    # Pressure
    'Pa': 'pressure', 'kPa': 'pressure', 'MPa': 'pressure', 'GPa': 'pressure',
    'bar': 'pressure', 'mbar': 'pressure', 'psi': 'pressure', 'ksi': 'pressure',
    # Temperature
    'K': 'temperature', '°C': 'temperature', 'degC': 'temperature', '°F': 'temperature', 'degF': 'temperature',
    # Energy
    'J': 'energy', 'kJ': 'energy', 'MJ': 'energy', 'cal': 'energy', 'BTU': 'energy',
    # Power
    'W': 'power', 'kW': 'power', 'MW': 'power', 'hp': 'power',
    # Force
    'N': 'force', 'kN': 'force', 'MN': 'force', 'lbf': 'force',
    # Mass
    'g': 'mass', 'kg': 'mass', 'mg': 'mass', 'lb': 'mass', 'oz': 'mass',
}


def migrate_properties(dry_run=True):
    """Migrate legacy ComponentProperty fields to ValueNodes."""
    db = SessionLocal()

    try:
        # Find properties with legacy values but no ValueNode
        legacy_props = db.query(ComponentProperty).filter(
            ComponentProperty.value_node_id.is_(None)
        ).all()

        # Filter to those with actual values
        props_to_migrate = []
        for prop in legacy_props:
            value = prop.single_value or prop.average_value or prop.min_value
            if value is not None:
                props_to_migrate.append(prop)

        print(f"\n=== Migration {'(DRY RUN)' if dry_run else '(EXECUTING)'} ===")
        print(f"Properties to migrate: {len(props_to_migrate)}")

        if not props_to_migrate:
            print("No properties need migration.")
            return

        migrated = 0
        errors = []

        for prop in props_to_migrate:
            try:
                # Get the value from legacy fields
                value = prop.single_value or prop.average_value or prop.min_value

                # Get unit info from property definition
                prop_unit = None
                si_value = value
                si_unit_symbol = None

                if prop.property_definition:
                    prop_unit = prop.property_definition.unit

                    # Convert to SI if we know the unit
                    if prop_unit and prop_unit in UNIT_TO_SI:
                        # Handle temperature offset conversion specially
                        if prop_unit in ('°C', 'degC'):
                            si_value = value + 273.15  # Celsius to Kelvin
                            si_unit_symbol = 'K'
                        elif prop_unit in ('°F', 'degF'):
                            si_value = (value - 32) * 5/9 + 273.15  # Fahrenheit to Kelvin
                            si_unit_symbol = 'K'
                        else:
                            conversion = UNIT_TO_SI[prop_unit]
                            si_value = value * conversion

                            # Get SI unit symbol
                            dimension = UNIT_TO_DIMENSION.get(prop_unit)
                            if dimension:
                                si_unit_symbol = DIMENSION_SI_UNITS.get(dimension)

                # Get description for the ValueNode
                comp_name = prop.component.name if prop.component else "Unknown"
                prop_name = prop.property_definition.name if prop.property_definition else "Unknown"
                description = f"{comp_name}.{prop_name}"

                if dry_run:
                    print(f"  Would migrate: {description} = {value} {prop_unit or ''} -> {si_value} {si_unit_symbol or ''}")
                else:
                    # Create the ValueNode
                    value_node = ValueNode(
                        node_type=NodeType.LITERAL,
                        numeric_value=si_value,
                        computed_value=si_value,
                        computed_unit_symbol=si_unit_symbol,
                        computation_status=ComputationStatus.VALID,
                        description=description,
                        created_at=datetime.utcnow(),
                    )
                    db.add(value_node)
                    db.flush()

                    # Link to ComponentProperty
                    prop.value_node_id = value_node.id

                    print(f"  Migrated: {description} (ValueNode id={value_node.id})")

                migrated += 1

                if migrated % 50 == 0:
                    print(f"  Progress: {migrated}/{len(props_to_migrate)}")

            except Exception as e:
                errors.append((prop.id, str(e)))
                print(f"  ERROR migrating property {prop.id}: {e}")

        if not dry_run:
            db.commit()
            print(f"\nMigration committed successfully!")
        else:
            print(f"\nDRY RUN complete - use --execute to actually migrate")

        print(f"\n=== Summary ===")
        print(f"Migrated: {migrated}")
        print(f"Errors: {len(errors)}")

        if errors:
            print("\nFirst 10 errors:")
            for prop_id, error in errors[:10]:
                print(f"  Property {prop_id}: {error}")

    finally:
        db.close()


if __name__ == "__main__":
    dry_run = "--execute" not in sys.argv

    if dry_run:
        print("DRY RUN MODE - Use --execute to actually migrate")
    else:
        print("EXECUTE MODE - Changes will be committed")
        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("Aborted.")
            sys.exit(0)

    migrate_properties(dry_run=dry_run)
