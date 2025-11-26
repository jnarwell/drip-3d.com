"""Unit calculation service for formula results"""
import re
from typing import Dict, Optional, Tuple, List
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class UnitExpression:
    """Represents a unit expression with exponents"""
    units: Dict[str, float]  # Base unit -> exponent
    
    def __str__(self) -> str:
        """Convert to human-readable format"""
        if not self.units:
            return ""
        
        # Sort units: positive exponents first, then negative
        positive = []
        negative = []
        
        for unit, exp in sorted(self.units.items()):
            if exp == 0:
                continue
            elif exp == 1:
                positive.append(unit)
            elif exp == -1:
                negative.append(unit)
            elif exp > 0:
                if exp == int(exp):
                    positive.append(f"{unit}^{int(exp)}")
                else:
                    positive.append(f"{unit}^{exp}")
            else:
                if exp == int(exp):
                    negative.append(f"{unit}^{int(-exp)}")
                else:
                    negative.append(f"{unit}^{-exp}")
        
        # Format the result
        if positive and negative:
            return f"{' · '.join(positive)} / {' · '.join(negative)}"
        elif positive:
            return " · ".join(positive)
        elif negative:
            return f"1 / {' · '.join(negative)}"
        else:
            return ""
    
    def multiply(self, other: 'UnitExpression') -> 'UnitExpression':
        """Multiply two unit expressions"""
        result = self.units.copy()
        
        for unit, exp in other.units.items():
            if unit in result:
                result[unit] += exp
                # Remove if exponent becomes zero
                if result[unit] == 0:
                    del result[unit]
            else:
                result[unit] = exp
        
        return UnitExpression(result)
    
    def divide(self, other: 'UnitExpression') -> 'UnitExpression':
        """Divide one unit expression by another"""
        result = self.units.copy()
        
        for unit, exp in other.units.items():
            if unit in result:
                result[unit] -= exp
                # Remove if exponent becomes zero
                if result[unit] == 0:
                    del result[unit]
            else:
                result[unit] = -exp
        
        return UnitExpression(result)
    
    def power(self, exponent: float) -> 'UnitExpression':
        """Raise unit expression to a power"""
        result = {}
        for unit, exp in self.units.items():
            new_exp = exp * exponent
            if new_exp != 0:
                result[unit] = new_exp
        
        return UnitExpression(result)


class UnitCalculator:
    """Calculates resulting units from mathematical operations"""
    
    # Common unit mappings to base units
    UNIT_DECOMPOSITION = {
        # Force
        "N": {"kg": 1, "m": 1, "s": -2},  # Newton = kg·m/s²
        "kN": {"kg": 1, "m": 1, "s": -2},  # kilo Newton (scale factor handled separately)
        "lbf": {"kg": 1, "m": 1, "s": -2},  # pound force
        
        # Pressure/Stress
        "Pa": {"kg": 1, "m": -1, "s": -2},  # Pascal = N/m²
        "kPa": {"kg": 1, "m": -1, "s": -2},
        "MPa": {"kg": 1, "m": -1, "s": -2},
        "GPa": {"kg": 1, "m": -1, "s": -2},
        "psi": {"kg": 1, "m": -1, "s": -2},
        
        # Energy
        "J": {"kg": 1, "m": 2, "s": -2},  # Joule = kg·m²/s²
        "kJ": {"kg": 1, "m": 2, "s": -2},
        
        # Power
        "W": {"kg": 1, "m": 2, "s": -3},  # Watt = J/s
        "kW": {"kg": 1, "m": 2, "s": -3},
        
        # Electrical
        "V": {"kg": 1, "m": 2, "s": -3, "A": -1},  # Volt
        "A": {"A": 1},  # Ampere (base unit)
        "Ω": {"kg": 1, "m": 2, "s": -3, "A": -2},  # Ohm
        
        # Thermal
        "K": {"K": 1},  # Kelvin (base unit)
        "°C": {"K": 1},  # Celsius (same dimension as Kelvin)
        
        # Frequency
        "Hz": {"s": -1},  # Hertz = 1/s
        "kHz": {"s": -1},
        "MHz": {"s": -1},
        
        # Base units
        "m": {"m": 1},
        "mm": {"m": 1},
        "cm": {"m": 1},
        "km": {"m": 1},
        "in": {"m": 1},
        "ft": {"m": 1},
        "kg": {"kg": 1},
        "g": {"kg": 1},
        "lb": {"kg": 1},
        "s": {"s": 1},
        "ms": {"s": 1},
        "min": {"s": 1},
        "h": {"s": 1},
    }
    
    @classmethod
    def parse_unit(cls, unit_str: str) -> UnitExpression:
        """Parse a unit string into a UnitExpression"""
        if not unit_str or unit_str.strip() == "":
            return UnitExpression({})
        
        unit_str = unit_str.strip()
        
        # Check if it's a known unit
        if unit_str in cls.UNIT_DECOMPOSITION:
            return UnitExpression(cls.UNIT_DECOMPOSITION[unit_str].copy())
        
        # Handle compound units like m/s, kg·m/s², etc.
        # For now, treat unknown units as base units
        return UnitExpression({unit_str: 1})
    
    @classmethod
    def calculate_formula_units(
        cls,
        expression: str,
        variable_units: Dict[str, str]
    ) -> Optional[str]:
        """
        Calculate the resulting unit from a formula expression
        
        Args:
            expression: The formula expression (e.g., "length * width")
            variable_units: Dict mapping variable names to their units
            
        Returns:
            The calculated unit string, or None if unable to calculate
        """
        try:
            # For addition/subtraction, all terms must have same unit
            # Constants are assumed to have the unit of the variable they're with
            if "+" in expression or "-" in expression:
                # Find the first variable in the expression to get the unit
                for var_name, unit in variable_units.items():
                    if var_name in expression:
                        return unit
                return None
            
            # Simple multiplication (no other operators)
            if "*" in expression and "/" not in expression and "^" not in expression:
                # Handle var * const or const * var
                parts = expression.split("*")
                if len(parts) == 2:
                    var1 = parts[0].strip()
                    var2 = parts[1].strip()
                    
                    # Both are variables
                    if var1 in variable_units and var2 in variable_units:
                        unit1 = cls.parse_unit(variable_units[var1])
                        unit2 = cls.parse_unit(variable_units[var2])
                        result = unit1.multiply(unit2)
                        return str(result)
                    
                    # One is a variable, one is a constant - unit stays the same
                    elif var1 in variable_units or var2 in variable_units:
                        return variable_units.get(var1, variable_units.get(var2))
            
            # Simple division
            if "/" in expression and "*" not in expression and "^" not in expression:
                parts = expression.split("/")
                if len(parts) == 2:
                    var1 = parts[0].strip()
                    var2 = parts[1].strip()
                    
                    # Variable / constant - unit stays the same
                    if var1 in variable_units and var2 not in variable_units:
                        return variable_units[var1]
                    
                    # Variable / variable
                    elif var1 in variable_units and var2 in variable_units:
                        unit1 = cls.parse_unit(variable_units[var1])
                        unit2 = cls.parse_unit(variable_units[var2])
                        result = unit1.divide(unit2)
                        return str(result)
            
            # For exponents like length^2
            exp_match = re.match(r'^(\w+)\s*\^\s*(\d+(?:\.\d+)?)$', expression.strip())
            if exp_match:
                var = exp_match.group(1)
                exp = float(exp_match.group(2))
                
                if var in variable_units:
                    unit = cls.parse_unit(variable_units[var])
                    result = unit.power(exp)
                    return str(result)
            
            # Default: return None if we can't determine the unit
            return None
            
        except Exception as e:
            logger.error(f"Error calculating units for expression '{expression}': {e}")
            return None
    
    @classmethod
    def simplify_unit(cls, unit_str: str) -> str:
        """Simplify a unit expression to common form"""
        # Handle special cases
        if unit_str == "m · m":
            return "m²"
        elif unit_str == "m · m · m":
            return "m³"
        elif unit_str == "m^2":
            return "m²"
        elif unit_str == "m^3":
            return "m³"
        
        # Add more simplifications as needed
        return unit_str