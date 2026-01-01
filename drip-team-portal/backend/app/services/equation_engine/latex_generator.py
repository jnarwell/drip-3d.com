"""
LaTeX Generator - AST to LaTeX Converter

Generates LaTeX representation of equations for display.
Uses SymPy's latex() function with custom symbol formatting.
"""

from typing import Dict, Any, Optional
import sympy
from sympy import latex as sympy_latex, Symbol, sqrt, sin, cos, tan, log, exp, pi, E, Abs
from sympy import Rational

from .exceptions import EquationParseError


# Common symbol name to LaTeX mappings
# Maps variable names to prettier LaTeX representations
SYMBOL_LATEX_MAP = {
    # Greek letters
    'alpha': r'\alpha',
    'beta': r'\beta',
    'gamma': r'\gamma',
    'delta': r'\delta',
    'epsilon': r'\epsilon',
    'theta': r'\theta',
    'lambda': r'\lambda',
    'mu': r'\mu',
    'nu': r'\nu',
    'rho': r'\rho',
    'sigma': r'\sigma',
    'tau': r'\tau',
    'phi': r'\phi',
    'omega': r'\omega',

    # Common engineering symbols
    'delta_T': r'\Delta T',
    'delta_t': r'\Delta t',
    'delta_x': r'\Delta x',
    'delta_y': r'\Delta y',
    'delta_z': r'\Delta z',
    'Delta_T': r'\Delta T',
    'Delta_t': r'\Delta t',

    # Material properties
    'CTE': r'\alpha',  # Coefficient of thermal expansion
    'E': r'E',  # Young's modulus
    'nu': r'\nu',  # Poisson's ratio
    'k': r'k',  # Thermal conductivity
    'rho': r'\rho',  # Density
    'Cp': r'C_p',  # Specific heat capacity
    'Cv': r'C_v',  # Specific heat at constant volume

    # Dimensions
    'length': r'L',
    'width': r'W',
    'height': r'H',
    'thickness': r't',
    'radius': r'r',
    'diameter': r'd',
    'area': r'A',
    'volume': r'V',

    # Forces and stresses
    'F': r'F',
    'stress': r'\sigma',
    'strain': r'\varepsilon',
    'pressure': r'P',

    # Temperature
    'T': r'T',
    'T1': r'T_1',
    'T2': r'T_2',
    'temp': r'T',
    'temperature': r'T',
}


def generate_latex(
    parsed_equation: Dict[str, Any],
    symbol_map: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate LaTeX representation from a parsed equation.

    Args:
        parsed_equation: The result from parse_equation(), must contain 'sympy_expr'
        symbol_map: Optional custom mapping of variable names to LaTeX symbols
                   Merges with default SYMBOL_LATEX_MAP (custom takes precedence)

    Returns:
        LaTeX string (e.g., "L \\cdot \\alpha \\cdot \\Delta T")

    Raises:
        EquationParseError: If sympy_expr is missing

    Example:
        parsed = parse_equation("length * CTE * delta_T")
        latex = generate_latex(parsed)
        # Returns: "L \\alpha \\Delta T"
    """
    sympy_expr = parsed_equation.get("sympy_expr")
    if sympy_expr is None:
        raise EquationParseError("Cannot generate LaTeX: sympy_expr missing from parsed equation")

    # Build combined symbol map
    combined_map = SYMBOL_LATEX_MAP.copy()
    if symbol_map:
        combined_map.update(symbol_map)

    # Perform symbol substitution for prettier output
    substituted_expr = _substitute_symbols(sympy_expr, combined_map)

    # Generate LaTeX using SymPy
    latex_str = sympy_latex(substituted_expr, mul_symbol='dot')

    return latex_str


def generate_latex_from_ast(
    ast: Dict[str, Any],
    symbol_map: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate LaTeX directly from an AST (without SymPy expression).

    This is useful when you only have the AST (e.g., loaded from database)
    and not the original SymPy expression.

    Args:
        ast: The AST dict
        symbol_map: Optional custom mapping of variable names to LaTeX symbols

    Returns:
        LaTeX string
    """
    combined_map = SYMBOL_LATEX_MAP.copy()
    if symbol_map:
        combined_map.update(symbol_map)

    return _ast_to_latex(ast, combined_map)


def _substitute_symbols(expr, symbol_map: Dict[str, str]):
    """
    Substitute symbols in SymPy expression with LaTeX-friendly versions.

    Creates new Symbol objects with LaTeX names for display.
    """
    # Get all symbols in the expression
    symbols = expr.free_symbols

    substitutions = {}
    for sym in symbols:
        name = str(sym)
        if name in symbol_map:
            # Create a new symbol with the LaTeX name
            # Using Symbol with latex representation
            latex_name = symbol_map[name]
            # Clean up the latex name for Symbol creation
            # SymPy will use this name directly
            new_sym = Symbol(latex_name)
            substitutions[sym] = new_sym

    if substitutions:
        return expr.subs(substitutions)
    return expr


def _ast_to_latex(node: Dict[str, Any], symbol_map: Dict[str, str]) -> str:
    """Recursively convert AST to LaTeX string."""
    node_type = node.get("type")

    # Constant
    if node_type == "const":
        value = node["value"]
        # Check for named constants
        name = node.get("name")
        if name == "pi":
            return r"\pi"
        if name == "e":
            return r"e"
        # Format numbers nicely
        if value == int(value):
            return str(int(value))
        return f"{value:.6g}"

    # Input variable
    if node_type == "input":
        name = node["name"]
        latex_name = symbol_map.get(name, name)
        # Wrap in text if it looks like a multi-letter variable without LaTeX
        if len(latex_name) > 1 and not latex_name.startswith('\\'):
            # Check if it has subscript notation
            if '_' in latex_name:
                parts = latex_name.split('_', 1)
                return f"{parts[0]}_{{{parts[1]}}}"
            return latex_name
        return latex_name

    # Addition
    if node_type == "add":
        operands = node.get("operands", [])
        terms = [_ast_to_latex(op, symbol_map) for op in operands]
        return " + ".join(terms)

    # Multiplication
    if node_type == "mul":
        operands = node.get("operands", [])
        terms = []
        for op in operands:
            term = _ast_to_latex(op, symbol_map)
            # Wrap additions in parentheses
            if op.get("type") == "add":
                term = f"\\left({term}\\right)"
            terms.append(term)
        return r" \cdot ".join(terms)

    # Division
    if node_type == "div":
        num = _ast_to_latex(node["numerator"], symbol_map)
        den = _ast_to_latex(node["denominator"], symbol_map)
        return f"\\frac{{{num}}}{{{den}}}"

    # Power
    if node_type == "pow":
        base = _ast_to_latex(node["base"], symbol_map)
        exp_node = node["exponent"]
        exp_latex = _ast_to_latex(exp_node, symbol_map)

        # Wrap complex bases in parentheses
        base_type = node["base"].get("type")
        if base_type in ("add", "mul", "div"):
            base = f"\\left({base}\\right)"

        return f"{base}^{{{exp_latex}}}"

    # Negation
    if node_type == "neg":
        operand = _ast_to_latex(node["operand"], symbol_map)
        op_type = node["operand"].get("type")
        if op_type in ("add", "mul"):
            return f"-\\left({operand}\\right)"
        return f"-{operand}"

    # Functions
    if node_type == "func":
        func_name = node["name"]
        arg = _ast_to_latex(node["arg"], symbol_map)

        if func_name == "sqrt":
            return f"\\sqrt{{{arg}}}"
        if func_name == "exp":
            return f"e^{{{arg}}}"
        if func_name == "ln":
            return f"\\ln\\left({arg}\\right)"
        if func_name == "log":
            return f"\\log\\left({arg}\\right)"
        if func_name == "sin":
            return f"\\sin\\left({arg}\\right)"
        if func_name == "cos":
            return f"\\cos\\left({arg}\\right)"
        if func_name == "tan":
            return f"\\tan\\left({arg}\\right)"
        if func_name == "abs":
            return f"\\left|{arg}\\right|"

        # Generic function
        return f"\\{func_name}\\left({arg}\\right)"

    return str(node)


def format_equation_display(
    equation_text: str,
    result_value: Optional[float] = None,
    result_unit: Optional[str] = None
) -> str:
    """
    Format a complete equation display with optional result.

    Args:
        equation_text: The original equation text
        result_value: Optional computed result
        result_unit: Optional unit for the result

    Returns:
        LaTeX string showing equation and result
    """
    from .parser import parse_equation

    try:
        parsed = parse_equation(equation_text)
        eq_latex = generate_latex(parsed)

        if result_value is not None:
            # Format result
            if abs(result_value) < 0.001 or abs(result_value) > 10000:
                result_str = f"{result_value:.4e}"
            else:
                result_str = f"{result_value:.6g}"

            if result_unit:
                return f"{eq_latex} = {result_str} \\; \\text{{{result_unit}}}"
            return f"{eq_latex} = {result_str}"

        return eq_latex

    except Exception as e:
        # Return original text wrapped in text mode if parsing fails
        return f"\\text{{{equation_text}}}"
