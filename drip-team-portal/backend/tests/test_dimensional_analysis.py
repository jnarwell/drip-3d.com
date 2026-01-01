"""
Dimensional Analysis Tests

Tests for physical dimension validation of equations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.dimensional_analysis import (
    Dimension,
    DimensionError,
    # Base dimensions
    DIMENSIONLESS, LENGTH, MASS, TIME, TEMPERATURE, CURRENT,
    # Derived dimensions
    AREA, VOLUME, VELOCITY, ACCELERATION,
    FORCE, PRESSURE, ENERGY, POWER,
    DENSITY, THERMAL_EXPANSION, THERMAL_CONDUCTIVITY,
    SPECIFIC_HEAT,
    # Functions
    validate_equation_dimensions,
    infer_dimension,
    check_dimensional_consistency,
    get_unit_dimension,
    dimension_to_string,
)


class TestDimensionArithmetic:
    """Test Dimension class arithmetic operations."""

    def test_length_times_length_is_area(self):
        """L * L = L²"""
        result = LENGTH * LENGTH
        assert result == AREA

    def test_length_cubed_is_volume(self):
        """L * L * L = L³"""
        result = LENGTH * LENGTH * LENGTH
        assert result == VOLUME

    def test_length_divided_by_time_is_velocity(self):
        """L / T = velocity"""
        result = LENGTH / TIME
        assert result == VELOCITY

    def test_velocity_divided_by_time_is_acceleration(self):
        """(L/T) / T = L/T²"""
        result = VELOCITY / TIME
        assert result == ACCELERATION

    def test_force_equals_mass_times_acceleration(self):
        """M * L/T² = Force"""
        result = MASS * ACCELERATION
        assert result == FORCE

    def test_force_divided_by_area_is_pressure(self):
        """F / A = Pressure"""
        result = FORCE / AREA
        assert result == PRESSURE

    def test_length_power_two(self):
        """L ** 2 = L²"""
        result = LENGTH ** 2
        assert result == AREA

    def test_length_power_three(self):
        """L ** 3 = L³"""
        result = LENGTH ** 3
        assert result == VOLUME


class TestDimensionEquality:
    """Test dimension equality and identity."""

    def test_dimensionless_is_dimensionless(self):
        """Dimensionless check."""
        assert DIMENSIONLESS.is_dimensionless()

    def test_length_is_not_dimensionless(self):
        """Length is not dimensionless."""
        assert not LENGTH.is_dimensionless()

    def test_dimension_equality(self):
        """Same dimension should be equal."""
        d1 = Dimension(length=1)
        d2 = Dimension(length=1)
        assert d1 == d2

    def test_dimension_inequality(self):
        """Different dimensions should not be equal."""
        assert LENGTH != MASS
        assert LENGTH != TIME


class TestThermalExpansion:
    """Test thermal expansion equation dimensionally."""

    def test_thermal_expansion_formula(self):
        """
        delta_L = L * CTE * delta_T
        L¹ = L¹ * Θ⁻¹ * Θ¹
        """
        # CTE has dimension 1/Temperature
        result = LENGTH * THERMAL_EXPANSION * TEMPERATURE
        assert result == LENGTH

    def test_validate_thermal_expansion_ast(self):
        """Validate AST for thermal expansion equation."""
        ast = {
            "type": "mul",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "CTE"},
                {"type": "input", "name": "delta_T"}
            ]
        }

        input_dims = {
            "length": LENGTH,
            "CTE": THERMAL_EXPANSION,  # Θ⁻¹
            "delta_T": TEMPERATURE     # Θ¹
        }

        is_valid, error = validate_equation_dimensions(ast, input_dims, LENGTH)

        assert is_valid == True
        assert error == ""


class TestDimensionMismatch:
    """Test detection of dimension mismatches."""

    def test_cannot_add_length_and_mass(self):
        """Cannot add length to mass."""
        ast = {
            "type": "add",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "mass"}
            ]
        }

        input_dims = {
            "length": LENGTH,
            "mass": MASS
        }

        is_valid, error = validate_equation_dimensions(ast, input_dims, LENGTH)

        assert is_valid == False
        assert "mismatch" in error.lower()

    def test_can_add_same_dimensions(self):
        """Can add lengths together."""
        ast = {
            "type": "add",
            "operands": [
                {"type": "input", "name": "length1"},
                {"type": "input", "name": "length2"}
            ]
        }

        input_dims = {
            "length1": LENGTH,
            "length2": LENGTH
        }

        is_valid, error = validate_equation_dimensions(ast, input_dims, LENGTH)

        assert is_valid == True


class TestInferDimension:
    """Test dimension inference from AST."""

    def test_infer_multiplication(self):
        """Infer dimension from multiplication."""
        ast = {
            "type": "mul",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "width"}
            ]
        }

        input_dims = {"length": LENGTH, "width": LENGTH}

        result = infer_dimension(ast, input_dims)
        assert result == AREA

    def test_infer_division(self):
        """Infer dimension from division."""
        ast = {
            "type": "div",
            "left": {"type": "input", "name": "distance"},
            "right": {"type": "input", "name": "time"}
        }

        input_dims = {"distance": LENGTH, "time": TIME}

        result = infer_dimension(ast, input_dims)
        assert result == VELOCITY

    def test_infer_sqrt(self):
        """Infer dimension from sqrt."""
        ast = {
            "type": "sqrt",
            "operand": {"type": "input", "name": "area"}
        }

        input_dims = {"area": AREA}

        result = infer_dimension(ast, input_dims)
        assert result == LENGTH

    def test_infer_literal(self):
        """Literals are dimensionless."""
        ast = {"type": "literal", "value": 3.14}

        result = infer_dimension(ast, {})
        assert result == DIMENSIONLESS

    def test_infer_unknown_input_raises(self):
        """Unknown input should raise error."""
        ast = {"type": "input", "name": "unknown"}

        with pytest.raises(DimensionError):
            infer_dimension(ast, {})


class TestCheckConsistency:
    """Test dimensional consistency checking."""

    def test_consistent_equation(self):
        """Check consistent equation."""
        ast = {
            "type": "mul",
            "operands": [
                {"type": "input", "name": "force"},
                {"type": "input", "name": "distance"}
            ]
        }

        input_dims = {"force": FORCE, "distance": LENGTH}

        is_consistent, error, dim = check_dimensional_consistency(ast, input_dims)

        assert is_consistent == True
        assert dim == ENERGY

    def test_inconsistent_equation(self):
        """Check inconsistent equation (adding incompatible dimensions)."""
        ast = {
            "type": "add",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "time"}
            ]
        }

        input_dims = {"length": LENGTH, "time": TIME}

        is_consistent, error, dim = check_dimensional_consistency(ast, input_dims)

        assert is_consistent == False
        assert dim is None


class TestUnitDimensionMapping:
    """Test unit to dimension mapping."""

    def test_length_units(self):
        """Test length units map to LENGTH dimension."""
        assert get_unit_dimension('m') == LENGTH
        assert get_unit_dimension('mm') == LENGTH
        assert get_unit_dimension('km') == LENGTH
        assert get_unit_dimension('in') == LENGTH
        assert get_unit_dimension('ft') == LENGTH

    def test_area_units(self):
        """Test area units map to AREA dimension."""
        assert get_unit_dimension('m²') == AREA
        assert get_unit_dimension('mm²') == AREA
        assert get_unit_dimension('ft²') == AREA

    def test_pressure_units(self):
        """Test pressure units map to PRESSURE dimension."""
        assert get_unit_dimension('Pa') == PRESSURE
        assert get_unit_dimension('kPa') == PRESSURE
        assert get_unit_dimension('MPa') == PRESSURE
        assert get_unit_dimension('psi') == PRESSURE

    def test_temperature_units(self):
        """Test temperature units map to TEMPERATURE dimension."""
        assert get_unit_dimension('K') == TEMPERATURE
        assert get_unit_dimension('°C') == TEMPERATURE
        assert get_unit_dimension('°F') == TEMPERATURE


class TestDimensionToString:
    """Test dimension string representation."""

    def test_dimensionless_string(self):
        """Dimensionless should show '1'."""
        result = dimension_to_string(DIMENSIONLESS)
        assert result == "1"

    def test_length_string(self):
        """Length should show 'L'."""
        result = dimension_to_string(LENGTH)
        assert 'L' in result

    def test_pressure_string(self):
        """Pressure should show M, L, T components."""
        result = dimension_to_string(PRESSURE)
        assert 'M' in result
        assert 'L' in result
        assert 'T' in result
