"""
Unit Engine - Dimensional Analysis and Unit Conversion Service

Provides:
- Unit multiplication/division (dimensional analysis)
- Unit compatibility checking
- Value conversion between units
- Result unit computation for expressions
"""

from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.units import Unit, UnitConversion, UnitAlias
import logging

logger = logging.getLogger(__name__)


class UnitEngine:
    """
    Service for performing dimensional analysis and unit conversions.
    """

    def __init__(self, db: Session):
        self.db = db
        self._unit_cache: Dict[str, Unit] = {}
        self._conversion_cache: Dict[Tuple[int, int], UnitConversion] = {}

    def get_unit_by_symbol(self, symbol: str) -> Optional[Unit]:
        """Get a unit by its symbol, with caching."""
        if symbol in self._unit_cache:
            return self._unit_cache[symbol]

        # Try direct symbol match
        unit = self.db.query(Unit).filter(Unit.symbol == symbol).first()

        # Try alias if not found
        if not unit:
            alias = self.db.query(UnitAlias).filter(UnitAlias.alias == symbol).first()
            if alias:
                unit = alias.unit

        if unit:
            self._unit_cache[symbol] = unit

        return unit

    def get_unit_by_id(self, unit_id: int) -> Optional[Unit]:
        """Get a unit by its ID."""
        return self.db.query(Unit).filter(Unit.id == unit_id).first()

    def are_compatible(self, unit1: Unit, unit2: Unit) -> bool:
        """
        Check if two units are dimensionally compatible (can be converted).

        Examples:
            m and km -> True (both length)
            m and kg -> False (length vs mass)
            W/(m·K) and BTU/(ft·hr·°F) -> True (both thermal conductivity)
        """
        return unit1.dimensions_match(unit2)

    def are_compatible_by_symbol(self, symbol1: str, symbol2: str) -> bool:
        """Check compatibility by symbol names."""
        unit1 = self.get_unit_by_symbol(symbol1)
        unit2 = self.get_unit_by_symbol(symbol2)

        if not unit1 or not unit2:
            return False

        return self.are_compatible(unit1, unit2)

    def multiply_units(self, unit1: Unit, unit2: Unit) -> Dict[str, int]:
        """
        Compute the dimensions of unit1 * unit2.

        Example: m * m = m² (length_dim: 1+1 = 2)
        Example: kg * m/s² = N (mass:1, length:1, time:-2)

        Returns a dict of dimension exponents.
        """
        return {
            "length_dim": unit1.length_dim + unit2.length_dim,
            "mass_dim": unit1.mass_dim + unit2.mass_dim,
            "time_dim": unit1.time_dim + unit2.time_dim,
            "current_dim": unit1.current_dim + unit2.current_dim,
            "temperature_dim": unit1.temperature_dim + unit2.temperature_dim,
            "amount_dim": unit1.amount_dim + unit2.amount_dim,
            "luminosity_dim": unit1.luminosity_dim + unit2.luminosity_dim,
        }

    def divide_units(self, unit1: Unit, unit2: Unit) -> Dict[str, int]:
        """
        Compute the dimensions of unit1 / unit2.

        Example: m / s = m/s (length:1, time:-1)
        Example: J / K = J/K (energy/temperature for entropy)

        Returns a dict of dimension exponents.
        """
        return {
            "length_dim": unit1.length_dim - unit2.length_dim,
            "mass_dim": unit1.mass_dim - unit2.mass_dim,
            "time_dim": unit1.time_dim - unit2.time_dim,
            "current_dim": unit1.current_dim - unit2.current_dim,
            "temperature_dim": unit1.temperature_dim - unit2.temperature_dim,
            "amount_dim": unit1.amount_dim - unit2.amount_dim,
            "luminosity_dim": unit1.luminosity_dim - unit2.luminosity_dim,
        }

    def power_unit(self, unit: Unit, exponent: int) -> Dict[str, int]:
        """
        Compute the dimensions of unit^exponent.

        Example: m^2 = m² (length:2)
        Example: s^-1 = 1/s = Hz (time:-1)
        """
        return {
            "length_dim": unit.length_dim * exponent,
            "mass_dim": unit.mass_dim * exponent,
            "time_dim": unit.time_dim * exponent,
            "current_dim": unit.current_dim * exponent,
            "temperature_dim": unit.temperature_dim * exponent,
            "amount_dim": unit.amount_dim * exponent,
            "luminosity_dim": unit.luminosity_dim * exponent,
        }

    def find_unit_by_dimensions(self, dimensions: Dict[str, int]) -> Optional[Unit]:
        """
        Find a unit that matches the given dimensions.

        Useful for finding the result unit after multiplication/division.
        Returns None if no matching unit exists in the database.
        """
        return self.db.query(Unit).filter(
            Unit.length_dim == dimensions.get("length_dim", 0),
            Unit.mass_dim == dimensions.get("mass_dim", 0),
            Unit.time_dim == dimensions.get("time_dim", 0),
            Unit.current_dim == dimensions.get("current_dim", 0),
            Unit.temperature_dim == dimensions.get("temperature_dim", 0),
            Unit.amount_dim == dimensions.get("amount_dim", 0),
            Unit.luminosity_dim == dimensions.get("luminosity_dim", 0),
        ).first()

    def get_conversion(self, from_unit: Unit, to_unit: Unit) -> Optional[UnitConversion]:
        """Get conversion between two units, with caching."""
        cache_key = (from_unit.id, to_unit.id)

        if cache_key in self._conversion_cache:
            return self._conversion_cache[cache_key]

        conversion = self.db.query(UnitConversion).filter(
            UnitConversion.from_unit_id == from_unit.id,
            UnitConversion.to_unit_id == to_unit.id
        ).first()

        if conversion:
            self._conversion_cache[cache_key] = conversion

        return conversion

    def convert_value(
        self,
        value: float,
        from_unit: Unit,
        to_unit: Unit
    ) -> Tuple[float, bool, Optional[str]]:
        """
        Convert a value from one unit to another.

        Returns: (converted_value, success, error_message)
        """
        # Same unit - no conversion needed
        if from_unit.id == to_unit.id:
            return (value, True, None)

        # Check compatibility
        if not self.are_compatible(from_unit, to_unit):
            return (
                value,
                False,
                f"Cannot convert between incompatible units: {from_unit.symbol} and {to_unit.symbol}"
            )

        # Try direct conversion
        conversion = self.get_conversion(from_unit, to_unit)
        if conversion:
            return (conversion.convert(value), True, None)

        # Try reverse conversion
        reverse = self.get_conversion(to_unit, from_unit)
        if reverse:
            return (reverse.reverse_convert(value), True, None)

        # No conversion found - this shouldn't happen for compatible units
        # with proper seeding, but handle gracefully
        return (
            value,
            False,
            f"No conversion found from {from_unit.symbol} to {to_unit.symbol}"
        )

    def convert_value_by_symbol(
        self,
        value: float,
        from_symbol: str,
        to_symbol: str
    ) -> Tuple[float, bool, Optional[str]]:
        """Convert a value using unit symbols."""
        from_unit = self.get_unit_by_symbol(from_symbol)
        to_unit = self.get_unit_by_symbol(to_symbol)

        if not from_unit:
            return (value, False, f"Unknown unit: {from_symbol}")
        if not to_unit:
            return (value, False, f"Unknown unit: {to_symbol}")

        return self.convert_value(value, from_unit, to_unit)

    def get_compatible_units(self, unit: Unit) -> List[Unit]:
        """Get all units that are dimensionally compatible with the given unit."""
        return self.db.query(Unit).filter(
            Unit.length_dim == unit.length_dim,
            Unit.mass_dim == unit.mass_dim,
            Unit.time_dim == unit.time_dim,
            Unit.current_dim == unit.current_dim,
            Unit.temperature_dim == unit.temperature_dim,
            Unit.amount_dim == unit.amount_dim,
            Unit.luminosity_dim == unit.luminosity_dim,
        ).all()

    def dimensions_to_string(self, dimensions: Dict[str, int]) -> str:
        """
        Convert dimensions to a human-readable string.

        Example: {length_dim: 1, time_dim: -2} -> "L·T⁻²"
        """
        symbols = [
            ("L", dimensions.get("length_dim", 0)),
            ("M", dimensions.get("mass_dim", 0)),
            ("T", dimensions.get("time_dim", 0)),
            ("I", dimensions.get("current_dim", 0)),
            ("Θ", dimensions.get("temperature_dim", 0)),
            ("N", dimensions.get("amount_dim", 0)),
            ("J", dimensions.get("luminosity_dim", 0)),
        ]

        superscript = {
            "-": "⁻", "0": "⁰", "1": "¹", "2": "²", "3": "³",
            "4": "⁴", "5": "⁵", "6": "⁶", "7": "⁷", "8": "⁸", "9": "⁹"
        }

        parts = []
        for symbol, exp in symbols:
            if exp == 0:
                continue
            elif exp == 1:
                parts.append(symbol)
            else:
                exp_str = "".join(superscript.get(c, c) for c in str(exp))
                parts.append(f"{symbol}{exp_str}")

        return "·".join(parts) if parts else "dimensionless"

    def validate_unit_operation(
        self,
        value1: float,
        unit1: Unit,
        value2: float,
        unit2: Unit,
        operation: str  # "add", "subtract", "multiply", "divide"
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, int]]]:
        """
        Validate a unit operation and return resulting dimensions.

        For add/subtract: units must be compatible
        For multiply/divide: any units work, result is computed

        Returns: (valid, error_message, result_dimensions)
        """
        if operation in ("add", "subtract"):
            if not self.are_compatible(unit1, unit2):
                return (
                    False,
                    f"Cannot {operation} values with different dimensions: "
                    f"{unit1.symbol} ({self.dimensions_to_string(self._unit_to_dims(unit1))}) and "
                    f"{unit2.symbol} ({self.dimensions_to_string(self._unit_to_dims(unit2))})",
                    None
                )
            return (True, None, self._unit_to_dims(unit1))

        elif operation == "multiply":
            result_dims = self.multiply_units(unit1, unit2)
            return (True, None, result_dims)

        elif operation == "divide":
            result_dims = self.divide_units(unit1, unit2)
            return (True, None, result_dims)

        return (False, f"Unknown operation: {operation}", None)

    def _unit_to_dims(self, unit: Unit) -> Dict[str, int]:
        """Convert a Unit to a dimensions dict."""
        return {
            "length_dim": unit.length_dim,
            "mass_dim": unit.mass_dim,
            "time_dim": unit.time_dim,
            "current_dim": unit.current_dim,
            "temperature_dim": unit.temperature_dim,
            "amount_dim": unit.amount_dim,
            "luminosity_dim": unit.luminosity_dim,
        }


def create_unit_engine(db: Session) -> UnitEngine:
    """Factory function to create a UnitEngine instance."""
    return UnitEngine(db)
