"""
Equation Engine - Expression Parsing, Evaluation, and LaTeX Generation

This module provides tools for working with mathematical equations in physics models:
- Parse equation text into structured AST (Abstract Syntax Tree)
- Validate equation structure and input references
- Evaluate equations given input values
- Generate LaTeX for display

Key difference from value_engine: This handles MODEL equations (templates with
named inputs like 'length', 'CTE', 'delta_T'), not component property expressions
(with #COMPONENT.property references).

Example Usage:
    from app.services.equation_engine import (
        parse_equation,
        evaluate_equation,
        generate_latex,
        EquationParseError,
        UnknownInputError,
        EvaluationError,
    )

    # Parse an equation
    parsed = parse_equation(
        "length * CTE * delta_T",
        allowed_inputs=["length", "CTE", "delta_T"]
    )

    # Evaluate with input values
    result = evaluate_equation(
        parsed["ast"],
        {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
    )
    # Returns: 0.00001215

    # Generate LaTeX for display
    latex = generate_latex(parsed)
    # Returns: "L \\cdot \\alpha \\cdot \\Delta T"
"""

from .parser import parse_equation, get_ast_inputs
from .evaluator import evaluate_equation, evaluate_with_result
from .latex_generator import (
    generate_latex,
    generate_latex_from_ast,
    format_equation_display,
    SYMBOL_LATEX_MAP,
)
from .exceptions import EquationParseError, UnknownInputError, EvaluationError

__all__ = [
    # Parser
    'parse_equation',
    'get_ast_inputs',

    # Evaluator
    'evaluate_equation',
    'evaluate_with_result',

    # LaTeX
    'generate_latex',
    'generate_latex_from_ast',
    'format_equation_display',
    'SYMBOL_LATEX_MAP',

    # Exceptions
    'EquationParseError',
    'UnknownInputError',
    'EvaluationError',
]
