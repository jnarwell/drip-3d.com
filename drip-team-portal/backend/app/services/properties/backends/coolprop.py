"""CoolProp backend - thermodynamic property lookups via CoolProp library."""

from typing import Dict, Any
import re

from ..schemas import PropertySource


class CoolPropError(Exception):
    """Error during CoolProp lookup."""
    pass


# Lazy import CoolProp to avoid import errors if not installed
_coolprop = None


def _get_coolprop():
    """Lazy load CoolProp."""
    global _coolprop
    if _coolprop is None:
        try:
            import CoolProp.CoolProp as CP
            _coolprop = CP
        except ImportError:
            raise CoolPropError(
                "CoolProp is not installed. Install with: pip install CoolProp"
            )
    return _coolprop


def resolve_coolprop(
    source: PropertySource,
    output_name: str,
    inputs: Dict[str, Any]
) -> float:
    """
    Resolve a CoolProp-based lookup.

    CoolProp uses pairs of inputs to define state:
    - T, P (temperature, pressure)
    - T, Q (temperature, quality - for saturation)
    - P, Q (pressure, quality - for saturation)
    - P, H (pressure, enthalpy)
    - etc.

    Example CoolProp call:
        CP.PropsSI('H', 'T', 300, 'P', 101325, 'Water')
        -> Returns enthalpy in J/kg
    """
    CP = _get_coolprop()

    resolution = source.resolution
    fluid = resolution.fluid
    output_mapping = resolution.output_mapping
    input_mapping = resolution.input_mapping

    if not fluid:
        raise CoolPropError("No fluid specified in library resolution")

    # Map our output name to CoolProp output key
    cp_output = output_mapping.get(output_name, output_name.upper())

    # Check for computed outputs like "1/D" (specific volume from density)
    if '/' in cp_output:
        parts = cp_output.split('/')
        if len(parts) == 2 and parts[0].strip() == '1':
            # It's a reciprocal: 1/D means specific volume = 1/density
            base_output = parts[1].strip()
            base_value = _call_coolprop(CP, base_output, inputs, input_mapping, fluid)
            if base_value == 0:
                raise CoolPropError(f"Cannot compute 1/{base_output}: division by zero")
            return 1.0 / base_value

    return _call_coolprop(CP, cp_output, inputs, input_mapping, fluid)


def _call_coolprop(
    CP,
    output_key: str,
    inputs: Dict[str, Any],
    input_mapping: Dict[str, str],
    fluid: str
) -> float:
    """Make the actual CoolProp PropsSI call."""

    # CoolProp.PropsSI requires exactly 2 input pairs
    # Common pairs: (T, P), (T, Q), (P, Q), (P, H), etc.
    # Q is vapor quality (0=liquid, 1=vapor) - only valid at saturation

    # Select the appropriate 2 inputs based on what's provided
    available_inputs = set(inputs.keys())

    # Priority order for input pair selection:
    # 1. T + P (most common for single-phase)
    # 2. T + Q (saturation at given T)
    # 3. P + Q (saturation at given P)
    # 4. P + H (pressure + enthalpy)
    # 5. First two available inputs

    if 'T' in available_inputs and 'P' in available_inputs and 'Q' not in available_inputs:
        selected = ['T', 'P']
    elif 'T' in available_inputs and 'Q' in available_inputs:
        selected = ['T', 'Q']
    elif 'P' in available_inputs and 'Q' in available_inputs:
        selected = ['P', 'Q']
    elif 'P' in available_inputs and 'H' in available_inputs:
        selected = ['P', 'H']
    else:
        # Use first two inputs
        selected = list(available_inputs)[:2]

    if len(selected) < 2:
        raise CoolPropError(
            f"CoolProp requires exactly 2 inputs, got: {list(available_inputs)}"
        )

    # Build input pairs
    input_pairs = []
    for name in selected:
        cp_name = input_mapping.get(name, name.upper())
        input_pairs.extend([cp_name, float(inputs[name])])

    try:
        # PropsSI(output, name1, val1, name2, val2, fluid)
        result = CP.PropsSI(output_key, *input_pairs, fluid)

        # Check for invalid results
        import math
        if math.isnan(result) or math.isinf(result):
            raise CoolPropError(
                f"CoolProp returned invalid value for {output_key}: "
                f"inputs={dict(zip(input_pairs[::2], input_pairs[1::2]))}"
            )

        return float(result)

    except Exception as e:
        if "CoolPropError" in str(type(e).__name__) or "ValueError" in str(type(e).__name__):
            raise CoolPropError(
                f"CoolProp error for {fluid}: {str(e)}. "
                f"Output={output_key}, Inputs={dict(zip(input_pairs[::2], input_pairs[1::2]))}"
            )
        raise


def get_saturation_property(
    source: PropertySource,
    output_name: str,
    fixed_input: str,
    fixed_value: float,
    phase: str  # "liquid" or "vapor"
) -> float:
    """
    Get saturation property at a given temperature or pressure.

    phase: "liquid" (Q=0) or "vapor" (Q=1)
    """
    Q = 0.0 if phase == "liquid" else 1.0

    inputs = {
        fixed_input: fixed_value,
        'Q': Q
    }

    return resolve_coolprop(source, output_name, inputs)


def list_coolprop_fluids() -> list:
    """List all available CoolProp fluids."""
    CP = _get_coolprop()
    # Get list of pure and pseudo-pure fluids
    fluids = CP.FluidsList()
    return sorted(fluids)
