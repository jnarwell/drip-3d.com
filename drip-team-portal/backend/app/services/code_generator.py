"""
Code Generator - Auto-generates unique codes for Components and Materials

Codes are used in formula references like: #HEATBED_001.thermal_conductivity

Code format: UPPER_SNAKE_CASE_NNN (e.g., HEATBED_001, SS_304_001)
"""

import re
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.component import Component
from app.models.material import Material


def name_to_base_code(name: str) -> str:
    """
    Convert a name to a base code (without number suffix).

    Examples:
        "Heatbed" -> "HEATBED"
        "Cartridge Heater" -> "CARTRIDGE_HEATER"
        "SS 304" -> "SS_304"
        "Al-6061-T6" -> "AL_6061_T6"
    """
    # Convert to uppercase
    code = name.upper()

    # Replace common separators with underscore
    code = re.sub(r'[\s\-\.]+', '_', code)

    # Remove any characters that aren't alphanumeric or underscore
    code = re.sub(r'[^A-Z0-9_]', '', code)

    # Remove leading/trailing underscores
    code = code.strip('_')

    # Collapse multiple underscores
    code = re.sub(r'_+', '_', code)

    return code


def generate_component_code(db: Session, name: str, custom_code: Optional[str] = None) -> str:
    """
    Generate a unique code for a Component.

    If custom_code is provided and unique, use it.
    Otherwise, generate from name with auto-incrementing suffix.

    Args:
        db: Database session
        name: Component name
        custom_code: Optional user-provided code

    Returns:
        Unique code string
    """
    if custom_code:
        # Validate and normalize custom code
        normalized = name_to_base_code(custom_code)
        if normalized:
            # Check if it's unique
            existing = db.query(Component).filter(Component.code == normalized).first()
            if not existing:
                return normalized
            # If not unique, fall through to auto-generation with custom as base

    # Generate base code from name
    base_code = name_to_base_code(name)
    if not base_code:
        base_code = "COMPONENT"

    # Find the highest existing number for this base code
    pattern = f"{base_code}_%"
    existing_codes = db.query(Component.code).filter(
        Component.code.like(pattern)
    ).all()

    # Extract numbers and find max
    max_num = 0
    for (code,) in existing_codes:
        if code:
            match = re.match(rf'{re.escape(base_code)}_(\d+)$', code)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    # Also check if base code without number exists
    exact_match = db.query(Component).filter(Component.code == base_code).first()
    if exact_match:
        max_num = max(max_num, 0)  # Ensure we start numbering

    # Generate new code with next number
    new_num = max_num + 1
    return f"{base_code}_{new_num:03d}"


def generate_material_code(db: Session, name: str, custom_code: Optional[str] = None) -> str:
    """
    Generate a unique code for a Material.

    If custom_code is provided and unique, use it.
    Otherwise, generate from name with auto-incrementing suffix.

    Args:
        db: Database session
        name: Material name
        custom_code: Optional user-provided code

    Returns:
        Unique code string
    """
    if custom_code:
        # Validate and normalize custom code
        normalized = name_to_base_code(custom_code)
        if normalized:
            # Check if it's unique (across both components and materials)
            existing_mat = db.query(Material).filter(Material.code == normalized).first()
            existing_comp = db.query(Component).filter(Component.code == normalized).first()
            if not existing_mat and not existing_comp:
                return normalized

    # Generate base code from name
    base_code = name_to_base_code(name)
    if not base_code:
        base_code = "MATERIAL"

    # Find the highest existing number for this base code
    pattern = f"{base_code}_%"
    existing_codes = db.query(Material.code).filter(
        Material.code.like(pattern)
    ).all()

    # Extract numbers and find max
    max_num = 0
    for (code,) in existing_codes:
        if code:
            match = re.match(rf'{re.escape(base_code)}_(\d+)$', code)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    # Also check if base code without number exists
    exact_match = db.query(Material).filter(Material.code == base_code).first()
    if exact_match:
        max_num = max(max_num, 0)

    # Generate new code with next number
    new_num = max_num + 1
    return f"{base_code}_{new_num:03d}"


def validate_code_unique(db: Session, code: str, exclude_component_id: Optional[int] = None, exclude_material_id: Optional[int] = None) -> bool:
    """
    Check if a code is unique across Components and Materials.

    Args:
        db: Database session
        code: Code to check
        exclude_component_id: Component ID to exclude (for updates)
        exclude_material_id: Material ID to exclude (for updates)

    Returns:
        True if unique, False otherwise
    """
    # Check Components
    comp_query = db.query(Component).filter(Component.code == code)
    if exclude_component_id:
        comp_query = comp_query.filter(Component.id != exclude_component_id)
    if comp_query.first():
        return False

    # Check Materials
    mat_query = db.query(Material).filter(Material.code == code)
    if exclude_material_id:
        mat_query = mat_query.filter(Material.id != exclude_material_id)
    if mat_query.first():
        return False

    return True
