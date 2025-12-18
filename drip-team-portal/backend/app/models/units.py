"""
Unit System with Dimensional Analysis

Uses the 7 SI base dimensions:
- Length (L) - meter [m]
- Mass (M) - kilogram [kg]
- Time (T) - second [s]
- Electric current (I) - ampere [A]
- Temperature (Θ) - kelvin [K]
- Amount of substance (N) - mole [mol]
- Luminous intensity (J) - candela [cd]

Each unit stores its dimensions as integer exponents.
Example: Force (Newton) = kg·m/s² → mass_dim=1, length_dim=1, time_dim=-2
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base


class Unit(Base):
    """
    Represents a unit of measurement with dimensional analysis.

    Examples:
        meter: symbol="m", length_dim=1, all others=0
        newton: symbol="N", mass_dim=1, length_dim=1, time_dim=-2
        watt: symbol="W", mass_dim=1, length_dim=2, time_dim=-3
        thermal_conductivity: symbol="W/(m·K)", mass_dim=1, length_dim=1, time_dim=-3, temperature_dim=-1
    """
    __tablename__ = "units"

    id = Column(Integer, primary_key=True)

    # Identity
    symbol = Column(String(50), nullable=False, unique=True)  # e.g., "m", "kg", "W/(m·K)"
    name = Column(String(100), nullable=False)  # e.g., "meter", "kilogram", "watts per meter kelvin"

    # Quantity type for grouping/filtering
    quantity_type = Column(String(50))  # e.g., "length", "mass", "thermal_conductivity", "pressure"

    # 7 SI base dimensions (stored as integer exponents)
    length_dim = Column(Integer, default=0)       # L - meter
    mass_dim = Column(Integer, default=0)         # M - kilogram
    time_dim = Column(Integer, default=0)         # T - second
    current_dim = Column(Integer, default=0)      # I - ampere
    temperature_dim = Column(Integer, default=0)  # Θ - kelvin
    amount_dim = Column(Integer, default=0)       # N - mole
    luminosity_dim = Column(Integer, default=0)   # J - candela

    # Is this a base SI unit?
    is_base_unit = Column(Boolean, default=False)

    # For display ordering and grouping
    display_order = Column(Integer, default=0)

    def __repr__(self):
        return f"<Unit {self.symbol} ({self.name})>"

    def dimensions_tuple(self):
        """Return dimensions as a tuple for easy comparison."""
        return (
            self.length_dim,
            self.mass_dim,
            self.time_dim,
            self.current_dim,
            self.temperature_dim,
            self.amount_dim,
            self.luminosity_dim
        )

    def is_dimensionless(self):
        """Check if this unit is dimensionless (all exponents are 0)."""
        return all(d == 0 for d in self.dimensions_tuple())

    def dimensions_match(self, other: "Unit") -> bool:
        """Check if two units have the same dimensions (are compatible)."""
        return self.dimensions_tuple() == other.dimensions_tuple()


class UnitConversion(Base):
    """
    Stores conversion factors between compatible units.

    Conversion formula: to_value = (from_value * multiplier) + offset

    Examples:
        km to m: multiplier=1000, offset=0
        °C to K: multiplier=1, offset=273.15
        °F to K: multiplier=5/9, offset=255.372 (approximately)
    """
    __tablename__ = "unit_conversions"

    id = Column(Integer, primary_key=True)

    # From/To units (must have same dimensions)
    from_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)
    to_unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    # Conversion formula: to_value = (from_value * multiplier) + offset
    multiplier = Column(Float, nullable=False, default=1.0)
    offset = Column(Float, nullable=False, default=0.0)

    # Relationships
    from_unit = relationship("Unit", foreign_keys=[from_unit_id])
    to_unit = relationship("Unit", foreign_keys=[to_unit_id])

    # Ensure unique conversions
    __table_args__ = (
        UniqueConstraint('from_unit_id', 'to_unit_id', name='unique_conversion'),
    )

    def __repr__(self):
        return f"<UnitConversion {self.from_unit_id} -> {self.to_unit_id} (×{self.multiplier} +{self.offset})>"

    def convert(self, value: float) -> float:
        """Convert a value from from_unit to to_unit."""
        return (value * self.multiplier) + self.offset

    def reverse_convert(self, value: float) -> float:
        """Convert a value from to_unit back to from_unit."""
        return (value - self.offset) / self.multiplier


class UnitAlias(Base):
    """
    Alternative names/symbols for units.

    Examples:
        "meters" -> Unit(symbol="m")
        "metre" -> Unit(symbol="m")
        "kilowatt" -> Unit(symbol="kW")
    """
    __tablename__ = "unit_aliases"

    id = Column(Integer, primary_key=True)
    alias = Column(String(50), nullable=False, unique=True)
    unit_id = Column(Integer, ForeignKey("units.id"), nullable=False)

    unit = relationship("Unit")

    def __repr__(self):
        return f"<UnitAlias {self.alias} -> {self.unit_id}>"
