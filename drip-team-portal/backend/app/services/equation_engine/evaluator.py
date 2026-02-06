"""
Equation Evaluator - AST Tree Walker

Evaluates equation AST given input values.
Handles math errors gracefully with EvaluationError.
"""

import math
import logging
from typing import Dict, Any, Union, Optional

from .exceptions import EvaluationError, UnknownInputError

logger = logging.getLogger(__name__)


def evaluate_equation(
    ast: Dict[str, Any],
    input_values: Dict[str, float],
    expression: Optional[str] = None
) -> float:
    """
    Evaluate an equation AST with given input values.

    Args:
        ast: The AST dict (from parse_equation result["ast"])
        input_values: Dict mapping input names to numeric values
                     Example: {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
        expression: Optional original expression string for error context

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
    logger.debug(
        f"evaluate_equation: Starting evaluation with {len(input_values)} inputs"
        + (f" for expression '{expression}'" if expression else "")
    )

    # Build case-insensitive lookup for input values
    # This handles mismatches between AST names (from equation) and schema names
    normalized_inputs = {
        k.replace(' ', '_').lower(): v
        for k, v in input_values.items()
    }

    try:
        result = _evaluate_node(ast, input_values, normalized_inputs, expression)
        logger.debug(f"evaluate_equation: Result = {result}")
        return result
    except UnknownInputError:
        raise
    except EvaluationError:
        raise
    except ZeroDivisionError as e:
        logger.error(f"evaluate_equation: Division by zero in '{expression}' with inputs {input_values}")
        raise EvaluationError(
            "Division by zero",
            expression=expression,
            input_values=input_values
        )
    except ValueError as e:
        logger.error(f"evaluate_equation: Math domain error in '{expression}': {e}")
        raise EvaluationError(
            f"Math domain error: {e}",
            expression=expression,
            input_values=input_values
        )
    except OverflowError as e:
        logger.error(f"evaluate_equation: Numeric overflow in '{expression}' with inputs {input_values}")
        raise EvaluationError(
            "Numeric overflow - result too large",
            expression=expression,
            input_values=input_values
        )
    except Exception as e:
        logger.error(f"evaluate_equation: Unexpected error in '{expression}': {type(e).__name__}: {e}")
        raise EvaluationError(
            f"Evaluation failed: {type(e).__name__}: {e}",
            expression=expression,
            input_values=input_values,
            details={"error_type": type(e).__name__}
        )


def _evaluate_node(
    node: Dict[str, Any],
    input_values: Dict[str, float],
    normalized_inputs: Dict[str, float],
    expression: Optional[str] = None
) -> float:
    """Recursively evaluate an AST node."""
    node_type = node.get("type")

    if node_type is None:
        logger.error(f"_evaluate_node: Invalid AST node with no 'type': {node}")
        raise EvaluationError(
            "Invalid AST node: missing 'type'",
            expression=expression,
            node_type=None,
            details={"node": node}
        )

    # Constant value
    if node_type == "const":
        return float(node["value"])

    # Input variable - use case-insensitive lookup
    if node_type == "input":
        name = node["name"]
        # First try exact match
        if name in input_values:
            value = float(input_values[name])
            logger.debug(f"_evaluate_node: Input '{name}' = {value} (exact match)")
            return value
        # Then try normalized (case-insensitive, space->underscore) lookup
        normalized_name = name.replace(' ', '_').lower()
        if normalized_name in normalized_inputs:
            value = float(normalized_inputs[normalized_name])
            logger.debug(f"_evaluate_node: Input '{name}' = {value} (normalized match)")
            return value
        logger.error(
            f"_evaluate_node: Unknown input '{name}'. "
            f"Available inputs: {list(input_values.keys())}"
        )
        raise UnknownInputError(name, list(input_values.keys()), expression=expression)

    # Addition
    if node_type == "add":
        operands = node.get("operands", [])
        if not operands:
            return 0.0
        result = 0.0
        for operand in operands:
            result += _evaluate_node(operand, input_values, normalized_inputs, expression)
        return result

    # Multiplication
    if node_type == "mul":
        operands = node.get("operands", [])
        if not operands:
            return 1.0
        result = 1.0
        for operand in operands:
            result *= _evaluate_node(operand, input_values, normalized_inputs, expression)
        return result

    # Division
    if node_type == "div":
        numerator = _evaluate_node(node["numerator"], input_values, normalized_inputs, expression)
        denominator = _evaluate_node(node["denominator"], input_values, normalized_inputs, expression)
        if denominator == 0:
            logger.error(f"_evaluate_node: Division by zero - numerator={numerator}")
            raise EvaluationError(
                "Division by zero",
                expression=expression,
                input_values=input_values,
                node_type="div",
                details={"numerator": numerator}
            )
        return numerator / denominator

    # Power/Exponentiation
    if node_type == "pow":
        base = _evaluate_node(node["base"], input_values, normalized_inputs, expression)
        exponent = _evaluate_node(node["exponent"], input_values, normalized_inputs, expression)

        # Check for invalid operations
        if base < 0 and not float(exponent).is_integer():
            logger.error(
                f"_evaluate_node: Cannot raise negative {base} to non-integer power {exponent}"
            )
            raise EvaluationError(
                f"Cannot raise negative number {base} to non-integer power {exponent}",
                expression=expression,
                input_values=input_values,
                node_type="pow",
                details={"base": base, "exponent": exponent}
            )
        if base == 0 and exponent < 0:
            logger.error("_evaluate_node: Cannot raise zero to negative power")
            raise EvaluationError(
                "Cannot raise zero to negative power",
                expression=expression,
                input_values=input_values,
                node_type="pow",
                details={"base": base, "exponent": exponent}
            )

        return math.pow(base, exponent)

    # Negation
    if node_type == "neg":
        operand = _evaluate_node(node["operand"], input_values, normalized_inputs, expression)
        return -operand

    # Functions
    if node_type == "func":
        func_name = node["name"]
        arg = _evaluate_node(node["arg"], input_values, normalized_inputs, expression)
        return _evaluate_function(func_name, arg, expression, input_values)

    logger.error(f"_evaluate_node: Unknown node type '{node_type}'")
    raise EvaluationError(
        f"Unknown AST node type: {node_type}",
        expression=expression,
        node_type=node_type
    )


def _evaluate_function(
    func_name: str,
    arg: float,
    expression: Optional[str] = None,
    input_values: Optional[Dict[str, float]] = None
) -> float:
    """Evaluate a mathematical function."""

    if func_name == "sqrt":
        if arg < 0:
            logger.error(f"_evaluate_function: Cannot take sqrt of negative number {arg}")
            raise EvaluationError(
                f"Cannot take square root of negative number: {arg}",
                expression=expression,
                input_values=input_values,
                node_type="func:sqrt",
                details={"argument": arg}
            )
        return math.sqrt(arg)

    if func_name == "exp":
        try:
            return math.exp(arg)
        except OverflowError:
            logger.error(f"_evaluate_function: Overflow in exp({arg})")
            raise EvaluationError(
                f"Overflow in exp({arg}) - argument too large",
                expression=expression,
                input_values=input_values,
                node_type="func:exp",
                details={"argument": arg}
            )

    if func_name == "ln":
        if arg <= 0:
            logger.error(f"_evaluate_function: Cannot take ln of non-positive number {arg}")
            raise EvaluationError(
                f"Cannot take logarithm of non-positive number: {arg}",
                expression=expression,
                input_values=input_values,
                node_type="func:ln",
                details={"argument": arg}
            )
        return math.log(arg)

    if func_name == "log":
        # log is natural log in our system (same as ln)
        if arg <= 0:
            logger.error(f"_evaluate_function: Cannot take log of non-positive number {arg}")
            raise EvaluationError(
                f"Cannot take logarithm of non-positive number: {arg}",
                expression=expression,
                input_values=input_values,
                node_type="func:log",
                details={"argument": arg}
            )
        return math.log(arg)

    if func_name == "sin":
        return math.sin(arg)

    if func_name == "cos":
        return math.cos(arg)

    if func_name == "tan":
        # Check for asymptotes (cos(arg) ≈ 0)
        cos_val = math.cos(arg)
        if abs(cos_val) < 1e-15:
            logger.error(f"_evaluate_function: tan undefined at {arg} (near asymptote)")
            raise EvaluationError(
                f"tan undefined at {arg} (near asymptote, cos(x) ≈ 0)",
                expression=expression,
                input_values=input_values,
                node_type="func:tan",
                details={"argument": arg, "cos_value": cos_val}
            )
        return math.tan(arg)

    if func_name == "abs":
        return abs(arg)

    logger.error(f"_evaluate_function: Unknown function '{func_name}'")
    raise EvaluationError(
        f"Unknown function: {func_name}",
        expression=expression,
        node_type=f"func:{func_name}"
    )


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
            "error_type": "EvaluationError",
            "error_details": {...}
        }
    """
    original_expression = parsed_equation.get("original")

    try:
        ast = parsed_equation.get("ast")
        if ast is None:
            logger.error(f"evaluate_with_result: No AST in parsed equation for '{original_expression}'")
            return {
                "success": False,
                "error": "No AST in parsed equation",
                "error_type": "EvaluationError",
                "expression": original_expression
            }

        value = evaluate_equation(ast, input_values, expression=original_expression)

        return {
            "success": True,
            "value": value,
            "inputs_used": input_values
        }

    except UnknownInputError as e:
        logger.warning(f"evaluate_with_result: Unknown input error: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "UnknownInputError",
            "error_details": e.to_dict() if hasattr(e, 'to_dict') else None
        }
    except EvaluationError as e:
        logger.warning(f"evaluate_with_result: Evaluation error: {e}")
        return {
            "success": False,
            "error": str(e),
            "error_type": "EvaluationError",
            "error_details": e.to_dict() if hasattr(e, 'to_dict') else None
        }
    except Exception as e:
        logger.error(f"evaluate_with_result: Unexpected error for '{original_expression}': {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {type(e).__name__}: {e}",
            "error_type": type(e).__name__,
            "expression": original_expression
        }
