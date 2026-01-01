"""
Equation Engine Parser Tests

Tests for parsing equations into AST.
"""

import pytest
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.equation_engine import (
    parse_equation,
    get_ast_inputs,
    EquationParseError,
    UnknownInputError
)


class TestBasicParsing:
    """Test basic equation parsing."""

    def test_parse_addition(self):
        """Parse simple addition."""
        result = parse_equation("a + b")
        assert result['ast']['type'] == 'add'
        assert set(result['inputs']) == {'a', 'b'}

    def test_parse_multiplication(self):
        """Parse simple multiplication."""
        result = parse_equation("a * b")
        assert result['ast']['type'] == 'mul'
        assert set(result['inputs']) == {'a', 'b'}

    def test_parse_complex_expression(self):
        """Parse complex multi-variable expression."""
        result = parse_equation("length * CTE * delta_T")
        assert set(result['inputs']) == {'length', 'CTE', 'delta_T'}

    def test_parse_with_constants(self):
        """Parse expression with pi constant."""
        result = parse_equation("pi * r * r")
        assert 'r' in result['inputs']
        # pi should not be in inputs (it's a constant)
        assert 'pi' not in result['inputs']

    def test_parse_division(self):
        """Parse division expression."""
        result = parse_equation("a / b")
        # Could be div or pow with negative exponent
        assert result['ast'] is not None
        assert set(result['inputs']) == {'a', 'b'}

    def test_parse_power(self):
        """Parse power/exponent expression."""
        result = parse_equation("x**2")
        assert set(result['inputs']) == {'x'}
        # Should have pow somewhere in the AST
        assert 'pow' in str(result['ast']) or 'const' in str(result['ast'])


class TestFunctionParsing:
    """Test parsing of mathematical functions."""

    def test_parse_sqrt(self):
        """Parse square root function."""
        result = parse_equation("sqrt(x)")
        assert set(result['inputs']) == {'x'}
        # Should have func with sqrt
        ast_str = str(result['ast'])
        assert 'func' in ast_str or 'sqrt' in ast_str

    def test_parse_trig_functions(self):
        """Parse trigonometric functions."""
        result = parse_equation("sin(x) + cos(y)")
        assert set(result['inputs']) == {'x', 'y'}

    def test_parse_nested_functions(self):
        """Parse nested function calls."""
        result = parse_equation("sqrt(x**2 + y**2)")
        assert set(result['inputs']) == {'x', 'y'}

    def test_parse_exp_log(self):
        """Parse exp and log functions."""
        result = parse_equation("exp(x) + ln(y)")
        assert set(result['inputs']) == {'x', 'y'}


class TestGetAstInputs:
    """Test extracting inputs from AST."""

    def test_get_inputs_simple(self):
        """Get inputs from simple expression."""
        result = parse_equation("a + b")
        inputs = get_ast_inputs(result['ast'])
        assert inputs == {'a', 'b'}

    def test_get_inputs_complex(self):
        """Get inputs from complex expression."""
        result = parse_equation("length * CTE * delta_T + offset")
        inputs = get_ast_inputs(result['ast'])
        assert inputs == {'length', 'CTE', 'delta_T', 'offset'}

    def test_get_inputs_with_functions(self):
        """Get inputs from expression with functions."""
        result = parse_equation("sqrt(x) * sin(theta)")
        inputs = get_ast_inputs(result['ast'])
        assert inputs == {'x', 'theta'}


class TestErrorHandling:
    """Test error handling during parsing."""

    def test_parse_empty_string(self):
        """Empty string should raise error."""
        with pytest.raises(EquationParseError):
            parse_equation("")

    def test_parse_whitespace_only(self):
        """Whitespace-only should raise error."""
        with pytest.raises(EquationParseError):
            parse_equation("   ")

    def test_parse_invalid_syntax(self):
        """Invalid syntax should raise error."""
        with pytest.raises(EquationParseError):
            parse_equation("a + * b")  # Adjacent operators

    def test_parse_unbalanced_parentheses(self):
        """Unbalanced parentheses should raise error."""
        with pytest.raises(EquationParseError):
            parse_equation("sqrt(x")


class TestAllowedInputs:
    """Test input validation with allowed_inputs."""

    def test_parse_with_valid_inputs(self):
        """Parse with all inputs in allowed set."""
        result = parse_equation("a + b", allowed_inputs=['a', 'b', 'c'])
        assert set(result['inputs']) == {'a', 'b'}

    def test_parse_with_invalid_input(self):
        """Parse with input not in allowed set should raise error."""
        with pytest.raises(UnknownInputError) as exc_info:
            parse_equation("a + x", allowed_inputs=['a', 'b'])
        assert 'x' in str(exc_info.value)
