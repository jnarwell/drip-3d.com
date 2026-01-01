"""
Centralized Unit Conversion Service

Single source of truth for unit conversions - queries the database.
All other services should use this instead of hardcoded conversion dicts.
"""

from typing import Dict, Optional, Tuple, List
from functools import lru_cache
from sqlalchemy.orm import Session

from app.models.units import Unit, UnitConversion, UnitAlias


class UnitService:
    """
    Provides unit conversion functionality from the database.

    Usage:
        from app.services.unit_service import unit_service

        # Convert value
        si_value = unit_service.to_si(100, 'mm')  # -> 0.1 (meters)

        # Get conversion factor
        factor = unit_service.get_to_si_factor('mm')  # -> 0.001

        # Convert between any units
        result = unit_service.convert(100, 'mm', 'in')  # -> 3.937...
    """

    def __init__(self):
        self._cache_loaded = False
        self._units: Dict[str, dict] = {}  # symbol -> unit data
        self._conversions: Dict[str, float] = {}  # symbol -> to_si_factor
        self._offsets: Dict[str, float] = {}  # symbol -> to_si_offset (for temperature)
        self._aliases: Dict[str, str] = {}  # alias -> canonical symbol
        self._si_units: Dict[str, str] = {}  # quantity_type -> SI base unit symbol

    def _load_cache(self, db: Session):
        """Load all unit data into memory cache."""
        if self._cache_loaded:
            return

        # Load units
        units = db.query(Unit).all()
        for u in units:
            self._units[u.symbol] = {
                'id': u.id,
                'name': u.name,
                'symbol': u.symbol,
                'quantity_type': u.quantity_type,
                'is_base_unit': u.is_base_unit,
                'dimensions': (
                    u.length_dim, u.mass_dim, u.time_dim,
                    u.current_dim, u.temperature_dim, u.amount_dim, u.luminosity_dim
                )
            }
            if u.is_base_unit and u.quantity_type:
                self._si_units[u.quantity_type] = u.symbol

        # Load conversions (to SI base unit)
        # We need to find conversions where to_unit is the SI base
        conversions = db.query(UnitConversion).all()
        for c in conversions:
            from_unit = db.query(Unit).get(c.from_unit_id)
            to_unit = db.query(Unit).get(c.to_unit_id)
            if from_unit and to_unit:
                # Store as from_symbol -> (multiplier, offset)
                self._conversions[from_unit.symbol] = c.multiplier
                self._offsets[from_unit.symbol] = c.offset

        # Load aliases
        aliases = db.query(UnitAlias).all()
        for a in aliases:
            unit = db.query(Unit).get(a.unit_id)
            if unit:
                self._aliases[a.alias] = unit.symbol

        # SI base units have factor=1, offset=0
        for symbol, data in self._units.items():
            if data['is_base_unit']:
                self._conversions[symbol] = 1.0
                self._offsets[symbol] = 0.0

        self._cache_loaded = True

    def ensure_loaded(self, db: Session):
        """Ensure cache is loaded. Call this before using other methods."""
        self._load_cache(db)

    def reload(self, db: Session):
        """Force reload cache from database."""
        self._cache_loaded = False
        self._units.clear()
        self._conversions.clear()
        self._offsets.clear()
        self._aliases.clear()
        self._si_units.clear()
        self._load_cache(db)

    def resolve_symbol(self, unit: str) -> str:
        """Resolve alias to canonical symbol."""
        return self._aliases.get(unit, unit)

    def get_to_si_factor(self, unit: str) -> float:
        """Get conversion factor to SI base unit."""
        symbol = self.resolve_symbol(unit)
        return self._conversions.get(symbol, 1.0)

    def get_to_si_offset(self, unit: str) -> float:
        """Get conversion offset to SI base unit (for temperature)."""
        symbol = self.resolve_symbol(unit)
        return self._offsets.get(symbol, 0.0)

    def to_si(self, value: float, unit: str) -> float:
        """Convert value to SI base unit."""
        symbol = self.resolve_symbol(unit)
        factor = self._conversions.get(symbol, 1.0)
        offset = self._offsets.get(symbol, 0.0)
        return value * factor + offset

    def from_si(self, value: float, unit: str) -> float:
        """Convert value from SI base unit to target unit."""
        symbol = self.resolve_symbol(unit)
        factor = self._conversions.get(symbol, 1.0)
        offset = self._offsets.get(symbol, 0.0)
        if factor == 0:
            return value
        return (value - offset) / factor

    def convert(self, value: float, from_unit: str, to_unit: str) -> float:
        """Convert value between any two compatible units."""
        if from_unit == to_unit:
            return value
        # Convert to SI, then to target
        si_value = self.to_si(value, from_unit)
        return self.from_si(si_value, to_unit)

    def get_si_unit(self, quantity_type: str) -> Optional[str]:
        """Get the SI base unit symbol for a quantity type."""
        return self._si_units.get(quantity_type)

    def get_quantity_type(self, unit: str) -> Optional[str]:
        """Get the quantity type for a unit."""
        symbol = self.resolve_symbol(unit)
        unit_data = self._units.get(symbol)
        return unit_data['quantity_type'] if unit_data else None

    def get_all_conversions(self) -> Dict[str, Tuple[float, float]]:
        """Get all conversion factors as dict: symbol -> (factor, offset)."""
        result = {}
        for symbol in self._conversions:
            result[symbol] = (
                self._conversions.get(symbol, 1.0),
                self._offsets.get(symbol, 0.0)
            )
        return result

    def get_units_by_quantity(self, quantity_type: str) -> List[dict]:
        """Get all units for a quantity type."""
        return [
            data for data in self._units.values()
            if data['quantity_type'] == quantity_type
        ]

    def get_all_units(self) -> Dict[str, dict]:
        """Get all units data."""
        return self._units.copy()

    def get_all_aliases(self) -> Dict[str, str]:
        """Get all aliases."""
        return self._aliases.copy()


# Singleton instance
unit_service = UnitService()


# Convenience functions for simple usage (require db session)
def to_si(db: Session, value: float, unit: str) -> float:
    """Convert value to SI. Ensures cache is loaded."""
    unit_service.ensure_loaded(db)
    return unit_service.to_si(value, unit)


def from_si(db: Session, value: float, unit: str) -> float:
    """Convert value from SI. Ensures cache is loaded."""
    unit_service.ensure_loaded(db)
    return unit_service.from_si(value, unit)


def convert(db: Session, value: float, from_unit: str, to_unit: str) -> float:
    """Convert between units. Ensures cache is loaded."""
    unit_service.ensure_loaded(db)
    return unit_service.convert(value, from_unit, to_unit)
