"""Audit which properties use legacy fields vs ValueNodes.

Run with: PYTHONPATH=. python scripts/audit_legacy_properties.py
"""

import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
# Import all models to ensure relationships are configured
from app.models.values import ValueNode, ValueDependency
from app.models.units import Unit
from app.models.property import ComponentProperty, PropertyDefinition
from app.models.component import Component
from app.models.material import Material, MaterialProperty


def audit_properties():
    db = SessionLocal()

    try:
        total = db.query(ComponentProperty).count()

        with_value_node = db.query(ComponentProperty).filter(
            ComponentProperty.value_node_id.isnot(None)
        ).count()

        legacy_only = total - with_value_node

        print(f"\n=== ComponentProperty Audit ===")
        print(f"Total ComponentProperties: {total}")
        print(f"With ValueNode: {with_value_node} ({with_value_node/total*100:.1f}%)" if total > 0 else "With ValueNode: 0")
        print(f"Legacy only: {legacy_only} ({legacy_only/total*100:.1f}%)" if total > 0 else "Legacy only: 0")

        # Find which ones need migration (have legacy value but no ValueNode)
        legacy_props = db.query(ComponentProperty).filter(
            ComponentProperty.value_node_id.is_(None),
        ).all()

        # Filter to those with actual values
        props_with_values = [
            p for p in legacy_props
            if p.single_value is not None or p.average_value is not None or p.min_value is not None
        ]

        print(f"\nProperties needing migration (have value, no ValueNode): {len(props_with_values)}")

        if props_with_values:
            print("\nFirst 10 properties needing migration:")
            for prop in props_with_values[:10]:
                comp_name = prop.component.name if prop.component else "Unknown"
                prop_name = prop.property_definition.name if prop.property_definition else "Unknown"
                value = prop.single_value or prop.average_value or prop.min_value
                unit = prop.property_definition.unit if prop.property_definition else ""
                print(f"  - {comp_name}.{prop_name}: {value} {unit}")

        # Summary of legacy fields usage
        print("\n=== Legacy Field Usage ===")
        single_count = db.query(ComponentProperty).filter(
            ComponentProperty.single_value.isnot(None)
        ).count()
        average_count = db.query(ComponentProperty).filter(
            ComponentProperty.average_value.isnot(None)
        ).count()
        min_count = db.query(ComponentProperty).filter(
            ComponentProperty.min_value.isnot(None)
        ).count()
        max_count = db.query(ComponentProperty).filter(
            ComponentProperty.max_value.isnot(None)
        ).count()

        print(f"single_value used: {single_count}")
        print(f"average_value used: {average_count}")
        print(f"min_value used: {min_count}")
        print(f"max_value used: {max_count}")

        # Check for properties with both legacy and ValueNode (shouldn't happen)
        both = db.query(ComponentProperty).filter(
            ComponentProperty.value_node_id.isnot(None),
            ComponentProperty.single_value.isnot(None)
        ).count()

        if both > 0:
            print(f"\nWARNING: {both} properties have BOTH value_node_id AND single_value set!")

    finally:
        db.close()


if __name__ == "__main__":
    audit_properties()
