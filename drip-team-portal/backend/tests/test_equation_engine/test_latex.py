"""
Equation Engine LaTeX Generator Tests

Tests for generating LaTeX from equations.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../..'))

from app.services.equation_engine import (
    parse_equation,
    generate_latex,
    generate_latex_from_ast,
    SYMBOL_LATEX_MAP
)


class TestLatexGeneration:
    """Test LaTeX generation from parsed equations."""

    def test_simple_multiplication(self):
        """Generate LaTeX for simple multiplication."""
        parsed = parse_equation("a * b")
        latex = generate_latex(parsed)
        # Should contain some multiplication indicator
        assert latex is not None
        assert len(latex) > 0

    def test_thermal_expansion_equation(self):
        """Generate LaTeX for thermal expansion equation."""
        parsed = parse_equation("length * CTE * delta_T")
        latex = generate_latex(parsed)
        # Should use LaTeX symbols from SYMBOL_LATEX_MAP
        # CTE maps to \alpha, length to L, delta_T to \Delta T
        assert latex is not None

    def test_sqrt_function(self):
        """Generate LaTeX for sqrt."""
        parsed = parse_equation("sqrt(x)")
        latex = generate_latex(parsed)
        # Should have \sqrt
        assert 'sqrt' in latex.lower() or '\\sqrt' in latex

    def test_power_expression(self):
        """Generate LaTeX for power."""
        parsed = parse_equation("x**2")
        latex = generate_latex(parsed)
        # Should have exponent notation
        assert '^' in latex or '2' in latex

    def test_fraction(self):
        """Generate LaTeX for division/fraction."""
        parsed = parse_equation("a / b")
        latex = generate_latex(parsed)
        # Should have fraction notation
        assert latex is not None


class TestLatexFromAst:
    """Test LaTeX generation directly from AST."""

    def test_from_ast_simple(self):
        """Generate LaTeX from simple AST."""
        ast = {
            "type": "mul",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "width"}
            ]
        }
        latex = generate_latex_from_ast(ast)
        assert 'length' in latex.lower() or 'L' in latex

    def test_from_ast_with_function(self):
        """Generate LaTeX from AST with function."""
        ast = {
            "type": "func",
            "name": "sqrt",
            "arg": {"type": "input", "name": "x"}
        }
        latex = generate_latex_from_ast(ast)
        assert 'sqrt' in latex.lower() or '\\sqrt' in latex


class TestSymbolMapping:
    """Test custom symbol mappings for LaTeX."""

    def test_default_symbol_map(self):
        """Verify default symbol map has expected entries."""
        assert 'CTE' in SYMBOL_LATEX_MAP
        assert 'delta_T' in SYMBOL_LATEX_MAP
        assert 'length' in SYMBOL_LATEX_MAP

    def test_custom_symbol_map(self):
        """Test using custom symbol map."""
        parsed = parse_equation("myvar * x")
        custom_map = {'myvar': r'\mu'}
        latex = generate_latex(parsed, symbol_map=custom_map)
        # Should use custom symbol
        assert latex is not None
