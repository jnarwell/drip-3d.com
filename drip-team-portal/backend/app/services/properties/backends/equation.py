"""Equation backend - evaluates mathematical formulas using sympy."""

from typing import Dict, Any
import re
from sympy import sympify, Symbol, N
from sympy.parsing.sympy_parser import parse_expr, standard_transformations, implicit_multiplication

from ..schemas import PropertySource


class EquationError(Exception):
    """Error during equation evaluation."""
    pass


def resolve_equation(
    source: PropertySource,
    output_name: str,
    inputs: Dict[str, Any]
) -> float:
    """
    Resolve an equation-based lookup.

    Uses sympy to parse and evaluate mathematical formulas.
    Supports:
    - Basic math operations (+, -, *, /, ^, **)
    - Common functions (exp, log, sin, cos, sqrt, abs)
    - Array constant lookup: alpha[material]
    - Conditional expressions: x if condition else y
    """
    resolution = source.resolution
    formulas = resolution.formulas
    constants = resolution.constants

    if output_name not in formulas:
        raise EquationError(f"No formula defined for output '{output_name}'")

    formula = formulas[output_name]

    # Build evaluation scope
    scope = {}

    # Add constants (may be nested dicts for array constants)
    for name, value in constants.items():
        if isinstance(value, dict):
            # Array constant like rho_0: {copper: 1.68e-8, aluminum: 2.65e-8}
            scope[name] = value
        else:
            scope[name] = float(value)

    # Add inputs
    for name, value in inputs.items():
        # Keep string inputs as-is for array lookups
        if isinstance(value, str):
            scope[name] = value
        else:
            scope[name] = float(value)

    # Pre-process formula to handle array access: alpha[material] -> alpha_material_value
    processed_formula = formula

    # Pattern: name[key] where key might be a variable or literal
    array_pattern = r'(\w+)\[(\w+)\]'
    matches = re.findall(array_pattern, formula)

    for arr_name, key_name in matches:
        if arr_name in scope and isinstance(scope[arr_name], dict):
            arr_dict = scope[arr_name]

            # key_name might be a variable (e.g., "material") or literal
            if key_name in scope:
                key_value = scope[key_name]
            else:
                key_value = key_name

            if key_value not in arr_dict:
                raise EquationError(
                    f"Key '{key_value}' not found in array constant '{arr_name}'"
                )

            # Replace array access with the actual value
            replacement = str(arr_dict[key_value])
            processed_formula = processed_formula.replace(
                f"{arr_name}[{key_name}]",
                replacement
            )

    # Handle conditional expressions: x < y ? a : b -> Piecewise((a, x < y), (b, True))
    # Python style: a if x < y else b
    ternary_pattern = r'(\w+)\s*<\s*(\w+)\s*\?\s*([^:]+)\s*:\s*([^\s)]+)'
    ternary_matches = re.findall(ternary_pattern, processed_formula)

    for left, right, if_true, if_false in ternary_matches:
        # Convert to Python conditional that sympy can handle
        # Actually, let's just evaluate the condition and substitute
        left_val = scope.get(left, left)
        right_val = scope.get(right, right)

        try:
            left_num = float(left_val) if not isinstance(left_val, str) else float(left_val)
            right_num = float(right_val) if not isinstance(right_val, str) else float(right_val)
            condition_result = left_num < right_num
        except (ValueError, TypeError):
            condition_result = True  # Default to true branch

        replacement = if_true.strip() if condition_result else if_false.strip()
        original = f"{left} < {right} ? {if_true} : {if_false}"
        processed_formula = processed_formula.replace(original, replacement)

    # Also handle Python-style: value if condition else other
    # Pattern: expr1 if expr2 else expr3
    py_ternary = r'([^\s]+)\s+if\s+([^e]+)\s+else\s+([^\s)]+)'

    # For now, let's use a simpler evaluation approach with exec
    # Build a clean numeric scope
    numeric_scope = {
        k: v for k, v in scope.items()
        if not isinstance(v, (dict, str)) or k in inputs
    }

    # Add math functions
    import math
    numeric_scope['exp'] = math.exp
    numeric_scope['log'] = math.log
    numeric_scope['log10'] = math.log10
    numeric_scope['sqrt'] = math.sqrt
    numeric_scope['sin'] = math.sin
    numeric_scope['cos'] = math.cos
    numeric_scope['tan'] = math.tan
    numeric_scope['abs'] = abs
    numeric_scope['pi'] = math.pi
    numeric_scope['e'] = math.e

    try:
        # Try direct Python eval first (simpler, handles conditionals)
        # Replace ^ with ** for exponentiation
        eval_formula = processed_formula.replace('^', '**')
        result = eval(eval_formula, {"__builtins__": {}}, numeric_scope)
        return float(result)
    except Exception as eval_error:
        # Fall back to sympy
        try:
            # Create sympy symbols for all variables
            symbols = {name: Symbol(name) for name in numeric_scope if isinstance(numeric_scope[name], (int, float))}

            # Parse the expression
            transformations = standard_transformations + (implicit_multiplication,)
            expr = parse_expr(processed_formula.replace('^', '**'), local_dict=symbols, transformations=transformations)

            # Substitute values
            for name, value in numeric_scope.items():
                if isinstance(value, (int, float)) and name in symbols:
                    expr = expr.subs(symbols[name], value)

            # Evaluate
            result = N(expr)
            return float(result)

        except Exception as sympy_error:
            raise EquationError(
                f"Failed to evaluate formula '{formula}': "
                f"eval error: {eval_error}, sympy error: {sympy_error}"
            )
