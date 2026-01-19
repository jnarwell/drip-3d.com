"""
Centralized Unit Conversion Constants

Single source of truth for unit conversion factors in the backend.
All services should import from here instead of defining their own dicts.

These constants mirror what's in the database but are available synchronously
for use in expression parsing and other performance-critical code paths.
"""

# SI base units for each dimension/quantity type
DIMENSION_SI_UNITS = {
    'length': 'm',
    'area': 'm²',
    'volume': 'm³',
    'mass': 'kg',
    'force': 'N',
    'pressure': 'Pa',
    'temperature': 'K',
    'time': 's',
    'frequency': 'Hz',
    'energy': 'J',
    'power': 'W',
    'torque': 'N·m',
    'current': 'A',
    'voltage': 'V',
    'resistance': 'Ω',
    'capacitance': 'F',
    'inductance': 'H',
    'angle': 'rad',
    'velocity': 'm/s',
    'acceleration': 'm/s²',
    'density': 'kg/m³',
    'dynamic_viscosity': 'Pa·s',
    'kinematic_viscosity': 'm²/s',
    'thermal_conductivity': 'W/(m·K)',
    'specific_heat': 'J/(kg·K)',
    'heat_transfer_coeff': 'W/(m²·K)',
    'volume_flow': 'm³/s',
    'mass_flow': 'kg/s',
}

# Map unit symbols to their dimension/quantity type
UNIT_TO_DIMENSION = {
    # Length
    'nm': 'length', 'μm': 'length', 'mm': 'length', 'cm': 'length', 'm': 'length', 'km': 'length',
    'in': 'length', 'ft': 'length', 'yd': 'length', 'mi': 'length', 'mil': 'length', 'thou': 'length',
    # Area
    'mm²': 'area', 'cm²': 'area', 'm²': 'area', 'km²': 'area', 'ha': 'area',
    'in²': 'area', 'ft²': 'area', 'yd²': 'area', 'mi²': 'area', 'acre': 'area',
    # Volume
    'mm³': 'volume', 'cm³': 'volume', 'mL': 'volume', 'L': 'volume', 'm³': 'volume', 'km³': 'volume',
    'in³': 'volume', 'ft³': 'volume', 'gal': 'volume', 'fl oz': 'volume', 'bbl': 'volume',
    # Mass
    'μg': 'mass', 'mg': 'mass', 'g': 'mass', 'kg': 'mass', 't': 'mass', 'Mt': 'mass',
    'oz': 'mass', 'lb': 'mass', 'ton': 'mass', 'grain': 'mass',
    # Force
    'μN': 'force', 'mN': 'force', 'N': 'force', 'kN': 'force', 'MN': 'force',
    'lbf': 'force', 'ozf': 'force', 'kip': 'force', 'pdl': 'force', 'kgf': 'force',
    # Pressure
    'Pa': 'pressure', 'kPa': 'pressure', 'MPa': 'pressure', 'GPa': 'pressure',
    'bar': 'pressure', 'mbar': 'pressure', 'psi': 'pressure', 'ksi': 'pressure',
    'psf': 'pressure', 'inHg': 'pressure', 'inH₂O': 'pressure',
    # Temperature (with common aliases)
    'K': 'temperature', 'kelvin': 'temperature',
    '°C': 'temperature', '℃': 'temperature', 'degC': 'temperature', 'celsius': 'temperature',
    '°F': 'temperature', '℉': 'temperature', 'degF': 'temperature', 'fahrenheit': 'temperature',
    '°R': 'temperature', 'rankine': 'temperature',
    # Time
    'ps': 'time', 'ns': 'time', 'μs': 'time', 'ms': 'time', 's': 'time',
    'min': 'time', 'h': 'time', 'd': 'time', 'wk': 'time', 'mo': 'time', 'yr': 'time',
    # Frequency
    'Hz': 'frequency', 'kHz': 'frequency', 'MHz': 'frequency', 'GHz': 'frequency', 'THz': 'frequency',
    'mHz': 'frequency', 'rpm': 'frequency', 'rps': 'frequency',
    # Energy
    'J': 'energy', 'kJ': 'energy', 'MJ': 'energy', 'GJ': 'energy',
    'Wh': 'energy', 'kWh': 'energy', 'cal': 'energy', 'eV': 'energy',
    'BTU': 'energy', 'ft·lbf': 'energy', 'hp·h': 'energy',
    # Power
    'W': 'power', 'mW': 'power', 'kW': 'power', 'MW': 'power', 'GW': 'power',
    'hp': 'power', 'BTU/h': 'power', 'ft·lbf/s': 'power',
    # Torque
    'N·m': 'torque', 'kN·m': 'torque', 'lb·ft': 'torque', 'lb·in': 'torque', 'lbf·ft': 'torque',
    # Electrical
    'A': 'current', 'mA': 'current', 'μA': 'current',
    'V': 'voltage', 'mV': 'voltage', 'kV': 'voltage',
    'Ω': 'resistance', 'kΩ': 'resistance', 'MΩ': 'resistance',
    'F': 'capacitance', 'μF': 'capacitance', 'nF': 'capacitance', 'pF': 'capacitance',
    'H': 'inductance', 'mH': 'inductance',
    # Angle
    'rad': 'angle', 'mrad': 'angle', 'deg': 'angle', '°': 'angle', "'": 'angle', '"': 'angle',
    # Velocity
    'm/s': 'velocity', 'km/h': 'velocity', 'ft/s': 'velocity', 'mph': 'velocity',
    # Acceleration
    'm/s²': 'acceleration', 'g₀': 'acceleration', 'ft/s²': 'acceleration',
    # Density
    'kg/m³': 'density', 'g/cm³': 'density', 'kg/L': 'density', 'g/mL': 'density',
    'lb/ft³': 'density', 'lb/in³': 'density', 'lb/gal': 'density', 'oz/in³': 'density',
    # Viscosity
    'Pa·s': 'dynamic_viscosity', 'mPa·s': 'dynamic_viscosity', 'cP': 'dynamic_viscosity',
    'm²/s': 'kinematic_viscosity', 'cSt': 'kinematic_viscosity',
    # Thermal
    'W/(m·K)': 'thermal_conductivity', 'W/(m·°C)': 'thermal_conductivity', 'BTU/(hr·ft·°F)': 'thermal_conductivity',
    'J/(kg·K)': 'specific_heat', 'kJ/(kg·K)': 'specific_heat', 'cal/(g·°C)': 'specific_heat', 'BTU/(lb·°F)': 'specific_heat',
    'W/(m²·K)': 'heat_transfer_coeff', 'BTU/(hr·ft²·°F)': 'heat_transfer_coeff',
    # Flow
    'm³/s': 'volume_flow', 'L/s': 'volume_flow', 'L/min': 'volume_flow', 'gpm': 'volume_flow', 'cfm': 'volume_flow',
    'kg/s': 'mass_flow', 'kg/hr': 'mass_flow', 'lb/s': 'mass_flow', 'lb/hr': 'mass_flow',
}

# Unit conversion factors to SI base units
# Multiply value in source unit by factor to get SI value
# Note: Temperature requires special handling (offset conversion)
UNIT_TO_SI = {
    # Length -> meters
    'nm': 1e-9, 'μm': 1e-6, 'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
    'in': 0.0254, 'ft': 0.3048, 'yd': 0.9144, 'mi': 1609.344,
    'mil': 0.0000254, 'thou': 0.0000254,
    # Area -> m²
    'mm²': 1e-6, 'cm²': 1e-4, 'm²': 1, 'km²': 1e6, 'ha': 1e4,
    'in²': 0.00064516, 'ft²': 0.092903, 'yd²': 0.836127, 'mi²': 2.59e6, 'acre': 4046.86,
    # Volume -> m³
    'mm³': 1e-9, 'cm³': 1e-6, 'mL': 1e-6, 'L': 0.001, 'm³': 1, 'km³': 1e9,
    'in³': 1.6387e-5, 'ft³': 0.0283168, 'fl oz': 2.9574e-5, 'gal': 0.00378541, 'bbl': 0.158987,
    # Mass -> kg
    'μg': 1e-9, 'mg': 1e-6, 'g': 0.001, 'kg': 1, 't': 1000, 'Mt': 1e6,
    'oz': 0.0283495, 'lb': 0.453592, 'ton': 907.185, 'grain': 6.4799e-5,
    # Force -> N
    'μN': 1e-6, 'mN': 1e-3, 'N': 1, 'kN': 1000, 'MN': 1e6,
    'lbf': 4.44822, 'ozf': 0.278014, 'kip': 4448.22, 'pdl': 0.138255, 'kgf': 9.80665,
    # Pressure -> Pa
    'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9,
    'bar': 1e5, 'mbar': 100, 'psi': 6894.76, 'ksi': 6.89476e6,
    'psf': 47.8803, 'inHg': 3386.39, 'inH₂O': 249.082,
    # Temperature -> K (factor only, offset handled separately)
    # These are scale factors, NOT for absolute temperature conversion
    'K': 1, 'kelvin': 1,
    '°C': 1, '℃': 1, 'degC': 1, 'celsius': 1,  # Same scale as K
    '°F': 5/9, '℉': 5/9, 'degF': 5/9, 'fahrenheit': 5/9,
    '°R': 5/9, 'rankine': 5/9,
    # Time -> seconds
    'ps': 1e-12, 'ns': 1e-9, 'μs': 1e-6, 'ms': 0.001, 's': 1,
    'min': 60, 'h': 3600, 'd': 86400, 'wk': 604800, 'mo': 2.628e6, 'yr': 3.154e7,
    # Frequency -> Hz
    'Hz': 1, 'kHz': 1000, 'MHz': 1e6, 'GHz': 1e9, 'THz': 1e12,
    'mHz': 0.001, 'rpm': 1/60, 'rps': 1,
    # Energy -> J
    'J': 1, 'kJ': 1000, 'MJ': 1e6, 'GJ': 1e9,
    'Wh': 3600, 'kWh': 3.6e6, 'cal': 4.184, 'eV': 1.6022e-19,
    'BTU': 1055.06, 'ft·lbf': 1.35582, 'hp·h': 2.685e6,
    # Power -> W
    'W': 1, 'mW': 0.001, 'kW': 1000, 'MW': 1e6, 'GW': 1e9,
    'hp': 745.7, 'BTU/h': 0.293071, 'ft·lbf/s': 1.35582,
    # Torque -> N·m
    'N·m': 1, 'kN·m': 1000, 'lb·ft': 1.35582, 'lb·in': 0.112985, 'lbf·ft': 1.35582,
    # Electrical
    'A': 1, 'mA': 0.001, 'μA': 1e-6,
    'V': 1, 'mV': 0.001, 'kV': 1000,
    'Ω': 1, 'kΩ': 1000, 'MΩ': 1e6,
    'F': 1, 'μF': 1e-6, 'nF': 1e-9, 'pF': 1e-12,
    'H': 1, 'mH': 0.001,
    # Angle -> radians
    'rad': 1, 'mrad': 0.001, 'deg': 0.0174533, '°': 0.0174533,
    "'": 0.000290888, '"': 4.8481e-6,  # arcminute, arcsecond
    # Velocity -> m/s
    'm/s': 1, 'km/h': 0.277778, 'ft/s': 0.3048, 'mph': 0.44704,
    # Acceleration -> m/s²
    'm/s²': 1, 'g₀': 9.80665, 'ft/s²': 0.3048,
    # Density -> kg/m³
    'kg/m³': 1, 'g/cm³': 1000, 'kg/L': 1000, 'g/mL': 1000,
    'lb/ft³': 16.0185, 'lb/in³': 27679.9, 'lb/gal': 119.826, 'oz/in³': 1729.99,
    # Viscosity
    'Pa·s': 1, 'mPa·s': 0.001, 'cP': 0.001,
    'm²/s': 1, 'cSt': 1e-6,
    # Thermal
    'W/(m·K)': 1, 'W/(m·°C)': 1, 'BTU/(hr·ft·°F)': 1.731,
    'J/(kg·K)': 1, 'kJ/(kg·K)': 1000, 'cal/(g·°C)': 4184, 'BTU/(lb·°F)': 4186.8,
    'W/(m²·K)': 1, 'BTU/(hr·ft²·°F)': 5.678,
    # Flow
    'm³/s': 1, 'L/s': 0.001, 'L/min': 1.6667e-5, 'gpm': 6.309e-5, 'cfm': 4.719e-4,
    'kg/s': 1, 'kg/hr': 1/3600, 'lb/s': 0.453592, 'lb/hr': 0.000126,
    # Thermal expansion
    '1/K': 1, '1/°C': 1, 'ppm/K': 1e-6, 'ppm/°C': 1e-6, 'µm/(m·K)': 1e-6,
    '1/°F': 1.8, '1/°R': 1.8, 'ppm/°F': 1.8e-6,
}

# Temperature conversion offsets (for absolute temperature, not intervals)
# Formula: K = value * factor + offset
TEMPERATURE_OFFSETS = {
    'K': 0,
    'kelvin': 0,
    '°C': 273.15,
    '℃': 273.15,
    'degC': 273.15,
    'celsius': 273.15,
    '°F': 255.372,  # (F - 32) * 5/9 + 273.15 = F * 5/9 + 255.372
    '℉': 255.372,
    'degF': 255.372,
    'fahrenheit': 255.372,
    '°R': 0,  # Rankine is absolute, just scaled
    'rankine': 0,
}


import re

def _normalize_unit_string(unit_str: str) -> str:
    """
    Convert ASCII caret notation to Unicode superscripts.

    This ensures consistent unit matching regardless of input format:
    - "mm^2" → "mm²"
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


def convert_to_si(value: float, unit: str) -> float:
    """Convert a value to SI base unit. Returns None if value is None."""
    if value is None:
        return None
    # Normalize unit string (e.g., mm^2 -> mm²) for consistent lookup
    normalized_unit = _normalize_unit_string(unit)
    if normalized_unit in TEMPERATURE_OFFSETS and normalized_unit not in ('K', 'kelvin', '°R', 'rankine'):
        # Temperature with offset
        factor = UNIT_TO_SI.get(normalized_unit, 1)
        offset = TEMPERATURE_OFFSETS.get(normalized_unit, 0)
        return value * factor + offset
    else:
        # Simple multiplication
        factor = UNIT_TO_SI.get(normalized_unit, 1)
        return value * factor


def convert_from_si(value: float, unit: str) -> float:
    """Convert a value from SI base unit to target unit. Returns None if value is None."""
    if value is None:
        return None
    # Normalize unit string (e.g., mm^2 -> mm²) for consistent lookup
    normalized_unit = _normalize_unit_string(unit)
    if normalized_unit in TEMPERATURE_OFFSETS and normalized_unit not in ('K', 'kelvin', '°R', 'rankine'):
        # Temperature with offset
        factor = UNIT_TO_SI.get(normalized_unit, 1)
        offset = TEMPERATURE_OFFSETS.get(normalized_unit, 0)
        if factor == 0:
            return value
        return (value - offset) / factor
    else:
        # Simple division
        factor = UNIT_TO_SI.get(normalized_unit, 1)
        if factor == 0:
            return value
        return value / factor


def get_si_unit(unit: str) -> str:
    """Get the SI base unit for a given unit."""
    # Normalize unit string for consistent lookup
    normalized_unit = _normalize_unit_string(unit)
    dimension = UNIT_TO_DIMENSION.get(normalized_unit)
    if dimension:
        return DIMENSION_SI_UNITS.get(dimension, unit)
    return unit
