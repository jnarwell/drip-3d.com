"""
Search API for expression autocomplete.

Provides endpoints for searching:
- Entities (components, materials) by code OR name
- Properties for a specific entity
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
import logging
import re

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.component import Component
from app.models.material import Material
from app.models.property import PropertyDefinition, ComponentProperty

router = APIRouter(prefix="/api/v1/search")
logger = logging.getLogger(__name__)


def generate_code_from_name(name: str) -> str:
    """Generate a code from entity name if no code exists (Python version for results)."""
    code = re.sub(r'[^a-zA-Z0-9]', '_', name.upper())
    code = re.sub(r'_+', '_', code)
    code = code.strip('_')
    return code


def get_generated_code_sql(name_column):
    """Get SQL expression for generating code from name column (PostgreSQL)."""
    return func.trim(
        func.regexp_replace(
            func.regexp_replace(
                func.upper(name_column),
                '[^a-zA-Z0-9]', '_', 'g'
            ),
            '_+', '_', 'g'
        ),
        '_'
    )


@router.get("/entities")
async def search_entities(
    q: str = Query("", description="Search query for entity code or name"),
    limit: int = Query(10, description="Max results to return"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for components and materials by code OR name.

    Used for autocomplete when user types `#` in expression input.
    Returns entity codes that match the query.
    If an entity doesn't have a code, generates one from the name.
    """
    results = []
    query_upper = q.upper()
    query_lower = q.lower()

    # Search components by code, name, OR generated code
    components = db.query(Component).filter(
        or_(
            Component.code.ilike(f"%{q}%"),
            Component.name.ilike(f"%{q}%"),
            get_generated_code_sql(Component.name).ilike(f"%{q}%")
        )
    ).limit(limit).all()

    for comp in components:
        # Use existing code or generate from name
        code = comp.code if comp.code else generate_code_from_name(comp.name)
        results.append({
            "code": code,
            "name": comp.name,
            "type": "component",
            "category": comp.category.value if comp.category else None
        })

    # Search materials by code, name, OR generated code
    materials = db.query(Material).filter(
        or_(
            Material.code.ilike(f"%{q}%"),
            Material.name.ilike(f"%{q}%"),
            get_generated_code_sql(Material.name).ilike(f"%{q}%")
        )
    ).limit(limit).all()

    for mat in materials:
        # Use existing code or generate from name
        code = mat.code if mat.code else generate_code_from_name(mat.name)
        results.append({
            "code": code,
            "name": mat.name,
            "type": "material",
            "category": mat.category
        })

    # Sort by relevance (exact prefix match first, then code match, then name match)
    def sort_key(x):
        code_upper = x["code"].upper()
        name_upper = x["name"].upper()
        # Exact prefix match on code
        if code_upper.startswith(query_upper):
            return (0, code_upper)
        # Exact prefix match on name
        if name_upper.startswith(query_upper):
            return (1, code_upper)
        # Contains in code
        if query_upper in code_upper:
            return (2, code_upper)
        # Contains in name
        return (3, code_upper)

    results.sort(key=sort_key)

    return results[:limit]


@router.get("/entities/{entity_code}/properties")
async def get_entity_properties(
    entity_code: str,
    q: str = Query("", description="Search query for property name"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get available properties for an entity.

    Used for autocomplete when user types `#CODE.` in expression input.
    Returns property names that have values on this entity.

    Looks up entity by code, or by generated code from name.
    """
    results = []
    query = q.lower()

    # Try component by code first
    component = db.query(Component).filter(Component.code == entity_code).first()

    # If not found, try by generated code from name using SQL
    if not component:
        component = db.query(Component).filter(
            get_generated_code_sql(Component.name) == entity_code
        ).first()

    if component:
        # Get properties that have values
        comp_props = db.query(ComponentProperty).filter(
            ComponentProperty.component_id == component.id
        ).all()

        for prop in comp_props:
            prop_def = prop.property_definition
            if prop_def and (not query or query in prop_def.name.lower()):
                results.append({
                    "name": prop_def.name,
                    "unit": prop_def.unit,
                    "type": prop_def.property_type.value if prop_def.property_type else None,
                    "has_value": prop.value_node_id is not None or prop.single_value is not None
                })

        return results

    # Try material by code
    material = db.query(Material).filter(Material.code == entity_code).first()

    # If not found, try by generated code from name using SQL
    if not material:
        material = db.query(Material).filter(
            get_generated_code_sql(Material.name) == entity_code
        ).first()

    if material:
        from app.models.material import MaterialProperty
        mat_props = db.query(MaterialProperty).filter(
            MaterialProperty.material_id == material.id
        ).all()

        for prop in mat_props:
            prop_def = prop.property_definition
            if prop_def and (not query or query in prop_def.name.lower()):
                results.append({
                    "name": prop_def.name,
                    "unit": prop_def.unit,
                    "type": prop_def.property_type.value if prop_def.property_type else None,
                    "has_value": prop.value_node_id is not None or prop.value is not None
                })

        return results

    # Entity not found - return all property definitions as suggestions
    all_props = db.query(PropertyDefinition).filter(
        PropertyDefinition.name.ilike(f"%{query}%")
    ).limit(20).all()

    for prop_def in all_props:
        results.append({
            "name": prop_def.name,
            "unit": prop_def.unit,
            "type": prop_def.property_type.value if prop_def.property_type else None,
            "has_value": False
        })

    return results
