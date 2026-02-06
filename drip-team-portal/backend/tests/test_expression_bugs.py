"""
Tests for expression parser bugs:
1. Space sensitivity - `Height ^2` fails while `Height^2` works
2. Unit inference - Dimension inference fails for expressions with exponents
3. Volume calculation - Products of multiple values don't compute correctly
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.equation_engine import (
    parse_equation,
    evaluate_equation,
    EquationParseError,
)


class TestSpaceSensitivity:
    """Test that whitespace around operators doesn't break parsing."""

    def test_caret_no_space(self):
        """Height^2 should work."""
        result = parse_equation("Height^2", allowed_inputs=["Height"])
        assert result['inputs'] == ["Height"]
        assert result['valid'] if 'valid' in result else True

    def test_caret_with_space_before(self):
        """Height ^2 should also work (space before caret)."""
        result = parse_equation("Height ^2", allowed_inputs=["Height"])
        assert "Height" in result['inputs']

    def test_caret_with_space_after(self):
        """Height^ 2 should also work (space after caret)."""
        result = parse_equation("Height^ 2", allowed_inputs=["Height"])
        assert "Height" in result['inputs']

    def test_caret_with_spaces_both_sides(self):
        """Height ^ 2 should also work (spaces both sides)."""
        result = parse_equation("Height ^ 2", allowed_inputs=["Height"])
        assert "Height" in result['inputs']

    def test_double_star_no_space(self):
        """Height**2 should work."""
        result = parse_equation("Height**2", allowed_inputs=["Height"])
        assert result['inputs'] == ["Height"]

    def test_double_star_with_spaces(self):
        """Height ** 2 should also work."""
        result = parse_equation("Height ** 2", allowed_inputs=["Height"])
        assert "Height" in result['inputs']

    def test_evaluate_caret_with_space(self):
        """Evaluate Height ^2 with space."""
        result = parse_equation("Height ^2", allowed_inputs=["Height"])
        value = evaluate_equation(result['ast'], {'Height': 3})
        assert value == 9.0

    def test_evaluate_caret_no_space(self):
        """Evaluate Height^2 without space."""
        result = parse_equation("Height^2", allowed_inputs=["Height"])
        value = evaluate_equation(result['ast'], {'Height': 3})
        assert value == 9.0


class TestVolumeCalculation:
    """Test that product expressions like Height * Width * Depth work."""

    def test_triple_product(self):
        """Height * Width * Depth should compute correctly."""
        result = parse_equation(
            "Height * Width * Depth",
            allowed_inputs=["Height", "Width", "Depth"]
        )
        assert set(result['inputs']) == {"Height", "Width", "Depth"}

        # Evaluate
        value = evaluate_equation(result['ast'], {
            'Height': 2.0,
            'Width': 3.0,
            'Depth': 4.0
        })
        assert value == 24.0

    def test_triple_product_with_parentheses(self):
        """(Height * Width) * Depth should also work."""
        result = parse_equation(
            "(Height * Width) * Depth",
            allowed_inputs=["Height", "Width", "Depth"]
        )
        value = evaluate_equation(result['ast'], {
            'Height': 2.0,
            'Width': 3.0,
            'Depth': 4.0
        })
        assert value == 24.0


class TestDimensionInferenceWithPower:
    """Test dimension inference for expressions with exponents."""

    def test_dimension_of_height_squared(self):
        """Test that Height^2 has dimension L² (area)."""
        from app.services.dimensional_analysis import (
            LENGTH, AREA, dimension_to_si_unit
        )

        # LENGTH ** 2 should equal AREA
        result = LENGTH ** 2
        assert result == AREA
        assert dimension_to_si_unit(result) == 'm²'

    def test_value_engine_dimension_inference(self):
        """Test that value_engine infers correct dimension for Height^2."""
        # This requires the full value_engine setup, which needs a DB session
        # For now, test the core logic directly
        from app.services.dimensional_analysis import (
            Dimension, DIMENSIONLESS, LENGTH, AREA, dimension_to_string
        )

        # Simulate what _infer_dimension_from_expr does for Pow nodes
        base_dim = LENGTH  # Height has length dimension
        exponent = 2

        # For integer exponents, dimension is raised to that power
        result_dim = base_dim ** exponent

        assert result_dim == AREA, f"Expected AREA, got {dimension_to_string(result_dim)}"


class TestCaretPreprocessing:
    """Test that ^ is correctly converted to ** in all contexts."""

    def test_caret_in_parser(self):
        """Test parser's _preprocess_equation handles caret."""
        from app.services.equation_engine.parser import _preprocess_equation

        result, mapping = _preprocess_equation("Height^2")
        assert "**" in result
        assert "^" not in result

    def test_caret_with_space_in_parser(self):
        """Test parser handles caret with surrounding spaces."""
        from app.services.equation_engine.parser import _preprocess_equation

        result, mapping = _preprocess_equation("Height ^ 2")
        assert "**" in result
        assert "^" not in result


class TestValueEngineExpressionParsing:
    """Test value_engine's _parse_expression for expression patterns."""

    def test_placeholder_power_no_space(self):
        """Test that __ref_0__^2 works in value_engine expression."""
        import re
        import sympy as sp
        from sympy import Symbol

        # Simulate value_engine's preprocessing
        expr = "__ref_0__^2"
        modified = re.sub(r'\^', '**', expr)

        assert modified == "__ref_0__**2"

        # Parse with sympy
        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        parsed = sp.sympify(modified, locals=local_dict)

        assert str(parsed) == "__ref_0__**2"

    def test_placeholder_power_with_space(self):
        """Test that __ref_0__ ^2 works in value_engine expression."""
        import re
        import sympy as sp
        from sympy import Symbol

        # Simulate value_engine's preprocessing
        expr = "__ref_0__ ^2"
        modified = re.sub(r'\^', '**', expr)

        # With space, this becomes "__ref_0__ **2"
        # SymPy should still parse this correctly
        assert modified == "__ref_0__ **2"

        local_dict = {'__ref_0__': Symbol('__ref_0__')}
        parsed = sp.sympify(modified, locals=local_dict)

        # Result should be the same
        assert str(parsed) == "__ref_0__**2"

    def test_sympy_handles_space_before_power(self):
        """Verify SymPy handles space before ** operator."""
        import sympy as sp
        from sympy import Symbol

        local_dict = {'Height': Symbol('Height')}

        # Without space
        expr1 = "Height**2"
        parsed1 = sp.sympify(expr1, locals=local_dict)

        # With space before **
        expr2 = "Height **2"
        parsed2 = sp.sympify(expr2, locals=local_dict)

        # With space after **
        expr3 = "Height** 2"
        parsed3 = sp.sympify(expr3, locals=local_dict)

        # With spaces both sides
        expr4 = "Height ** 2"
        parsed4 = sp.sympify(expr4, locals=local_dict)

        # All should produce the same result
        assert str(parsed1) == str(parsed2) == str(parsed3) == str(parsed4)


class TestInferDimensionFromExpr:
    """Test _infer_dimension_from_expr in value_engine."""

    def test_infer_dimension_simple_power(self):
        """Test dimension inference for Height**2."""
        import sympy as sp
        from sympy import Symbol
        from app.services.dimensional_analysis import (
            Dimension, DIMENSIONLESS, LENGTH, AREA, dimension_to_string
        )

        # Create a simple Pow expression
        Height = Symbol('Height')
        expr = Height ** 2

        # Build placeholder_dims map
        placeholder_dims = {'Height': LENGTH}

        # Walk the expression tree manually (simulating _infer_dimension_from_expr)
        assert isinstance(expr, sp.Pow)
        base = expr.args[0]  # Height
        exponent = expr.args[1]  # 2

        assert str(base) == 'Height'
        assert exponent.is_number
        assert float(exponent) == 2.0

        # Get base dimension
        base_dim = placeholder_dims[str(base)]
        assert base_dim == LENGTH

        # Compute result dimension
        result_dim = base_dim ** int(float(exponent))
        assert result_dim == AREA, f"Expected AREA, got {dimension_to_string(result_dim)}"

    def test_infer_dimension_mul_with_power(self):
        """Test dimension inference for pi * Height**2."""
        import sympy as sp
        from sympy import Symbol, pi
        from app.services.dimensional_analysis import (
            Dimension, DIMENSIONLESS, LENGTH, AREA, dimension_to_string
        )

        # Create expression: pi * Height**2
        Height = Symbol('Height')
        expr = pi * Height ** 2

        # This is a Mul of (pi, Height**2)
        assert isinstance(expr, sp.Mul)

        # Find the dimension through tree walk
        placeholder_dims = {'Height': LENGTH}

        def infer(node):
            if isinstance(node, Symbol):
                name = str(node)
                return placeholder_dims.get(name, DIMENSIONLESS)
            if node.is_number:
                return DIMENSIONLESS
            if isinstance(node, sp.Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    result = result * infer(arg)
                return result
            if isinstance(node, sp.Pow):
                base_dim = infer(node.args[0])
                exp = node.args[1]
                if exp.is_number:
                    return base_dim ** int(float(exp))
                return DIMENSIONLESS  # variable exponent
            return DIMENSIONLESS

        result = infer(expr)
        assert result == AREA, f"Expected AREA, got {dimension_to_string(result)}"


class TestVolumeExpressionInValueEngine:
    """Test that Volume = Height * Width * Depth computes correctly through value_engine patterns."""

    def test_triple_product_dimension(self):
        """Test that Height * Width * Depth has dimension L³ (volume)."""
        import sympy as sp
        from sympy import Symbol
        from app.services.dimensional_analysis import (
            DIMENSIONLESS, LENGTH, VOLUME, dimension_to_string
        )

        # Create expression
        Height = Symbol('Height')
        Width = Symbol('Width')
        Depth = Symbol('Depth')
        expr = Height * Width * Depth

        placeholder_dims = {
            'Height': LENGTH,
            'Width': LENGTH,
            'Depth': LENGTH,
        }

        def infer(node):
            if isinstance(node, Symbol):
                name = str(node)
                return placeholder_dims.get(name, DIMENSIONLESS)
            if node.is_number:
                return DIMENSIONLESS
            if isinstance(node, sp.Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    result = result * infer(arg)
                return result
            return DIMENSIONLESS

        result = infer(expr)
        assert result == VOLUME, f"Expected VOLUME (L³), got {dimension_to_string(result)}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
