"""
Equation Evaluator - AST Tree Walker

Evaluates equation AST given input values.
Handles math errors gracefully with EvaluationError.
"""

import math
from typing import Dict, Any, Union

from .exceptions import EvaluationError, UnknownInputError


def evaluate_equation(
    ast: Dict[str, Any],
    input_values: Dict[str, float]
) -> float:
    """
    Evaluate an equation AST with given input values.

    Args:
        ast: The AST dict (from parse_equation result["ast"])
        input_values: Dict mapping input names to numeric values
                     Example: {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}

    Returns:
        The computed result as a float

    Raises:
        UnknownInputError: AST references an input not in input_values
        EvaluationError: Math error (div by zero, domain error, etc.)

    Example:
        ast = {
            "type": "mul",
            "operands": [
                {"type": "input", "name": "length"},
                {"type": "input", "name": "CTE"},
                {"type": "input", "name": "delta_T"}
            ]
        }
        input_values = {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
        result = evaluate_equation(ast, input_values)
        # Returns: 0.00001215
    """
    # Build case-insensitive lookup for input values
    # This handles mismatches between AST names (from equation) and schema names
    normalized_inputs = {
        k.replace(' ', '_').lower(): v
        for k, v in input_values.items()
    }

    try:
        return _evaluate_node(ast, input_values, normalized_inputs)
    except UnknownInputError:
        raise
    except EvaluationError:
        raise
    except ZeroDivisionError:
        raise EvaluationError("Division by zero")
    except ValueError as e:
        raise EvaluationError(f"Math domain error: {e}")
    except OverflowError:
        raise EvaluationError("Numeric overflow")
    except Exception as e:
        raise EvaluationError(f"Evaluation failed: {e}")


def _evaluate_node(
    node: Dict[str, Any],
    input_values: Dict[str, float],
    normalized_inputs: Dict[str, float]
) -> float:
    """Recursively evaluate an AST node."""
    node_type = node.get("type")

    if node_type is None:
        raise EvaluationError("Invalid AST node: missing 'type'")

    # Constant value
    if node_type == "const":
        return float(node["value"])

    # Input variable - use case-insensitive lookup
    if node_type == "input":
        name = node["name"]
        # First try exact match
        if name in input_values:
            return float(input_values[name])
        # Then try normalized (case-insensitive, space->underscore) lookup
        normalized_name = name.replace(' ', '_').lower()
        if normalized_name in normalized_inputs:
            return float(normalized_inputs[normalized_name])
        raise UnknownInputError(name, list(input_values.keys()))

    # Addition
    if node_type == "add":
        operands = node.get("operands", [])
        if not operands:
            return 0.0
        result = 0.0
        for operand in operands:
            result += _evaluate_node(operand, input_values, normalized_inputs)
        return result

    # Multiplication
    if node_type == "mul":
        operands = node.get("operands", [])
        if not operands:
            return 1.0
        result = 1.0
        for operand in operands:
            result *= _evaluate_node(operand, input_values, normalized_inputs)
        return result

    # Division
    if node_type == "div":
        numerator = _evaluate_node(node["numerator"], input_values, normalized_inputs)
        denominator = _evaluate_node(node["denominator"], input_values, normalized_inputs)
        if denominator == 0:
            raise EvaluationError("Division by zero")
        return numerator / denominator

    # Power/Exponentiation
    if node_type == "pow":
        base = _evaluate_node(node["base"], input_values, normalized_inputs)
        exponent = _evaluate_node(node["exponent"], input_values, normalized_inputs)

        # Check for invalid operations
        if base < 0 and not exponent.is_integer():
            raise EvaluationError(
                f"Cannot raise negative number {base} to non-integer power {exponent}"
            )
        if base == 0 and exponent < 0:
            raise EvaluationError("Cannot raise zero to negative power")

        return math.pow(base, exponent)

    # Negation
    if node_type == "neg":
        operand = _evaluate_node(node["operand"], input_values, normalized_inputs)
        return -operand

    # Functions
    if node_type == "func":
        func_name = node["name"]
        arg = _evaluate_node(node["arg"], input_values, normalized_inputs)
        return _evaluate_function(func_name, arg)

    raise EvaluationError(f"Unknown AST node type: {node_type}")


def _evaluate_function(func_name: str, arg: float) -> float:
    """Evaluate a mathematical function."""

    if func_name == "sqrt":
        if arg < 0:
            raise EvaluationError(f"Cannot take square root of negative number: {arg}")
        return math.sqrt(arg)

    if func_name == "exp":
        try:
            return math.exp(arg)
        except OverflowError:
            raise EvaluationError(f"Overflow in exp({arg})")

    if func_name == "ln":
        if arg <= 0:
            raise EvaluationError(f"Cannot take logarithm of non-positive number: {arg}")
        return math.log(arg)

    if func_name == "log":
        # log is natural log in our system (same as ln)
        if arg <= 0:
            raise EvaluationError(f"Cannot take logarithm of non-positive number: {arg}")
        return math.log(arg)

    if func_name == "sin":
        return math.sin(arg)

    if func_name == "cos":
        return math.cos(arg)

    if func_name == "tan":
        # Check for asymptotes (cos(arg) ≈ 0)
        cos_val = math.cos(arg)
        if abs(cos_val) < 1e-15:
            raise EvaluationError(f"tan undefined at {arg} (near asymptote)")
        return math.tan(arg)

    if func_name == "abs":
        return abs(arg)

    raise EvaluationError(f"Unknown function: {func_name}")


def evaluate_with_result(
    parsed_equation: Dict[str, Any],
    input_values: Dict[str, float]
) -> Dict[str, Any]:
    """
    Evaluate a parsed equation and return structured result.

    This is a convenience wrapper that takes the full parsed equation
    dict (from parse_equation) and returns a result dict.

    Args:
        parsed_equation: The full result from parse_equation()
        input_values: Dict mapping input names to numeric values

    Returns:
        {
            "success": True,
            "value": 0.00001215,
            "inputs_used": {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
        }
        or
        {
            "success": False,
            "error": "Division by zero",
            "error_type": "EvaluationError"
        }
    """
    try:
        ast = parsed_equation.get("ast")
        if ast is None:
            return {
                "success": False,
                "error": "No AST in parsed equation",
                "error_type": "EvaluationError"
            }

        value = evaluate_equation(ast, input_values)

        return {
            "success": True,
            "value": value,
            "inputs_used": input_values
        }

    except UnknownInputError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "UnknownInputError"
        }
    except EvaluationError as e:
        return {
            "success": False,
            "error": str(e),
            "error_type": "EvaluationError"
        }
