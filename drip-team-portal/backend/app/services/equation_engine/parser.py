"""
Equation Parser - SymPy to AST Converter

Parses equation text into a JSON-serializable AST structure.
Validates that all inputs are in the allowed set.
"""

from typing import Dict, Any, List, Optional, Set
import logging
import sympy
from sympy import sympify, Symbol, sqrt, sin, cos, tan, log, exp, pi, E, Abs
from sympy.core.add import Add
from sympy.core.mul import Mul
from sympy.core.power import Pow
from sympy.core.numbers import (
    Integer, Float, Rational, Pi, Exp1, NegativeOne, One, Zero, Half
)
from sympy.core.symbol import Symbol as SymbolType
from sympy.functions.elementary.exponential import log as sympy_log, exp as sympy_exp
from sympy.functions.elementary.miscellaneous import sqrt as sympy_sqrt
from sympy.functions.elementary.trigonometric import sin as sympy_sin, cos as sympy_cos, tan as sympy_tan
from sympy.functions.elementary.complexes import Abs as sympy_abs

from .exceptions import EquationParseError, UnknownInputError
import re

logger = logging.getLogger(__name__)


def _preprocess_equation(
    equation_text: str,
    allowed_inputs: Optional[List[str]] = None
) -> tuple[str, dict[str, str]]:
    """
    Preprocess equation text for engineer-friendly syntax.

    Conversions:
    - ^ to ** (exponentiation): Engineers commonly use ^ for powers
    - Spaces in variable names to underscores (when allowed_inputs provided)

    Args:
        equation_text: Raw equation string
        allowed_inputs: Optional list of valid input names (used to identify
                       multi-word variable names that need space-to-underscore)

    Returns:
        Tuple of (preprocessed equation string, mapping of normalized to original names)
    """
    result = equation_text
    name_mapping = {}  # normalized_name -> original_name

    # Replace spaces in known input names with underscores
    # Sort by length descending to handle longer names first (avoid partial matches)
    if allowed_inputs:
        for input_name in sorted(allowed_inputs, key=len, reverse=True):
            if ' ' in input_name:
                normalized = input_name.replace(' ', '_')
                # Use word boundary-aware replacement to avoid partial matches
                # Match the input name when surrounded by non-word chars or string boundaries
                pattern = r'(?<![a-zA-Z0-9_])' + re.escape(input_name) + r'(?![a-zA-Z0-9_])'
                result = re.sub(pattern, normalized, result, flags=re.IGNORECASE)
                name_mapping[normalized.lower()] = input_name

    # Convert ^ to ** for exponentiation
    # This handles cases like: x^2, x ^ 2, (a+b)^2
    result = re.sub(r'\^', '**', result)

    return result, name_mapping


# Supported functions mapping
SUPPORTED_FUNCTIONS = {
    'sqrt': sqrt,
    'sin': sin,
    'cos': cos,
    'tan': tan,
    'log': log,
    'ln': log,  # ln is alias for log
    'exp': exp,
    'abs': Abs,
}

# Supported constants
SUPPORTED_CONSTANTS = {
    'pi': pi,
    'e': E,
}


def parse_equation(
    equation_text: str,
    allowed_inputs: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Parse equation text into a JSON-serializable AST.

    Args:
        equation_text: The equation string (e.g., "length * CTE * delta_T")
        allowed_inputs: Optional list of valid input names. If provided,
                       raises UnknownInputError for undefined inputs.

    Returns:
        Dict with structure:
        {
            "original": "length * CTE * delta_T",
            "ast": {
                "type": "mul",
                "operands": [
                    {"type": "input", "name": "length"},
                    {"type": "input", "name": "CTE"},
                    {"type": "input", "name": "delta_T"}
                ]
            },
            "inputs": ["length", "CTE", "delta_T"],
            "sympy_expr": <SymPy expression object>
        }

    Raises:
        EquationParseError: Invalid syntax
        UnknownInputError: References undefined input (if allowed_inputs provided)
    """
    logger.debug(f"parse_equation: Parsing '{equation_text}' with allowed_inputs={allowed_inputs}")

    if not equation_text or not equation_text.strip():
        logger.warning("parse_equation: Received empty equation")
        raise EquationParseError(
            "Empty equation",
            expression=equation_text
        )

    equation_text = equation_text.strip()

    # Preprocess for engineer-friendly syntax (^ to **, spaces to underscores)
    processed_text, name_mapping = _preprocess_equation(equation_text, allowed_inputs)
    if processed_text != equation_text:
        logger.debug(f"parse_equation: Preprocessed '{equation_text}' -> '{processed_text}'")

    # Build local dict for sympify
    local_dict = {}
    local_dict.update(SUPPORTED_FUNCTIONS)
    local_dict.update(SUPPORTED_CONSTANTS)

    # Pre-define user variables as Symbol objects so they take precedence
    # over SymPy built-ins (e.g., 'I' -> Symbol('I') instead of ImaginaryUnit,
    # 'E' -> Symbol('E') instead of Euler's number, 'S' -> Symbol('S'), etc.)
    if allowed_inputs:
        for inp in allowed_inputs:
            norm = inp.replace(' ', '_')
            if norm not in local_dict:
                local_dict[norm] = Symbol(norm)

    try:
        # Parse with SymPy
        sympy_expr = sympify(processed_text, locals=local_dict)
        logger.debug(f"parse_equation: SymPy parsed successfully: {sympy_expr}")
    except SyntaxError as e:
        logger.error(f"parse_equation: Syntax error in '{equation_text}': {e}")
        # Try to extract position from SyntaxError
        position = getattr(e, 'offset', None)
        raise EquationParseError(
            f"Syntax error: {e}",
            expression=equation_text,
            position=position,
            details={"processed_text": processed_text}
        )
    except Exception as e:
        logger.error(f"parse_equation: Failed to parse '{equation_text}': {type(e).__name__}: {e}")
        raise EquationParseError(
            f"Failed to parse equation: {e}",
            expression=equation_text,
            details={"processed_text": processed_text, "error_type": type(e).__name__}
        )

    # Extract all input symbols from the expression
    found_inputs = _extract_inputs(sympy_expr)
    logger.debug(f"parse_equation: Found inputs: {found_inputs}")

    # Validate inputs if allowed_inputs provided
    # Need to compare normalized names (spaces replaced with underscores)
    if allowed_inputs is not None:
        # Build normalized allowed set
        normalized_allowed = {
            name.replace(' ', '_').lower(): name
            for name in allowed_inputs
        }
        for inp in found_inputs:
            inp_lower = inp.lower()
            if inp_lower not in normalized_allowed:
                logger.warning(
                    f"parse_equation: Unknown input '{inp}' in expression '{equation_text}'. "
                    f"Allowed inputs: {allowed_inputs}"
                )
                raise UnknownInputError(
                    inp,
                    allowed_inputs,
                    expression=equation_text
                )

    # Convert SymPy expression to AST
    try:
        ast = _sympy_to_ast(sympy_expr)
    except EquationParseError:
        raise
    except Exception as e:
        logger.error(f"parse_equation: Failed to convert to AST for '{equation_text}': {e}")
        raise EquationParseError(
            f"Failed to convert expression to AST: {e}",
            expression=equation_text,
            details={"sympy_expr": str(sympy_expr), "error_type": type(e).__name__}
        )

    # Map inputs back to original names (with spaces if that's how they were defined)
    original_inputs = set()
    if allowed_inputs:
        normalized_allowed = {
            name.replace(' ', '_').lower(): name
            for name in allowed_inputs
        }
        for inp in found_inputs:
            inp_lower = inp.lower()
            if inp_lower in normalized_allowed:
                original_inputs.add(normalized_allowed[inp_lower])
            else:
                original_inputs.add(inp)
    else:
        original_inputs = found_inputs

    logger.debug(f"parse_equation: Successfully parsed '{equation_text}' with inputs {sorted(original_inputs)}")

    return {
        "original": equation_text,
        "ast": ast,
        "inputs": sorted(original_inputs),
        "sympy_expr": sympy_expr,  # Keep for LaTeX generation
    }


def _extract_inputs(expr) -> Set[str]:
    """Extract all input variable names from a SymPy expression."""
    inputs = set()

    # Get all free symbols (variables that aren't defined constants)
    for symbol in expr.free_symbols:
        name = str(symbol)
        # Skip if it's a known constant
        if name not in SUPPORTED_CONSTANTS:
            inputs.add(name)

    return inputs


def _sympy_to_ast(expr) -> Dict[str, Any]:
    """
    Convert a SymPy expression to a JSON-serializable AST dict.

    AST node types:
    - {"type": "const", "value": 3.14}
    - {"type": "input", "name": "length"}
    - {"type": "add", "operands": [...]}
    - {"type": "mul", "operands": [...]}
    - {"type": "pow", "base": {...}, "exponent": {...}}
    - {"type": "neg", "operand": {...}}
    - {"type": "func", "name": "sqrt", "arg": {...}}
    """
    # Handle numbers
    if isinstance(expr, (Integer, Float, Rational)):
        return {"type": "const", "value": float(expr)}

    if isinstance(expr, Zero):
        return {"type": "const", "value": 0.0}

    if isinstance(expr, One):
        return {"type": "const", "value": 1.0}

    if isinstance(expr, NegativeOne):
        return {"type": "const", "value": -1.0}

    if isinstance(expr, Half):
        return {"type": "const", "value": 0.5}

    # Handle pi and e constants
    if isinstance(expr, Pi):
        return {"type": "const", "value": 3.141592653589793, "name": "pi"}

    if isinstance(expr, Exp1):
        return {"type": "const", "value": 2.718281828459045, "name": "e"}

    # Handle symbols (input variables)
    if isinstance(expr, SymbolType):
        name = str(expr)
        if name in SUPPORTED_CONSTANTS:
            # It's pi or e used as symbol
            if name == 'pi':
                return {"type": "const", "value": 3.141592653589793, "name": "pi"}
            elif name == 'e':
                return {"type": "const", "value": 2.718281828459045, "name": "e"}
        return {"type": "input", "name": name}

    # Handle addition
    if isinstance(expr, Add):
        operands = [_sympy_to_ast(arg) for arg in expr.args]
        return {"type": "add", "operands": operands}

    # Handle multiplication
    if isinstance(expr, Mul):
        operands = []
        for arg in expr.args:
            # Check for negation (multiplication by -1)
            if isinstance(arg, NegativeOne):
                # Skip -1, we'll handle it as negation of the whole thing
                continue
            operands.append(_sympy_to_ast(arg))

        # If there was a -1 factor, wrap in negation
        if any(isinstance(arg, NegativeOne) for arg in expr.args):
            if len(operands) == 1:
                return {"type": "neg", "operand": operands[0]}
            else:
                return {"type": "neg", "operand": {"type": "mul", "operands": operands}}

        if len(operands) == 1:
            return operands[0]
        return {"type": "mul", "operands": operands}

    # Handle power/exponentiation
    if isinstance(expr, Pow):
        base = _sympy_to_ast(expr.args[0])
        exponent = _sympy_to_ast(expr.args[1])

        # Check for sqrt (power of 1/2)
        if isinstance(expr.args[1], Rational) and expr.args[1] == Rational(1, 2):
            return {"type": "func", "name": "sqrt", "arg": base}

        # Check for negative exponent (division)
        if isinstance(expr.args[1], NegativeOne):
            return {"type": "div", "numerator": {"type": "const", "value": 1.0}, "denominator": base}

        return {"type": "pow", "base": base, "exponent": exponent}

    # Handle functions
    func_name = type(expr).__name__

    # sqrt
    if func_name == 'sqrt' or (isinstance(expr, Pow) and expr.args[1] == Rational(1, 2)):
        return {"type": "func", "name": "sqrt", "arg": _sympy_to_ast(expr.args[0])}

    # exp
    if func_name == 'exp':
        return {"type": "func", "name": "exp", "arg": _sympy_to_ast(expr.args[0])}

    # log/ln
    if func_name == 'log':
        return {"type": "func", "name": "ln", "arg": _sympy_to_ast(expr.args[0])}

    # Trig functions
    if func_name == 'sin':
        return {"type": "func", "name": "sin", "arg": _sympy_to_ast(expr.args[0])}

    if func_name == 'cos':
        return {"type": "func", "name": "cos", "arg": _sympy_to_ast(expr.args[0])}

    if func_name == 'tan':
        return {"type": "func", "name": "tan", "arg": _sympy_to_ast(expr.args[0])}

    # abs
    if func_name == 'Abs':
        return {"type": "func", "name": "abs", "arg": _sympy_to_ast(expr.args[0])}

    # Fallback for unhandled types
    logger.warning(f"_sympy_to_ast: Unsupported expression type '{func_name}' for expr: {expr}")
    raise EquationParseError(
        f"Unsupported expression type: {func_name}",
        expression=str(expr),
        details={"sympy_type": func_name, "args": [str(a) for a in getattr(expr, 'args', [])]}
    )


def get_ast_inputs(ast: Dict[str, Any]) -> Set[str]:
    """
    Extract all input names from an AST.
    Useful for validation without re-parsing.
    """
    inputs = set()
    _collect_inputs(ast, inputs)
    return inputs


def _collect_inputs(node: Dict[str, Any], inputs: Set[str]):
    """Recursively collect input names from AST nodes."""
    node_type = node.get("type")

    if node_type == "input":
        inputs.add(node["name"])
    elif node_type in ("add", "mul"):
        for operand in node.get("operands", []):
            _collect_inputs(operand, inputs)
    elif node_type == "pow":
        _collect_inputs(node["base"], inputs)
        _collect_inputs(node["exponent"], inputs)
    elif node_type == "div":
        _collect_inputs(node["numerator"], inputs)
        _collect_inputs(node["denominator"], inputs)
    elif node_type == "neg":
        _collect_inputs(node["operand"], inputs)
    elif node_type == "func":
        _collect_inputs(node["arg"], inputs)
    # "const" nodes have no inputs to collect
