"""
Equation Engine Exceptions

Custom exception classes for equation parsing and evaluation errors.
"""


class EquationParseError(Exception):
    """Invalid equation syntax."""
    pass


class UnknownInputError(Exception):
    """Equation references undefined input."""

    def __init__(self, input_name: str, allowed_inputs: list = None):
        self.input_name = input_name
        self.allowed_inputs = allowed_inputs or []
        if allowed_inputs:
            msg = f"Unknown input '{input_name}'. Allowed inputs: {', '.join(allowed_inputs)}"
        else:
            msg = f"Unknown input '{input_name}'"
        super().__init__(msg)


class EvaluationError(Exception):
    """Runtime math error (div by zero, domain error, etc.)."""
    pass
