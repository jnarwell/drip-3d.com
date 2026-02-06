"""
Equation Engine Exceptions

Custom exception classes for equation parsing and evaluation errors.
All exceptions include structured context for debugging.
"""

from typing import Optional, List, Dict, Any


class EquationParseError(Exception):
    """
    Invalid equation syntax.

    Attributes:
        expression: The expression that failed to parse
        position: Character position where parsing failed (if known)
        details: Additional context about the failure
    """

    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        position: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.expression = expression
        self.position = position
        self.details = details or {}

        # Build informative message
        full_msg = message
        if expression:
            # Truncate very long expressions
            display_expr = expression if len(expression) <= 100 else expression[:97] + "..."
            full_msg = f"{message} | Expression: '{display_expr}'"
            if position is not None:
                full_msg += f" (at position {position})"

        super().__init__(full_msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "EquationParseError",
            "message": str(self.args[0]) if self.args else "Parse error",
            "expression": self.expression,
            "position": self.position,
            "details": self.details,
        }


class UnknownInputError(Exception):
    """
    Equation references undefined input.

    Attributes:
        input_name: The undefined input name referenced
        allowed_inputs: List of valid input names
        expression: The expression containing the reference (if known)
    """

    def __init__(
        self,
        input_name: str,
        allowed_inputs: Optional[List[str]] = None,
        expression: Optional[str] = None
    ):
        self.input_name = input_name
        self.allowed_inputs = allowed_inputs or []
        self.expression = expression

        if allowed_inputs:
            msg = f"Unknown input '{input_name}'. Allowed inputs: {', '.join(sorted(allowed_inputs))}"
        else:
            msg = f"Unknown input '{input_name}'"

        if expression:
            display_expr = expression if len(expression) <= 80 else expression[:77] + "..."
            msg += f" | Expression: '{display_expr}'"

        super().__init__(msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "UnknownInputError",
            "message": str(self.args[0]) if self.args else "Unknown input",
            "input_name": self.input_name,
            "allowed_inputs": self.allowed_inputs,
            "expression": self.expression,
        }


class EvaluationError(Exception):
    """
    Runtime math error (div by zero, domain error, etc.).

    Attributes:
        expression: The expression being evaluated (if known)
        input_values: The input values used for evaluation (if known)
        node_type: The AST node type where error occurred (if known)
        details: Additional context about the failure
    """

    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        input_values: Optional[Dict[str, float]] = None,
        node_type: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.expression = expression
        self.input_values = input_values
        self.node_type = node_type
        self.details = details or {}

        # Build informative message
        full_msg = message
        context_parts = []

        if expression:
            display_expr = expression if len(expression) <= 60 else expression[:57] + "..."
            context_parts.append(f"expression='{display_expr}'")

        if node_type:
            context_parts.append(f"node={node_type}")

        if input_values:
            # Show first few input values
            vals = list(input_values.items())[:3]
            vals_str = ", ".join(f"{k}={v}" for k, v in vals)
            if len(input_values) > 3:
                vals_str += f", ... (+{len(input_values) - 3} more)"
            context_parts.append(f"inputs={{{vals_str}}}")

        if context_parts:
            full_msg = f"{message} | {' | '.join(context_parts)}"

        super().__init__(full_msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "EvaluationError",
            "message": str(self.args[0]) if self.args else "Evaluation error",
            "expression": self.expression,
            "input_values": self.input_values,
            "node_type": self.node_type,
            "details": self.details,
        }


class DimensionInferenceError(Exception):
    """
    Error during dimensional analysis.

    Attributes:
        expression: The expression being analyzed
        placeholder_dimensions: Available placeholder dimensions at time of error
        details: Additional context
    """

    def __init__(
        self,
        message: str,
        expression: Optional[str] = None,
        placeholder_dimensions: Optional[Dict[str, str]] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.expression = expression
        self.placeholder_dimensions = placeholder_dimensions
        self.details = details or {}

        full_msg = message
        if expression:
            display_expr = expression if len(expression) <= 80 else expression[:77] + "..."
            full_msg = f"{message} | Expression: '{display_expr}'"

        if placeholder_dimensions:
            dims_str = ", ".join(f"{k}: {v}" for k, v in list(placeholder_dimensions.items())[:5])
            if len(placeholder_dimensions) > 5:
                dims_str += f", ... (+{len(placeholder_dimensions) - 5} more)"
            full_msg += f" | Available dimensions: {{{dims_str}}}"

        super().__init__(full_msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "DimensionInferenceError",
            "message": str(self.args[0]) if self.args else "Dimension inference error",
            "expression": self.expression,
            "placeholder_dimensions": self.placeholder_dimensions,
            "details": self.details,
        }
