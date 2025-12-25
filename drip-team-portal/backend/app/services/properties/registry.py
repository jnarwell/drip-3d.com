"""Registry for loading and managing PropertySource definitions from YAML files."""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml

from .schemas import PropertySource, ViewConfig, GridSpec, ColumnDef


class RegistryError(Exception):
    """Error in property source registry."""
    pass


# Global registry of loaded sources
_sources: Dict[str, PropertySource] = {}
_loaded = False


def _get_data_dir() -> Path:
    """Get the path to the data directory."""
    # Relative to this file: backend/app/services/properties/registry.py
    # Data is at: backend/data/
    current_file = Path(__file__)
    backend_dir = current_file.parent.parent.parent.parent
    return backend_dir / "data"


def _load_yaml_file(file_path: Path) -> Optional[dict]:
    """Load a single YAML file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"Warning: Failed to load {file_path}: {e}")
        return None


def _parse_source(data: dict, file_path: Path) -> Optional[PropertySource]:
    """Parse a YAML dict into a PropertySource."""
    try:
        return PropertySource(**data)
    except Exception as e:
        print(f"Warning: Failed to parse {file_path}: {e}")
        return None


def load_all_sources(force_reload: bool = False) -> Dict[str, PropertySource]:
    """
    Load all PropertySource definitions from the data directory.

    Scans all subdirectories for .yaml files and loads them.
    """
    global _sources, _loaded

    if _loaded and not force_reload:
        return _sources

    _sources = {}
    data_dir = _get_data_dir()

    if not data_dir.exists():
        print(f"Warning: Data directory not found: {data_dir}")
        _loaded = True
        return _sources

    # Scan all subdirectories
    for yaml_file in data_dir.rglob("*.yaml"):
        data = _load_yaml_file(yaml_file)
        if data:
            source = _parse_source(data, yaml_file)
            if source:
                if source.id in _sources:
                    print(f"Warning: Duplicate source ID '{source.id}' in {yaml_file}")
                _sources[source.id] = source

    # Also load .yml files
    for yaml_file in data_dir.rglob("*.yml"):
        data = _load_yaml_file(yaml_file)
        if data:
            source = _parse_source(data, yaml_file)
            if source:
                if source.id in _sources:
                    print(f"Warning: Duplicate source ID '{source.id}' in {yaml_file}")
                _sources[source.id] = source

    _loaded = True
    print(f"Loaded {len(_sources)} property sources from {data_dir}")
    return _sources


def get_source(source_id: str) -> PropertySource:
    """Get a PropertySource by ID."""
    load_all_sources()

    if source_id not in _sources:
        raise RegistryError(f"Unknown property source: '{source_id}'")

    return _sources[source_id]


def list_sources(include_no_views: bool = False) -> List[dict]:
    """List all available property sources with summary info.

    Args:
        include_no_views: If True, include sources with no views (LOOKUP-only sources)
    """
    load_all_sources()

    result = []
    for s in _sources.values():
        # Skip sources with no views unless explicitly requested
        if not s.views and not include_no_views:
            continue

        # Count columns from default view (more accurate than output count)
        default_view = next((v for v in s.views if v.id == "default"), s.views[0] if s.views else None)
        column_count = len(default_view.columns) if default_view else len(s.outputs)

        # If source has a lookup_source_id, get inputs from that source instead
        lookup_source = None
        if s.lookup_source_id and s.lookup_source_id in _sources:
            lookup_source = _sources[s.lookup_source_id]

        inputs_source = lookup_source if lookup_source else s

        result.append({
            'id': s.id,
            'name': s.name,
            'category': s.category,
            'description': s.description,
            'type': s.type,
            'source': s.source,
            'inputs': [{'name': i.name, 'unit': i.unit, 'type': i.type, 'optional': i.optional} for i in inputs_source.inputs],
            'outputs': [{'name': o.name, 'unit': o.unit} for o in s.outputs],
            'view_count': len(s.views),
            'column_count': column_count,
            'lookup_source_id': s.lookup_source_id,
        })
    return result


def list_views(source_id: str) -> List[dict]:
    """List available views for a property source."""
    source = get_source(source_id)

    return [
        {
            'id': v.id,
            'name': v.name,
            'description': v.description,
            'layout': v.layout,
            'column_count': len(v.columns)
        }
        for v in source.views
    ]


def generate_view(source_id: str, view_id: str) -> dict:
    """
    Generate a table view for display.

    Returns a structured table with headers and rows.
    """
    from .router import lookup

    source = get_source(source_id)

    # Find the view
    view = next((v for v in source.views if v.id == view_id), None)

    # If "default" was requested and not found, use the first available view
    if not view and view_id == "default" and source.views:
        view = source.views[0]

    if not view:
        raise RegistryError(f"View '{view_id}' not found in source '{source_id}'")

    # Build grid points
    grid_points = {}
    for input_name, grid_spec in view.grid.items():
        if grid_spec.type == "list" and grid_spec.values:
            grid_points[input_name] = grid_spec.values
        elif grid_spec.type == "range":
            start = grid_spec.start or 0
            end = grid_spec.end or 100
            step = grid_spec.step or 10
            grid_points[input_name] = list(_frange(start, end, step))
        elif grid_spec.type == "computed":
            # Computed grids are handled per-row in nested layouts
            grid_points[input_name] = None
        else:
            grid_points[input_name] = grid_spec.values or []

    # Build headers - first add input columns, then output columns
    headers = []

    # Add headers for input columns (from grid)
    for input_name, grid_spec in view.grid.items():
        # Get unit from grid spec or from source input definition
        input_unit = grid_spec.unit or ''
        if not input_unit:
            input_def = next((i for i in source.inputs if i.name == input_name), None)
            if input_def and input_def.unit != 'none':
                input_unit = input_def.unit

        # Format label (replace underscores, title case)
        label = input_name.replace('_', ' ').title()

        headers.append({
            'key': input_name,
            'label': label,
            'unit': input_unit,
            'subscript': None,
            'is_input': True
        })

    # Add headers for output columns
    for col in view.columns:
        # Build key to match row value keys (include phase suffix if present)
        key = col.output or col.computed or col.header
        if col.phase:
            key = f"{key}_{col.phase}"
        headers.append({
            'key': key,
            'label': col.header,
            'unit': col.unit or '',
            'subscript': col.subscript,
            'is_input': False
        })

    # Generate rows
    rows = []

    if view.layout == "flat":
        # Single-level iteration
        input_names = list(grid_points.keys())
        if len(input_names) == 1:
            # Single input grid
            input_name = input_names[0]
            for val in grid_points[input_name]:
                row_values = _generate_row_values(
                    source, view, {input_name: val}, lookup
                )
                rows.append({'values': row_values})

        elif len(input_names) == 2:
            # Two input grids - iterate over both
            name1, name2 = input_names
            for val1 in grid_points[name1]:
                for val2 in grid_points[name2]:
                    row_values = _generate_row_values(
                        source, view, {name1: val1, name2: val2}, lookup
                    )
                    rows.append({'values': row_values})

    elif view.layout == "nested":
        # Nested layout - outer input becomes sections
        input_names = list(grid_points.keys())
        if len(input_names) >= 1:
            outer_name = input_names[0]
            inner_name = input_names[1] if len(input_names) > 1 else None

            for outer_val in grid_points[outer_name]:
                section = {
                    'label': outer_name,
                    'value': outer_val,
                    'unit': view.grid[outer_name].unit or ''
                }

                if inner_name:
                    inner_values = grid_points[inner_name] or []
                    for inner_val in inner_values:
                        row_values = _generate_row_values(
                            source, view,
                            {outer_name: outer_val, inner_name: inner_val},
                            lookup
                        )
                        rows.append({'section': section, 'values': row_values})
                else:
                    row_values = _generate_row_values(
                        source, view, {outer_name: outer_val}, lookup
                    )
                    rows.append({'section': section, 'values': row_values})

    return {
        'metadata': {
            'source_id': source_id,
            'source_name': source.name,
            'view_id': view_id,
            'view_name': view.name,
        },
        'headers': headers,
        'rows': rows
    }


def _generate_row_values(
    source: PropertySource,
    view: ViewConfig,
    inputs: dict,
    lookup_fn
) -> dict:
    """Generate values for a single row."""
    values = {}

    # Add input values to row (with display unit conversion)
    for name, val in inputs.items():
        display_val = val
        # Check if grid specifies a display unit different from input's base unit
        if name in view.grid:
            grid_spec = view.grid[name]
            if grid_spec.unit:
                input_def = next((i for i in source.inputs if i.name == name), None)
                if input_def and input_def.unit != grid_spec.unit:
                    # Convert from SI to display unit
                    conversion_key = (input_def.unit, grid_spec.unit)
                    if conversion_key in _UNIT_CONVERSIONS:
                        display_val = val * _UNIT_CONVERSIONS[conversion_key]
        values[name] = display_val

    # Apply constraints
    all_inputs = {**inputs}
    for name, val in view.constraints.items():
        all_inputs[name] = val

    for col in view.columns:
        if col.output:
            # Direct output lookup
            try:
                # Handle phase-specific lookups
                if col.phase:
                    phase_inputs = {**all_inputs}
                    phase_inputs['Q'] = 0.0 if col.phase == "liquid" else 1.0
                    value = lookup_fn(source.id, col.output, **phase_inputs)
                else:
                    value = lookup_fn(source.id, col.output, **all_inputs)

                # Apply unit conversion if column specifies a different unit
                if col.unit and value is not None:
                    value = _convert_display_unit(value, col.output, col.unit, source)

                values[col.output + ('_' + col.phase if col.phase else '')] = value
            except Exception as e:
                values[col.output + ('_' + col.phase if col.phase else '')] = None

        elif col.computed:
            # Computed column - need to evaluate expression
            # For now, skip computed columns (need more implementation)
            values[col.header] = None

    return values


def _frange(start: float, end: float, step: float):
    """Float range generator."""
    current = start
    while current <= end:
        yield current
        current += step


# Unit conversion factors: (from_unit, to_unit) -> multiplier
# Values in SI base units are multiplied by this factor to get display units
_UNIT_CONVERSIONS = {
    # Energy
    ('J', 'kJ'): 0.001,
    ('J', 'MJ'): 0.000001,
    ('kJ', 'J'): 1000,
    ('MJ', 'J'): 1000000,
    # Specific energy (enthalpy, internal energy)
    ('J/kg', 'kJ/kg'): 0.001,
    ('J/kg', 'MJ/kg'): 0.000001,
    ('kJ/kg', 'J/kg'): 1000,
    # Specific entropy / specific heat
    ('J/(kg·K)', 'kJ/(kg·K)'): 0.001,
    ('kJ/(kg·K)', 'J/(kg·K)'): 1000,
    # Pressure
    ('Pa', 'kPa'): 0.001,
    ('Pa', 'MPa'): 0.000001,
    ('Pa', 'bar'): 0.00001,
    ('kPa', 'Pa'): 1000,
    ('MPa', 'Pa'): 1000000,
    ('bar', 'Pa'): 100000,
    # Volume
    ('m³', 'L'): 1000,
    ('L', 'm³'): 0.001,
    ('m³/kg', 'L/kg'): 1000,
    ('L/kg', 'm³/kg'): 0.001,
    # Density
    ('kg/m³', 'g/cm³'): 0.001,
    ('g/cm³', 'kg/m³'): 1000,
    # Temperature (note: offset conversions not handled here)
    # Length
    ('m', 'mm'): 1000,
    ('m', 'cm'): 100,
    ('mm', 'm'): 0.001,
    ('cm', 'm'): 0.01,
    # Power
    ('W', 'kW'): 0.001,
    ('W', 'MW'): 0.000001,
    ('kW', 'W'): 1000,
    ('MW', 'W'): 1000000,
}


def _convert_display_unit(
    value: float,
    output_name: str,
    display_unit: str,
    source: PropertySource
) -> float:
    """
    Convert a value from SI base unit to display unit.

    Uses simple multiplier conversions for common engineering prefixes.
    This is for display purposes only - the formula system uses UnitEngine
    for full dimensional analysis.
    """
    if value is None:
        return None

    # Get the SI unit from the source output definition
    output_def = next((o for o in source.outputs if o.name == output_name), None)
    if not output_def:
        return value

    si_unit = output_def.unit
    if si_unit == display_unit:
        return value

    # Look up conversion
    conversion_key = (si_unit, display_unit)
    if conversion_key in _UNIT_CONVERSIONS:
        return value * _UNIT_CONVERSIONS[conversion_key]

    # No conversion found - return as-is with warning
    # In production, might want to log this
    return value


def reload_sources():
    """Force reload all sources from disk."""
    global _loaded
    _loaded = False
    load_all_sources(force_reload=True)
