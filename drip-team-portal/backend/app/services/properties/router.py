"""LOOKUP router - dispatches lookups to appropriate backend based on source type."""

from typing import Dict, Any, Union

from .registry import get_source
from .schemas import PropertySource
from .backends.table import resolve_table, TableLookupError
from .backends.equation import resolve_equation, EquationError
from .backends.coolprop import resolve_coolprop, CoolPropError


class LookupError(Exception):
    """Error during property lookup."""
    pass


def lookup(
    source_id: str,
    output_name: str,
    **inputs
) -> float:
    """
    Look up a property value from a source.

    This is the main entry point for the properties API.

    Args:
        source_id: ID of the property source (e.g., "steam", "aisc_w_shapes")
        output_name: Name of the output property (e.g., "h", "Ix")
        **inputs: Input values as keyword arguments (e.g., T=300, P=101325)

    Returns:
        The property value as a float

    Raises:
        LookupError: If the lookup fails

    Examples:
        >>> lookup("steam", "h", T=373.15, P=101325)
        2675500.0

        >>> lookup("aisc_w_shapes", "Ix", designation="W14X90")
        999.0

        >>> lookup("al_6061_t6", "Sy", T=373.15)
        250000000.0
    """
    # Get the source definition
    try:
        source = get_source(source_id)
    except Exception as e:
        raise LookupError(f"Unknown property source: '{source_id}'")

    # Validate and normalize inputs (e.g., case-insensitive matching)
    normalized_inputs = _validate_inputs(source, inputs)

    # Validate output
    output_names = [o.name for o in source.outputs]
    if output_name not in output_names:
        raise LookupError(
            f"Unknown output '{output_name}' for source '{source_id}'. "
            f"Available outputs: {output_names}"
        )

    # Route to appropriate backend with normalized inputs
    try:
        if source.type == "table":
            return resolve_table(source, output_name, normalized_inputs)
        elif source.type == "equation":
            return resolve_equation(source, output_name, normalized_inputs)
        elif source.type == "library":
            return resolve_coolprop(source, output_name, normalized_inputs)
        else:
            raise LookupError(f"Unknown source type: {source.type}")

    except (TableLookupError, EquationError, CoolPropError) as e:
        raise LookupError(str(e))
    except Exception as e:
        raise LookupError(f"Lookup failed: {str(e)}")


def _validate_inputs(source: PropertySource, inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Validate that all required inputs are provided and within range.

    Returns normalized inputs (e.g., case-corrected discrete values).
    """
    normalized = dict(inputs)

    for input_def in source.inputs:
        name = input_def.name

        # Check required inputs (skip optional ones)
        if name not in inputs:
            if input_def.optional:
                continue
            raise LookupError(f"Missing required input: '{name}'")

        value = inputs[name]

        # Validate discrete inputs
        if input_def.type == "discrete":
            if input_def.values:
                # Case-insensitive matching for string values
                if isinstance(value, str):
                    value_lower = value.lower()
                    matched = None
                    for v in input_def.values:
                        if isinstance(v, str) and v.lower() == value_lower:
                            matched = v
                            break
                    if matched is not None:
                        normalized[name] = matched  # Use canonical case
                    else:
                        raise LookupError(
                            f"Invalid value for '{name}': '{value}'. "
                            f"Must be one of: {input_def.values[:10]}{'...' if len(input_def.values) > 10 else ''}"
                        )
                elif value not in input_def.values:
                    raise LookupError(
                        f"Invalid value for '{name}': '{value}'. "
                        f"Must be one of: {input_def.values[:10]}{'...' if len(input_def.values) > 10 else ''}"
                    )

        # Validate continuous inputs
        else:
            try:
                float_value = float(value)
            except (TypeError, ValueError):
                raise LookupError(
                    f"Input '{name}' must be numeric, got: {type(value).__name__}"
                )

            if input_def.range:
                min_val, max_val = input_def.range
                if float_value < min_val or float_value > max_val:
                    if input_def.extrap == "error":
                        raise LookupError(
                            f"Input '{name}'={float_value} outside valid range "
                            f"[{min_val}, {max_val}]"
                        )

    return normalized


# Alias for the lookup function (capital case for formula compatibility)
LOOKUP = lookup


def get_available_outputs(source_id: str) -> list:
    """Get list of available outputs for a source."""
    source = get_source(source_id)
    return [
        {
            'name': o.name,
            'unit': o.unit,
            'description': o.description
        }
        for o in source.outputs
    ]


def get_required_inputs(source_id: str) -> list:
    """Get list of required inputs for a source."""
    source = get_source(source_id)
    return [
        {
            'name': i.name,
            'unit': i.unit,
            'type': i.type,
            'description': i.description,
            'range': i.range,
            'values': i.values[:20] if i.values and len(i.values) > 20 else i.values
        }
        for i in source.inputs
    ]
