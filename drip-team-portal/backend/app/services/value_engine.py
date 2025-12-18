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
# Property names must start with a letter (e.g., Density, thermal_conductivity)
REFERENCE_PATTERN = re.compile(r'#([a-zA-Z0-9][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)?)')


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

    def __init__(self, db: Session):
        self.db = db
        self.unit_engine = UnitEngine(db)
        self._evaluation_stack: Set[int] = set()  # For circular dependency detection

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

    def _parse_expression(self, expression: str) -> Dict[str, Any]:
        """
        Parse an expression string into an AST-like structure.

        Supports:
        - Basic math: +, -, *, /, ^, **
        - Functions: sqrt, sin, cos, tan, log, exp, abs
        - Constants: pi, e
        - References: #entity.property

        Returns a dict with parsing results.
        """
        # Replace references with placeholder symbols
        placeholders = {}
        refs = self._extract_references(expression)

        modified_expr = expression
        for i, ref in enumerate(refs):
            placeholder = f"__ref_{i}__"
            placeholders[placeholder] = ref
            # Replace #ref with placeholder (handle the # prefix)
            modified_expr = modified_expr.replace(f"#{ref}", placeholder)

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

            parsed = sympify(modified_expr, locals=local_dict)

            return {
                "original": expression,
                "modified": modified_expr,
                "placeholders": placeholders,
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
        print(f"DEBUG: Resolving reference: entity_code={entity_code}, prop_name={prop_name}")

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
            # Find the property definition
            prop_def = self.db.query(PropertyDefinition).filter(
                PropertyDefinition.name == prop_name
            ).first()
            print(f"DEBUG: Property definition lookup for '{prop_name}': {prop_def.id if prop_def else 'NOT FOUND'}")

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
                            print(f"DEBUG: Creating literal ValueNode for property with value={literal_value}")
                            # Create a new literal ValueNode for this property
                            # Note: unit_id would require looking up the unit in the units table
                            # For now, we just store the numeric value
                            new_node = ValueNode(
                                node_type=NodeType.LITERAL,
                                numeric_value=literal_value,
                                computed_value=literal_value,
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

            logger.warning(f"Component {entity_code} found but property {prop_name} not found or has no value_node")

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
            # Find the property definition
            prop_def = self.db.query(PropertyDefinition).filter(
                PropertyDefinition.name == prop_name
            ).first()

            if prop_def:
                # Find the MaterialProperty linking them
                mat_prop = self.db.query(MaterialProperty).filter(
                    MaterialProperty.material_id == material.id,
                    MaterialProperty.property_definition_id == prop_def.id
                ).first()

                if mat_prop and mat_prop.value_node_id:
                    return self.db.query(ValueNode).filter(
                        ValueNode.id == mat_prop.value_node_id
                    ).first()

            logger.debug(f"Material {entity_code} found but property {prop_name} not found or has no value_node")

        # Fallback: Try to find by description (legacy/direct value node reference)
        node = self.db.query(ValueNode).filter(
            ValueNode.description == ref
        ).first()

        if node:
            return node

        logger.warning(f"Could not resolve reference: {ref}")
        return None

    # ==================== EXPRESSION EVALUATION ====================

    def compute_value(self, node: ValueNode) -> Tuple[float, Optional[int], bool, Optional[str]]:
        """
        Compute the value of a node.

        Returns: (value, unit_id, success, error_message)
        """
        # Circular dependency check
        if node.id in self._evaluation_stack:
            node.computation_status = ComputationStatus.CIRCULAR
            node.computation_error = "Circular dependency detected"
            return (None, None, False, "Circular dependency detected")

        self._evaluation_stack.add(node.id)

        try:
            if node.node_type == NodeType.LITERAL:
                return (node.numeric_value, node.unit_id, True, None)

            elif node.node_type == NodeType.REFERENCE:
                if not node.reference_node:
                    return (None, None, False, "Referenced node not found")
                ref_value, ref_unit, success, error = self.compute_value(node.reference_node)
                return (ref_value, ref_unit, success, error)

            elif node.node_type == NodeType.EXPRESSION:
                return self._evaluate_expression(node)

            else:
                return (None, None, False, f"Unknown node type: {node.node_type}")

        finally:
            self._evaluation_stack.discard(node.id)

    def _evaluate_expression(self, node: ValueNode) -> Tuple[float, Optional[int], bool, Optional[str]]:
        """
        Evaluate an expression node.

        Resolves all dependencies, substitutes values, and computes result.
        Also tracks unit propagation through the expression.
        """
        if not node.parsed_expression:
            return (None, None, False, "Expression not parsed")

        parsed = node.parsed_expression
        if not parsed.get("valid"):
            return (None, None, False, "Invalid parsed expression")

        # Get values for all dependencies
        values = {}
        units = {}

        for dep in node.dependencies:
            source = dep.source_node
            val, unit_id, success, error = self.compute_value(source)

            if not success:
                return (None, None, False, f"Dependency '{dep.variable_name}' failed: {error}")

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

            # Add placeholder values
            for p, val in values.items():
                local_dict[p] = val

            # Evaluate
            result = eval(modified_expr, {"__builtins__": {}}, local_dict)

            # TODO: Compute resulting unit through dimensional analysis
            # For now, return None for unit (will be implemented with more complex expressions)
            result_unit_id = self._compute_result_unit(parsed, units)

            return (float(result), result_unit_id, True, None)

        except Exception as e:
            logger.error(f"Failed to evaluate expression: {e}")
            return (None, None, False, f"Evaluation error: {e}")

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

        value, unit_id, success, error = self.compute_value(node)

        if success:
            node.computed_value = value
            node.computed_unit_id = unit_id
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

    def recalculate_stale(self, node: ValueNode) -> List[ValueNode]:
        """
        Recalculate all stale nodes in the dependency tree rooted at node.

        Uses topological sort to ensure dependencies are calculated first.

        Returns list of recalculated nodes.
        """
        # Get all stale nodes in dependency order
        stale_nodes = self._get_stale_nodes_ordered(node)
        recalculated = []

        for n in stale_nodes:
            success, error = self.recalculate(n)
            if success:
                recalculated.append(n)
            else:
                logger.warning(f"Failed to recalculate node {n.id}: {error}")

        return recalculated

    def _get_stale_nodes_ordered(self, node: ValueNode, visited: Set[int] = None) -> List[ValueNode]:
        """Get all stale nodes in topological order (dependencies first)."""
        if visited is None:
            visited = set()

        if node.id in visited:
            return []

        visited.add(node.id)
        result = []

        # First, process dependencies
        for dep in node.dependencies:
            result.extend(self._get_stale_nodes_ordered(dep.source_node, visited))

        # Then add this node if stale
        if node.is_stale():
            result.append(node)

        return result

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
