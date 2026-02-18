"""
Model Evaluation Service

Evaluates ModelInstances by:
1. Resolving input bindings to actual values
2. Evaluating model equations using the equation engine
3. Creating output ValueNodes with source_model_instance_id tracking

This service bridges the physics model system with the value/expression system.
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
import logging

from app.models.physics_model import ModelInstance, ModelInput, PhysicsModelVersion
from app.models.values import ValueNode, ComputationStatus, NodeType
from app.models.component import Component
from app.services.equation_engine import parse_equation, evaluate_equation, EvaluationError

logger = logging.getLogger(__name__)

# Thread-local set tracking which analyses are currently being evaluated
# Used to detect circular dependencies during #REF resolution
_evaluation_stack: set = set()


class ModelEvaluationError(Exception):
    """
    Error during model evaluation.

    Attributes:
        model_name: Name of the model being evaluated (if known)
        input_name: Name of the input that caused the error (if applicable)
        output_name: Name of the output being computed (if applicable)
        details: Additional context about the failure
    """

    def __init__(
        self,
        message: str,
        model_name: Optional[str] = None,
        input_name: Optional[str] = None,
        output_name: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        self.model_name = model_name
        self.input_name = input_name
        self.output_name = output_name
        self.details = details or {}

        # Build informative message with context
        context_parts = []
        if model_name:
            context_parts.append(f"model='{model_name}'")
        if input_name:
            context_parts.append(f"input='{input_name}'")
        if output_name:
            context_parts.append(f"output='{output_name}'")

        full_msg = message
        if context_parts:
            full_msg = f"{message} | {', '.join(context_parts)}"

        super().__init__(full_msg)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "ModelEvaluationError",
            "message": str(self.args[0]) if self.args else "Model evaluation error",
            "model_name": self.model_name,
            "input_name": self.input_name,
            "output_name": self.output_name,
            "details": self.details,
        }


class CircularDependencyError(ModelEvaluationError):
    """Raised when a circular dependency is detected between analyses."""

    def __init__(self, message: str, analysis_chain: Optional[List[str]] = None):
        self.analysis_chain = analysis_chain or []
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "error_type": "CircularDependencyError",
            "message": str(self.args[0]) if self.args else "Circular dependency",
            "analysis_chain": self.analysis_chain,
        }


def resolve_model_input(
    model_input: ModelInput,
    db: Session,
    evaluation_stack: set = None
) -> float:
    """
    Resolve a ModelInput binding to an actual float value.

    Handles:
    - source_value_node_id: Get ValueNode.computed_value
    - literal_value + literal_unit_id: Return literal (assumed already in SI)
    - source_lookup: Execute LOOKUP, #REF, #CONST, #Component.property

    Args:
        model_input: The ModelInput to resolve
        db: Database session
        evaluation_stack: Set of analysis IDs currently being evaluated (for circular detection)

    Returns:
        The resolved float value

    Raises:
        ModelEvaluationError: If the input cannot be resolved
        CircularDependencyError: If a circular reference is detected
    """
    if evaluation_stack is None:
        evaluation_stack = set()

    def _check_circular(value_node: ValueNode, input_name: str):
        """Check if resolving this ValueNode would create a circular dependency."""
        if value_node.source_model_instance_id and value_node.source_model_instance_id in evaluation_stack:
            # Get analysis names for better error message
            source_instance = db.query(ModelInstance).filter(
                ModelInstance.id == value_node.source_model_instance_id
            ).first()
            source_name = source_instance.name if source_instance else f"Analysis {value_node.source_model_instance_id}"

            raise CircularDependencyError(
                f"Circular dependency detected: Cannot use output from '{source_name}' "
                f"as it depends on the analysis currently being evaluated. "
                f"Input '{input_name}' references ValueNode {value_node.id} from '{source_name}'."
            )

    # If it's a ValueNode reference
    if model_input.source_value_node_id:
        value_node = db.query(ValueNode).filter(
            ValueNode.id == model_input.source_value_node_id
        ).first()

        if not value_node:
            raise ModelEvaluationError(
                f"ValueNode {model_input.source_value_node_id} not found for input '{model_input.input_name}'"
            )

        # Check for circular dependency
        _check_circular(value_node, model_input.input_name)

        # Get effective value (handles both literal and computed nodes)
        value, unit_id, is_valid = value_node.get_effective_value()

        if value is None:
            raise ModelEvaluationError(
                f"ValueNode {model_input.source_value_node_id} has no value for input '{model_input.input_name}'"
            )

        if not is_valid:
            logger.warning(
                f"ValueNode {model_input.source_value_node_id} has stale/invalid value for input '{model_input.input_name}'"
            )

        return float(value)

    # If it's a literal value
    if model_input.literal_value is not None:
        return float(model_input.literal_value)

    # If it's a source_lookup, resolve the expression
    if model_input.source_lookup:
        expression = model_input.source_lookup.get('expression', '')

        # Handle #REF:{valueNodeId} format for analysis-to-analysis references
        if expression.startswith('#REF:'):
            try:
                value_node_id = int(expression[5:])  # Skip "#REF:"
            except ValueError:
                raise ModelEvaluationError(
                    f"Invalid #REF format for '{model_input.input_name}': {expression}. "
                    f"Expected format: #REF:{{valueNodeId}}"
                )

            value_node = db.query(ValueNode).filter(
                ValueNode.id == value_node_id
            ).first()

            if not value_node:
                raise ModelEvaluationError(
                    f"ValueNode {value_node_id} not found for input '{model_input.input_name}'"
                )

            # Check for circular dependency
            _check_circular(value_node, model_input.input_name)

            if value_node.computed_value is None:
                raise ModelEvaluationError(
                    f"ValueNode {value_node_id} has no computed value for input '{model_input.input_name}'. "
                    f"Status: {value_node.computation_status}"
                )

            return float(value_node.computed_value)

        # Handle $CONST.name or #CONST.name for system constants
        if expression.upper().startswith('$CONST.') or expression.upper().startswith('#CONST.'):
            const_name = expression.split('.', 1)[1] if '.' in expression else ''
            if not const_name:
                raise ModelEvaluationError(
                    f"Invalid constant reference for '{model_input.input_name}': {expression}. "
                    f"Expected: $CONST.name or #CONST.name"
                )

            from app.models.resources import SystemConstant
            # Try exact name match first, then symbol, then case-insensitive
            constant = db.query(SystemConstant).filter(
                SystemConstant.name == const_name
            ).first()

            if not constant:
                constant = db.query(SystemConstant).filter(
                    SystemConstant.symbol == const_name
                ).first()

            if not constant:
                from sqlalchemy import func
                constant = db.query(SystemConstant).filter(
                    func.lower(SystemConstant.name) == const_name.lower()
                ).first()

            if not constant:
                raise ModelEvaluationError(
                    f"Constant '{const_name}' not found for input '{model_input.input_name}'"
                )

            return float(constant.value)

        # Handle #ComponentCode.PropertyName format for component property references
        if expression.startswith('#'):
            # Parse #FRAME.Length → component_code='FRAME', property_name='Length'
            ref_parts = expression[1:].split('.', 1)
            if len(ref_parts) != 2:
                raise ModelEvaluationError(
                    f"Invalid # reference format for '{model_input.input_name}': {expression}. "
                    f"Expected: #REF:{{id}} or #ComponentCode.PropertyName"
                )

            component_code, property_name = ref_parts

            # Find component by code
            component = db.query(Component).filter(
                Component.code == component_code
            ).first()

            if not component:
                raise ModelEvaluationError(
                    f"Component '{component_code}' not found for input '{model_input.input_name}'"
                )

            # Find property by name via PropertyDefinition join
            from app.models.property import ComponentProperty, PropertyDefinition
            property_obj = db.query(ComponentProperty).join(
                PropertyDefinition,
                ComponentProperty.property_definition_id == PropertyDefinition.id
            ).filter(
                ComponentProperty.component_id == component.id,
                PropertyDefinition.name == property_name
            ).first()

            if not property_obj:
                raise ModelEvaluationError(
                    f"Property '{property_name}' not found on component '{component_code}' "
                    f"for input '{model_input.input_name}'"
                )

            # Get the value - prefer ValueNode if linked, otherwise use single_value
            if property_obj.value_node_id:
                value_node = db.query(ValueNode).filter(
                    ValueNode.id == property_obj.value_node_id
                ).first()

                if value_node and value_node.computed_value is not None:
                    return float(value_node.computed_value)
                elif value_node:
                    raise ModelEvaluationError(
                        f"Property '{component_code}.{property_name}' has no computed value "
                        f"for input '{model_input.input_name}'. Status: {value_node.computation_status}"
                    )

            # Fall back to single_value on ComponentProperty
            if property_obj.single_value is not None:
                return float(property_obj.single_value)

            raise ModelEvaluationError(
                f"Property '{component_code}.{property_name}' has no value "
                f"for input '{model_input.input_name}'"
            )
        else:
            # Try to evaluate as a numeric expression (fallback for legacy bindings like 2.65*10^-8)
            try:
                from sympy import sympify, N as sym_N
                expr_py = expression.replace('^', '**')
                sym_result = sympify(expr_py)
                if sym_result.is_number:
                    return float(sym_N(sym_result))
            except Exception:
                pass
            # Other lookup types not yet supported
            raise NotImplementedError(
                f"Non-#REF lookup not implemented for input '{model_input.input_name}': {expression}"
            )

    raise ModelEvaluationError(
        f"ModelInput '{model_input.input_name}' has no valid source (no value_node, literal, or lookup)"
    )


def evaluate_model_instance(
    instance: ModelInstance,
    db: Session,
    evaluation_stack: set = None
) -> List[ValueNode]:
    """
    Evaluate a ModelInstance and create output ValueNodes.

    This is the main entry point for model evaluation. It:
    1. Gets the model version with equations
    2. Resolves all input bindings to float values
    3. Evaluates each output equation
    4. Creates ValueNode for each output with source tracking

    Args:
        instance: ModelInstance to evaluate
        db: Database session
        evaluation_stack: Set of analysis IDs currently being evaluated (for circular detection)

    Returns:
        List of created ValueNode objects (one per output)

    Raises:
        ModelEvaluationError: If evaluation fails
        CircularDependencyError: If a circular reference is detected
    """
    # Initialize evaluation stack for circular dependency detection
    if evaluation_stack is None:
        evaluation_stack = set()

    # Check if we're already evaluating this instance (direct circular ref)
    if instance.id in evaluation_stack:
        raise CircularDependencyError(
            f"Circular dependency detected: Analysis '{instance.name or instance.id}' "
            f"references itself through its dependencies."
        )

    # Add this instance to the evaluation stack
    evaluation_stack.add(instance.id)

    try:
        # Get model version
        version = instance.model_version
        if not version:
            raise ModelEvaluationError(
                f"ModelInstance {instance.id} has no associated model version"
            )

        logger.info(f"Evaluating ModelInstance {instance.id} (version {version.id})")

        # Validate inputs exist
        if not version.inputs:
            raise ModelEvaluationError(
                f"Model version {version.id} has no input schema defined"
            )

        # Build case-insensitive map of expected input names
        # Maps normalized (lowercase) name -> canonical (schema) name
        expected_inputs_map = {
            inp['name'].lower(): inp['name']
            for inp in version.inputs
        }

        # Resolve all inputs to values
        # Use canonical names from schema for consistency with equation parsing
        input_values: Dict[str, float] = {}
        for model_input in instance.inputs:
            input_name_lower = model_input.input_name.lower()
            if input_name_lower not in expected_inputs_map:
                logger.warning(
                    f"ModelInput '{model_input.input_name}' not in version schema, skipping"
                )
                continue

            # Use canonical name from schema
            canonical_name = expected_inputs_map[input_name_lower]

            try:
                value = resolve_model_input(model_input, db, evaluation_stack)
                input_values[canonical_name] = value
                logger.debug(f"  Resolved input '{canonical_name}' = {value}")
            except CircularDependencyError:
                raise  # Re-raise circular dependency errors as-is
            except Exception as e:
                raise ModelEvaluationError(
                    f"Failed to resolve input '{model_input.input_name}': {str(e)}"
                )

        # Check all required inputs are provided (case-insensitive)
        input_values_lower = {k.lower() for k in input_values.keys()}
        for inp in version.inputs:
            if inp.get('required', True) and inp['name'].lower() not in input_values_lower:
                raise ModelEvaluationError(
                    f"Required input '{inp['name']}' is not bound in instance {instance.id}"
                )

        # Get equations (support both 'equations' dict and 'outputs' with expressions)
        equations = version.equations or {}

        # Also check outputs for inline expressions
        if version.outputs:
            for output in version.outputs:
                output_name = output.get('name')
                if output_name and 'expression' in output:
                    # Inline expression in output schema
                    if output_name not in equations:
                        equations[output_name] = output['expression']

        if not equations:
            raise ModelEvaluationError(
                f"Model version {version.id} has no equations defined"
            )

        # Get existing output ValueNodes for this instance (keyed by output_name)
        # We UPDATE existing nodes instead of DELETE+INSERT to preserve FK references
        existing_nodes = {
            node.source_output_name: node
            for node in db.query(ValueNode).filter(
                ValueNode.source_model_instance_id == instance.id
            ).all()
        }

        # Evaluate each output equation
        output_nodes: List[ValueNode] = []

        for output in (version.outputs or []):
            output_name = output.get('name')
            if not output_name:
                continue

            output_unit = output.get('unit', '')

            # Get equation for this output
            equation = equations.get(output_name)
            if not equation:
                logger.warning(f"No equation for output '{output_name}', skipping")
                continue

            # Get pre-parsed AST if available
            equation_ast = None
            if version.equation_ast and output_name in version.equation_ast:
                equation_ast = version.equation_ast[output_name]

            if not equation_ast:
                # Parse equation now
                try:
                    parsed = parse_equation(equation, allowed_inputs=list(input_values.keys()))
                    equation_ast = parsed['ast']
                except Exception as e:
                    raise ModelEvaluationError(
                        f"Failed to parse equation for output '{output_name}': {str(e)}"
                    )

            # Evaluate
            try:
                result = evaluate_equation(equation_ast, input_values)
                logger.debug(f"  Evaluated output '{output_name}' = {result}")
            except EvaluationError as e:
                raise ModelEvaluationError(
                    f"Evaluation failed for output '{output_name}': {str(e)}"
                )

            # Update existing ValueNode or create new one
            if output_name in existing_nodes:
                # UPDATE existing node (preserves ID for FK references)
                value_node = existing_nodes[output_name]
                value_node.numeric_value = result
                value_node.computed_value = result
                value_node.computed_unit_symbol = output_unit
                value_node.computation_status = ComputationStatus.VALID
                value_node.last_computed = datetime.utcnow()
            else:
                # CREATE new node
                value_node = ValueNode(
                    node_type=NodeType.LITERAL,  # Computed results are stored as literals
                    numeric_value=result,
                    computed_value=result,
                    computed_unit_symbol=output_unit,
                    computation_status=ComputationStatus.VALID,
                    last_computed=datetime.utcnow(),
                    source_model_instance_id=instance.id,
                    source_output_name=output_name,
                    description=f"Model output: {output_name}"
                )
                db.add(value_node)

            output_nodes.append(value_node)

        # Update instance status
        instance.last_computed = datetime.utcnow()
        instance.computation_status = ComputationStatus.VALID
        instance.error_message = None  # Clear any previous error message

        db.flush()  # Get IDs for value_nodes

        logger.info(f"Created {len(output_nodes)} output ValueNodes for instance {instance.id}")

        return output_nodes

    except Exception as e:
        # On any evaluation error, mark instance and output nodes as ERROR
        logger.error(f"Evaluation failed for instance {instance.id}: {e}")

        instance.computation_status = ComputationStatus.ERROR
        instance.last_computed = datetime.utcnow()
        
        # Store detailed error message for user diagnostics
        if isinstance(e, ModelEvaluationError):
            # Use the full context from ModelEvaluationError
            error_msg = str(e)
        elif isinstance(e, CircularDependencyError):
            error_msg = f"Circular dependency: {str(e)}"
        else:
            # Generic error - capture type and message
            error_msg = f"{type(e).__name__}: {str(e)}"
        
        instance.error_message = error_msg

        # Mark existing output nodes as ERROR (don't delete them - preserve FK refs)
        existing_outputs = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance.id
        ).all()
        for node in existing_outputs:
            node.computation_status = ComputationStatus.ERROR

        db.flush()

        # Re-raise the exception so caller knows evaluation failed
        raise

    finally:
        # Always remove from evaluation stack when done (success or failure)
        evaluation_stack.discard(instance.id)


def create_component_properties_for_outputs(
    instance: ModelInstance,
    output_nodes: List[ValueNode],
    db: Session
) -> List[Any]:
    """
    Create ComponentProperty records for model outputs.

    If the instance is attached to a component, creates properties like:
    #COMPONENT.thermal_expansion

    Args:
        instance: The ModelInstance
        output_nodes: ValueNodes created by evaluate_model_instance
        db: Database session

    Returns:
        List of created ComponentProperty objects
    """
    if not instance.component_id:
        return []

    from app.models.property import ComponentProperty, PropertyDefinition, PropertyType

    component = db.query(Component).filter(
        Component.id == instance.component_id
    ).first()

    if not component:
        raise ModelEvaluationError(f"Component {instance.component_id} not found")

    properties = []
    version = instance.model_version

    for output_node in output_nodes:
        output_name = output_node.source_output_name
        if not output_name:
            continue

        # Find output definition to get unit
        output_def = next(
            (o for o in (version.outputs or []) if o.get('name') == output_name),
            None
        )

        output_unit = output_def.get('unit', '') if output_def else ''

        # Check if PropertyDefinition already exists
        prop_def = db.query(PropertyDefinition).filter(
            PropertyDefinition.name == output_name
        ).first()

        if not prop_def:
            # Create new PropertyDefinition
            prop_def = PropertyDefinition(
                name=output_name,
                property_type=PropertyType.OTHER,  # Default type for model outputs
                unit=output_unit,
                description=f"Model output: {output_name}",
                is_custom=True
            )
            db.add(prop_def)
            db.flush()

        # Check if ComponentProperty already exists
        existing_prop = db.query(ComponentProperty).filter(
            ComponentProperty.component_id == instance.component_id,
            ComponentProperty.property_definition_id == prop_def.id
        ).first()

        if existing_prop:
            # Update existing property to point to new value node
            existing_prop.value_node_id = output_node.id
            existing_prop.single_value = output_node.computed_value
            existing_prop.updated_at = datetime.utcnow()
            properties.append(existing_prop)
        else:
            # Create new ComponentProperty
            comp_prop = ComponentProperty(
                component_id=instance.component_id,
                property_definition_id=prop_def.id,
                value_node_id=output_node.id,
                single_value=output_node.computed_value
            )
            db.add(comp_prop)
            properties.append(comp_prop)

    db.flush()
    return properties


def evaluate_and_attach(
    instance: ModelInstance,
    db: Session
) -> Dict[str, Any]:
    """
    Evaluate model instance and create component properties if attached.

    This is a convenience function that:
    1. Evaluates the model instance
    2. Creates component properties for outputs (if attached to a component)
    3. Returns structured result with references

    Args:
        instance: The ModelInstance to evaluate
        db: Database session

    Returns:
        Dict with:
        - output_nodes: List of ValueNode objects
        - properties: List of ComponentProperty objects (if attached)
        - references: List of reference strings (e.g., "#SYSTEM.thermal_expansion")
    """
    output_nodes = evaluate_model_instance(instance, db)
    properties = create_component_properties_for_outputs(instance, output_nodes, db)

    # Build reference strings
    references = []
    if instance.component:
        component_code = instance.component.code
        for node in output_nodes:
            if node.source_output_name:
                references.append(f"#{component_code}.{node.source_output_name}")

    return {
        "output_nodes": output_nodes,
        "properties": properties,
        "references": references
    }


def get_instance_outputs(
    instance: ModelInstance,
    db: Session
) -> List[ValueNode]:
    """
    Get existing output ValueNodes for a ModelInstance.

    Useful for retrieving previously computed outputs without re-evaluating.

    Args:
        instance: The ModelInstance
        db: Database session

    Returns:
        List of ValueNode objects that are outputs of this instance
    """
    return db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == instance.id
    ).all()


def invalidate_instance_outputs(
    instance: ModelInstance,
    db: Session
) -> int:
    """
    Mark all output ValueNodes for a ModelInstance as stale.

    Called when input bindings change and outputs need recalculation.

    Args:
        instance: The ModelInstance
        db: Database session

    Returns:
        Number of nodes marked stale
    """
    count = 0
    outputs = get_instance_outputs(instance, db)

    for node in outputs:
        if node.computation_status == ComputationStatus.VALID:
            node.computation_status = ComputationStatus.STALE
            count += 1

    instance.computation_status = ComputationStatus.STALE
    db.flush()

    return count


def evaluate_inline_model(
    model_name: str,
    bindings: Dict[str, float],
    output_name: Optional[str],
    db: Session
) -> float:
    """
    Evaluate a model inline without creating a ModelInstance record.

    This function is used by the MODEL() expression function to evaluate
    physics models directly within property expressions.

    Args:
        model_name: Name of the physics model (case-insensitive)
        bindings: Dict of input_name -> value (already resolved to floats)
        output_name: Which output to return (required for multi-output models)
        db: Database session

    Returns:
        Computed value for the specified output

    Raises:
        ModelEvaluationError: If model not found, inputs missing, or evaluation fails

    Example:
        result = evaluate_inline_model(
            model_name="Thermal Expansion",
            bindings={"CTE": 2.3e-5, "delta_T": 100, "L0": 1.0},
            output_name="delta_L",
            db=db
        )
        # Returns: 0.0023
    """
    from app.models.physics_model import PhysicsModel

    # 1. Look up model by name (case-insensitive)
    model = PhysicsModel.find_by_name(db, model_name)

    if not model:
        raise ModelEvaluationError(f"Model '{model_name}' not found")

    # 2. Get current version
    version = model.current_version
    if not version:
        raise ModelEvaluationError(f"Model '{model_name}' has no current version")

    # 3. Validate all required inputs are provided (case-insensitive)
    # Also normalize bindings to use canonical names from schema
    normalized_bindings = {}
    if version.inputs:
        # Build case-insensitive map: lowercase -> canonical name
        input_name_map = {
            inp.get('name', '').lower(): inp.get('name')
            for inp in version.inputs
        }

        # Normalize provided bindings to use canonical names
        for key, value in bindings.items():
            canonical = input_name_map.get(key.lower())
            if canonical:
                normalized_bindings[canonical] = value
            else:
                normalized_bindings[key] = value

        required_inputs = {
            inp.get('name') for inp in version.inputs
            if inp.get('required', True)
        }
        provided_lower = {k.lower() for k in normalized_bindings.keys()}

        missing = {r for r in required_inputs if r.lower() not in provided_lower}
        if missing:
            raise ModelEvaluationError(
                f"Model '{model_name}' missing required inputs: {', '.join(sorted(missing))}"
            )
    else:
        normalized_bindings = bindings

    # 4. Build equations dict (support both 'equations' dict and 'outputs' with expressions)
    equations = version.equations or {}

    # Also check outputs for inline expressions
    if version.outputs:
        for output in version.outputs:
            out_name = output.get('name')
            if out_name and 'expression' in output:
                if out_name not in equations:
                    equations[out_name] = output['expression']

    if not equations:
        raise ModelEvaluationError(
            f"Model '{model_name}' version {version.version} has no equations defined"
        )

    # 5. Determine which output to return
    output_keys = list(equations.keys())

    if output_name:
        # Specific output requested
        if output_name not in equations:
            raise ModelEvaluationError(
                f"Model '{model_name}' has no output '{output_name}'. "
                f"Available outputs: {', '.join(output_keys)}"
            )
        target_output = output_name
    else:
        # No output specified - use first/only output
        if len(output_keys) > 1:
            raise ModelEvaluationError(
                f"Model '{model_name}' has multiple outputs: {', '.join(output_keys)}. "
                f"Specify which using: output: \"name\""
            )
        target_output = output_keys[0]

    # 6. Get equation AST for target output (prefer pre-parsed, fall back to parsing)
    equation_ast = None
    if version.equation_ast and target_output in version.equation_ast:
        equation_ast = version.equation_ast[target_output]

    if not equation_ast:
        # Parse equation now
        equation_text = equations[target_output]
        try:
            parsed = parse_equation(equation_text, allowed_inputs=list(normalized_bindings.keys()))
            equation_ast = parsed['ast']
        except Exception as e:
            raise ModelEvaluationError(
                f"Failed to parse equation for output '{target_output}': {str(e)}"
            )

    # 7. Evaluate equation with normalized bindings
    try:
        result = evaluate_equation(equation_ast, normalized_bindings)
        logger.debug(
            f"evaluate_inline_model('{model_name}', output='{target_output}'): "
            f"inputs={bindings} -> {result}"
        )
        return result
    except EvaluationError as e:
        raise ModelEvaluationError(
            f"Evaluation failed for model '{model_name}' output '{target_output}': {str(e)}"
        )
