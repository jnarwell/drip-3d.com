"""
Tests for value_engine dimension inference bugs.

Focus on:
1. Space sensitivity around ^ operator
2. Dimension inference for power expressions
3. Volume (product) calculations
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import re
import sympy as sp
from sympy import Symbol, Pow, Mul, Add

from app.services.dimensional_analysis import (
    Dimension, DimensionError, DIMENSIONLESS, LENGTH, AREA, VOLUME,
    dimension_to_string, dimension_to_si_unit, get_unit_dimension
)


class TestValueEngineCaretConversion:
    """Test that value_engine's ^ to ** conversion handles spaces."""

    def test_caret_no_space(self):
        """__ref_0__^2 should convert to __ref_0__**2"""
        expr = "__ref_0__^2"
        result = re.sub(r'\^', '**', expr)
        assert result == "__ref_0__**2"

    def test_caret_space_before(self):
        """__ref_0__ ^2 should convert to __ref_0__ **2"""
        expr = "__ref_0__ ^2"
        result = re.sub(r'\^', '**', expr)
        assert result == "__ref_0__ **2"

    def test_caret_space_after(self):
        """__ref_0__^ 2 should convert to __ref_0__** 2"""
        expr = "__ref_0__^ 2"
        result = re.sub(r'\^', '**', expr)
        assert result == "__ref_0__** 2"

    def test_caret_spaces_both(self):
        """__ref_0__ ^ 2 should convert to __ref_0__ ** 2"""
        expr = "__ref_0__ ^ 2"
        result = re.sub(r'\^', '**', expr)
        assert result == "__ref_0__ ** 2"


class TestSympyParsingWithSpaces:
    """Test SymPy parsing of expressions with spaces around **."""

    def test_power_no_space(self):
        """__ref_0__**2 should parse correctly."""
        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        expr = sp.sympify("__ref_0__**2", locals=local_dict)
        assert isinstance(expr, Pow)
        assert expr.args[0] == Symbol('__ref_0__')
        assert expr.args[1] == 2

    def test_power_space_before(self):
        """__ref_0__ **2 should parse correctly."""
        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        expr = sp.sympify("__ref_0__ **2", locals=local_dict)
        assert isinstance(expr, Pow)
        assert expr.args[0] == Symbol('__ref_0__')
        assert expr.args[1] == 2

    def test_power_space_after(self):
        """__ref_0__** 2 should parse correctly."""
        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        expr = sp.sympify("__ref_0__** 2", locals=local_dict)
        assert isinstance(expr, Pow)
        assert expr.args[0] == Symbol('__ref_0__')
        assert expr.args[1] == 2

    def test_power_spaces_both(self):
        """__ref_0__ ** 2 should parse correctly."""
        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        expr = sp.sympify("__ref_0__ ** 2", locals=local_dict)
        assert isinstance(expr, Pow)
        assert expr.args[0] == Symbol('__ref_0__')
        assert expr.args[1] == 2


class TestDimensionInferenceForPow:
    """Test dimension inference for Pow nodes (like Height^2)."""

    def _infer_dim(self, node, placeholder_dims):
        """Simplified version of value_engine's dimension inference."""
        # Symbol - look up in placeholder_dims
        if isinstance(node, Symbol):
            name = str(node)
            return placeholder_dims.get(name, DIMENSIONLESS)

        # Number - dimensionless
        if node.is_number:
            return DIMENSIONLESS

        # Addition - all operands must have same dimension
        if isinstance(node, Add):
            first_dim = self._infer_dim(node.args[0], placeholder_dims)
            for arg in node.args[1:]:
                arg_dim = self._infer_dim(arg, placeholder_dims)
                if arg_dim != first_dim and not arg_dim.is_dimensionless():
                    raise DimensionError(f"Dimension mismatch in addition")
            return first_dim

        # Multiplication - dimensions multiply
        if isinstance(node, Mul):
            result = DIMENSIONLESS
            for arg in node.args:
                result = result * self._infer_dim(arg, placeholder_dims)
            return result

        # Power - base dimension raised to exponent
        if isinstance(node, Pow):
            base_dim = self._infer_dim(node.args[0], placeholder_dims)
            exponent = node.args[1]

            if exponent.is_number:
                exp_val = float(exponent)
                if exp_val == int(exp_val):
                    return base_dim ** int(exp_val)
                else:
                    if not base_dim.is_dimensionless():
                        raise DimensionError(
                            f"Cannot raise dimensional quantity to non-integer power {exp_val}"
                        )
                    return DIMENSIONLESS
            else:
                if not base_dim.is_dimensionless():
                    raise DimensionError("Cannot raise dimensional quantity to variable power")
                return DIMENSIONLESS

        return DIMENSIONLESS

    def test_length_squared_gives_area(self):
        """LENGTH^2 should give AREA."""
        expr = Symbol('Height') ** 2
        placeholder_dims = {'Height': LENGTH}
        result = self._infer_dim(expr, placeholder_dims)
        assert result == AREA

    def test_length_cubed_gives_volume(self):
        """LENGTH^3 should give VOLUME."""
        expr = Symbol('Height') ** 3
        placeholder_dims = {'Height': LENGTH}
        result = self._infer_dim(expr, placeholder_dims)
        assert result == VOLUME

    def test_length_times_area_gives_volume(self):
        """LENGTH * AREA = VOLUME."""
        Height = Symbol('Height')
        Width = Symbol('Width')
        expr = Height * Width * Width  # L * L * L = L^3
        placeholder_dims = {'Height': LENGTH, 'Width': LENGTH}
        result = self._infer_dim(expr, placeholder_dims)
        assert result == VOLUME

    def test_triple_product_gives_volume(self):
        """HEIGHT * WIDTH * DEPTH = VOLUME."""
        Height = Symbol('Height')
        Width = Symbol('Width')
        Depth = Symbol('Depth')
        expr = Height * Width * Depth
        placeholder_dims = {'Height': LENGTH, 'Width': LENGTH, 'Depth': LENGTH}
        result = self._infer_dim(expr, placeholder_dims)
        assert result == VOLUME


class TestExponentIsNumberCheck:
    """Test that SymPy's is_number works correctly for exponents."""

    def test_integer_exponent(self):
        """Integer exponent should have is_number=True."""
        expr = Symbol('x') ** 2
        exponent = expr.args[1]
        assert exponent.is_number == True
        assert float(exponent) == 2.0

    def test_float_exponent(self):
        """Float exponent should have is_number=True."""
        expr = Symbol('x') ** 0.5
        exponent = expr.args[1]
        assert exponent.is_number == True
        assert float(exponent) == 0.5

    def test_symbol_exponent(self):
        """Symbol exponent should have is_number=False."""
        expr = Symbol('x') ** Symbol('n')
        exponent = expr.args[1]
        assert exponent.is_number == False

    def test_negative_exponent(self):
        """Negative exponent should have is_number=True."""
        expr = Symbol('x') ** (-1)
        exponent = expr.args[1]
        assert exponent.is_number == True
        assert float(exponent) == -1.0


class TestValueEngineInferDimensionFromExpr:
    """Test the actual _infer_dimension_from_expr logic."""

    def test_simple_power(self):
        """Test Height**2 dimension inference."""
        # This simulates what value_engine does
        expr_str = "__ref_0__**2"
        placeholder_dims = {'__ref_0__': LENGTH}

        # Build local dict and parse
        local_dict = {p: Symbol(p) for p in placeholder_dims}
        parsed_expr = sp.sympify(expr_str, locals=local_dict)

        # Now infer dimension
        def infer_dim(node):
            if isinstance(node, Symbol):
                return placeholder_dims.get(str(node), DIMENSIONLESS)
            if node.is_number:
                return DIMENSIONLESS
            if isinstance(node, Pow):
                base_dim = infer_dim(node.args[0])
                exp = node.args[1]
                if exp.is_number:
                    exp_val = float(exp)
                    if exp_val == int(exp_val):
                        return base_dim ** int(exp_val)
                return DIMENSIONLESS
            if isinstance(node, Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    result = result * infer_dim(arg)
                return result
            return DIMENSIONLESS

        result = infer_dim(parsed_expr)
        assert result == AREA, f"Expected AREA, got {dimension_to_string(result)}"

    def test_power_with_space(self):
        """Test Height **2 (with space) dimension inference."""
        expr_str = "__ref_0__ **2"  # Note the space
        placeholder_dims = {'__ref_0__': LENGTH}

        local_dict = {p: Symbol(p) for p in placeholder_dims}
        parsed_expr = sp.sympify(expr_str, locals=local_dict)

        def infer_dim(node):
            if isinstance(node, Symbol):
                return placeholder_dims.get(str(node), DIMENSIONLESS)
            if node.is_number:
                return DIMENSIONLESS
            if isinstance(node, Pow):
                base_dim = infer_dim(node.args[0])
                exp = node.args[1]
                if exp.is_number:
                    exp_val = float(exp)
                    if exp_val == int(exp_val):
                        return base_dim ** int(exp_val)
                return DIMENSIONLESS
            if isinstance(node, Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    result = result * infer_dim(arg)
                return result
            return DIMENSIONLESS

        result = infer_dim(parsed_expr)
        assert result == AREA, f"Expected AREA, got {dimension_to_string(result)}"

    def test_product_of_three_lengths(self):
        """Test Height * Width * Depth = Volume."""
        expr_str = "__ref_0__ * __ref_1__ * __ref_2__"
        placeholder_dims = {
            '__ref_0__': LENGTH,
            '__ref_1__': LENGTH,
            '__ref_2__': LENGTH,
        }

        local_dict = {p: Symbol(p) for p in placeholder_dims}
        parsed_expr = sp.sympify(expr_str, locals=local_dict)

        def infer_dim(node):
            if isinstance(node, Symbol):
                return placeholder_dims.get(str(node), DIMENSIONLESS)
            if node.is_number:
                return DIMENSIONLESS
            if isinstance(node, Pow):
                base_dim = infer_dim(node.args[0])
                exp = node.args[1]
                if exp.is_number:
                    exp_val = float(exp)
                    if exp_val == int(exp_val):
                        return base_dim ** int(exp_val)
                return DIMENSIONLESS
            if isinstance(node, Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    result = result * infer_dim(arg)
                return result
            return DIMENSIONLESS

        result = infer_dim(parsed_expr)
        assert result == VOLUME, f"Expected VOLUME, got {dimension_to_string(result)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
