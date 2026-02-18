"""
Dimensional Analysis System

Validates physical equations have correct units using SI base quantities.
Catches physics errors BEFORE runtime by checking dimensional consistency.

SI Base Quantities:
- L (length) - meters
- M (mass) - kilograms
- T (time) - seconds
- Θ (temperature) - kelvin
- I (current) - amperes
- N (amount) - moles
- J (luminosity) - candelas
"""

import re
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Union


class DimensionError(Exception):
    """Raised when dimensions are incompatible for an operation."""
    pass


@dataclass(frozen=True)
class Dimension:
    """
    Physical dimensions using SI base quantities.

    Immutable and hashable - can be used as dict keys.
    Supports arithmetic for dimensional analysis.

    Example:
        Force = Mass * Acceleration
        Dimension(mass=1, length=1, time=-2) = M * L * T^-2
    """
    length: int = 0       # L (meters)
    mass: int = 0         # M (kilograms)
    time: int = 0         # T (seconds)
    temperature: int = 0  # Θ (kelvin)
    current: int = 0      # I (amperes)
    amount: int = 0       # N (moles)
    luminosity: int = 0   # J (candelas)

    def __mul__(self, other: 'Dimension') -> 'Dimension':
        """Multiply dimensions: L * L = L²"""
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(
            length=self.length + other.length,
            mass=self.mass + other.mass,
            time=self.time + other.time,
            temperature=self.temperature + other.temperature,
            current=self.current + other.current,
            amount=self.amount + other.amount,
            luminosity=self.luminosity + other.luminosity
        )

    def __truediv__(self, other: 'Dimension') -> 'Dimension':
        """Divide dimensions: L / T = L·T⁻¹ (velocity)"""
        if not isinstance(other, Dimension):
            return NotImplemented
        return Dimension(
            length=self.length - other.length,
            mass=self.mass - other.mass,
            time=self.time - other.time,
            temperature=self.temperature - other.temperature,
            current=self.current - other.current,
            amount=self.amount - other.amount,
            luminosity=self.luminosity - other.luminosity
        )

    def __pow__(self, exponent: int) -> 'Dimension':
        """Raise dimension to power: L² = L ** 2"""
        if not isinstance(exponent, (int, float)):
            return NotImplemented
        exp = int(exponent)
        return Dimension(
            length=self.length * exp,
            mass=self.mass * exp,
            time=self.time * exp,
            temperature=self.temperature * exp,
            current=self.current * exp,
            amount=self.amount * exp,
            luminosity=self.luminosity * exp
        )

    def __repr__(self) -> str:
        """Human-readable dimension representation."""
        parts = []
        symbols = [
            ('L', self.length),
            ('M', self.mass),
            ('T', self.time),
            ('Θ', self.temperature),
            ('I', self.current),
            ('N', self.amount),
            ('J', self.luminosity),
        ]
        for sym, exp in symbols:
            if exp == 1:
                parts.append(sym)
            elif exp != 0:
                parts.append(f"{sym}^{exp}")

        if not parts:
            return "Dimension(dimensionless)"
        return f"Dimension({' · '.join(parts)})"

    def is_dimensionless(self) -> bool:
        """Check if this is a dimensionless quantity."""
        return (
            self.length == 0 and
            self.mass == 0 and
            self.time == 0 and
            self.temperature == 0 and
            self.current == 0 and
            self.amount == 0 and
            self.luminosity == 0
        )

    def is_compatible_with(self, other: 'Dimension') -> bool:
        """Check if two dimensions can be added/subtracted."""
        return self == other


# =============================================================================
# PREDEFINED DIMENSIONS
# =============================================================================

# Base dimensions
DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
TEMPERATURE = Dimension(temperature=1)
CURRENT = Dimension(current=1)
AMOUNT = Dimension(amount=1)
LUMINOSITY = Dimension(luminosity=1)

# Derived geometric dimensions
AREA = Dimension(length=2)                    # L²
VOLUME = Dimension(length=3)                  # L³

# Mechanical dimensions
VELOCITY = Dimension(length=1, time=-1)                      # L·T⁻¹
ACCELERATION = Dimension(length=1, time=-2)                  # L·T⁻²
FORCE = Dimension(mass=1, length=1, time=-2)                 # M·L·T⁻² (N)
PRESSURE = Dimension(mass=1, length=-1, time=-2)             # M·L⁻¹·T⁻² (Pa)
ENERGY = Dimension(mass=1, length=2, time=-2)                # M·L²·T⁻² (J)
POWER = Dimension(mass=1, length=2, time=-3)                 # M·L²·T⁻³ (W)
TORQUE = Dimension(mass=1, length=2, time=-2)                # M·L²·T⁻² (N·m, same as energy)
FREQUENCY = Dimension(time=-1)                               # T⁻¹ (Hz)
ANGLE = DIMENSIONLESS                                        # Radians are dimensionless

# Density and flow
DENSITY = Dimension(mass=1, length=-3)                       # M·L⁻³ (kg/m³)
VOLUME_FLOW = Dimension(length=3, time=-1)                   # L³·T⁻¹ (m³/s)
MASS_FLOW = Dimension(mass=1, time=-1)                       # M·T⁻¹ (kg/s)

# Viscosity
DYNAMIC_VISCOSITY = Dimension(mass=1, length=-1, time=-1)    # M·L⁻¹·T⁻¹ (Pa·s)
KINEMATIC_VISCOSITY = Dimension(length=2, time=-1)           # L²·T⁻¹ (m²/s)

# Electrical dimensions
VOLTAGE = Dimension(mass=1, length=2, time=-3, current=-1)   # M·L²·T⁻³·I⁻¹ (V)
RESISTANCE = Dimension(mass=1, length=2, time=-3, current=-2)  # M·L²·T⁻³·I⁻² (Ω)
CAPACITANCE = Dimension(mass=-1, length=-2, time=4, current=2)  # M⁻¹·L⁻²·T⁴·I² (F)
INDUCTANCE = Dimension(mass=1, length=2, time=-2, current=-2)   # M·L²·T⁻²·I⁻² (H)

# Thermal dimensions
THERMAL_CONDUCTIVITY = Dimension(mass=1, length=1, time=-3, temperature=-1)  # M·L·T⁻³·Θ⁻¹ (W/(m·K))
SPECIFIC_HEAT = Dimension(length=2, time=-2, temperature=-1)                  # L²·T⁻²·Θ⁻¹ (J/(kg·K))
HEAT_CAPACITY = Dimension(mass=1, length=2, time=-2, temperature=-1)         # M·L²·T⁻²·Θ⁻¹ (J/K) - thermal mass
HEAT_TRANSFER_COEFF = Dimension(mass=1, time=-3, temperature=-1)             # M·T⁻³·Θ⁻¹ (W/(m²·K))
THERMAL_EXPANSION = Dimension(temperature=-1)                                 # Θ⁻¹ (1/K)

# Specific (per-mass) properties - from steam.yaml
SPECIFIC_ENERGY = Dimension(length=2, time=-2)                               # L²·T⁻² (J/kg)
SPECIFIC_ENTROPY = Dimension(length=2, time=-2, temperature=-1)              # L²·T⁻²·Θ⁻¹ (J/(kg·K))
SPECIFIC_VOLUME = Dimension(length=3, mass=-1)                               # L³·M⁻¹ (m³/kg)
RESISTIVITY = Dimension(mass=1, length=3, time=-3, current=-2)               # M·L³·T⁻³·I⁻² (Ohm*m)
PERMEABILITY = Dimension(mass=1, length=1, time=-2, current=-2)              # M·L·T⁻²·I⁻² (H/m)

# =============================================================================
# UNIT TO DIMENSION MAPPING
# =============================================================================

UNIT_DIMENSIONS: Dict[str, Dimension] = {
    # -------------------------------------------------------------------------
    # Length -> L
    # -------------------------------------------------------------------------
    'nm': LENGTH,
    'μm': LENGTH,
    'mm': LENGTH,
    'cm': LENGTH,
    'm': LENGTH,
    'km': LENGTH,
    'in': LENGTH,
    'ft': LENGTH,
    'yd': LENGTH,
    'mi': LENGTH,
    'mil': LENGTH,
    'thou': LENGTH,

    # -------------------------------------------------------------------------
    # Area -> L²
    # -------------------------------------------------------------------------
    'mm²': AREA,
    'cm²': AREA,
    'm²': AREA,
    'km²': AREA,
    'ha': AREA,
    'in²': AREA,
    'ft²': AREA,
    'yd²': AREA,
    'mi²': AREA,
    'acre': AREA,

    # -------------------------------------------------------------------------
    # Volume -> L³
    # -------------------------------------------------------------------------
    'mm³': VOLUME,
    'cm³': VOLUME,
    'mL': VOLUME,
    'L': VOLUME,
    'm³': VOLUME,
    'km³': VOLUME,
    'in³': VOLUME,
    'ft³': VOLUME,
    'gal': VOLUME,
    'fl oz': VOLUME,
    'bbl': VOLUME,

    # -------------------------------------------------------------------------
    # Mass -> M
    # -------------------------------------------------------------------------
    'μg': MASS,
    'mg': MASS,
    'g': MASS,
    'kg': MASS,
    't': MASS,
    'Mt': MASS,
    'oz': MASS,
    'lb': MASS,
    'ton': MASS,
    'grain': MASS,

    # -------------------------------------------------------------------------
    # Force -> M·L·T⁻²
    # -------------------------------------------------------------------------
    'μN': FORCE,
    'mN': FORCE,
    'N': FORCE,
    'kN': FORCE,
    'MN': FORCE,
    'lbf': FORCE,
    'ozf': FORCE,
    'kip': FORCE,
    'pdl': FORCE,
    'kgf': FORCE,

    # -------------------------------------------------------------------------
    # Pressure -> M·L⁻¹·T⁻²
    # -------------------------------------------------------------------------
    'Pa': PRESSURE,
    'kPa': PRESSURE,
    'MPa': PRESSURE,
    'GPa': PRESSURE,
    'bar': PRESSURE,
    'mbar': PRESSURE,
    'psi': PRESSURE,
    'ksi': PRESSURE,
    'psf': PRESSURE,
    'inHg': PRESSURE,
    'inH₂O': PRESSURE,

    # -------------------------------------------------------------------------
    # Temperature -> Θ
    # -------------------------------------------------------------------------
    'K': TEMPERATURE,
    'kelvin': TEMPERATURE,
    '°C': TEMPERATURE,
    '℃': TEMPERATURE,
    'degC': TEMPERATURE,
    'celsius': TEMPERATURE,
    '°F': TEMPERATURE,
    '℉': TEMPERATURE,
    'degF': TEMPERATURE,
    'fahrenheit': TEMPERATURE,
    '°R': TEMPERATURE,
    'rankine': TEMPERATURE,

    # -------------------------------------------------------------------------
    # Time -> T
    # -------------------------------------------------------------------------
    'ps': TIME,
    'ns': TIME,
    'μs': TIME,
    'ms': TIME,
    's': TIME,
    'min': TIME,
    'h': TIME,
    'd': TIME,
    'wk': TIME,
    'mo': TIME,
    'yr': TIME,

    # -------------------------------------------------------------------------
    # Frequency -> T⁻¹
    # -------------------------------------------------------------------------
    'Hz': FREQUENCY,
    'kHz': FREQUENCY,
    'MHz': FREQUENCY,
    'GHz': FREQUENCY,
    'THz': FREQUENCY,
    'mHz': FREQUENCY,
    'rpm': FREQUENCY,
    'rps': FREQUENCY,
    '1/s': FREQUENCY,
    's⁻¹': FREQUENCY,

    # -------------------------------------------------------------------------
    # Electrical - Resistivity -> M·L³·T⁻³·I⁻²
    # -------------------------------------------------------------------------
    'Ω·m': RESISTIVITY,
    'Ohm·m': RESISTIVITY,
    'Ohm*m': RESISTIVITY,
    'kg*m^3/(A^2*s^3)': RESISTIVITY,    # raw caret form
    'kg*m³/(A²*s³)': RESISTIVITY,       # normalized unicode form (matches _normalize_unit_string output)

    # -------------------------------------------------------------------------
    # Magnetic Permeability -> M·L·T⁻²·I⁻²
    # -------------------------------------------------------------------------
    'H/m': PERMEABILITY,
    'μH/m': PERMEABILITY,
    'mH/m': PERMEABILITY,
    'kg*m/(A^2*s^2)': PERMEABILITY,    # raw caret form
    'kg*m/(A²*s²)': PERMEABILITY,      # normalized unicode form (matches _normalize_unit_string output)

    # -------------------------------------------------------------------------
    # Energy -> M·L²·T⁻²
    # -------------------------------------------------------------------------
    'J': ENERGY,
    'kJ': ENERGY,
    'MJ': ENERGY,
    'GJ': ENERGY,
    'Wh': ENERGY,
    'kWh': ENERGY,
    'cal': ENERGY,
    'eV': ENERGY,
    'BTU': ENERGY,
    'ft·lbf': ENERGY,
    'hp·h': ENERGY,

    # -------------------------------------------------------------------------
    # Power -> M·L²·T⁻³
    # -------------------------------------------------------------------------
    'W': POWER,
    'mW': POWER,
    'kW': POWER,
    'MW': POWER,
    'GW': POWER,
    'hp': POWER,
    'BTU/h': POWER,
    'ft·lbf/s': POWER,

    # -------------------------------------------------------------------------
    # Torque -> M·L²·T⁻² (same dimension as energy)
    # -------------------------------------------------------------------------
    'N·m': TORQUE,
    'kN·m': TORQUE,
    'lb·ft': TORQUE,
    'lb·in': TORQUE,
    'lbf·ft': TORQUE,

    # -------------------------------------------------------------------------
    # Electrical - Current -> I
    # -------------------------------------------------------------------------
    'A': CURRENT,
    'mA': CURRENT,
    'μA': CURRENT,

    # -------------------------------------------------------------------------
    # Electrical - Voltage -> M·L²·T⁻³·I⁻¹
    # -------------------------------------------------------------------------
    'V': VOLTAGE,
    'mV': VOLTAGE,
    'kV': VOLTAGE,

    # -------------------------------------------------------------------------
    # Electrical - Resistance -> M·L²·T⁻³·I⁻²
    # -------------------------------------------------------------------------
    'Ω': RESISTANCE,
    'kΩ': RESISTANCE,
    'MΩ': RESISTANCE,

    # -------------------------------------------------------------------------
    # Electrical - Capacitance -> M⁻¹·L⁻²·T⁴·I²
    # -------------------------------------------------------------------------
    'F': CAPACITANCE,
    'μF': CAPACITANCE,
    'nF': CAPACITANCE,
    'pF': CAPACITANCE,

    # -------------------------------------------------------------------------
    # Electrical - Inductance -> M·L²·T⁻²·I⁻²
    # -------------------------------------------------------------------------
    'H': INDUCTANCE,
    'mH': INDUCTANCE,

    # -------------------------------------------------------------------------
    # Angle -> Dimensionless
    # -------------------------------------------------------------------------
    'rad': DIMENSIONLESS,
    'mrad': DIMENSIONLESS,
    'deg': DIMENSIONLESS,
    '°': DIMENSIONLESS,
    "'": DIMENSIONLESS,  # arcminute
    '"': DIMENSIONLESS,  # arcsecond

    # -------------------------------------------------------------------------
    # Velocity -> L·T⁻¹
    # -------------------------------------------------------------------------
    'm/s': VELOCITY,
    'km/h': VELOCITY,
    'ft/s': VELOCITY,
    'mph': VELOCITY,

    # -------------------------------------------------------------------------
    # Acceleration -> L·T⁻²
    # -------------------------------------------------------------------------
    'm/s²': ACCELERATION,
    'm/s^2': ACCELERATION,
    'g₀': ACCELERATION,
    'g': ACCELERATION,  # gravitational acceleration shorthand
    'ft/s²': ACCELERATION,
    'ft/s^2': ACCELERATION,
    'in/s^2': ACCELERATION,
    'mm/s^2': ACCELERATION,

    # -------------------------------------------------------------------------
    # Density -> M·L⁻³
    # -------------------------------------------------------------------------
    'kg/m³': DENSITY,
    'kg/m^3': DENSITY,
    'g/cm³': DENSITY,
    'g/cm^3': DENSITY,
    'kg/L': DENSITY,
    'g/mL': DENSITY,
    'lb/ft³': DENSITY,
    'lb/ft^3': DENSITY,
    'lb/in³': DENSITY,
    'lb/in^3': DENSITY,
    'lb/gal': DENSITY,
    'oz/in³': DENSITY,

    # -------------------------------------------------------------------------
    # Dynamic Viscosity -> M·L⁻¹·T⁻¹
    # -------------------------------------------------------------------------
    'Pa·s': DYNAMIC_VISCOSITY,
    'mPa·s': DYNAMIC_VISCOSITY,
    'cP': DYNAMIC_VISCOSITY,

    # -------------------------------------------------------------------------
    # Kinematic Viscosity -> L²·T⁻¹
    # -------------------------------------------------------------------------
    'm²/s': KINEMATIC_VISCOSITY,
    'cSt': KINEMATIC_VISCOSITY,

    # -------------------------------------------------------------------------
    # Thermal Conductivity -> M·L·T⁻³·Θ⁻¹
    # -------------------------------------------------------------------------
    'W/(m·K)': THERMAL_CONDUCTIVITY,
    'W/(m·°C)': THERMAL_CONDUCTIVITY,
    'BTU/(hr·ft·°F)': THERMAL_CONDUCTIVITY,

    # -------------------------------------------------------------------------
    # Specific Heat -> L²·T⁻²·Θ⁻¹
    # -------------------------------------------------------------------------
    'J/(kg·K)': SPECIFIC_HEAT,
    'kJ/(kg·K)': SPECIFIC_HEAT,
    'cal/(g·°C)': SPECIFIC_HEAT,
    'BTU/(lb·°F)': SPECIFIC_HEAT,

    # -------------------------------------------------------------------------
    # Heat Capacity (thermal mass) -> M·L²·T⁻²·Θ⁻¹
    # -------------------------------------------------------------------------
    'J/K': HEAT_CAPACITY,
    'kJ/K': HEAT_CAPACITY,
    'cal/K': HEAT_CAPACITY,
    'BTU/°F': HEAT_CAPACITY,
    'J/°C': HEAT_CAPACITY,
    'kJ/°C': HEAT_CAPACITY,

    # -------------------------------------------------------------------------
    # Heat Transfer Coefficient -> M·T⁻³·Θ⁻¹
    # -------------------------------------------------------------------------
    'W/(m²·K)': HEAT_TRANSFER_COEFF,
    'BTU/(hr·ft²·°F)': HEAT_TRANSFER_COEFF,

    # -------------------------------------------------------------------------
    # Volume Flow -> L³·T⁻¹
    # -------------------------------------------------------------------------
    'm³/s': VOLUME_FLOW,
    'L/s': VOLUME_FLOW,
    'L/min': VOLUME_FLOW,
    'gpm': VOLUME_FLOW,
    'cfm': VOLUME_FLOW,

    # -------------------------------------------------------------------------
    # Mass Flow -> M·T⁻¹
    # -------------------------------------------------------------------------
    'kg/s': MASS_FLOW,
    'kg/hr': MASS_FLOW,
    'lb/s': MASS_FLOW,
    'lb/hr': MASS_FLOW,

    # -------------------------------------------------------------------------
    # Thermal Expansion -> Θ⁻¹
    # -------------------------------------------------------------------------
    '1/K': THERMAL_EXPANSION,
    '1/°C': THERMAL_EXPANSION,
    'ppm/K': THERMAL_EXPANSION,
    'ppm/°C': THERMAL_EXPANSION,
    'µm/(m·K)': THERMAL_EXPANSION,
    '1/°F': THERMAL_EXPANSION,
    '1/°R': THERMAL_EXPANSION,
    'ppm/°F': THERMAL_EXPANSION,

    # -------------------------------------------------------------------------
    # Specific properties (from steam.yaml and thermodynamics)
    # -------------------------------------------------------------------------
    # Specific energy (J/kg) -> L²·T⁻²
    'J/kg': SPECIFIC_ENERGY,
    'kJ/kg': SPECIFIC_ENERGY,
    'BTU/lb': SPECIFIC_ENERGY,

    # Specific entropy / specific heat (J/(kg·K)) -> L²·T⁻²·Θ⁻¹
    # Note: J/(kg·K) already mapped above as SPECIFIC_HEAT

    # Specific volume (m³/kg) -> L³·M⁻¹
    'm³/kg': SPECIFIC_VOLUME,
    'L/kg': SPECIFIC_VOLUME,
    'ft³/lb': SPECIFIC_VOLUME,

    # -------------------------------------------------------------------------
    # Dimensionless quantities
    # -------------------------------------------------------------------------
    'none': DIMENSIONLESS,
    '': DIMENSIONLESS,
    '1': DIMENSIONLESS,
    'ratio': DIMENSIONLESS,
    '%': DIMENSIONLESS,
    'ppm': DIMENSIONLESS,
    'ppb': DIMENSIONLESS,
}


# =============================================================================
# DIMENSION NAME MAPPING (for compatibility with unit_constants.py)
# =============================================================================

DIMENSION_NAME_TO_DIMENSION: Dict[str, Dimension] = {
    'length': LENGTH,
    'area': AREA,
    'volume': VOLUME,
    'mass': MASS,
    'force': FORCE,
    'pressure': PRESSURE,
    'temperature': TEMPERATURE,
    'time': TIME,
    'frequency': FREQUENCY,
    'energy': ENERGY,
    'power': POWER,
    'torque': TORQUE,
    'current': CURRENT,
    'voltage': VOLTAGE,
    'resistance': RESISTANCE,
    'capacitance': CAPACITANCE,
    'inductance': INDUCTANCE,
    'angle': ANGLE,
    'velocity': VELOCITY,
    'acceleration': ACCELERATION,
    'density': DENSITY,
    'dynamic_viscosity': DYNAMIC_VISCOSITY,
    'kinematic_viscosity': KINEMATIC_VISCOSITY,
    'thermal_conductivity': THERMAL_CONDUCTIVITY,
    'specific_heat': SPECIFIC_HEAT,
    'heat_capacity': HEAT_CAPACITY,
    'heat_transfer_coeff': HEAT_TRANSFER_COEFF,
    'volume_flow': VOLUME_FLOW,
    'mass_flow': MASS_FLOW,
    # Additional types
    'thermal_expansion': THERMAL_EXPANSION,
    'specific_energy': SPECIFIC_ENERGY,
    'specific_entropy': SPECIFIC_ENTROPY,
    'specific_volume': SPECIFIC_VOLUME,
    'dimensionless': DIMENSIONLESS,
}


# =============================================================================
# UNIT STRING NORMALIZATION
# =============================================================================

def _normalize_unit_string(unit_str: str) -> str:
    """
    Convert ASCII caret notation to Unicode superscripts.

    This ensures consistent unit matching regardless of input format:
    - "m/s^2" → "m/s²"
    - "kg^-1" → "kg⁻¹"

    Args:
        unit_str: Unit string potentially containing caret notation

    Returns:
        Normalized unit string with Unicode superscripts
    """
    if not unit_str:
        return unit_str

    # Map ASCII to Unicode superscripts
    superscript_map = {
        '0': '⁰', '1': '¹', '2': '²', '3': '³', '4': '⁴',
        '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
        '-': '⁻', '+': '⁺'
    }

    def replace_exponent(match):
        exp = match.group(1)
        return ''.join(superscript_map.get(c, c) for c in exp)

    # Convert ^2 → ², ^-1 → ⁻¹, etc.
    return re.sub(r'\^([-+]?[0-9]+)', replace_exponent, unit_str)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================

def get_unit_dimension(unit: str) -> Optional[Dimension]:
    """
    Get the Dimension for a unit symbol.

    Args:
        unit: Unit symbol (e.g., 'm', 'Pa', 'J/(kg·K)')

    Returns:
        Dimension object or None if unit not found
    """
    # Normalize caret notation to Unicode superscripts (m/s^2 → m/s²)
    unit = _normalize_unit_string(unit)
    return UNIT_DIMENSIONS.get(unit)


def infer_dimension(
    ast_node: dict,
    input_dimensions: Dict[str, Dimension]
) -> Dimension:
    """
    Infer resulting dimension from AST node.

    Recursively walks AST to compute output dimension.

    AST format (from Instance 2):
        {"type": "input", "name": "length"}
        {"type": "literal", "value": 2.5}
        {"type": "add", "operands": [...]}
        {"type": "mul", "operands": [...]}
        {"type": "div", "left": {...}, "right": {...}}
        {"type": "pow", "base": {...}, "exponent": 2}
        {"type": "sqrt", "operand": {...}}
        {"type": "function", "name": "sin", "args": [...]}

    Args:
        ast_node: AST node dictionary
        input_dimensions: Map of input names to their dimensions

    Returns:
        Computed Dimension

    Raises:
        DimensionError: If dimensions are incompatible
    """
    node_type = ast_node.get("type", "")

    # Input variable - look up dimension
    if node_type == "input":
        name = ast_node.get("name", "")
        dim = input_dimensions.get(name)
        if dim is None:
            raise DimensionError(f"Unknown input '{name}' - no dimension provided")
        return dim

    # Literal/constant number - dimensionless
    # Parser uses "const" for numeric literals, but we also accept "literal" for compatibility
    if node_type in ("const", "literal"):
        return DIMENSIONLESS

    # Helper to check if an AST node is a literal constant (for permissive mode)
    def is_literal_constant(node: dict) -> bool:
        """Check if node is a numeric literal constant."""
        if isinstance(node, dict):
            return node.get("type") in ("const", "literal")
        return False

    # Addition/Subtraction - dimensions should match, but be permissive with literal constants
    # Engineering practice: constants like 0.01 for numerical stability are treated as having
    # the same dimension as the other operand (implicit unit matching)
    if node_type in ("add", "sub"):
        operands = ast_node.get("operands", [])
        if not operands:
            return DIMENSIONLESS

        # First pass: find the "dominant" dimension (first non-dimensionless, non-literal operand)
        result_dim = None
        for operand in operands:
            operand_dim = infer_dimension(operand, input_dimensions)
            if not operand_dim.is_dimensionless() or not is_literal_constant(operand):
                result_dim = operand_dim
                break

        # If all operands are dimensionless literals, return dimensionless
        if result_dim is None:
            return DIMENSIONLESS

        # Second pass: verify all non-literal operands match, allow literals to adapt
        for i, operand in enumerate(operands, start=1):
            operand_dim = infer_dimension(operand, input_dimensions)
            if operand_dim != result_dim:
                # Permissive: if this operand is a literal constant, assume it matches
                if is_literal_constant(operand) and operand_dim.is_dimensionless():
                    continue  # Allow literal constants to adapt to the dominant dimension
                # Strict: non-literals must match exactly
                raise DimensionError(
                    f"Dimension mismatch in {'addition' if node_type == 'add' else 'subtraction'}: "
                    f"operand 1 is {result_dim}, operand {i} is {operand_dim}"
                )
        return result_dim

    # Multiplication - dimensions add
    if node_type == "mul":
        operands = ast_node.get("operands", [])
        if not operands:
            return DIMENSIONLESS

        result_dim = DIMENSIONLESS
        for operand in operands:
            operand_dim = infer_dimension(operand, input_dimensions)
            result_dim = result_dim * operand_dim
        return result_dim

    # Division - dimensions subtract
    # Parser uses "numerator"/"denominator", accept both for compatibility
    if node_type == "div":
        left = ast_node.get("left") or ast_node.get("numerator")
        right = ast_node.get("right") or ast_node.get("denominator")

        if left is None or right is None:
            raise DimensionError("Division node missing 'left'/'right' or 'numerator'/'denominator'")

        left_dim = infer_dimension(left, input_dimensions)
        right_dim = infer_dimension(right, input_dimensions)
        return left_dim / right_dim

    # Power - dimension multiplies by exponent
    if node_type == "pow":
        base = ast_node.get("base")
        exponent = ast_node.get("exponent")

        if base is None:
            raise DimensionError("Power node missing 'base'")

        base_dim = infer_dimension(base, input_dimensions)

        # Check if exponent is a literal constant (parser uses "const" or "literal")
        if isinstance(exponent, dict):
            exp_type = exponent.get("type")
            if exp_type in ("const", "literal"):
                # It's a numeric literal - extract the value and use it directly
                exp_val = exponent.get("value", 1)
                return base_dim ** int(exp_val)
            else:
                # It's a complex expression - check dimensionality
                exp_dim = infer_dimension(exponent, input_dimensions)
                if not exp_dim.is_dimensionless():
                    raise DimensionError(f"Exponent must be dimensionless, got {exp_dim}")
                # Can't determine dimension with variable exponent unless base is dimensionless
                if not base_dim.is_dimensionless():
                    raise DimensionError(
                        "Cannot raise dimensional quantity to variable power - "
                        "use literal exponent"
                    )
                return DIMENSIONLESS
        else:
            # Numeric exponent (raw number, not a dict)
            exp_val = int(exponent) if exponent is not None else 1
            return base_dim ** exp_val

    # Square root - dimension exponent halved
    if node_type == "sqrt":
        operand = ast_node.get("operand")
        if operand is None:
            raise DimensionError("Sqrt node missing 'operand'")

        operand_dim = infer_dimension(operand, input_dimensions)

        # Check that all exponents are even (can take sqrt)
        if (operand_dim.length % 2 != 0 or
            operand_dim.mass % 2 != 0 or
            operand_dim.time % 2 != 0 or
            operand_dim.temperature % 2 != 0 or
            operand_dim.current % 2 != 0 or
            operand_dim.amount % 2 != 0 or
            operand_dim.luminosity % 2 != 0):
            raise DimensionError(
                f"Cannot take sqrt of {operand_dim} - exponents must be even"
            )

        return Dimension(
            length=operand_dim.length // 2,
            mass=operand_dim.mass // 2,
            time=operand_dim.time // 2,
            temperature=operand_dim.temperature // 2,
            current=operand_dim.current // 2,
            amount=operand_dim.amount // 2,
            luminosity=operand_dim.luminosity // 2,
        )

    # Unary negation - preserves dimension
    if node_type == "neg":
        operand = ast_node.get("operand")
        if operand is None:
            raise DimensionError("Negation node missing 'operand'")
        return infer_dimension(operand, input_dimensions)

    # Trigonometric functions - require dimensionless input, return dimensionless
    # Parser may use "function", "func", or "call" for function calls
    if node_type in ("function", "func", "call"):
        func_name = ast_node.get("name", "")
        # Try multiple field names for arguments - parsers vary
        args = ast_node.get("args") or ast_node.get("arguments") or []
        # For single-argument functions, also check "arg" and "operand"
        if not args:
            single_arg = ast_node.get("arg") or ast_node.get("operand")
            if single_arg:
                args = [single_arg]

        # Trig functions: input must be angle (dimensionless), output is dimensionless
        if func_name in ("sin", "cos", "tan", "asin", "acos", "atan", "sinh", "cosh", "tanh"):
            if args:
                arg_dim = infer_dimension(args[0], input_dimensions)
                if not arg_dim.is_dimensionless():
                    raise DimensionError(
                        f"Function {func_name} requires dimensionless argument, got {arg_dim}"
                    )
            return DIMENSIONLESS

        # Log/exp: input must be dimensionless, output is dimensionless
        if func_name in ("log", "ln", "log10", "exp"):
            if args:
                arg_dim = infer_dimension(args[0], input_dimensions)
                if not arg_dim.is_dimensionless():
                    raise DimensionError(
                        f"Function {func_name} requires dimensionless argument, got {arg_dim}"
                    )
            return DIMENSIONLESS

        # abs preserves dimension
        if func_name == "abs":
            if args:
                return infer_dimension(args[0], input_dimensions)
            return DIMENSIONLESS

        # sqrt halves dimension exponents (sqrt(L²) = L)
        if func_name == "sqrt":
            if args:
                operand_dim = infer_dimension(args[0], input_dimensions)
                # Check that all exponents are even (can take sqrt)
                if (operand_dim.length % 2 != 0 or
                    operand_dim.mass % 2 != 0 or
                    operand_dim.time % 2 != 0 or
                    operand_dim.temperature % 2 != 0 or
                    operand_dim.current % 2 != 0 or
                    operand_dim.amount % 2 != 0 or
                    operand_dim.luminosity % 2 != 0):
                    raise DimensionError(
                        f"Cannot take sqrt of {operand_dim} - exponents must be even"
                    )
                return Dimension(
                    length=operand_dim.length // 2,
                    mass=operand_dim.mass // 2,
                    time=operand_dim.time // 2,
                    temperature=operand_dim.temperature // 2,
                    current=operand_dim.current // 2,
                    amount=operand_dim.amount // 2,
                    luminosity=operand_dim.luminosity // 2,
                )
            return DIMENSIONLESS

        # pow/power function (e.g., pow(x, 2))
        if func_name in ("pow", "power"):
            if len(args) >= 2:
                base_dim = infer_dimension(args[0], input_dimensions)
                # Try to get exponent value
                exp_node = args[1]
                if isinstance(exp_node, dict) and exp_node.get("type") in ("const", "literal"):
                    exp_val = int(exp_node.get("value", 1))
                    return base_dim ** exp_val
                # Variable exponent - base must be dimensionless
                if not base_dim.is_dimensionless():
                    raise DimensionError(
                        "Cannot raise dimensional quantity to variable power"
                    )
            return DIMENSIONLESS

        # min/max preserve dimension (all args must have same dimension)
        if func_name in ("min", "max"):
            if args:
                first_dim = infer_dimension(args[0], input_dimensions)
                for arg in args[1:]:
                    arg_dim = infer_dimension(arg, input_dimensions)
                    if arg_dim != first_dim:
                        raise DimensionError(
                            f"All arguments to {func_name} must have same dimension"
                        )
                return first_dim
            return DIMENSIONLESS

        # Unknown function - assume dimensionless
        return DIMENSIONLESS

    # Unknown node type
    raise DimensionError(f"Unknown AST node type: {node_type}")


def validate_equation_dimensions(
    equation_ast: dict,
    input_dimensions: Dict[str, Dimension],
    expected_output_dimension: Dimension
) -> Tuple[bool, str]:
    """
    Validate that equation has correct dimensions.

    Walks the AST to compute the resulting dimension and compares
    with the expected output dimension.

    Args:
        equation_ast: Parsed equation as AST dictionary
        input_dimensions: Map of input variable names to their Dimensions
        expected_output_dimension: The expected dimension of the result

    Returns:
        (is_valid, error_message)

    Example:
        # Thermal expansion: delta_L = L * CTE * delta_T
        ast = {"type": "mul", "operands": [
            {"type": "input", "name": "length"},
            {"type": "input", "name": "CTE"},
            {"type": "input", "name": "delta_T"}
        ]}

        input_dimensions = {
            "length": LENGTH,                    # L
            "CTE": THERMAL_EXPANSION,            # Θ⁻¹
            "delta_T": TEMPERATURE               # Θ
        }

        expected = LENGTH  # L

        # L * Θ⁻¹ * Θ = L ✓
        validate_equation_dimensions(ast, input_dimensions, expected)
        # Returns: (True, "")
    """
    try:
        computed_dimension = infer_dimension(equation_ast, input_dimensions)

        if computed_dimension == expected_output_dimension:
            return True, ""
        else:
            return False, (
                f"Dimension mismatch: equation produces {computed_dimension}, "
                f"but expected {expected_output_dimension}"
            )
    except DimensionError as e:
        return False, str(e)


def check_dimensional_consistency(
    equation_ast: dict,
    input_dimensions: Dict[str, Dimension]
) -> Tuple[bool, str, Optional[Dimension]]:
    """
    Check if an equation is dimensionally consistent and return its dimension.

    Unlike validate_equation_dimensions, this doesn't compare against an
    expected dimension - it just checks internal consistency (e.g., no
    adding lengths to masses).

    Args:
        equation_ast: Parsed equation as AST dictionary
        input_dimensions: Map of input variable names to their Dimensions

    Returns:
        (is_consistent, error_message, computed_dimension)
    """
    try:
        computed_dimension = infer_dimension(equation_ast, input_dimensions)
        return True, "", computed_dimension
    except DimensionError as e:
        return False, str(e), None


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def dimension_to_string(dim: Dimension) -> str:
    """
    Convert a Dimension to a human-readable string.

    Example:
        FORCE -> "M·L·T⁻²"
        PRESSURE -> "M·L⁻¹·T⁻²"
    """
    parts = []
    symbols = [
        ('L', dim.length),
        ('M', dim.mass),
        ('T', dim.time),
        ('Θ', dim.temperature),
        ('I', dim.current),
        ('N', dim.amount),
        ('J', dim.luminosity),
    ]

    superscript = {
        '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
        '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
    }

    def to_superscript(n: int) -> str:
        return ''.join(superscript.get(c, c) for c in str(n))

    for sym, exp in symbols:
        if exp == 1:
            parts.append(sym)
        elif exp != 0:
            parts.append(f"{sym}{to_superscript(exp)}")

    if not parts:
        return "1"  # Dimensionless
    return '·'.join(parts)


# =============================================================================
# DIMENSION TO SI UNIT MAPPING
# =============================================================================

# Map Dimension objects to their SI unit symbols
# Used to determine the result unit after dimensional analysis
DIMENSION_TO_SI_UNIT: Dict[Dimension, str] = {
    DIMENSIONLESS: '',
    LENGTH: 'm',
    AREA: 'm²',
    VOLUME: 'm³',
    MASS: 'kg',
    TIME: 's',
    TEMPERATURE: 'K',
    CURRENT: 'A',
    AMOUNT: 'mol',
    LUMINOSITY: 'cd',
    VELOCITY: 'm/s',
    ACCELERATION: 'm/s²',
    FORCE: 'N',
    PRESSURE: 'Pa',
    ENERGY: 'J',
    POWER: 'W',
    TORQUE: 'N·m',
    FREQUENCY: 'Hz',
    DENSITY: 'kg/m³',
    VOLUME_FLOW: 'm³/s',
    MASS_FLOW: 'kg/s',
    DYNAMIC_VISCOSITY: 'Pa·s',
    KINEMATIC_VISCOSITY: 'm²/s',
    VOLTAGE: 'V',
    RESISTANCE: 'Ω',
    CAPACITANCE: 'F',
    INDUCTANCE: 'H',
    THERMAL_CONDUCTIVITY: 'W/(m·K)',
    SPECIFIC_HEAT: 'J/(kg·K)',
    HEAT_CAPACITY: 'J/K',
    HEAT_TRANSFER_COEFF: 'W/(m²·K)',
    THERMAL_EXPANSION: '1/K',
    SPECIFIC_ENERGY: 'J/kg',
    SPECIFIC_ENTROPY: 'J/(kg·K)',
    SPECIFIC_VOLUME: 'm³/kg',
    RESISTIVITY: 'Ω·m',
    PERMEABILITY: 'H/m',
}


def dimension_to_si_unit(dim: Dimension) -> Optional[str]:
    """
    Get the SI unit symbol for a Dimension.

    Returns the SI unit symbol (e.g., 'm³' for VOLUME) or None if
    the dimension doesn't match a known physical quantity.

    Args:
        dim: Dimension object

    Returns:
        SI unit symbol string or None
    """
    # Direct lookup first
    if dim in DIMENSION_TO_SI_UNIT:
        return DIMENSION_TO_SI_UNIT[dim]

    # For dimensions not in the map, try to construct a symbol
    # This handles computed dimensions like L^4 or M^2
    if dim.is_dimensionless():
        return ''

    # Build a unit string from the dimension components
    parts = []
    if dim.length != 0:
        if dim.length == 1:
            parts.append('m')
        else:
            superscript = {
                '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
                '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
            }
            exp_str = ''.join(superscript.get(c, c) for c in str(dim.length))
            parts.append(f'm{exp_str}')
    if dim.mass != 0:
        if dim.mass == 1:
            parts.append('kg')
        else:
            superscript = {
                '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
                '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
            }
            exp_str = ''.join(superscript.get(c, c) for c in str(dim.mass))
            parts.append(f'kg{exp_str}')
    if dim.time != 0:
        superscript = {
            '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
            '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
        }
        exp_str = ''.join(superscript.get(c, c) for c in str(dim.time))
        if dim.time == 1:
            parts.append('s')
        else:
            parts.append(f's{exp_str}')
    if dim.temperature != 0:
        superscript = {
            '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
            '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹'
        }
        exp_str = ''.join(superscript.get(c, c) for c in str(dim.temperature))
        if dim.temperature == 1:
            parts.append('K')
        else:
            parts.append(f'K{exp_str}')

    if parts:
        return '·'.join(parts)

    return None
