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
    r'K|°C|°F|'  # Temperature
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

    # SI base units for each dimension
    DIMENSION_SI_UNITS = {
        'length': 'm',
        'area': 'm²',
        'volume': 'm³',
        'mass': 'kg',
        'force': 'N',
        'pressure': 'Pa',
        'temperature': 'K',
        'time': 's',
        'frequency': 'Hz',
        'energy': 'J',
        'power': 'W',
        'torque': 'N·m',
        'current': 'A',
        'voltage': 'V',
        'resistance': 'Ω',
        'angle': 'rad',
        'velocity': 'm/s',
        'acceleration': 'm/s²',
        'density': 'kg/m³',
    }

    # Map unit symbols to their dimension
    UNIT_TO_DIMENSION = {
        # Length
        'nm': 'length', 'μm': 'length', 'mm': 'length', 'cm': 'length', 'm': 'length', 'km': 'length',
        'in': 'length', 'ft': 'length',
        # Area
        'mm²': 'area', 'cm²': 'area', 'm²': 'area', 'km²': 'area', 'ha': 'area', 'in²': 'area', 'ft²': 'area',
        # Volume
        'mm³': 'volume', 'cm³': 'volume', 'mL': 'volume', 'L': 'volume', 'm³': 'volume',
        'in³': 'volume', 'ft³': 'volume', 'gal': 'volume',
        # Mass
        'μg': 'mass', 'mg': 'mass', 'g': 'mass', 'kg': 'mass', 't': 'mass', 'oz': 'mass', 'lb': 'mass',
        # Force
        'μN': 'force', 'mN': 'force', 'N': 'force', 'kN': 'force', 'MN': 'force', 'lbf': 'force',
        # Pressure
        'Pa': 'pressure', 'kPa': 'pressure', 'MPa': 'pressure', 'GPa': 'pressure',
        'bar': 'pressure', 'mbar': 'pressure', 'psi': 'pressure', 'ksi': 'pressure',
        # Temperature
        'K': 'temperature', '°C': 'temperature', '°F': 'temperature',
        # Time
        'ps': 'time', 'ns': 'time', 'μs': 'time', 'ms': 'time', 's': 'time',
        'min': 'time', 'h': 'time', 'd': 'time', 'yr': 'time',
        # Frequency
        'Hz': 'frequency', 'kHz': 'frequency', 'MHz': 'frequency', 'GHz': 'frequency',
        # Energy
        'J': 'energy', 'kJ': 'energy', 'MJ': 'energy', 'Wh': 'energy', 'kWh': 'energy', 'BTU': 'energy',
        # Power
        'W': 'power', 'mW': 'power', 'kW': 'power', 'MW': 'power', 'hp': 'power',
        # Torque
        'N·m': 'torque', 'kN·m': 'torque', 'lbf·ft': 'torque',
        # Electrical
        'A': 'current', 'mA': 'current', 'μA': 'current',
        'V': 'voltage', 'mV': 'voltage', 'kV': 'voltage',
        'Ω': 'resistance', 'kΩ': 'resistance', 'MΩ': 'resistance',
        # Angle
        'rad': 'angle', 'mrad': 'angle', 'deg': 'angle', '°': 'angle',
        # Velocity
        'm/s': 'velocity', 'km/h': 'velocity', 'ft/s': 'velocity', 'mph': 'velocity',
        # Acceleration
        'm/s²': 'acceleration',
        # Density
        'kg/m³': 'density', 'g/cm³': 'density', 'lb/ft³': 'density',
    }

    # Unit conversion factors to SI base units
    UNIT_TO_SI = {
        # Length -> meters
        'nm': 1e-9, 'μm': 1e-6, 'mm': 0.001, 'cm': 0.01, 'm': 1, 'km': 1000,
        'in': 0.0254, 'ft': 0.3048,
        # Area -> m²
        'mm²': 1e-6, 'cm²': 1e-4, 'm²': 1, 'km²': 1e6, 'ha': 1e4,
        'in²': 0.00064516, 'ft²': 0.092903,
        # Volume -> m³
        'mm³': 1e-9, 'cm³': 1e-6, 'mL': 1e-6, 'L': 0.001, 'm³': 1,
        'in³': 1.6387e-5, 'ft³': 0.0283168, 'gal': 0.00378541,
        # Mass -> kg
        'μg': 1e-9, 'mg': 1e-6, 'g': 0.001, 'kg': 1, 't': 1000,
        'oz': 0.0283495, 'lb': 0.453592,
        # Force -> N
        'μN': 1e-6, 'mN': 1e-3, 'N': 1, 'kN': 1000, 'MN': 1e6,
        'lbf': 4.44822,
        # Pressure -> Pa
        'Pa': 1, 'kPa': 1000, 'MPa': 1e6, 'GPa': 1e9,
        'bar': 1e5, 'mbar': 100, 'psi': 6894.76, 'ksi': 6.89476e6,
        # Temperature -> K (special handling needed for offset)
        'K': 1, '°C': 1, '°F': 5/9,  # Note: offset conversion handled separately
        # Time -> seconds
        'ps': 1e-12, 'ns': 1e-9, 'μs': 1e-6, 'ms': 0.001, 's': 1,
        'min': 60, 'h': 3600, 'd': 86400, 'yr': 3.154e7,
        # Frequency -> Hz
        'Hz': 1, 'kHz': 1000, 'MHz': 1e6, 'GHz': 1e9,
        # Energy -> J
        'J': 1, 'kJ': 1000, 'MJ': 1e6, 'Wh': 3600, 'kWh': 3.6e6, 'BTU': 1055.06,
        # Power -> W
        'W': 1, 'mW': 0.001, 'kW': 1000, 'MW': 1e6, 'hp': 745.7,
        # Torque -> N·m
        'N·m': 1, 'kN·m': 1000, 'lbf·ft': 1.35582,
        # Electrical
        'A': 1, 'mA': 0.001, 'μA': 1e-6,
        'V': 1, 'mV': 0.001, 'kV': 1000,
        'Ω': 1, 'kΩ': 1000, 'MΩ': 1e6,
        # Angle -> radians
        'rad': 1, 'mrad': 0.001, 'deg': 0.0174533, '°': 0.0174533,
        # Velocity -> m/s
        'm/s': 1, 'km/h': 0.277778, 'ft/s': 0.3048, 'mph': 0.44704,
        # Acceleration -> m/s²
        'm/s²': 1,
        # Density -> kg/m³
        'kg/m³': 1, 'g/cm³': 1000, 'lb/ft³': 16.0185,
    }

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

            parsed = sympify(modified_expr, locals=local_dict)

            return {
                "original": expression,
                "modified": modified_expr,
                "placeholders": placeholders,
                "ref_units": ref_units,  # Unit symbols for each reference placeholder
                "literal_values": literal_values,
                "bare_literals": bare_literals,  # Unitless numbers that need user unit conversion
                "lookup_calls": lookup_calls,  # LOOKUP() function calls
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

    def _generate_code_from_name(self, name: str) -> str:
        """Generate a code from entity name if no code exists."""
        code = re.sub(r'[^a-zA-Z0-9]', '_', name.upper())
        code = re.sub(r'_+', '_', code)
        code = code.strip('_')
        return code

    def _get_reference_unit(self, ref: str) -> Optional[str]:
        """
        Get the unit symbol for a reference.

        Returns the unit symbol (e.g., 'mm', 'Pa') or None if not found.
        """
        parts = ref.split(".")
        if len(parts) != 2:
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
            prop_def = self.db.query(PropertyDefinition).filter(PropertyDefinition.name == prop_name_normalized).first()
            if prop_def:
                return prop_def.unit

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
            prop_def = self.db.query(PropertyDefinition).filter(PropertyDefinition.name == prop_name_normalized).first()
            if prop_def:
                return prop_def.unit

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
        print(f"DEBUG: Resolving reference: entity_code={entity_code}, prop_name={prop_name} -> normalized={prop_name_normalized}")

        # Try to find Component by code
        component = self.db.query(Component).filter(
            Component.code == entity_code
        ).first()
        print(f"DEBUG: Component by code lookup: {component.name if component else 'NOT FOUND'}")

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
            print(f"DEBUG: Component by generated code SQL lookup: {component.name if component else 'NOT FOUND'}")

        if component:
            print(f"DEBUG: Component found: id={component.id}, name={component.name}")
            # Find the property definition (use normalized name with spaces)
            prop_def = self.db.query(PropertyDefinition).filter(
                PropertyDefinition.name == prop_name_normalized
            ).first()
            print(f"DEBUG: Property definition lookup for '{prop_name_normalized}': {prop_def.id if prop_def else 'NOT FOUND'}")

            if prop_def:
                # Find the ComponentProperty linking them
                comp_prop = self.db.query(ComponentProperty).filter(
                    ComponentProperty.component_id == component.id,
                    ComponentProperty.property_definition_id == prop_def.id
                ).first()
                print(f"DEBUG: ComponentProperty lookup (comp_id={component.id}, prop_def_id={prop_def.id}): {comp_prop.id if comp_prop else 'NOT FOUND'}")

                if comp_prop:
                    print(f"DEBUG: ComponentProperty details: value_node_id={comp_prop.value_node_id}, single_value={comp_prop.single_value}")
                    if comp_prop.value_node_id:
                        node = self.db.query(ValueNode).filter(
                            ValueNode.id == comp_prop.value_node_id
                        ).first()
                        print(f"DEBUG: ValueNode found: {node.id if node else 'NOT FOUND'}")
                        return node
                    else:
                        # Property exists but has no value_node - create one from the literal value
                        literal_value = comp_prop.single_value or comp_prop.average_value or comp_prop.min_value
                        print(f"DEBUG: No value_node, checking literal_value={literal_value}")
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
                                print(f"DEBUG: Converting component property: {literal_value} {prop_unit} -> {si_value} {si_unit_symbol}")
                            else:
                                print(f"DEBUG: Creating literal ValueNode for property with value={literal_value} (no unit conversion)")

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
                            print(f"DEBUG: Created and linked ValueNode id={new_node.id}")
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

    def compute_value(self, node: ValueNode) -> Tuple[float, Optional[int], bool, Optional[str], Optional[str]]:
        """
        Compute the value of a node.

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
                ref_value, ref_unit, success, error, si_unit = self.compute_value(node.reference_node)
                return (ref_value, ref_unit, success, error, si_unit)

            elif node.node_type == NodeType.EXPRESSION:
                return self._evaluate_expression(node)

            else:
                return (None, None, False, f"Unknown node type: {node.node_type}", None)

        finally:
            self._evaluation_stack.discard(node.id)

    def _evaluate_expression(self, node: ValueNode) -> Tuple[float, Optional[int], bool, Optional[str], Optional[str]]:
        """
        Evaluate an expression node.

        Resolves all dependencies, substitutes values, and computes result.
        Also tracks unit propagation through the expression.

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
                    # It's a literal number
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

            # Determine the SI unit symbol for the result
            # For simple expressions (add/subtract), result has same dimension as inputs
            result_si_unit = None
            if len(dimensions_used) == 1:
                dimension = list(dimensions_used)[0]
                result_si_unit = self.DIMENSION_SI_UNITS.get(dimension)

            # Store SI unit symbol in parsed_expression for later use
            result_unit_id = self._compute_result_unit(parsed, units)

            return (float(result), result_unit_id, True, None, result_si_unit)

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

    # ==================== DEPENDENCY MANAGEMENT ====================

    def recalculate(self, node: ValueNode) -> Tuple[bool, Optional[str]]:
        """
        Recalculate a node's value and update cache.

        Returns: (success, error_message)
        """
        self._evaluation_stack.clear()

        value, unit_id, success, error, si_unit_symbol = self.compute_value(node)

        if success:
            node.computed_value = value
            node.computed_unit_id = unit_id
            # Store the SI unit symbol for frontend display conversion
            if si_unit_symbol:
                node.computed_unit_symbol = si_unit_symbol
            node.computation_status = ComputationStatus.VALID
            node.computation_error = None
            node.last_computed = datetime.utcnow()
        else:
            node.computation_status = ComputationStatus.ERROR
            node.computation_error = error

        self.db.flush()
        return (success, error)

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


def create_value_engine(db: Session) -> ValueEngine:
    """Factory function to create a ValueEngine instance."""
    return ValueEngine(db)
