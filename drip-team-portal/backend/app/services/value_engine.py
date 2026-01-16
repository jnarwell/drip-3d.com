"""
Value Engine - Expression Parsing and Evaluation with Unit Propagation

Handles:
- Expression parsing (using SymPy)
- Expression evaluation with unit tracking
- Dependency graph management
- Stale detection and recalculation
- Circular dependency prevention

Reference syntax: #entity.property
Examples:
  - #cmp001.thermal_conductivity
  - #steel.density
  - #table1.lookup(temp=100)

================================================================================
ValueNode Expression Storage Format
================================================================================

ValueNodes with node_type=EXPRESSION store parsed expressions in the
`parsed_expression` JSON field. This enables fast re-evaluation without
re-parsing.

Property References (#refs)
---------------------------
References to component/material properties are extracted and stored as
placeholders:

    Expression: "#PART.length + #MAT.density * 2"

    parsed_expression = {
        "original": "#PART.length + #MAT.density * 2",
        "modified": "__ref_0__ + __ref_1__ * 2",
        "placeholders": {
            "__ref_0__": "PART.length",
            "__ref_1__": "MAT.density"
        },
        "references": ["PART.length", "MAT.density"],
        "valid": True
    }

LOOKUP() Function Calls
-----------------------
Table lookups are extracted and stored separately for evaluation:

    Expression: "LOOKUP(\"steam\", \"h\", T=373)"

    parsed_expression = {
        "original": "LOOKUP(\"steam\", \"h\", T=373)",
        "modified": "__lookup_0__",
        "lookup_calls": {
            "__lookup_0__": {
                "table_code": "steam",
                "output_column": "h",
                "key_column": "T",
                "key_value_expr": "373"
            }
        },
        "valid": True
    }

MODEL() Function Calls
----------------------
Physics model evaluations are extracted similarly to LOOKUP():

    Expression: "#PART.length + MODEL(\"Thermal Expansion\", CTE: 2.3e-5, delta_T: 100, L0: 1m)"

    parsed_expression = {
        "original": "#PART.length + MODEL(\"Thermal Expansion\", CTE: 2.3e-5, delta_T: 100, L0: 1m)",
        "modified": "__ref_0__ + __model_0__",
        "placeholders": {
            "__ref_0__": "PART.length"
        },
        "model_calls": {
            "__model_0__": {
                "model_name": "Thermal Expansion",
                "bindings": {
                    "CTE": "2.3e-5",
                    "delta_T": "100",
                    "L0": "1m"
                },
                "output_name": null
            }
        },
        "valid": True
    }

MODEL() bindings can contain:
- Literal numbers: "100", "2.3e-5"
- Literals with units: "1m", "25°C", "100Pa"
- Property references: "#MAT.cte"
- Expressions: "#PART.temp - 273.15"
- Nested LOOKUP(): "LOOKUP(\"steam\", \"h\", T=373)"

Multi-output models use the output parameter:

    MODEL("Rectangle", length: 5, width: 3, output: "area")

    model_calls = {
        "__model_0__": {
            "model_name": "Rectangle",
            "bindings": {"length": "5", "width": "3"},
            "output_name": "area"
        }
    }

Evaluation Flow
---------------
1. Parse expression → extract #refs, LOOKUP(), MODEL() calls
2. Create ValueNode with parsed_expression JSON
3. Create ValueDependency records for #ref sources
4. When computing:
   a. Resolve #refs to float values
   b. Evaluate LOOKUP() calls using table lookup service
   c. Evaluate MODEL() calls using evaluate_inline_model()
   d. Substitute all placeholders with values
   e. Evaluate final expression with SymPy
   f. Store result in computed_value
5. Mark dependents stale when sources change

================================================================================
"""

from typing import Optional, List, Dict, Any, Set, Tuple
from sqlalchemy.orm import Session
from datetime import datetime
import re
import logging
import sympy
from sympy import sympify, Symbol, sqrt, sin, cos, tan, log, exp, pi, E
from sympy.core.numbers import Float as SympyFloat

from app.models.values import ValueNode, ValueDependency, NodeType, ComputationStatus
from app.models.units import Unit
from app.models.component import Component
from app.models.material import Material, MaterialProperty
from app.models.property import ComponentProperty, PropertyDefinition
from app.services.unit_engine import UnitEngine
from app.services.dimensional_analysis import (
    Dimension, DimensionError, DIMENSIONLESS, UNIT_DIMENSIONS,
    get_unit_dimension, dimension_to_si_unit, dimension_to_string
)

logger = logging.getLogger(__name__)

# Regex for variable references: #entity.property
# Entity codes can start with numbers (e.g., 304_STAINLESS_STEEL_001)
# Property names use underscores for spaces (e.g., Yield_Strength matches "Yield Strength")
REFERENCE_PATTERN = re.compile(r'#([a-zA-Z0-9][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)?)')

# Regex for literal values with units: 12mm, 5 m, 100Pa, 3.14 kg, etc.
# Captures: number (with optional decimal), optional space, unit symbol
LITERAL_WITH_UNIT_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9_])(-?\d+\.?\d*)\s*'  # Number (negative allowed)
    r'(nm|μm|mm|cm|m|km|in|ft|'  # Length (metric + imperial)
    r'mm²|cm²|m²|km²|ha|in²|ft²|'  # Area
    r'mm³|cm³|mL|L|m³|in³|ft³|gal|'  # Volume
    r'μg|mg|g|kg|t|oz|lb|'  # Mass
    r'μN|mN|N|kN|MN|lbf|'  # Force
    r'Pa|kPa|MPa|GPa|bar|mbar|psi|ksi|'  # Pressure
    r'K|kelvin|°C|℃|degC|celsius|°F|℉|degF|fahrenheit|°R|rankine|'  # Temperature (with aliases)
    r'ps|ns|μs|ms|s|min|h|d|yr|'  # Time
    r'Hz|kHz|MHz|GHz|'  # Frequency
    r'J|kJ|MJ|Wh|kWh|BTU|'  # Energy
    r'W|mW|kW|MW|hp|'  # Power
    r'N·m|kN·m|lbf·ft|'  # Torque
    r'A|mA|μA|V|mV|kV|Ω|kΩ|MΩ|'  # Electrical
    r'rad|mrad|deg|°|'  # Angle
    r'm/s|km/h|ft/s|mph|'  # Velocity
    r'm/s²|'  # Acceleration
    r'kg/m³|g/cm³|lb/ft³'  # Density
    r')(?![a-zA-Z0-9_])',  # Negative lookahead to avoid partial matches
    re.UNICODE
)

# Regex for bare numeric literals (numbers without units)
# Used to identify literals that need user-preferred unit conversion
# Matches integers and decimals, negative numbers, scientific notation
# Excludes numbers already captured by LITERAL_WITH_UNIT_PATTERN (has unit suffix)
BARE_LITERAL_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9_\.])(-?\d+\.?\d*(?:[eE][+-]?\d+)?)(?![a-zA-Z0-9_\.])',
    re.UNICODE
)

# Regex for LOOKUP function calls
# LOOKUP("TableCode", "Column", KeyColumn=value)
# LOOKUP("STEAM", "Pressure", Temperature=150)
# LOOKUP("STEAM", "Pressure", Temperature=#PART.temp)
LOOKUP_PATTERN = re.compile(
    r'LOOKUP\s*\(\s*"([^"]+)"\s*,\s*"([^"]+)"\s*,\s*([a-zA-Z][a-zA-Z0-9_]*)\s*=\s*([^)]+)\s*\)',
    re.UNICODE
)

# Regex for MODEL function calls - simple pattern to find MODEL( start
# Full extraction done by _extract_model_calls() with proper paren matching
MODEL_START_PATTERN = re.compile(r'MODEL\s*\(', re.UNICODE)


def _extract_model_calls(expr: str) -> List[Dict[str, Any]]:
    """
    Extract MODEL() calls from expression with proper parenthesis matching.

    Handles nested MODEL() and LOOKUP() calls in bindings:
        MODEL("A", x: MODEL("B", y: 1))  -> extracts both correctly

    Works inside-out: extracts innermost MODEL() calls first so nested
    calls are replaced before outer calls are processed.

    Args:
        expr: Expression string containing MODEL() calls

    Returns:
        List of dicts with 'full_match', 'model_name', 'params_str', 'start', 'end'
        Ordered from innermost to outermost for proper replacement.
    """
    results = []
    working_expr = expr

    # Keep extracting until no more MODEL() calls found
    while True:
        # Find MODEL( start positions
        match = MODEL_START_PATTERN.search(working_expr)
        if not match:
            break

        start_idx = match.start()
        paren_start = match.end() - 1  # Position of opening (

        # Find matching closing paren with proper nesting
        depth = 1
        pos = paren_start + 1
        in_string = False
        string_char = None

        while pos < len(working_expr) and depth > 0:
            char = working_expr[pos]

            # Handle string literals
            if char in ('"', "'") and not in_string:
                in_string = True
                string_char = char
            elif char == string_char and in_string:
                # Check for escaped quote
                if pos > 0 and working_expr[pos-1] != '\\':
                    in_string = False
                    string_char = None
            elif not in_string:
                if char == '(':
                    depth += 1
                elif char == ')':
                    depth -= 1
            pos += 1

        if depth != 0:
            # Unbalanced parentheses - skip this match
            # Replace just "MODEL" to prevent infinite loop
            working_expr = working_expr[:start_idx] + "_MODEL_" + working_expr[start_idx+5:]
            continue

        end_idx = pos
        full_match = working_expr[start_idx:end_idx]

        # Extract model name and params from the matched string
        # Format: MODEL("name", params...) or MODEL("name")
        inner = full_match[full_match.index('(')+1:-1].strip()  # Content inside parens

        # Find the model name (first quoted string)
        name_match = re.match(r'\s*"([^"]+)"', inner)
        if not name_match:
            # Invalid format - skip
            working_expr = working_expr[:start_idx] + "_MODEL_" + working_expr[start_idx+5:]
            continue

        model_name = name_match.group(1)
        params_str = inner[name_match.end():].strip()

        # Remove leading comma from params if present
        if params_str.startswith(','):
            params_str = params_str[1:].strip()

        results.append({
            'full_match': full_match,
            'model_name': model_name,
            'params_str': params_str,
            'start': start_idx,
            'end': end_idx,
        })

        # Replace this MODEL() with a placeholder to find outer ones
        placeholder = f"__MODEL_EXTRACTED_{len(results)-1}__"
        working_expr = working_expr[:start_idx] + placeholder + working_expr[end_idx:]

    return results


def _split_model_params(params_str: str) -> list:
    """
    Split MODEL() parameter string by commas, respecting nested parentheses.

    Handles cases like: a: 1, b: MODEL("X", c: 2), d: 3
    Don't split on commas inside nested MODEL() or LOOKUP() calls.

    Args:
        params_str: Parameter string like "CTE: 2.3e-5, delta_T: 100, output: \"delta_L\""

    Returns:
        List of parameter strings like ["CTE: 2.3e-5", "delta_T: 100", "output: \"delta_L\""]
    """
    if not params_str:
        return []

    params = []
    current = ""
    depth = 0
    in_string = False
    string_char = None

    for char in params_str:
        if char in ('"', "'") and not in_string:
            in_string = True
            string_char = char
        elif char == string_char and in_string:
            in_string = False
            string_char = None
        elif char == '(' and not in_string:
            depth += 1
        elif char == ')' and not in_string:
            depth -= 1
        elif char == ',' and depth == 0 and not in_string:
            if current.strip():
                params.append(current.strip())
            current = ""
            continue
        current += char

    if current.strip():
        params.append(current.strip())

    return params


def _parse_model_binding(binding_str: str) -> tuple:
    """
    Parse a single MODEL() binding like "CTE: 2.3e-5" or "output: \"delta_L\"".

    Args:
        binding_str: String like "CTE: 2.3e-5" or "output: \"delta_L\""

    Returns:
        Tuple of (key, value) where value is the raw string expression
    """
    # Find the first colon (key: value separator)
    colon_idx = binding_str.find(':')
    if colon_idx == -1:
        raise ValueError(f"Invalid MODEL() binding (missing ':'): {binding_str}")

    key = binding_str[:colon_idx].strip()
    value = binding_str[colon_idx + 1:].strip()

    return (key, value)


class ExpressionError(Exception):
    """Error during expression parsing or evaluation."""
    pass


class CircularDependencyError(Exception):
    """Circular dependency detected in value graph."""
    pass


class ValueEngine:
    """
    Core engine for managing the value system.

    Provides:
    - Expression parsing and validation
    - Value computation with unit propagation
    - Dependency tracking
    - Cascade updates when values change
    """

    def __init__(self, db: Session, user_id: Optional[int] = None):
        self.db = db
        self.user_id = user_id
        self.unit_engine = UnitEngine(db)
        self._evaluation_stack: Set[int] = set()  # For circular dependency detection
        self._user_unit_prefs: Optional[Dict[str, str]] = None  # Cache for user preferences

    def _get_user_unit_preference(self, dimension: str) -> Optional[str]:
        """
        Get user's preferred unit symbol for a given dimension.

        Returns the unit symbol (e.g., 'mm') or None if no preference set.
        """
        if not self.user_id:
            return None

        # Lazy load and cache preferences
        if self._user_unit_prefs is None:
            self._user_unit_prefs = {}
            from app.models.user_preferences import UserUnitPreference
            prefs = self.db.query(UserUnitPreference).filter(
                UserUnitPreference.user_id == self.user_id
            ).all()
            for pref in prefs:
                unit = self.db.query(Unit).filter(Unit.id == pref.preferred_unit_id).first()
                if unit:
                    self._user_unit_prefs[pref.quantity_type] = unit.symbol

        return self._user_unit_prefs.get(dimension)

    # ==================== TABLE LOOKUP ====================

    def lookup_table(
        self,
        table_code: str,
        output_column: str,
        key_column: str,
        key_value: Any
    ) -> Tuple[Optional[float], bool, Optional[str]]:
        """
        Look up a value using the Engineering Properties API.

        Args:
            table_code: The source ID (e.g., "steam", "wire_gauge_awg")
            output_column: The output property name (e.g., "h", "diameter")
            key_column: The input name (e.g., "T", "gauge")
            key_value: The value to look up (number or string for discrete inputs)

        Returns:
            (value, interpolated, error_message)
        """
        try:
            from app.services.properties.router import lookup

            # Perform the lookup
            inputs = {key_column: key_value}
            result = lookup(table_code, output_column, **inputs)

            # The new API always returns interpolated values for continuous inputs
            return (result, True, None)

        except Exception as e:
            logger.error(f"LOOKUP error for {table_code}.{output_column}: {e}")
            return (None, False, str(e))

    # ==================== VALUE CREATION ====================

    def create_literal(
        self,
        value: float,
        unit_id: Optional[int] = None,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ValueNode:
        """Create a literal value node."""
        node = ValueNode(
            node_type=NodeType.LITERAL,
            numeric_value=value,
            unit_id=unit_id,
            computed_value=value,
            computed_unit_id=unit_id,
            computation_status=ComputationStatus.VALID,
            description=description,
            created_by=created_by,
            last_computed=datetime.utcnow()
        )
        self.db.add(node)
        self.db.flush()
        return node

    def create_expression(
        self,
        expression: str,
        description: Optional[str] = None,
        created_by: Optional[str] = None,
        resolve_references: bool = True
    ) -> ValueNode:
        """
        Create an expression value node.

        Args:
            expression: The expression string (e.g., "sqrt(#cmp001.length * 2)")
            description: Optional description
            created_by: User who created this
            resolve_references: If True, resolve and link dependencies

        Returns:
            The created ValueNode
        """
        # Parse and validate the expression
        parsed = self._parse_expression(expression)

        node = ValueNode(
            node_type=NodeType.EXPRESSION,
            expression_string=expression,
            parsed_expression=parsed,
            computation_status=ComputationStatus.PENDING,
            description=description,
            created_by=created_by
        )
        self.db.add(node)
        self.db.flush()

        # Extract and link dependencies
        if resolve_references:
            references = self._extract_references(expression)
            for ref in references:
                # Look up the referenced value node
                source_node = self._resolve_reference(ref)
                if source_node:
                    dep = ValueDependency(
                        dependent_id=node.id,
                        source_id=source_node.id,
                        variable_name=ref
                    )
                    self.db.add(dep)

        self.db.flush()
        return node

    def create_reference(
        self,
        reference_node_id: int,
        description: Optional[str] = None,
        created_by: Optional[str] = None
    ) -> ValueNode:
        """Create a reference value node that points to another node."""
        node = ValueNode(
            node_type=NodeType.REFERENCE,
            reference_node_id=reference_node_id,
            computation_status=ComputationStatus.PENDING,
            description=description,
            created_by=created_by
        )
        self.db.add(node)
        self.db.flush()

        # Create dependency
        dep = ValueDependency(
            dependent_id=node.id,
            source_id=reference_node_id,
            variable_name=f"ref_{reference_node_id}"
        )
        self.db.add(dep)
        self.db.flush()

        return node

    # ==================== EXPRESSION PARSING ====================

    # Import unit constants from centralized source (single source of truth)
    from app.services.unit_constants import (
        DIMENSION_SI_UNITS as _DIMENSION_SI_UNITS,
        UNIT_TO_DIMENSION as _UNIT_TO_DIMENSION,
        UNIT_TO_SI as _UNIT_TO_SI,
    )
    DIMENSION_SI_UNITS = _DIMENSION_SI_UNITS
    UNIT_TO_DIMENSION = _UNIT_TO_DIMENSION
    UNIT_TO_SI = _UNIT_TO_SI

    def _parse_expression(self, expression: str) -> Dict[str, Any]:
        """
        Parse an expression string into an AST-like structure.

        Supports:
        - Basic math: +, -, *, /, ^, **
        - Functions: sqrt, sin, cos, tan, log, exp, abs
        - Constants: pi, e
        - References: #entity.property
        - Literal values with units: 12mm, 5 m, 100Pa

        Returns a dict with parsing results.
        """
        # Replace references with placeholder symbols
        placeholders = {}
        ref_units = {}  # Store unit symbols for each reference
        literal_values = {}  # Store converted literal values
        refs = self._extract_references(expression)

        modified_expr = expression

        # Preprocess: Convert ^ to ** for exponentiation
        # Engineers commonly use ^ for powers instead of Python's **
        # Must be done early before any other processing
        modified_expr = re.sub(r'\^', '**', modified_expr)

        for i, ref in enumerate(refs):
            placeholder = f"__ref_{i}__"
            placeholders[placeholder] = ref
            # Look up and store the unit for this reference
            unit_symbol = self._get_reference_unit(ref)
            if unit_symbol:
                ref_units[placeholder] = unit_symbol
            # Replace #ref with placeholder (handle the # prefix)
            modified_expr = modified_expr.replace(f"#{ref}", placeholder)

        # Process LOOKUP() function calls
        # LOOKUP("TableCode", "Column", KeyColumn=value)
        lookup_calls = {}
        lookup_matches = LOOKUP_PATTERN.findall(modified_expr)
        for m, (table_code, output_col, key_col, key_val) in enumerate(lookup_matches):
            original_call = f'LOOKUP("{table_code}", "{output_col}", {key_col}={key_val})'
            placeholder = f"__lookup_{m}__"
            lookup_calls[placeholder] = {
                'original': original_call,
                'table_code': table_code,
                'output_column': output_col,
                'key_column': key_col,
                'key_value_expr': key_val.strip(),  # May be a reference like #PART.temp or a literal
            }
            modified_expr = modified_expr.replace(original_call, placeholder, 1)

        # Process MODEL() function calls with proper parenthesis matching
        # MODEL("Model Name", input1: value1, input2: #REF.prop, output: "output_name")
        # Handles nested MODEL() calls: MODEL("A", x: MODEL("B", y: 1))
        model_calls = {}
        extracted_models = _extract_model_calls(modified_expr)

        # Process in order (innermost first due to extraction algorithm)
        for model_info in extracted_models:
            model_name = model_info['model_name']
            params_str = model_info['params_str']

            # Parse parameters: key: value pairs
            bindings = {}
            output_name = None

            for param in _split_model_params(params_str):
                try:
                    key, value = _parse_model_binding(param)
                    if key == 'output':
                        # Remove quotes from output name
                        output_name = value.strip('"\'')
                    else:
                        bindings[key] = value
                except ValueError as e:
                    logger.warning(f"Skipping invalid MODEL() param: {e}")
                    continue

            placeholder = f"__model_{len(model_calls)}__"
            model_calls[placeholder] = {
                'original': model_info['full_match'],
                'model_name': model_name,
                'bindings': bindings,
                'output_name': output_name
            }

            # Replace MODEL() with placeholder symbol
            modified_expr = modified_expr.replace(model_info['full_match'], placeholder, 1)

        # Replace literal values with units (e.g., 12mm -> converted SI value)
        literal_matches = LITERAL_WITH_UNIT_PATTERN.findall(modified_expr)
        for j, (value_str, unit) in enumerate(literal_matches):
            original_text = f"{value_str}{unit}"
            # Also handle with space
            original_with_space = f"{value_str} {unit}"

            numeric_value = float(value_str)
            # Convert to SI base unit
            conversion_factor = self.UNIT_TO_SI.get(unit, 1)
            si_value = numeric_value * conversion_factor

            placeholder = f"__lit_{j}__"
            literal_values[placeholder] = {
                'original': original_text,
                'value': numeric_value,
                'unit': unit,
                'si_value': si_value
            }

            # Replace in expression (try both with and without space)
            if original_with_space in modified_expr:
                modified_expr = modified_expr.replace(original_with_space, placeholder, 1)
            else:
                modified_expr = modified_expr.replace(original_text, placeholder, 1)

        # Capture bare numeric literals (numbers without units)
        # These need to be converted using user's preferred unit for the expression's dimension
        bare_literals = {}
        # Find bare literals in the modified expression (after unit literals are replaced)
        bare_matches = BARE_LITERAL_PATTERN.findall(modified_expr)
        for k, value_str in enumerate(bare_matches):
            # Skip if this is a placeholder reference (starts with __)
            if '__' in str(value_str):
                continue
            try:
                numeric_value = float(value_str)
                placeholder = f"__bare_{k}__"
                bare_literals[placeholder] = {
                    'original': value_str,
                    'value': numeric_value,
                }
                # Replace in expression
                # Use word boundary replacement to avoid partial matches
                modified_expr = re.sub(
                    rf'(?<![a-zA-Z0-9_\.]){re.escape(value_str)}(?![a-zA-Z0-9_\.])',
                    placeholder,
                    modified_expr,
                    count=1
                )
            except ValueError:
                continue

        # Try to parse with SymPy
        try:
            # Define allowed functions and constants
            local_dict = {
                'sqrt': sqrt,
                'sin': sin,
                'cos': cos,
                'tan': tan,
                'log': log,
                'ln': log,
                'exp': exp,
                'abs': sympy.Abs,
                'pi': pi,
                'e': E,
            }

            # Add placeholders as symbols
            for p in placeholders:
                local_dict[p] = Symbol(p)
            for p in literal_values:
                local_dict[p] = Symbol(p)
            for p in bare_literals:
                local_dict[p] = Symbol(p)
            for p in lookup_calls:
                local_dict[p] = Symbol(p)
            for p in model_calls:
                local_dict[p] = Symbol(p)

            parsed = sympify(modified_expr, locals=local_dict)

            return {
                "original": expression,
                "modified": modified_expr,
                "placeholders": placeholders,
                "ref_units": ref_units,  # Unit symbols for each reference placeholder
                "literal_values": literal_values,
                "bare_literals": bare_literals,  # Unitless numbers that need user unit conversion
                "lookup_calls": lookup_calls,  # LOOKUP() function calls
                "model_calls": model_calls,  # MODEL() function calls
                "sympy_repr": str(parsed),
                "references": refs,
                "valid": True
            }

        except Exception as e:
            logger.error(f"Failed to parse expression '{expression}': {e}")
            raise ExpressionError(f"Invalid expression: {e}")

    def _extract_references(self, expression: str) -> List[str]:
        """Extract all variable references from an expression."""
        matches = REFERENCE_PATTERN.findall(expression)
        return list(set(matches))  # Remove duplicates

    def _get_reference_unit(self, ref: str) -> Optional[str]:
        """
        Get the unit symbol for a reference.

        Returns the unit symbol (e.g., 'mm', 'Pa') or None if not found.
        """
        parts = ref.split(".")
        if len(parts) != 2:
            logger.debug(f"_get_reference_unit: Invalid ref format '{ref}' (expected CODE.property)")
            return None

        entity_code, prop_name = parts
        # Normalize property name: underscores → spaces (Yield_Strength → "Yield Strength")
        prop_name_normalized = prop_name.replace('_', ' ')

        # Try Component
        component = self.db.query(Component).filter(Component.code == entity_code).first()
        if not component:
            from sqlalchemy import func
            generated_code_expr = func.trim(
                func.regexp_replace(
                    func.regexp_replace(func.upper(Component.name), '[^a-zA-Z0-9]', '_', 'g'),
                    '_+', '_', 'g'
                ), '_'
            )
            component = self.db.query(Component).filter(generated_code_expr == entity_code).first()

        if component:
            # Try exact match first
            prop_def = self.db.query(PropertyDefinition).filter(PropertyDefinition.name == prop_name_normalized).first()
            if not prop_def:
                # Try case-insensitive match
                from sqlalchemy import func
                prop_def = self.db.query(PropertyDefinition).filter(
                    func.lower(PropertyDefinition.name) == prop_name_normalized.lower()
                ).first()
            if prop_def:
                logger.debug(f"_get_reference_unit: Found unit '{prop_def.unit}' for {ref}")
                return prop_def.unit
            else:
                logger.debug(f"_get_reference_unit: Component {entity_code} found but property '{prop_name_normalized}' not found")

        # Try Material
        material = self.db.query(Material).filter(Material.code == entity_code).first()
        if not material:
            from sqlalchemy import func
            generated_code_expr = func.trim(
                func.regexp_replace(
                    func.regexp_replace(func.upper(Material.name), '[^a-zA-Z0-9]', '_', 'g'),
                    '_+', '_', 'g'
                ), '_'
            )
            material = self.db.query(Material).filter(generated_code_expr == entity_code).first()

        if material:
            # Try exact match first
            prop_def = self.db.query(PropertyDefinition).filter(PropertyDefinition.name == prop_name_normalized).first()
            if not prop_def:
                # Try case-insensitive match
                from sqlalchemy import func
                prop_def = self.db.query(PropertyDefinition).filter(
                    func.lower(PropertyDefinition.name) == prop_name_normalized.lower()
                ).first()
            if prop_def:
                logger.debug(f"_get_reference_unit: Found unit '{prop_def.unit}' for {ref}")
                return prop_def.unit
            else:
                logger.debug(f"_get_reference_unit: Material {entity_code} found but property '{prop_name_normalized}' not found")

        logger.debug(f"_get_reference_unit: Could not find entity or property for {ref}")
        return None

    def _resolve_reference(self, ref: str) -> Optional[ValueNode]:
        """
        Resolve a reference string to a ValueNode.

        Reference formats:
        - "HEATBED_001.thermal_conductivity" -> Component property (by code)
        - "SS304_001.density" -> Material property (by code)
        - "FRAME.Height" -> Component by generated code from name

        Resolution order:
        1. Try Component by code
        2. Try Component by generated code from name
        3. Try Material by code
        4. Try Material by generated code from name
        5. Fallback: Try by description (legacy)

        Returns the ValueNode or None if not found.
        """
        parts = ref.split(".")
        if len(parts) != 2:
            logger.warning(f"Invalid reference format: {ref} (expected CODE.property)")
            return None

        entity_code, prop_name = parts
        # Normalize property name: underscores → spaces (Yield_Strength → "Yield Strength")
        prop_name_normalized = prop_name.replace('_', ' ')

        # Try to find Component by code
        component = self.db.query(Component).filter(
            Component.code == entity_code
        ).first()

        # If not found by code, try by generated code from name using SQL
        if not component:
            from sqlalchemy import func
            # PostgreSQL: TRIM(BOTH '_' FROM REGEXP_REPLACE(REGEXP_REPLACE(UPPER(name), '[^a-zA-Z0-9]', '_', 'g'), '_+', '_', 'g'))
            generated_code_expr = func.trim(
                func.regexp_replace(
                    func.regexp_replace(
                        func.upper(Component.name),
                        '[^a-zA-Z0-9]', '_', 'g'
                    ),
                    '_+', '_', 'g'
                ),
                '_'
            )
            component = self.db.query(Component).filter(
                generated_code_expr == entity_code
            ).first()

        if component:
            # Find the property definition (use normalized name with spaces)
            prop_def = self.db.query(PropertyDefinition).filter(
                PropertyDefinition.name == prop_name_normalized
            ).first()

            if prop_def:
                # Find the ComponentProperty linking them
                comp_prop = self.db.query(ComponentProperty).filter(
                    ComponentProperty.component_id == component.id,
                    ComponentProperty.property_definition_id == prop_def.id
                ).first()

                if comp_prop:
                    if comp_prop.value_node_id:
                        node = self.db.query(ValueNode).filter(
                            ValueNode.id == comp_prop.value_node_id
                        ).first()
                        return node
                    else:
                        # Property exists but has no value_node - create one from the literal value
                        literal_value = comp_prop.single_value or comp_prop.average_value or comp_prop.min_value
                        if literal_value is not None:
                            # Convert from property unit to SI base unit
                            prop_unit = prop_def.unit if prop_def else None
                            si_value = literal_value
                            si_unit_symbol = None

                            if prop_unit and prop_unit in self.UNIT_TO_SI:
                                conversion_factor = self.UNIT_TO_SI[prop_unit]
                                si_value = literal_value * conversion_factor
                                # Get the SI base unit for this dimension
                                dimension = self.UNIT_TO_DIMENSION.get(prop_unit)
                                if dimension:
                                    si_unit_symbol = self.DIMENSION_SI_UNITS.get(dimension)

                            # Create a new literal ValueNode for this property (in SI units)
                            new_node = ValueNode(
                                node_type=NodeType.LITERAL,
                                numeric_value=si_value,
                                computed_value=si_value,
                                computed_unit_symbol=si_unit_symbol,
                                computation_status=ComputationStatus.VALID,
                                description=f"{entity_code}.{prop_name}"
                            )
                            self.db.add(new_node)
                            self.db.flush()
                            # Link it back to the ComponentProperty
                            comp_prop.value_node_id = new_node.id
                            self.db.flush()
                            return new_node

            logger.warning(f"Component {entity_code} found but property '{prop_name_normalized}' not found or has no value_node")

        # Try to find Material by code
        material = self.db.query(Material).filter(
            Material.code == entity_code
        ).first()

        # If not found by code, try by generated code from name using SQL
        if not material:
            from sqlalchemy import func
            generated_code_expr = func.trim(
                func.regexp_replace(
                    func.regexp_replace(
                        func.upper(Material.name),
                        '[^a-zA-Z0-9]', '_', 'g'
                    ),
                    '_+', '_', 'g'
                ),
                '_'
            )
            material = self.db.query(Material).filter(
                generated_code_expr == entity_code
            ).first()

        if material:
            # Find the property definition (use normalized name with spaces)
            prop_def = self.db.query(PropertyDefinition).filter(
                PropertyDefinition.name == prop_name_normalized
            ).first()

            if prop_def:
                # Find the MaterialProperty linking them
                mat_prop = self.db.query(MaterialProperty).filter(
                    MaterialProperty.material_id == material.id,
                    MaterialProperty.property_definition_id == prop_def.id
                ).first()

                if mat_prop:
                    if mat_prop.value_node_id:
                        return self.db.query(ValueNode).filter(
                            ValueNode.id == mat_prop.value_node_id
                        ).first()
                    else:
                        # Property exists but has no value_node - create one from the legacy value
                        literal_value = mat_prop.value or mat_prop.value_min
                        if literal_value is not None:
                            # Convert from property unit to SI base unit
                            prop_unit = prop_def.unit if prop_def else None
                            si_value = literal_value
                            si_unit_symbol = None

                            if prop_unit and prop_unit in self.UNIT_TO_SI:
                                conversion_factor = self.UNIT_TO_SI[prop_unit]
                                si_value = literal_value * conversion_factor
                                # Get the SI base unit for this dimension
                                dimension = self.UNIT_TO_DIMENSION.get(prop_unit)
                                if dimension:
                                    si_unit_symbol = self.DIMENSION_SI_UNITS.get(dimension)
                                logger.info(f"Converting material property: {literal_value} {prop_unit} -> {si_value} {si_unit_symbol}")
                            else:
                                logger.info(f"Creating literal ValueNode for material property with value={literal_value} (no unit conversion)")

                            # Create a new literal ValueNode for this property (in SI units)
                            new_node = ValueNode(
                                node_type=NodeType.LITERAL,
                                numeric_value=si_value,
                                computed_value=si_value,
                                computed_unit_symbol=si_unit_symbol,
                                computation_status=ComputationStatus.VALID,
                                description=f"{entity_code}.{prop_name}"
                            )
                            self.db.add(new_node)
                            self.db.flush()
                            # Link it back to the MaterialProperty
                            mat_prop.value_node_id = new_node.id
                            self.db.flush()
                            return new_node

            logger.debug(f"Material {entity_code} found but property '{prop_name_normalized}' not found or has no value")

        # Fallback: Try to find by description (legacy/direct value node reference)
        node = self.db.query(ValueNode).filter(
            ValueNode.description == ref
        ).first()

        if node:
            return node

        logger.warning(f"Could not resolve reference: {ref}")
        return None

    # ==================== EXPRESSION EVALUATION ====================

    def compute_value(
        self,
        node: ValueNode,
        expected_unit: Optional[str] = None
    ) -> Tuple[float, Optional[int], bool, Optional[str], Optional[str]]:
        """
        Compute the value of a node.

        Args:
            node: The ValueNode to compute
            expected_unit: Optional unit symbol from PropertyDefinition for validation

        Returns: (value, unit_id, success, error_message, si_unit_symbol)
        """
        # Circular dependency check
        if node.id in self._evaluation_stack:
            node.computation_status = ComputationStatus.CIRCULAR
            node.computation_error = "Circular dependency detected"
            return (None, None, False, "Circular dependency detected", None)

        self._evaluation_stack.add(node.id)

        try:
            if node.node_type == NodeType.LITERAL:
                return (node.numeric_value, node.unit_id, True, None, None)

            elif node.node_type == NodeType.REFERENCE:
                if not node.reference_node:
                    return (None, None, False, "Referenced node not found", None)
                ref_value, ref_unit, success, error, si_unit = self.compute_value(node.reference_node, expected_unit)
                return (ref_value, ref_unit, success, error, si_unit)

            elif node.node_type == NodeType.EXPRESSION:
                return self._evaluate_expression(node, expected_unit)

            else:
                return (None, None, False, f"Unknown node type: {node.node_type}", None)

        finally:
            self._evaluation_stack.discard(node.id)

    def _evaluate_expression(
        self,
        node: ValueNode,
        expected_unit: Optional[str] = None
    ) -> Tuple[float, Optional[int], bool, Optional[str], Optional[str]]:
        """
        Evaluate an expression node.

        Resolves all dependencies, substitutes values, and computes result.
        Also tracks unit propagation through the expression.

        Args:
            node: The expression ValueNode to evaluate
            expected_unit: Optional unit symbol from PropertyDefinition for validation

        Returns: (value, unit_id, success, error_message, si_unit_symbol)
        """
        if not node.parsed_expression:
            return (None, None, False, "Expression not parsed", None)

        parsed = node.parsed_expression
        if not parsed.get("valid"):
            return (None, None, False, "Invalid parsed expression", None)

        # Get values for all dependencies
        values = {}
        units = {}

        for dep in node.dependencies:
            source = dep.source_node
            val, unit_id, success, error, _ = self.compute_value(source)

            if not success:
                return (None, None, False, f"Dependency '{dep.variable_name}' failed: {error}", None)

            placeholder = None
            for p, ref in parsed.get("placeholders", {}).items():
                if ref == dep.variable_name:
                    placeholder = p
                    break

            if placeholder:
                values[placeholder] = val
                units[placeholder] = unit_id

        # Substitute values into the expression
        try:
            modified_expr = parsed["modified"]

            # Define functions and constants
            local_dict = {
                'sqrt': lambda x: x ** 0.5,
                'sin': lambda x: __import__('math').sin(x),
                'cos': lambda x: __import__('math').cos(x),
                'tan': lambda x: __import__('math').tan(x),
                'log': lambda x: __import__('math').log(x),
                'ln': lambda x: __import__('math').log(x),
                'exp': lambda x: __import__('math').exp(x),
                'abs': abs,
                'pi': 3.141592653589793,
                'e': 2.718281828459045,
            }

            # Add placeholder values (from references)
            # NOTE: Values from referenced ValueNodes are ALREADY in SI (stored that way)
            # So we do NOT convert them again. We only use ref_units to track dimensions.
            ref_units = parsed.get("ref_units", {})
            dimensions_used = set()  # Track dimensions for SI unit determination
            for p, val in values.items():
                # Value is already in SI from compute_value, no conversion needed
                local_dict[p] = val
                # Track the dimension for bare literal handling
                unit_symbol = ref_units.get(p)
                if unit_symbol:
                    dimension = self.UNIT_TO_DIMENSION.get(unit_symbol)
                    if dimension:
                        dimensions_used.add(dimension)

            # Add literal values with units (already converted to SI)
            for p, lit_info in parsed.get("literal_values", {}).items():
                local_dict[p] = lit_info['si_value']
                # Track the dimension from literal
                lit_unit = lit_info.get('unit')
                if lit_unit:
                    dimension = self.UNIT_TO_DIMENSION.get(lit_unit)
                    if dimension:
                        dimensions_used.add(dimension)

            # Evaluate LOOKUP() function calls
            for p, lookup_info in parsed.get("lookup_calls", {}).items():
                # Get the key value - could be a literal or a reference
                key_val_expr = lookup_info['key_value_expr']

                # Check if the key value is a reference (starts with #)
                if key_val_expr.startswith('#'):
                    # It's a reference - look it up in values dict
                    ref_name = key_val_expr[1:]  # Remove # prefix
                    key_val = None
                    for placeholder, ref in parsed.get("placeholders", {}).items():
                        if ref == ref_name:
                            key_val = values.get(placeholder)
                            break
                    if key_val is None:
                        return (None, None, False, f"LOOKUP key reference '{key_val_expr}' could not be resolved", None)
                elif key_val_expr.startswith('"') and key_val_expr.endswith('"'):
                    # It's a quoted string (for discrete inputs like "M5")
                    key_val = key_val_expr[1:-1]  # Remove quotes
                elif key_val_expr.startswith("'") and key_val_expr.endswith("'"):
                    # Also support single quotes
                    key_val = key_val_expr[1:-1]  # Remove quotes
                else:
                    # It's a literal number - possibly with a unit suffix
                    # First check if it matches a literal with unit (e.g., "100°C", "373K")
                    unit_match = LITERAL_WITH_UNIT_PATTERN.match(key_val_expr.strip())
                    if unit_match:
                        # Parse value and unit, convert to SI
                        numeric_str = unit_match.group(1)
                        unit_str = unit_match.group(2)
                        try:
                            raw_value = float(numeric_str)
                        except ValueError:
                            return (None, None, False, f"LOOKUP key value '{key_val_expr}' has invalid numeric part", None)

                        # Convert to SI using the unit conversion table
                        if unit_str in self.UNIT_TO_SI:
                            # Handle temperature specially (needs offset conversion, not just scaling)
                            if unit_str in ['K', 'kelvin']:
                                key_val = raw_value  # Already in Kelvin
                            elif unit_str in ['°C', '℃', 'degC', 'celsius']:
                                key_val = raw_value + 273.15  # Convert °C to K
                            elif unit_str in ['°F', '℉', 'degF', 'fahrenheit']:
                                key_val = (raw_value - 32) * 5/9 + 273.15  # Convert °F to K
                            elif unit_str in ['°R', 'rankine']:
                                key_val = raw_value * 5/9  # Convert °R to K
                            else:
                                # Standard multiplicative conversion
                                key_val = raw_value * self.UNIT_TO_SI[unit_str]
                            logger.debug(f"LOOKUP input converted: {raw_value}{unit_str} -> {key_val} (SI)")
                        else:
                            # Unknown unit - just use the raw value
                            key_val = raw_value
                            logger.warning(f"LOOKUP input has unknown unit '{unit_str}', using raw value {raw_value}")
                    else:
                        # No unit suffix - try parsing as plain number
                        try:
                            key_val = float(key_val_expr)
                        except ValueError:
                            return (None, None, False, f"LOOKUP key value '{key_val_expr}' is not a valid number or string", None)

                # Perform the lookup
                lookup_result, interpolated, lookup_error = self.lookup_table(
                    lookup_info['table_code'],
                    lookup_info['output_column'],
                    lookup_info['key_column'],
                    key_val
                )

                if lookup_error:
                    return (None, None, False, f"LOOKUP error: {lookup_error}", None)

                local_dict[p] = lookup_result
                logger.debug(f"LOOKUP({lookup_info['table_code']}, {lookup_info['output_column']}, {lookup_info['key_column']}={key_val}) = {lookup_result} (interpolated: {interpolated})")

            # Evaluate MODEL() function calls
            for p, model_info in parsed.get("model_calls", {}).items():
                model_name = model_info['model_name']
                bindings = model_info['bindings']
                output_name = model_info.get('output_name')

                # Resolve binding values (may contain #refs, literals with units, or expressions)
                resolved_bindings = {}
                for input_name, binding_expr in bindings.items():
                    resolved_expr = binding_expr

                    # Substitute any #ref placeholders that were already resolved
                    for ref_placeholder, ref in parsed.get("placeholders", {}).items():
                        if ref_placeholder in resolved_expr or f"#{ref}" in resolved_expr:
                            # Get the resolved value for this reference
                            ref_value = values.get(ref_placeholder)
                            if ref_value is not None:
                                resolved_expr = resolved_expr.replace(ref_placeholder, str(ref_value))
                                resolved_expr = resolved_expr.replace(f"#{ref}", str(ref_value))

                    # Try to evaluate the binding expression
                    try:
                        # First check if it's a literal with unit (e.g., "1m", "25°C")
                        unit_match = LITERAL_WITH_UNIT_PATTERN.match(resolved_expr.strip())
                        if unit_match:
                            numeric_str = unit_match.group(1)
                            unit_str = unit_match.group(2)
                            raw_value = float(numeric_str)

                            # Convert to SI
                            if unit_str in self.UNIT_TO_SI:
                                # Handle temperature specially
                                if unit_str in ['°C', '℃', 'degC', 'celsius']:
                                    resolved_bindings[input_name] = raw_value + 273.15
                                elif unit_str in ['°F', '℉', 'degF', 'fahrenheit']:
                                    resolved_bindings[input_name] = (raw_value - 32) * 5/9 + 273.15
                                elif unit_str in ['°R', 'rankine']:
                                    resolved_bindings[input_name] = raw_value * 5/9
                                else:
                                    resolved_bindings[input_name] = raw_value * self.UNIT_TO_SI[unit_str]
                            else:
                                resolved_bindings[input_name] = raw_value
                        else:
                            # Try as a plain number or expression
                            # Use safe eval with math functions
                            import math
                            safe_dict = {
                                'sqrt': math.sqrt,
                                'sin': math.sin,
                                'cos': math.cos,
                                'tan': math.tan,
                                'log': math.log,
                                'ln': math.log,
                                'exp': math.exp,
                                'abs': abs,
                                'pi': math.pi,
                                'e': math.e,
                            }
                            resolved_bindings[input_name] = float(eval(resolved_expr, {"__builtins__": {}}, safe_dict))
                    except Exception as e:
                        return (None, None, False, f"MODEL() binding '{input_name}: {binding_expr}' could not be resolved: {e}", None)

                # Evaluate the model
                try:
                    from app.services.model_evaluation import evaluate_inline_model, ModelEvaluationError
                    model_result = evaluate_inline_model(
                        model_name=model_name,
                        bindings=resolved_bindings,
                        output_name=output_name,
                        db=self.db
                    )
                    local_dict[p] = model_result
                    logger.debug(f"MODEL('{model_name}', output='{output_name}') with {resolved_bindings} = {model_result}")
                except ModelEvaluationError as e:
                    return (None, None, False, f"MODEL() error: {e}", None)
                except Exception as e:
                    return (None, None, False, f"MODEL() evaluation failed: {e}", None)

            # Handle bare literals (numbers without units)
            # Only convert them using user's preferred unit for ADDITIVE expressions
            # For expressions with * or /, bare literals should be dimensionless scalars
            bare_literals = parsed.get("bare_literals", {})
            original_expr = parsed.get("original", "")

            # Check if expression has multiplication/division operators
            # If so, bare literals should NOT be unit-converted (they're dimensionless scalars like "divide by 2")
            has_mult_div = '*' in original_expr or '/' in original_expr

            if bare_literals and len(dimensions_used) == 1 and not has_mult_div:
                # Pure additive expression - convert bare literals using user's preferred unit
                dimension = list(dimensions_used)[0]
                user_unit = self._get_user_unit_preference(dimension)
                if user_unit:
                    conversion_factor = self.UNIT_TO_SI.get(user_unit, 1)
                    logger.info(f"Converting bare literals using user preference: {user_unit} (factor: {conversion_factor})")
                    for p, bare_info in bare_literals.items():
                        si_val = bare_info['value'] * conversion_factor
                        logger.debug(f"Bare literal {p}: {bare_info['value']} {user_unit} -> {si_val} SI")
                        local_dict[p] = si_val
                else:
                    # No user preference - use raw value (interpreted as SI)
                    for p, bare_info in bare_literals.items():
                        local_dict[p] = bare_info['value']
            else:
                # Has * or /, no dimension context, or multiple dimensions - use raw values (dimensionless)
                for p, bare_info in bare_literals.items():
                    local_dict[p] = bare_info['value']

            # Evaluate
            result = eval(modified_expr, {"__builtins__": {}}, local_dict)

            # Compute the result dimension through full dimensional analysis
            # This handles *, /, ^, **, sqrt, (), +, - operators correctly
            computed_dimension, dim_error = self._compute_expression_dimension(parsed)

            result_si_unit = None
            dimension_warning = None
            if computed_dimension is not None:
                # Get the SI unit symbol for the computed dimension
                result_si_unit = dimension_to_si_unit(computed_dimension)
                if result_si_unit is None and not computed_dimension.is_dimensionless():
                    # Fallback: construct from dimension string
                    result_si_unit = dimension_to_string(computed_dimension)
                logger.debug(f"Expression '{parsed.get('original', '')}' has dimension {dimension_to_string(computed_dimension)} -> SI unit '{result_si_unit}'")

                # Validate against expected unit from PropertyDefinition
                if expected_unit:
                    expected_dimension = get_unit_dimension(expected_unit)
                    if expected_dimension is not None and computed_dimension != expected_dimension:
                        # Dimension mismatch!
                        dimension_warning = (
                            f"Unit mismatch: expression produces {dimension_to_string(computed_dimension)} "
                            f"(SI: {result_si_unit or 'dimensionless'}), but property expects "
                            f"{dimension_to_string(expected_dimension)} ({expected_unit})"
                        )
                        logger.warning(f"Dimension validation warning: {dimension_warning}")
                        # Store the warning but don't fail - let the user see the computed value
                        # The warning will be visible in the computation_error field
            elif dim_error:
                # Dimension error - log warning but don't fail the computation
                logger.warning(f"Dimension analysis warning for '{parsed.get('original', '')}': {dim_error}")
                dimension_warning = dim_error
            else:
                # Fallback to old behavior for simple expressions
                if len(dimensions_used) == 1:
                    dimension = list(dimensions_used)[0]
                    result_si_unit = self.DIMENSION_SI_UNITS.get(dimension)

            # Store SI unit symbol in parsed_expression for later use
            result_unit_id = self._compute_result_unit(parsed, units)

            # Return with warning if there's a dimension issue
            # We still return success=True so the value is stored, but include warning in error slot
            return (float(result), result_unit_id, True, dimension_warning, result_si_unit)

        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            return (None, None, False, f"Evaluation error: {e}", None)

    def _compute_result_unit(self, parsed: Dict, units: Dict[str, int]) -> Optional[int]:
        """
        Compute the resulting unit of an expression through dimensional analysis.

        This is a simplified version - full implementation would track dimensions
        through each operation.
        """
        # If all inputs have the same unit and expression is simple, result has same unit
        unique_units = set(u for u in units.values() if u is not None)

        if len(unique_units) == 1:
            # Check if expression is just addition/subtraction (preserves units)
            expr = parsed.get("original", "")
            if not any(op in expr for op in ["*", "/", "^", "**", "sqrt"]):
                return list(unique_units)[0]

        # For complex expressions, need full dimensional analysis
        # This will be enhanced in later iterations
        return None

    def _compute_expression_dimension(self, parsed: Dict) -> Tuple[Optional[Dimension], Optional[str]]:
        """
        Compute the resulting dimension of an expression through dimensional analysis.

        Tracks dimensions through all operators: *, /, ^, **, sqrt, +, -

        Args:
            parsed: The parsed expression dict containing literal_values, ref_units, etc.

        Returns:
            (dimension, error_message) - Dimension object or None with error
        """
        original_expr = parsed.get("original", "")
        modified_expr = parsed.get("modified", "")

        # Build a map of placeholder -> Dimension
        placeholder_dimensions: Dict[str, Dimension] = {}

        # Get dimensions for literal values with units
        for placeholder, lit_info in parsed.get("literal_values", {}).items():
            unit_symbol = lit_info.get('unit')
            if unit_symbol:
                dim = get_unit_dimension(unit_symbol)
                if dim:
                    placeholder_dimensions[placeholder] = dim
                else:
                    # Unknown unit - treat as dimensionless
                    placeholder_dimensions[placeholder] = DIMENSIONLESS
            else:
                placeholder_dimensions[placeholder] = DIMENSIONLESS

        # Get dimensions for reference placeholders
        # First, use ref_units (from PropertyDefinition.unit)
        for placeholder, unit_symbol in parsed.get("ref_units", {}).items():
            if unit_symbol:
                dim = get_unit_dimension(unit_symbol)
                if dim:
                    placeholder_dimensions[placeholder] = dim
                else:
                    placeholder_dimensions[placeholder] = DIMENSIONLESS
            else:
                placeholder_dimensions[placeholder] = DIMENSIONLESS

        # Also check placeholders that might not be in ref_units
        # This can happen if _get_reference_unit couldn't find the PropertyDefinition
        # but the ValueNode still has a computed_unit_symbol
        for placeholder, ref in parsed.get("placeholders", {}).items():
            if placeholder not in placeholder_dimensions:
                # Try to resolve the reference and get its computed_unit_symbol
                source_node = self._resolve_reference(ref)
                if source_node and source_node.computed_unit_symbol:
                    dim = get_unit_dimension(source_node.computed_unit_symbol)
                    if dim:
                        placeholder_dimensions[placeholder] = dim
                        logger.debug(f"Resolved dimension for {placeholder} ({ref}) from ValueNode: {dimension_to_string(dim)}")
                    else:
                        placeholder_dimensions[placeholder] = DIMENSIONLESS
                else:
                    # No unit info available - default to dimensionless
                    placeholder_dimensions[placeholder] = DIMENSIONLESS
                    logger.debug(f"No dimension info for {placeholder} ({ref}), defaulting to dimensionless")

        # Bare literals are dimensionless scalars (like "* 2" or "/ 3")
        for placeholder in parsed.get("bare_literals", {}).keys():
            placeholder_dimensions[placeholder] = DIMENSIONLESS

        # LOOKUP and MODEL calls - for now treat as dimensionless (could be enhanced)
        for placeholder in parsed.get("lookup_calls", {}).keys():
            placeholder_dimensions[placeholder] = DIMENSIONLESS
        for placeholder in parsed.get("model_calls", {}).keys():
            placeholder_dimensions[placeholder] = DIMENSIONLESS

        # Now parse the modified expression to compute dimension
        # We use a simple recursive descent approach on the expression string
        try:
            result_dim = self._infer_dimension_from_expr(modified_expr, placeholder_dimensions)
            return (result_dim, None)
        except DimensionError as e:
            return (None, str(e))
        except Exception as e:
            logger.warning(f"Failed to infer dimension for '{original_expr}': {e}")
            return (None, f"Dimension inference failed: {e}")

    def _infer_dimension_from_expr(self, expr: str, placeholder_dims: Dict[str, Dimension]) -> Dimension:
        """
        Infer dimension from a modified expression string.

        Uses sympy to parse and then walks the expression tree to compute dimensions.

        Args:
            expr: The modified expression with placeholders
            placeholder_dims: Map of placeholder names to their Dimensions

        Returns:
            Computed Dimension

        Raises:
            DimensionError: If dimensions are incompatible
        """
        import sympy as sp
        from sympy import Symbol, Pow, Mul, Add, sqrt as sp_sqrt, sin as sp_sin, cos as sp_cos
        from sympy import tan as sp_tan, log as sp_log, exp as sp_exp, Abs

        # Build sympy local dict
        local_dict = {
            'sqrt': sp.sqrt,
            'sin': sp.sin,
            'cos': sp.cos,
            'tan': sp.tan,
            'log': sp.log,
            'ln': sp.log,
            'exp': sp.exp,
            'abs': sp.Abs,
            'pi': sp.pi,
            'e': sp.E,
        }

        # Add placeholders as symbols
        for p in placeholder_dims:
            local_dict[p] = Symbol(p)

        try:
            parsed_expr = sp.sympify(expr, locals=local_dict)
        except Exception as e:
            raise DimensionError(f"Failed to parse expression: {e}")

        def infer_dim(node) -> Dimension:
            """Recursively infer dimension from sympy expression tree."""
            # Symbol - look up in placeholder_dims
            if isinstance(node, Symbol):
                name = str(node)
                return placeholder_dims.get(name, DIMENSIONLESS)

            # Number - dimensionless
            if node.is_number:
                return DIMENSIONLESS

            # Addition/Subtraction - all operands must have same dimension
            if isinstance(node, Add):
                args = node.args
                if not args:
                    return DIMENSIONLESS

                first_dim = infer_dim(args[0])
                for i, arg in enumerate(args[1:], start=2):
                    arg_dim = infer_dim(arg)
                    # Allow dimensionless constants to adapt
                    if arg_dim != first_dim:
                        if arg_dim.is_dimensionless() and arg.is_number:
                            continue  # Numeric constant adapts
                        if first_dim.is_dimensionless():
                            first_dim = arg_dim  # First was dimensionless, update
                            continue
                        raise DimensionError(
                            f"Dimension mismatch in addition: operand 1 is {dimension_to_string(first_dim)}, "
                            f"operand {i} is {dimension_to_string(arg_dim)}"
                        )
                return first_dim

            # Multiplication - dimensions add
            if isinstance(node, Mul):
                result = DIMENSIONLESS
                for arg in node.args:
                    arg_dim = infer_dim(arg)
                    result = result * arg_dim
                return result

            # Power - dimension multiplied by exponent
            if isinstance(node, Pow):
                base = node.args[0]
                exponent = node.args[1]

                base_dim = infer_dim(base)

                # Check if exponent is a number
                if exponent.is_number:
                    exp_val = float(exponent)
                    # Check for sqrt (exponent 0.5)
                    if exp_val == 0.5:
                        # Sqrt - dimensions halved
                        if (base_dim.length % 2 != 0 or base_dim.mass % 2 != 0 or
                            base_dim.time % 2 != 0 or base_dim.temperature % 2 != 0 or
                            base_dim.current % 2 != 0 or base_dim.amount % 2 != 0 or
                            base_dim.luminosity % 2 != 0):
                            raise DimensionError(
                                f"Cannot take sqrt of {dimension_to_string(base_dim)} - exponents must be even"
                            )
                        return Dimension(
                            length=base_dim.length // 2,
                            mass=base_dim.mass // 2,
                            time=base_dim.time // 2,
                            temperature=base_dim.temperature // 2,
                            current=base_dim.current // 2,
                            amount=base_dim.amount // 2,
                            luminosity=base_dim.luminosity // 2,
                        )
                    elif exp_val == int(exp_val):
                        # Integer exponent
                        return base_dim ** int(exp_val)
                    else:
                        # Non-integer, non-sqrt exponent
                        if not base_dim.is_dimensionless():
                            raise DimensionError(
                                f"Cannot raise dimensional quantity {dimension_to_string(base_dim)} "
                                f"to non-integer power {exp_val}"
                            )
                        return DIMENSIONLESS
                else:
                    # Variable exponent - base must be dimensionless
                    if not base_dim.is_dimensionless():
                        raise DimensionError(
                            "Cannot raise dimensional quantity to variable power"
                        )
                    return DIMENSIONLESS

            # Function calls
            func_name = type(node).__name__
            args = getattr(node, 'args', ())

            # Trig functions - require dimensionless input, return dimensionless
            if func_name in ('sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh'):
                if args:
                    arg_dim = infer_dim(args[0])
                    if not arg_dim.is_dimensionless():
                        raise DimensionError(
                            f"Function {func_name} requires dimensionless argument, got {dimension_to_string(arg_dim)}"
                        )
                return DIMENSIONLESS

            # Log/exp - require dimensionless
            if func_name in ('log', 'exp'):
                if args:
                    arg_dim = infer_dim(args[0])
                    if not arg_dim.is_dimensionless():
                        raise DimensionError(
                            f"Function {func_name} requires dimensionless argument, got {dimension_to_string(arg_dim)}"
                        )
                return DIMENSIONLESS

            # Abs preserves dimension
            if func_name == 'Abs':
                if args:
                    return infer_dim(args[0])
                return DIMENSIONLESS

            # For any other node type, try to recurse on args
            if args:
                # If it has args, try to infer from first arg
                return infer_dim(args[0])

            # Default to dimensionless
            return DIMENSIONLESS

        return infer_dim(parsed_expr)

    # ==================== DEPENDENCY MANAGEMENT ====================

    def recalculate(
        self,
        node: ValueNode,
        expected_unit: Optional[str] = None
    ) -> Tuple[bool, Optional[str]]:
        """
        Recalculate a node's value and update cache.

        Args:
            node: The ValueNode to recalculate
            expected_unit: Optional unit symbol from PropertyDefinition for validation

        Returns: (success, error_message)
        """
        self._evaluation_stack.clear()

        value, unit_id, success, error_or_warning, si_unit_symbol = self.compute_value(node, expected_unit)

        if success:
            node.computed_value = value
            node.computed_unit_id = unit_id
            # Store the SI unit symbol for frontend display conversion
            if si_unit_symbol:
                node.computed_unit_symbol = si_unit_symbol
            node.computation_status = ComputationStatus.VALID
            # Store dimension warning if present (still valid but with warning)
            node.computation_error = error_or_warning  # This will be the dimension warning or None
            node.last_computed = datetime.utcnow()
        else:
            node.computation_status = ComputationStatus.ERROR
            node.computation_error = error_or_warning

        self.db.flush()
        return (success, error_or_warning)

    def mark_dependents_stale(self, node: ValueNode):
        """
        Mark all nodes that depend on this node as stale.

        This triggers a cascade through the dependency graph.
        """
        for dep in node.dependents:
            dependent = dep.dependent_node
            if dependent.computation_status == ComputationStatus.VALID:
                dependent.computation_status = ComputationStatus.STALE
                # Recursively mark dependents
                self.mark_dependents_stale(dependent)

        self.db.flush()

    def transfer_dependents(self, old_node: ValueNode, new_node: ValueNode):
        """
        Transfer all dependents from old_node to new_node.

        Used when replacing a node (e.g., expression -> literal) to maintain
        dependency relationships. Also marks all transferred dependents as stale
        recursively (including their dependents).
        """
        # Get all dependencies where old_node is the source
        deps_to_transfer = self.db.query(ValueDependency).filter(
            ValueDependency.source_id == old_node.id
        ).all()

        logger.info(f"Transferring {len(deps_to_transfer)} dependents from node {old_node.id} to node {new_node.id}")

        for dep in deps_to_transfer:
            # Update the source_id to point to new node
            dep.source_id = new_node.id
            # Mark the dependent AND all its downstream dependents as stale (recursive)
            self._mark_node_and_dependents_stale(dep.dependent_node)

        self.db.flush()

    def _mark_node_and_dependents_stale(self, node: ValueNode):
        """Mark this node and all its downstream dependents as stale (recursive)."""
        if node.computation_status == ComputationStatus.VALID:
            node.computation_status = ComputationStatus.STALE
        # Recursively mark all downstream dependents
        for dep in node.dependents:
            self._mark_node_and_dependents_stale(dep.dependent_node)

    def recalculate_stale(self, node: ValueNode) -> List[ValueNode]:
        """
        Recalculate all stale dependents of this node.

        Walks downstream (dependents) to find stale nodes, then recalculates
        them in proper order (dependencies first).

        Returns list of recalculated nodes.
        """
        # First ensure all downstream dependents are marked stale (recursive)
        self.mark_dependents_stale(node)

        # Then collect all stale dependents (walking downstream)
        stale_nodes = self._collect_stale_dependents(node)

        if not stale_nodes:
            logger.debug(f"No stale dependents found for node {node.id}")
            return []

        logger.info(f"Found {len(stale_nodes)} stale dependents to recalculate")

        # Sort by dependency order (nodes with fewer dependencies first)
        # This ensures we recalculate in the right order
        stale_nodes = self._sort_by_dependency_order(stale_nodes)

        recalculated = []
        for n in stale_nodes:
            logger.debug(f"Recalculating stale node {n.id}: {n.expression_string}")
            success, error = self.recalculate(n)
            if success:
                recalculated.append(n)
                logger.info(f"Successfully recalculated node {n.id}, new value: {n.computed_value}")
            else:
                logger.warning(f"Failed to recalculate node {n.id}: {error}")

        self.db.flush()
        return recalculated

    def _collect_stale_dependents(self, node: ValueNode, visited: Set[int] = None) -> List[ValueNode]:
        """Collect all stale nodes that depend on this node (walk downstream)."""
        if visited is None:
            visited = set()

        result = []

        # Walk through dependents (things that depend ON this node)
        for dep in node.dependents:
            dependent = dep.dependent_node
            if dependent.id in visited:
                continue
            visited.add(dependent.id)

            # If this dependent is stale, add it
            if dependent.is_stale():
                result.append(dependent)

            # Recursively collect from this dependent's dependents
            result.extend(self._collect_stale_dependents(dependent, visited))

        return result

    def _sort_by_dependency_order(self, nodes: List[ValueNode]) -> List[ValueNode]:
        """Sort nodes so dependencies are calculated before dependents."""
        node_ids = {n.id for n in nodes}

        # Calculate dependency depth for each node
        depths = {}
        for node in nodes:
            depths[node.id] = self._get_dependency_depth(node, node_ids)

        # Sort by depth (lower depth = fewer dependencies = calculate first)
        return sorted(nodes, key=lambda n: depths[n.id])

    def _get_dependency_depth(self, node: ValueNode, relevant_ids: Set[int]) -> int:
        """Get the dependency depth of a node within a set of relevant nodes."""
        max_depth = 0
        for dep in node.dependencies:
            if dep.source_id in relevant_ids:
                source_node = dep.source_node
                max_depth = max(max_depth, 1 + self._get_dependency_depth(source_node, relevant_ids))
        return max_depth

    def get_dependency_tree(self, node: ValueNode, depth: int = 10) -> Dict[str, Any]:
        """
        Get the dependency tree for a node.

        Returns a nested dict structure showing all dependencies.
        """
        if depth <= 0:
            return {"id": node.id, "truncated": True}

        result = {
            "id": node.id,
            "type": node.node_type.value,
            "status": node.computation_status.value,
            "value": node.computed_value,
            "expression": node.expression_string,
            "dependencies": []
        }

        for dep in node.dependencies:
            result["dependencies"].append(
                self.get_dependency_tree(dep.source_node, depth - 1)
            )

        return result

    def check_circular_dependency(self, node_id: int, target_id: int, visited: Set[int] = None) -> bool:
        """
        Check if adding a dependency from node_id to target_id would create a cycle.

        Returns True if it would create a circular dependency.
        """
        if visited is None:
            visited = set()

        if node_id == target_id:
            return True

        if target_id in visited:
            return False

        visited.add(target_id)

        target = self.db.query(ValueNode).get(target_id)
        if not target:
            return False

        for dep in target.dependencies:
            if self.check_circular_dependency(node_id, dep.source_id, visited):
                return True

        return False

    # ==================== UPDATE HANDLERS ====================

    def update_literal(self, node: ValueNode, value: float, unit_id: Optional[int] = None):
        """
        Update a literal node's value and cascade updates to dependents.
        """
        if node.node_type != NodeType.LITERAL:
            raise ValueError("Can only update literal nodes directly")

        node.numeric_value = value
        node.computed_value = value
        if unit_id is not None:
            node.unit_id = unit_id
            node.computed_unit_id = unit_id
        node.last_computed = datetime.utcnow()

        # Mark all dependents as stale
        self.mark_dependents_stale(node)
        self.db.flush()

    def update_expression(self, node: ValueNode, expression: str):
        """
        Update an expression node with a new expression.
        """
        if node.node_type != NodeType.EXPRESSION:
            raise ValueError("Can only update expression on expression nodes")

        # Clear old dependencies
        self.db.query(ValueDependency).filter(
            ValueDependency.dependent_id == node.id
        ).delete()

        # Parse new expression
        parsed = self._parse_expression(expression)
        node.expression_string = expression
        node.parsed_expression = parsed
        node.computation_status = ComputationStatus.PENDING

        # Create new dependencies
        references = self._extract_references(expression)
        for ref in references:
            source_node = self._resolve_reference(ref)
            if source_node:
                dep = ValueDependency(
                    dependent_id=node.id,
                    source_id=source_node.id,
                    variable_name=ref
                )
                self.db.add(dep)

        # Mark dependents as stale
        self.mark_dependents_stale(node)
        self.db.flush()
