"""
Seed Units - Populate the database with common engineering units

Units are categorized by quantity type and include full dimensional analysis.
Conversions are provided between compatible units.
"""

from sqlalchemy.orm import Session
from app.models.units import Unit, UnitConversion, UnitAlias
import logging

logger = logging.getLogger(__name__)


# Unit definitions: (symbol, name, quantity_type, L, M, T, I, Θ, N, J, is_base)
# Dimensions: Length, Mass, Time, Current, Temperature, Amount, Luminosity
UNITS = [
    # ============== BASE SI UNITS ==============
    ("m", "meter", "length", 1, 0, 0, 0, 0, 0, 0, True),
    ("kg", "kilogram", "mass", 0, 1, 0, 0, 0, 0, 0, True),
    ("s", "second", "time", 0, 0, 1, 0, 0, 0, 0, True),
    ("A", "ampere", "electric_current", 0, 0, 0, 1, 0, 0, 0, True),
    ("K", "kelvin", "temperature", 0, 0, 0, 0, 1, 0, 0, True),
    ("mol", "mole", "amount", 0, 0, 0, 0, 0, 1, 0, True),
    ("cd", "candela", "luminosity", 0, 0, 0, 0, 0, 0, 1, True),

    # ============== LENGTH ==============
    ("mm", "millimeter", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("cm", "centimeter", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("km", "kilometer", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("in", "inch", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("ft", "foot", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("yd", "yard", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("mi", "mile", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("um", "micrometer", "length", 1, 0, 0, 0, 0, 0, 0, False),
    ("nm", "nanometer", "length", 1, 0, 0, 0, 0, 0, 0, False),

    # ============== AREA ==============
    ("m²", "square meter", "area", 2, 0, 0, 0, 0, 0, 0, False),
    ("cm²", "square centimeter", "area", 2, 0, 0, 0, 0, 0, 0, False),
    ("mm²", "square millimeter", "area", 2, 0, 0, 0, 0, 0, 0, False),
    ("km²", "square kilometer", "area", 2, 0, 0, 0, 0, 0, 0, False),
    ("in²", "square inch", "area", 2, 0, 0, 0, 0, 0, 0, False),
    ("ft²", "square foot", "area", 2, 0, 0, 0, 0, 0, 0, False),

    # ============== VOLUME ==============
    ("m³", "cubic meter", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("cm³", "cubic centimeter", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("mm³", "cubic millimeter", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("L", "liter", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("mL", "milliliter", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("gal", "gallon", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("in³", "cubic inch", "volume", 3, 0, 0, 0, 0, 0, 0, False),
    ("ft³", "cubic foot", "volume", 3, 0, 0, 0, 0, 0, 0, False),

    # ============== MASS ==============
    ("g", "gram", "mass", 0, 1, 0, 0, 0, 0, 0, False),
    ("mg", "milligram", "mass", 0, 1, 0, 0, 0, 0, 0, False),
    ("t", "metric ton", "mass", 0, 1, 0, 0, 0, 0, 0, False),
    ("lb", "pound", "mass", 0, 1, 0, 0, 0, 0, 0, False),
    ("oz", "ounce", "mass", 0, 1, 0, 0, 0, 0, 0, False),

    # ============== TIME ==============
    ("ms", "millisecond", "time", 0, 0, 1, 0, 0, 0, 0, False),
    ("us", "microsecond", "time", 0, 0, 1, 0, 0, 0, 0, False),
    ("min", "minute", "time", 0, 0, 1, 0, 0, 0, 0, False),
    ("hr", "hour", "time", 0, 0, 1, 0, 0, 0, 0, False),
    ("day", "day", "time", 0, 0, 1, 0, 0, 0, 0, False),

    # ============== FREQUENCY ==============
    ("Hz", "hertz", "frequency", 0, 0, -1, 0, 0, 0, 0, False),
    ("kHz", "kilohertz", "frequency", 0, 0, -1, 0, 0, 0, 0, False),
    ("MHz", "megahertz", "frequency", 0, 0, -1, 0, 0, 0, 0, False),
    ("GHz", "gigahertz", "frequency", 0, 0, -1, 0, 0, 0, 0, False),
    ("rpm", "revolutions per minute", "frequency", 0, 0, -1, 0, 0, 0, 0, False),

    # ============== VELOCITY ==============
    ("m/s", "meters per second", "velocity", 1, 0, -1, 0, 0, 0, 0, False),
    ("km/h", "kilometers per hour", "velocity", 1, 0, -1, 0, 0, 0, 0, False),
    ("mph", "miles per hour", "velocity", 1, 0, -1, 0, 0, 0, 0, False),
    ("ft/s", "feet per second", "velocity", 1, 0, -1, 0, 0, 0, 0, False),

    # ============== ACCELERATION ==============
    ("m/s²", "meters per second squared", "acceleration", 1, 0, -2, 0, 0, 0, 0, False),
    ("g₀", "standard gravity", "acceleration", 1, 0, -2, 0, 0, 0, 0, False),
    ("ft/s²", "feet per second squared", "acceleration", 1, 0, -2, 0, 0, 0, 0, False),

    # ============== FORCE ==============
    ("N", "newton", "force", 1, 1, -2, 0, 0, 0, 0, False),
    ("kN", "kilonewton", "force", 1, 1, -2, 0, 0, 0, 0, False),
    ("mN", "millinewton", "force", 1, 1, -2, 0, 0, 0, 0, False),
    ("lbf", "pound-force", "force", 1, 1, -2, 0, 0, 0, 0, False),
    ("kgf", "kilogram-force", "force", 1, 1, -2, 0, 0, 0, 0, False),

    # ============== PRESSURE ==============
    ("Pa", "pascal", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("kPa", "kilopascal", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("MPa", "megapascal", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("GPa", "gigapascal", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("bar", "bar", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("atm", "atmosphere", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("psi", "pounds per square inch", "pressure", -1, 1, -2, 0, 0, 0, 0, False),
    ("torr", "torr", "pressure", -1, 1, -2, 0, 0, 0, 0, False),

    # ============== ENERGY ==============
    ("J", "joule", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("kJ", "kilojoule", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("MJ", "megajoule", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("cal", "calorie", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("kcal", "kilocalorie", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("Wh", "watt-hour", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("kWh", "kilowatt-hour", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("eV", "electron-volt", "energy", 2, 1, -2, 0, 0, 0, 0, False),
    ("BTU", "British thermal unit", "energy", 2, 1, -2, 0, 0, 0, 0, False),

    # ============== POWER ==============
    ("W", "watt", "power", 2, 1, -3, 0, 0, 0, 0, False),
    ("mW", "milliwatt", "power", 2, 1, -3, 0, 0, 0, 0, False),
    ("kW", "kilowatt", "power", 2, 1, -3, 0, 0, 0, 0, False),
    ("MW", "megawatt", "power", 2, 1, -3, 0, 0, 0, 0, False),
    ("hp", "horsepower", "power", 2, 1, -3, 0, 0, 0, 0, False),

    # ============== TEMPERATURE ==============
    ("°C", "degree Celsius", "temperature", 0, 0, 0, 0, 1, 0, 0, False),
    ("°F", "degree Fahrenheit", "temperature", 0, 0, 0, 0, 1, 0, 0, False),
    ("°R", "degree Rankine", "temperature", 0, 0, 0, 0, 1, 0, 0, False),

    # ============== THERMAL CONDUCTIVITY ==============
    ("W/(m·K)", "watts per meter kelvin", "thermal_conductivity", 1, 1, -3, 0, -1, 0, 0, False),
    ("W/(m·°C)", "watts per meter celsius", "thermal_conductivity", 1, 1, -3, 0, -1, 0, 0, False),
    ("BTU/(hr·ft·°F)", "BTU per hour foot fahrenheit", "thermal_conductivity", 1, 1, -3, 0, -1, 0, 0, False),

    # ============== SPECIFIC HEAT CAPACITY ==============
    ("J/(kg·K)", "joules per kilogram kelvin", "specific_heat", 2, 0, -2, 0, -1, 0, 0, False),
    ("kJ/(kg·K)", "kilojoules per kilogram kelvin", "specific_heat", 2, 0, -2, 0, -1, 0, 0, False),
    ("BTU/(lb·°F)", "BTU per pound fahrenheit", "specific_heat", 2, 0, -2, 0, -1, 0, 0, False),

    # ============== HEAT TRANSFER COEFFICIENT ==============
    ("W/(m²·K)", "watts per square meter kelvin", "heat_transfer_coeff", 0, 1, -3, 0, -1, 0, 0, False),
    ("BTU/(hr·ft²·°F)", "BTU per hour square foot fahrenheit", "heat_transfer_coeff", 0, 1, -3, 0, -1, 0, 0, False),

    # ============== DENSITY ==============
    ("kg/m³", "kilograms per cubic meter", "density", -3, 1, 0, 0, 0, 0, 0, False),
    ("g/cm³", "grams per cubic centimeter", "density", -3, 1, 0, 0, 0, 0, 0, False),
    ("lb/ft³", "pounds per cubic foot", "density", -3, 1, 0, 0, 0, 0, 0, False),
    ("lb/in³", "pounds per cubic inch", "density", -3, 1, 0, 0, 0, 0, 0, False),

    # ============== DYNAMIC VISCOSITY ==============
    ("Pa·s", "pascal second", "dynamic_viscosity", -1, 1, -1, 0, 0, 0, 0, False),
    ("mPa·s", "millipascal second", "dynamic_viscosity", -1, 1, -1, 0, 0, 0, 0, False),
    ("cP", "centipoise", "dynamic_viscosity", -1, 1, -1, 0, 0, 0, 0, False),

    # ============== KINEMATIC VISCOSITY ==============
    ("m²/s", "square meters per second", "kinematic_viscosity", 2, 0, -1, 0, 0, 0, 0, False),
    ("cSt", "centistokes", "kinematic_viscosity", 2, 0, -1, 0, 0, 0, 0, False),

    # ============== ELECTRIC ==============
    ("V", "volt", "voltage", 2, 1, -3, -1, 0, 0, 0, False),
    ("mV", "millivolt", "voltage", 2, 1, -3, -1, 0, 0, 0, False),
    ("kV", "kilovolt", "voltage", 2, 1, -3, -1, 0, 0, 0, False),
    ("Ω", "ohm", "resistance", 2, 1, -3, -2, 0, 0, 0, False),
    ("kΩ", "kilohm", "resistance", 2, 1, -3, -2, 0, 0, 0, False),
    ("MΩ", "megohm", "resistance", 2, 1, -3, -2, 0, 0, 0, False),
    ("mA", "milliampere", "electric_current", 0, 0, 0, 1, 0, 0, 0, False),
    ("μA", "microampere", "electric_current", 0, 0, 0, 1, 0, 0, 0, False),
    ("C", "coulomb", "electric_charge", 0, 0, 1, 1, 0, 0, 0, False),
    ("F", "farad", "capacitance", -2, -1, 4, 2, 0, 0, 0, False),
    ("μF", "microfarad", "capacitance", -2, -1, 4, 2, 0, 0, 0, False),
    ("nF", "nanofarad", "capacitance", -2, -1, 4, 2, 0, 0, 0, False),
    ("pF", "picofarad", "capacitance", -2, -1, 4, 2, 0, 0, 0, False),
    ("H", "henry", "inductance", 2, 1, -2, -2, 0, 0, 0, False),
    ("mH", "millihenry", "inductance", 2, 1, -2, -2, 0, 0, 0, False),

    # ============== SOUND ==============
    ("dB", "decibel", "sound_level", 0, 0, 0, 0, 0, 0, 0, False),  # Dimensionless (logarithmic)
    ("dB(A)", "A-weighted decibel", "sound_level", 0, 0, 0, 0, 0, 0, 0, False),

    # ============== ANGLE ==============
    ("rad", "radian", "angle", 0, 0, 0, 0, 0, 0, 0, False),  # Dimensionless
    ("°", "degree", "angle", 0, 0, 0, 0, 0, 0, 0, False),
    ("'", "arcminute", "angle", 0, 0, 0, 0, 0, 0, 0, False),
    ("\"", "arcsecond", "angle", 0, 0, 0, 0, 0, 0, 0, False),

    # ============== DIMENSIONLESS ==============
    ("%", "percent", "ratio", 0, 0, 0, 0, 0, 0, 0, False),
    ("ppm", "parts per million", "ratio", 0, 0, 0, 0, 0, 0, 0, False),

    # ============== STRESS/YOUNG'S MODULUS (same dimensions as pressure) ==============
    # Already covered by pressure units (Pa, MPa, GPa, psi)

    # ============== TORQUE ==============
    ("N·m", "newton meter", "torque", 2, 1, -2, 0, 0, 0, 0, False),
    ("kN·m", "kilonewton meter", "torque", 2, 1, -2, 0, 0, 0, 0, False),
    ("lb·ft", "pound-foot", "torque", 2, 1, -2, 0, 0, 0, 0, False),
    ("lb·in", "pound-inch", "torque", 2, 1, -2, 0, 0, 0, 0, False),

    # ============== MASS FLOW RATE ==============
    ("kg/s", "kilograms per second", "mass_flow", 0, 1, -1, 0, 0, 0, 0, False),
    ("kg/hr", "kilograms per hour", "mass_flow", 0, 1, -1, 0, 0, 0, 0, False),
    ("lb/s", "pounds per second", "mass_flow", 0, 1, -1, 0, 0, 0, 0, False),
    ("lb/hr", "pounds per hour", "mass_flow", 0, 1, -1, 0, 0, 0, 0, False),

    # ============== VOLUMETRIC FLOW RATE ==============
    ("m³/s", "cubic meters per second", "volume_flow", 3, 0, -1, 0, 0, 0, 0, False),
    ("L/s", "liters per second", "volume_flow", 3, 0, -1, 0, 0, 0, 0, False),
    ("L/min", "liters per minute", "volume_flow", 3, 0, -1, 0, 0, 0, 0, False),
    ("gpm", "gallons per minute", "volume_flow", 3, 0, -1, 0, 0, 0, 0, False),
    ("cfm", "cubic feet per minute", "volume_flow", 3, 0, -1, 0, 0, 0, 0, False),
]


# Conversions: (from_symbol, to_symbol, multiplier, offset)
# Formula: to_value = from_value * multiplier + offset
CONVERSIONS = [
    # Length
    ("mm", "m", 0.001, 0),
    ("cm", "m", 0.01, 0),
    ("km", "m", 1000, 0),
    ("in", "m", 0.0254, 0),
    ("ft", "m", 0.3048, 0),
    ("yd", "m", 0.9144, 0),
    ("mi", "m", 1609.344, 0),
    ("um", "m", 1e-6, 0),
    ("nm", "m", 1e-9, 0),

    # Area
    ("cm²", "m²", 0.0001, 0),
    ("mm²", "m²", 1e-6, 0),
    ("km²", "m²", 1e6, 0),
    ("in²", "m²", 0.00064516, 0),
    ("ft²", "m²", 0.092903, 0),

    # Volume
    ("cm³", "m³", 1e-6, 0),
    ("mm³", "m³", 1e-9, 0),
    ("L", "m³", 0.001, 0),
    ("mL", "m³", 1e-6, 0),
    ("gal", "m³", 0.003785412, 0),
    ("in³", "m³", 1.6387064e-5, 0),
    ("ft³", "m³", 0.0283168, 0),

    # Mass
    ("g", "kg", 0.001, 0),
    ("mg", "kg", 1e-6, 0),
    ("t", "kg", 1000, 0),
    ("lb", "kg", 0.45359237, 0),
    ("oz", "kg", 0.028349523, 0),

    # Time
    ("ms", "s", 0.001, 0),
    ("us", "s", 1e-6, 0),
    ("min", "s", 60, 0),
    ("hr", "s", 3600, 0),
    ("day", "s", 86400, 0),

    # Frequency
    ("kHz", "Hz", 1000, 0),
    ("MHz", "Hz", 1e6, 0),
    ("GHz", "Hz", 1e9, 0),
    ("rpm", "Hz", 1/60, 0),

    # Velocity
    ("km/h", "m/s", 1/3.6, 0),
    ("mph", "m/s", 0.44704, 0),
    ("ft/s", "m/s", 0.3048, 0),

    # Acceleration
    ("g₀", "m/s²", 9.80665, 0),
    ("ft/s²", "m/s²", 0.3048, 0),

    # Force
    ("kN", "N", 1000, 0),
    ("mN", "N", 0.001, 0),
    ("lbf", "N", 4.448222, 0),
    ("kgf", "N", 9.80665, 0),

    # Pressure
    ("kPa", "Pa", 1000, 0),
    ("MPa", "Pa", 1e6, 0),
    ("GPa", "Pa", 1e9, 0),
    ("bar", "Pa", 1e5, 0),
    ("atm", "Pa", 101325, 0),
    ("psi", "Pa", 6894.757, 0),
    ("torr", "Pa", 133.322, 0),

    # Energy
    ("kJ", "J", 1000, 0),
    ("MJ", "J", 1e6, 0),
    ("cal", "J", 4.184, 0),
    ("kcal", "J", 4184, 0),
    ("Wh", "J", 3600, 0),
    ("kWh", "J", 3.6e6, 0),
    ("eV", "J", 1.602176634e-19, 0),
    ("BTU", "J", 1055.06, 0),

    # Power
    ("mW", "W", 0.001, 0),
    ("kW", "W", 1000, 0),
    ("MW", "W", 1e6, 0),
    ("hp", "W", 745.7, 0),

    # Temperature (with offsets)
    ("°C", "K", 1, 273.15),
    ("°F", "K", 5/9, 255.372222),  # (°F + 459.67) × 5/9
    ("°R", "K", 5/9, 0),

    # Thermal Conductivity
    ("W/(m·°C)", "W/(m·K)", 1, 0),  # Same for thermal conductivity
    ("BTU/(hr·ft·°F)", "W/(m·K)", 1.730735, 0),

    # Specific Heat
    ("kJ/(kg·K)", "J/(kg·K)", 1000, 0),
    ("BTU/(lb·°F)", "J/(kg·K)", 4186.8, 0),

    # Heat Transfer Coefficient
    ("BTU/(hr·ft²·°F)", "W/(m²·K)", 5.678263, 0),

    # Density
    ("g/cm³", "kg/m³", 1000, 0),
    ("lb/ft³", "kg/m³", 16.01846, 0),
    ("lb/in³", "kg/m³", 27679.9, 0),

    # Dynamic Viscosity
    ("mPa·s", "Pa·s", 0.001, 0),
    ("cP", "Pa·s", 0.001, 0),

    # Kinematic Viscosity
    ("cSt", "m²/s", 1e-6, 0),

    # Voltage
    ("mV", "V", 0.001, 0),
    ("kV", "V", 1000, 0),

    # Resistance
    ("kΩ", "Ω", 1000, 0),
    ("MΩ", "Ω", 1e6, 0),

    # Current
    ("mA", "A", 0.001, 0),
    ("μA", "A", 1e-6, 0),

    # Capacitance
    ("μF", "F", 1e-6, 0),
    ("nF", "F", 1e-9, 0),
    ("pF", "F", 1e-12, 0),

    # Inductance
    ("mH", "H", 0.001, 0),

    # Angle
    ("°", "rad", 0.017453293, 0),  # π/180
    ("'", "rad", 0.000290888, 0),   # π/10800
    ("\"", "rad", 4.84814e-6, 0),   # π/648000

    # Ratio
    ("ppm", "%", 0.0001, 0),

    # Torque
    ("kN·m", "N·m", 1000, 0),
    ("lb·ft", "N·m", 1.355818, 0),
    ("lb·in", "N·m", 0.1129848, 0),

    # Mass Flow
    ("kg/hr", "kg/s", 1/3600, 0),
    ("lb/s", "kg/s", 0.45359237, 0),
    ("lb/hr", "kg/s", 0.45359237/3600, 0),

    # Volume Flow
    ("L/s", "m³/s", 0.001, 0),
    ("L/min", "m³/s", 1/60000, 0),
    ("gpm", "m³/s", 6.30902e-5, 0),
    ("cfm", "m³/s", 0.000471947, 0),
]


# Common aliases
ALIASES = [
    ("meter", "m"),
    ("meters", "m"),
    ("metre", "m"),
    ("metres", "m"),
    ("kilometer", "km"),
    ("kilometers", "km"),
    ("kilometre", "km"),
    ("kilometres", "km"),
    ("centimeter", "cm"),
    ("centimeters", "cm"),
    ("centimetre", "cm"),
    ("centimetres", "cm"),
    ("millimeter", "mm"),
    ("millimeters", "mm"),
    ("millimetre", "mm"),
    ("millimetres", "mm"),
    ("inch", "in"),
    ("inches", "in"),
    ("foot", "ft"),
    ("feet", "ft"),
    ("kilogram", "kg"),
    ("kilograms", "kg"),
    ("gram", "g"),
    ("grams", "g"),
    ("pound", "lb"),
    ("pounds", "lb"),
    ("second", "s"),
    ("seconds", "s"),
    ("sec", "s"),
    ("minute", "min"),
    ("minutes", "min"),
    ("hour", "hr"),
    ("hours", "hr"),
    ("watt", "W"),
    ("watts", "W"),
    ("kilowatt", "kW"),
    ("kilowatts", "kW"),
    ("joule", "J"),
    ("joules", "J"),
    ("newton", "N"),
    ("newtons", "N"),
    ("pascal", "Pa"),
    ("pascals", "Pa"),
    ("kelvin", "K"),
    ("celsius", "°C"),
    ("fahrenheit", "°F"),
    ("hertz", "Hz"),
    ("volt", "V"),
    ("volts", "V"),
    ("ampere", "A"),
    ("amperes", "A"),
    ("amp", "A"),
    ("amps", "A"),
    ("ohm", "Ω"),
    ("ohms", "Ω"),
    ("degree", "°"),
    ("degrees", "°"),
    ("deg", "°"),
    ("radian", "rad"),
    ("radians", "rad"),
    ("liter", "L"),
    ("liters", "L"),
    ("litre", "L"),
    ("litres", "L"),
]


def seed_units(db: Session, force: bool = False) -> dict:
    """
    Seed the database with common engineering units.

    Args:
        db: Database session
        force: If True, delete existing units first

    Returns:
        dict with counts of created items
    """
    created = {"units": 0, "conversions": 0, "aliases": 0}

    if force:
        db.query(UnitAlias).delete()
        db.query(UnitConversion).delete()
        db.query(Unit).delete()
        db.commit()
        logger.info("Cleared existing units data")

    # Create units
    unit_map = {}  # symbol -> Unit
    for i, (symbol, name, qty_type, L, M, T, I, Th, N, J, is_base) in enumerate(UNITS):
        existing = db.query(Unit).filter(Unit.symbol == symbol).first()
        if existing:
            unit_map[symbol] = existing
            continue

        unit = Unit(
            symbol=symbol,
            name=name,
            quantity_type=qty_type,
            length_dim=L,
            mass_dim=M,
            time_dim=T,
            current_dim=I,
            temperature_dim=Th,
            amount_dim=N,
            luminosity_dim=J,
            is_base_unit=is_base,
            display_order=i
        )
        db.add(unit)
        db.flush()  # Get the ID
        unit_map[symbol] = unit
        created["units"] += 1

    db.commit()

    # Create conversions
    for from_sym, to_sym, mult, offset in CONVERSIONS:
        from_unit = unit_map.get(from_sym)
        to_unit = unit_map.get(to_sym)

        if not from_unit or not to_unit:
            logger.warning(f"Skipping conversion {from_sym} -> {to_sym}: unit not found")
            continue

        existing = db.query(UnitConversion).filter(
            UnitConversion.from_unit_id == from_unit.id,
            UnitConversion.to_unit_id == to_unit.id
        ).first()
        if existing:
            continue

        conversion = UnitConversion(
            from_unit_id=from_unit.id,
            to_unit_id=to_unit.id,
            multiplier=mult,
            offset=offset
        )
        db.add(conversion)
        created["conversions"] += 1

    db.commit()

    # Create aliases
    for alias_name, symbol in ALIASES:
        unit = unit_map.get(symbol)
        if not unit:
            continue

        existing = db.query(UnitAlias).filter(UnitAlias.alias == alias_name).first()
        if existing:
            continue

        alias = UnitAlias(alias=alias_name, unit_id=unit.id)
        db.add(alias)
        created["aliases"] += 1

    db.commit()

    logger.info(f"Seeded units: {created['units']} units, {created['conversions']} conversions, {created['aliases']} aliases")
    return created
