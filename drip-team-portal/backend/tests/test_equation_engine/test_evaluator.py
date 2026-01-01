"""
Equation Engine Evaluator Tests

Tests for evaluating equation ASTs.
"""

import pytest
import math
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.equation_engine import (
    parse_equation,
    evaluate_equation,
    evaluate_with_result,
    EvaluationError,
    UnknownInputError
)


class TestBasicEvaluation:
    """Test basic arithmetic evaluation."""

    def test_addition(self):
        """Evaluate addition."""
        parsed = parse_equation("a + b")
        result = evaluate_equation(parsed['ast'], {'a': 2, 'b': 3})
        assert result == 5.0

    def test_subtraction(self):
        """Evaluate subtraction."""
        parsed = parse_equation("a - b")
        result = evaluate_equation(parsed['ast'], {'a': 10, 'b': 3})
        assert result == 7.0

    def test_multiplication(self):
        """Evaluate multiplication."""
        parsed = parse_equation("a * b")
        result = evaluate_equation(parsed['ast'], {'a': 4, 'b': 5})
        assert result == 20.0

    def test_division(self):
        """Evaluate division."""
        parsed = parse_equation("a / b")
        result = evaluate_equation(parsed['ast'], {'a': 10, 'b': 2})
        assert result == 5.0

    def test_power(self):
        """Evaluate exponentiation."""
        parsed = parse_equation("x**2")
        result = evaluate_equation(parsed['ast'], {'x': 3})
        assert result == 9.0

    def test_complex_expression(self):
        """Evaluate complex multi-variable expression."""
        parsed = parse_equation("length * CTE * delta_T")
        result = evaluate_equation(parsed['ast'], {
            'length': 0.003,   # 3mm in meters
            'CTE': 8.1e-6,     # 1/K
            'delta_T': 500     # K
        })
        expected = 0.003 * 8.1e-6 * 500
        assert abs(result - expected) < 1e-15


class TestFunctionEvaluation:
    """Test evaluation of mathematical functions."""

    def test_sqrt(self):
        """Evaluate square root."""
        parsed = parse_equation("sqrt(x)")
        result = evaluate_equation(parsed['ast'], {'x': 4})
        assert result == 2.0

    def test_sqrt_and_addition(self):
        """Evaluate sqrt plus constant."""
        parsed = parse_equation("sqrt(x) + 2")
        result = evaluate_equation(parsed['ast'], {'x': 4})
        assert result == 4.0

    def test_sin(self):
        """Evaluate sine function."""
        parsed = parse_equation("sin(x)")
        result = evaluate_equation(parsed['ast'], {'x': 0})
        assert abs(result) < 1e-10

    def test_cos(self):
        """Evaluate cosine function."""
        parsed = parse_equation("cos(x)")
        result = evaluate_equation(parsed['ast'], {'x': 0})
        assert abs(result - 1.0) < 1e-10

    def test_exp(self):
        """Evaluate exponential function."""
        parsed = parse_equation("exp(x)")
        result = evaluate_equation(parsed['ast'], {'x': 0})
        assert result == 1.0

    def test_ln(self):
        """Evaluate natural log."""
        parsed = parse_equation("ln(x)")
        result = evaluate_equation(parsed['ast'], {'x': math.e})
        assert abs(result - 1.0) < 1e-10

    def test_abs(self):
        """Evaluate absolute value."""
        parsed = parse_equation("abs(x)")
        result = evaluate_equation(parsed['ast'], {'x': -5})
        assert result == 5.0


class TestConstantsEvaluation:
    """Test evaluation with mathematical constants."""

    def test_pi(self):
        """Evaluate expression with pi."""
        parsed = parse_equation("pi * r**2")
        result = evaluate_equation(parsed['ast'], {'r': 1})
        assert abs(result - math.pi) < 1e-10

    def test_e_constant(self):
        """Evaluate expression with e."""
        parsed = parse_equation("e * x")
        result = evaluate_equation(parsed['ast'], {'x': 2})
        assert abs(result - 2 * math.e) < 1e-10


class TestErrorHandling:
    """Test error handling during evaluation."""

    def test_division_by_zero(self):
        """Division by zero should raise error."""
        parsed = parse_equation("a / b")
        with pytest.raises(EvaluationError) as exc_info:
            evaluate_equation(parsed['ast'], {'a': 1, 'b': 0})
        assert 'zero' in str(exc_info.value).lower()

    def test_missing_input(self):
        """Missing input should raise error."""
        parsed = parse_equation("a + b")
        with pytest.raises(UnknownInputError):
            evaluate_equation(parsed['ast'], {'a': 1})  # Missing 'b'

    def test_sqrt_negative(self):
        """Square root of negative should raise error."""
        parsed = parse_equation("sqrt(x)")
        with pytest.raises(EvaluationError):
            evaluate_equation(parsed['ast'], {'x': -1})

    def test_log_zero(self):
        """Log of zero should raise error."""
        parsed = parse_equation("ln(x)")
        with pytest.raises(EvaluationError):
            evaluate_equation(parsed['ast'], {'x': 0})

    def test_log_negative(self):
        """Log of negative should raise error."""
        parsed = parse_equation("ln(x)")
        with pytest.raises(EvaluationError):
            evaluate_equation(parsed['ast'], {'x': -1})


class TestEvaluateWithResult:
    """Test the evaluate_with_result helper function."""

    def test_successful_evaluation(self):
        """Test successful evaluation returns proper structure."""
        parsed = parse_equation("a * b")
        result = evaluate_with_result(parsed, {'a': 3, 'b': 4})
        assert result['success'] == True
        assert result['value'] == 12.0
        assert 'inputs_used' in result

    def test_failed_evaluation(self):
        """Test failed evaluation returns error info."""
        parsed = parse_equation("a / b")
        result = evaluate_with_result(parsed, {'a': 1, 'b': 0})
        assert result['success'] == False
        assert 'error' in result
        assert result['error_type'] in ('EvaluationError', 'UnknownInputError')
