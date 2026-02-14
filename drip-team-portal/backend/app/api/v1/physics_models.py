"""
Physics Models API - CRUD endpoints for physics model templates and instances.

Provides:
- List/Get physics models with versions
- Validate model equations (dimensional analysis)
- Create new physics models
- Create model instances with input bindings
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json
import re

from app.db.database import get_db
from app.models.physics_model import (
    PhysicsModel,
    PhysicsModelVersion,
    ModelInstance,
    ModelInput,
)
from app.services.equation_engine import (
    parse_equation,
    generate_latex,
    EquationParseError,
    UnknownInputError,
)
from app.services.dimensional_analysis import (
    UNIT_DIMENSIONS,
    validate_equation_dimensions,
    DimensionError,
)
from app.services.model_evaluation import (
    evaluate_and_attach,
    ModelEvaluationError,
    CircularDependencyError,
)
from app.services.websocket_manager import manager as ws_manager

router = APIRouter(prefix="/api/v1")


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class InputSchema(BaseModel):
    name: str
    unit: Optional[str] = None
    dimension: Optional[str] = None  # Frontend sends this
    required: bool = True
    description: Optional[str] = None

    class Config:
        extra = "ignore"  # Ignore extra fields from frontend


class OutputSchema(BaseModel):
    name: str
    unit: Optional[str] = None
    dimension: Optional[str] = None  # Frontend sends this
    description: Optional[str] = None

    class Config:
        extra = "ignore"


class EquationSchema(BaseModel):
    """Frontend sends equations as array of {output_name, expression}"""
    output_name: str
    expression: str


class ModelValidateRequest(BaseModel):
    inputs: List[InputSchema]
    outputs: List[OutputSchema]
    # Accept both formats: dict {"name": "expr"} or list [{output_name, expression}]
    equations: List[EquationSchema] | dict


class ModelCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: str
    inputs: List[InputSchema]
    outputs: List[OutputSchema]
    # Accept both formats: dict {"name": "expr"} or list [{output_name, expression}]
    equations: List[EquationSchema] | dict


class InstanceCreateRequest(BaseModel):
    name: str
    model_version_id: int
    target_component_id: Optional[int] = None
    bindings: dict  # {"input_name": "binding_expression"}


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def normalize_equations(equations: List[EquationSchema] | dict) -> dict:
    """
    Convert equations from list format to dict format.

    Frontend sends: [{"output_name": "y", "expression": "x*2"}]
    Backend needs:  {"y": "x*2"}
    """
    if isinstance(equations, dict):
        return equations

    # Convert list of EquationSchema to dict
    return {eq.output_name: eq.expression for eq in equations}


def parse_binding_value(binding_expr: str) -> dict:
    """
    Parse a binding expression to determine its type and value.

    Returns a dict with binding info:
    - {"type": "literal", "value": 123.45} for numeric literals
    - {"type": "value_node", "node_id": 77} for direct ValueNode refs (#REF:77, #NODE:77)
    - {"type": "lookup", "expression": "..."} for LOOKUP expressions
    - {"type": "reference", "expression": "..."} for property references (#COMP.prop)
    """
    if not binding_expr:
        return {"type": "empty", "value": None}

    # Trim whitespace
    expr = str(binding_expr).strip()

    # Try to parse as a number (including scientific notation)
    try:
        value = float(expr)
        return {"type": "literal", "value": value}
    except ValueError:
        pass

    # Check for direct ValueNode reference: #REF:77 or #NODE:77
    # This enables analysis-to-analysis chaining
    node_match = re.match(r'^#(?:REF|NODE):(\d+)$', expr, re.IGNORECASE)
    if node_match:
        return {"type": "value_node", "node_id": int(node_match.group(1))}

    # Check for LOOKUP expression
    if expr.upper().startswith("LOOKUP("):
        return {"type": "lookup", "expression": expr}

    # Check for property reference (e.g., #COMPONENT.prop or $CONST.name)
    if expr.startswith("#") or expr.startswith("$"):
        return {"type": "reference", "expression": expr}

    # Default: treat as expression (could be a formula or unknown format)
    return {"type": "expression", "expression": expr}


# =============================================================================
# LIST / GET ENDPOINTS
# =============================================================================

@router.get("/physics-models")
async def list_physics_models(
    category: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    List all physics models with their current versions.

    Optional filter by category (thermal, mechanical, fluid, electrical).
    """
    query = db.query(PhysicsModel)
    if category:
        query = query.filter(PhysicsModel.category == category)

    models = query.all()

    result = []
    for model in models:
        # Get current version
        current_version = next(
            (v for v in model.versions if v.is_current),
            None
        )

        # Include inputs/outputs at top level for frontend convenience
        result.append({
            "id": model.id,
            "name": model.name,
            "description": model.description,
            "category": model.category,
            "created_at": model.created_at.isoformat() if model.created_at else None,
            # Top-level fields for frontend convenience
            "inputs": current_version.inputs if current_version else [],
            "outputs": current_version.outputs if current_version else [],
            "version_id": current_version.id if current_version else None,  # For model instance creation
            "current_version": {
                "id": current_version.id,
                "version": current_version.version,
                "inputs": current_version.inputs,
                "outputs": current_version.outputs,
                "equations": current_version.equations
            } if current_version else None
        })

    return result


@router.get("/physics-models/categories")
async def list_categories():
    """
    List available physics model categories.
    """
    return {
        "categories": [
            {"id": "thermal", "name": "Thermal", "description": "Heat transfer, thermal expansion"},
            {"id": "mechanical", "name": "Mechanical", "description": "Stress, strain, deformation"},
            {"id": "fluid", "name": "Fluid Dynamics", "description": "Flow, pressure drop"},
            {"id": "electrical", "name": "Electrical", "description": "Circuits, resistance"},
            {"id": "acoustic", "name": "Acoustic", "description": "Sound, vibration"},
            {"id": "optical", "name": "Optical", "description": "Light, refraction"},
        ]
    }


@router.get("/physics-models/{model_id}")
async def get_physics_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single physics model with all its versions.
    """
    model = db.query(PhysicsModel).filter(PhysicsModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    current_version = next((v for v in model.versions if v.is_current), None)

    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "category": model.category,
        "created_by": model.created_by,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        # Top-level fields for frontend convenience
        "inputs": current_version.inputs if current_version else [],
        "outputs": current_version.outputs if current_version else [],
        "version_id": current_version.id if current_version else None,  # For model instance creation
        "versions": [{
            "id": v.id,
            "version": v.version,
            "is_current": v.is_current,
            "inputs": v.inputs,
            "outputs": v.outputs,
            "equations": v.equations,
            "equation_latex": v.equation_latex,
            "created_at": v.created_at.isoformat() if v.created_at else None
        } for v in model.versions],
        "current_version": {
            "id": current_version.id,
            "version": current_version.version,
            "inputs": current_version.inputs,
            "outputs": current_version.outputs,
            "equations": current_version.equations,
            "equation_latex": current_version.equation_latex
        } if current_version else None
    }


@router.get("/physics-models/by-name/{model_name:path}")
async def get_physics_model_by_name(
    model_name: str,
    db: Session = Depends(get_db)
):
    """
    Get a physics model by name (case-insensitive).

    Used internally by MODEL() function evaluation for fast lookup.
    Also useful for debugging and testing.

    Args:
        model_name: Name of the model (case-insensitive match)

    Returns:
        Model with current version and all metadata needed for evaluation.

    Raises:
        404 if model not found
    """
    model = db.query(PhysicsModel).filter(
        func.lower(PhysicsModel.name) == model_name.lower()
    ).first()

    if not model:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found"
        )

    current_version = next((v for v in model.versions if v.is_current), None)

    if not current_version:
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' has no current version"
        )

    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "category": model.category,
        "created_at": model.created_at.isoformat() if model.created_at else None,
        "current_version": {
            "id": current_version.id,
            "version": current_version.version,
            "inputs": current_version.inputs,
            "outputs": current_version.outputs,
            "equations": current_version.equations,
            "equation_ast": current_version.equation_ast,
            "equation_latex": current_version.equation_latex
        }
    }


class ModelUpdateRequest(BaseModel):
    """Request body for updating a physics model."""
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    inputs: Optional[List[InputSchema]] = None
    outputs: Optional[List[OutputSchema]] = None
    equations: Optional[List[EquationSchema] | dict] = None


@router.patch("/physics-models/{model_id}")
async def update_physics_model(
    model_id: int,
    data: ModelUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update a physics model.

    Updates name/category/description on the model itself.
    If inputs/outputs/equations change, creates a new version.
    """
    model = db.query(PhysicsModel).filter(PhysicsModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    # Update model metadata
    if data.name is not None:
        # Check for name conflicts
        existing = db.query(PhysicsModel).filter(
            PhysicsModel.name == data.name,
            PhysicsModel.id != model_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Model with name '{data.name}' already exists"
            )
        model.name = data.name

    if data.category is not None:
        model.category = data.category

    if data.description is not None:
        model.description = data.description

    # Check if structure changed (inputs/outputs/equations)
    current_version = next((v for v in model.versions if v.is_current), None)

    structure_changed = False
    new_inputs = None
    new_outputs = None
    new_equations = None

    if data.inputs is not None:
        new_inputs = [inp.model_dump() for inp in data.inputs]
        structure_changed = True

    if data.outputs is not None:
        new_outputs = [out.model_dump() for out in data.outputs]
        structure_changed = True

    if data.equations is not None:
        new_equations = normalize_equations(data.equations)
        structure_changed = True

    if structure_changed and current_version:
        # Use existing values for unchanged fields
        final_inputs = new_inputs if new_inputs is not None else current_version.inputs
        final_outputs = new_outputs if new_outputs is not None else current_version.outputs
        final_equations = new_equations if new_equations is not None else current_version.equations

        # Parse equations and generate AST/LaTeX
        input_names = [inp['name'] for inp in final_inputs]
        equations_ast = {}
        equations_latex = {}

        for output in final_outputs:
            output_name = output['name']
            equation = final_equations.get(output_name, '')

            if equation:
                try:
                    parsed = parse_equation(equation, allowed_inputs=input_names)
                    equations_ast[output_name] = parsed['ast']
                    equations_latex[output_name] = generate_latex(parsed)
                except (EquationParseError, UnknownInputError) as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Error parsing equation for '{output_name}': {str(e)}"
                    )

        # Mark current version as not current
        current_version.is_current = False

        # Create new version
        new_version = PhysicsModelVersion(
            physics_model_id=model.id,
            version=current_version.version + 1,
            is_current=True,
            inputs=final_inputs,
            outputs=final_outputs,
            equations=final_equations,
            equation_ast=equations_ast,
            equation_latex=json.dumps(equations_latex),
            created_by="system"
        )
        db.add(new_version)

    db.commit()
    db.refresh(model)

    # Get updated current version
    updated_version = next((v for v in model.versions if v.is_current), None)

    return {
        "id": model.id,
        "name": model.name,
        "description": model.description,
        "category": model.category,
        "inputs": updated_version.inputs if updated_version else [],
        "outputs": updated_version.outputs if updated_version else [],
        "current_version": {
            "id": updated_version.id,
            "version": updated_version.version,
            "inputs": updated_version.inputs,
            "outputs": updated_version.outputs,
            "equations": updated_version.equations,
            "equation_latex": updated_version.equation_latex
        } if updated_version else None
    }


@router.delete("/physics-models/{model_id}")
async def delete_physics_model(
    model_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a physics model and all its versions.

    WARNING: Cannot delete if any instances are using this model.
    """
    # Check if model exists
    model = db.query(PhysicsModel).filter(PhysicsModel.id == model_id).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")

    model_name = model.name  # Save for response message

    # Check if any instances use this model (via versions)
    instances_using_model = db.query(ModelInstance).join(
        PhysicsModelVersion,
        ModelInstance.model_version_id == PhysicsModelVersion.id
    ).filter(
        PhysicsModelVersion.physics_model_id == model_id
    ).count()

    if instances_using_model > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete model '{model_name}': {instances_using_model} instance(s) are using this model. Delete instances first."
        )

    # Safe to delete - no instances using it

    # Delete all versions first (foreign key constraint)
    db.query(PhysicsModelVersion).filter(
        PhysicsModelVersion.physics_model_id == model_id
    ).delete()

    # Delete the model
    db.delete(model)
    db.commit()

    return {
        "success": True,
        "message": f"Successfully deleted model '{model_name}' and all its versions"
    }


# =============================================================================
# VALIDATION ENDPOINT
# =============================================================================

@router.post("/physics-models/validate")
async def validate_physics_model(data: ModelValidateRequest):
    """
    Validate model equations before creation.

    Checks:
    - Equation parsing (syntax)
    - Input reference validation (all inputs exist)
    - Dimensional analysis (units are consistent)

    Called by ModelBuilder Step 4 before final creation.
    """
    errors = []
    dimensional_results = {}
    parsed_equations = {}

    # Normalize equations to dict format
    equations_dict = normalize_equations(data.equations)

    # Get allowed input names
    input_names = {inp.name for inp in data.inputs}

    # Parse and validate each equation
    for output in data.outputs:
        output_name = output.name
        equation = equations_dict.get(output_name)

        if not equation:
            errors.append(f"Missing equation for output '{output_name}'")
            continue

        # Parse equation
        try:
            parsed = parse_equation(equation, allowed_inputs=list(input_names))
            parsed_equations[output_name] = parsed
        except EquationParseError as e:
            errors.append(f"Parse error in '{output_name}': {str(e)}")
            continue
        except UnknownInputError as e:
            errors.append(f"Unknown input in '{output_name}': {str(e)}")
            continue

        # Validate dimensions
        try:
            input_dims = {}
            for inp in data.inputs:
                unit = inp.unit
                if unit and unit in UNIT_DIMENSIONS:
                    input_dims[inp.name] = UNIT_DIMENSIONS[unit]

            output_unit = output.unit
            expected_dim = UNIT_DIMENSIONS.get(output_unit) if output_unit else None

            # BUGFIX Issue-04: Always validate if output has dimensional expectations
            # Previously: if expected_dim and input_dims: (skipped when input_dims was {})
            # Now: Always validate when expected_dim exists, let validation catch undefined inputs
            if expected_dim:
                is_valid, error_msg = validate_equation_dimensions(
                    parsed['ast'],
                    input_dims,
                    expected_dim
                )

                dimensional_results[output_name] = {
                    "valid": is_valid,
                    "message": error_msg if not is_valid else "Dimensions valid"
                }

                if not is_valid:
                    errors.append(f"Dimension error in '{output_name}': {error_msg}")
            else:
                # Output has no unit specified - skip dimensional validation
                # This is acceptable for truly dimensionless outputs
                dimensional_results[output_name] = {
                    "valid": True,
                    "message": "Dimensions not checked (no output unit specified)"
                }
        except DimensionError as e:
            errors.append(f"Dimension validation error in '{output_name}': {str(e)}")
            dimensional_results[output_name] = {
                "valid": False,
                "message": str(e)
            }
        except Exception as e:
            errors.append(f"Validation error in '{output_name}': {str(e)}")

    # Generate LaTeX preview for parsed equations
    latex_preview = {}
    for output_name, parsed in parsed_equations.items():
        try:
            latex_preview[output_name] = generate_latex(parsed)
        except Exception:
            latex_preview[output_name] = equations_dict.get(output_name, "")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "dimensional_analysis": dimensional_results,
        "latex_preview": latex_preview
    }


# =============================================================================
# CREATE ENDPOINTS
# =============================================================================

@router.post("/physics-models")
async def create_physics_model(
    data: ModelCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new physics model with version 1.

    Should be called after validation passes.
    """
    # Normalize equations to dict format
    equations_dict = normalize_equations(data.equations)

    # Get allowed input names
    input_names = [inp.name for inp in data.inputs]

    # Parse equations and generate AST/LaTeX
    equations_ast = {}
    equations_latex = {}

    for output in data.outputs:
        output_name = output.name
        equation = equations_dict.get(output_name)

        if not equation:
            raise HTTPException(
                status_code=400,
                detail=f"Missing equation for output '{output_name}'"
            )

        try:
            parsed = parse_equation(equation, allowed_inputs=input_names)
            equations_ast[output_name] = parsed['ast']
            equations_latex[output_name] = generate_latex(parsed)
        except (EquationParseError, UnknownInputError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"Error parsing equation for '{output_name}': {str(e)}"
            )

    # Convert Pydantic models to dicts for JSON storage
    inputs_json = [inp.model_dump() for inp in data.inputs]
    outputs_json = [out.model_dump() for out in data.outputs]

    # Create model
    model = PhysicsModel(
        name=data.name,
        description=data.description,
        category=data.category,
        created_by="system"  # TODO: Get from current user
    )

    # Create version 1
    version = PhysicsModelVersion(
        version=1,
        is_current=True,
        inputs=inputs_json,
        outputs=outputs_json,
        equations=equations_dict,  # Store as dict format
        equation_ast=equations_ast,
        equation_latex=json.dumps(equations_latex),  # Serialize to JSON string for Text column
        created_by="system"
    )

    model.versions.append(version)
    db.add(model)
    db.commit()
    db.refresh(model)

    return {
        "id": model.id,
        "name": model.name,
        "category": model.category,
        "current_version": {
            "id": version.id,
            "version": version.version,
            "equation_latex": version.equation_latex
        }
    }


@router.post("/model-instances")
async def create_model_instance(
    data: InstanceCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a model instance with input bindings.

    Called by InstanceCreator after user binds inputs.

    NOTE: This endpoint creates the instance structure.
    Instance 2's model evaluation service will be called to compute outputs.
    """
    # Get model version
    version = db.query(PhysicsModelVersion).filter(
        PhysicsModelVersion.id == data.model_version_id
    ).first()

    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    # Validate that all required inputs have bindings
    required_inputs = [
        inp['name'] for inp in (version.inputs or [])
        if inp.get('required', True)
    ]
    missing_inputs = [
        name for name in required_inputs
        if name not in data.bindings
    ]

    if missing_inputs:
        raise HTTPException(
            status_code=400,
            detail=f"Missing bindings for required inputs: {missing_inputs}"
        )

    # Create instance
    instance = ModelInstance(
        model_version_id=data.model_version_id,
        component_id=data.target_component_id,
        name=data.name,
        created_by="system"  # TODO: Get from current user
    )

    # Create inputs with proper binding type detection
    for input_name, binding_expr in data.bindings.items():
        parsed = parse_binding_value(binding_expr)

        model_input = ModelInput(input_name=input_name)

        if parsed["type"] == "literal":
            # Store as literal value (ready for evaluation)
            model_input.literal_value = parsed["value"]
        elif parsed["type"] == "value_node":
            # Direct ValueNode binding - enables analysis-to-analysis chaining
            model_input.source_value_node_id = parsed["node_id"]
        elif parsed["type"] in ("lookup", "reference", "expression"):
            # Store as source_lookup for later resolution
            model_input.source_lookup = {"expression": parsed.get("expression", binding_expr)}
        else:
            # Empty or unknown - store original as lookup
            model_input.source_lookup = {"expression": str(binding_expr)}

        instance.inputs.append(model_input)

    db.add(instance)
    db.flush()  # Get instance ID before evaluation

    # Evaluate the model and create output ValueNodes
    output_nodes = []
    evaluation_error = None

    try:
        result = evaluate_and_attach(instance, db)
        output_nodes = result.get("output_nodes", [])
    except ModelEvaluationError as e:
        evaluation_error = str(e)
        # Don't fail creation, just log the error
        import logging
        logging.warning(f"Model evaluation failed for instance {instance.id}: {e}")
    except Exception as e:
        evaluation_error = f"Unexpected error: {str(e)}"
        import logging
        logging.error(f"Unexpected evaluation error for instance {instance.id}: {e}")

    db.commit()
    db.refresh(instance)

    # Build response with output nodes
    response = {
        "id": instance.id,
        "name": instance.name,
        "model_version_id": instance.model_version_id,
        "component_id": instance.component_id,
        "is_analysis": instance.component_id is None,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "inputs": [
            {
                "input_name": inp.input_name,
                "literal_value": inp.literal_value,
                "source_lookup": inp.source_lookup,
            }
            for inp in instance.inputs
        ],
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }

    if evaluation_error:
        response["evaluation_error"] = evaluation_error

    # Broadcast via WebSocket if this is an analysis (no component_id)
    if instance.component_id is None:
        import asyncio
        asyncio.create_task(ws_manager.broadcast_analysis_update(
            instance.id, "created", response
        ))

    return response


@router.get("/model-instances/{instance_id}")
async def get_model_instance(
    instance_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a model instance with its inputs and output values.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == instance_id
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Model instance not found")

    # Query output ValueNodes for this instance
    output_nodes = db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == instance_id
    ).all()

    return {
        "id": instance.id,
        "name": instance.name,
        "model_version_id": instance.model_version_id,
        "component_id": instance.component_id,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "computation_status": instance.computation_status.value if instance.computation_status else None,
        "error_message": instance.error_message,
        "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "inputs": [
            {
                "input_name": inp.input_name,
                "source_value_node_id": inp.source_value_node_id,
                "source_lookup": inp.source_lookup,
                "literal_value": inp.literal_value,
                "literal_unit_id": inp.literal_unit_id,
            }
            for inp in instance.inputs
        ],
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }


# =============================================================================
# ANALYSIS CRUD ENDPOINTS (Named Model Instances)
# =============================================================================

class AnalysisCreateRequest(BaseModel):
    """Request body for creating a new analysis."""
    name: str
    model_version_id: int
    description: Optional[str] = None
    bindings: dict = {}  # {"input_name": "value"}


class AnalysisUpdateRequest(BaseModel):
    """Request body for updating an analysis."""
    name: Optional[str] = None
    description: Optional[str] = None
    bindings: Optional[dict] = None  # Optional: update input bindings


@router.post("/analyses")
async def create_analysis(
    data: AnalysisCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a named analysis instance.

    An analysis is a model instance without a component_id.
    Names must be unique among analyses.
    """
    from app.models.values import ValueNode, ComputationStatus
    import logging

    # Validate name
    if not data.name or not data.name.strip():
        raise HTTPException(status_code=400, detail="Analysis name is required")

    # Validate model version exists
    version = db.query(PhysicsModelVersion).filter(
        PhysicsModelVersion.id == data.model_version_id
    ).first()
    if not version:
        raise HTTPException(status_code=404, detail="Model version not found")

    # Check name uniqueness (analyses only - where component_id is NULL)
    existing = db.query(ModelInstance).filter(
        ModelInstance.name == data.name.strip(),
        ModelInstance.component_id.is_(None)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Analysis name '{data.name}' already exists"
        )

    # Validate required inputs have bindings
    required_inputs = [
        inp['name'] for inp in (version.inputs or [])
        if inp.get('required', True)
    ]
    missing_inputs = [
        name for name in required_inputs
        if name not in data.bindings
    ]
    if missing_inputs:
        raise HTTPException(
            status_code=400,
            detail=f"Missing bindings for required inputs: {missing_inputs}"
        )

    # Create analysis instance
    instance = ModelInstance(
        model_version_id=data.model_version_id,
        name=data.name.strip(),
        description=data.description,
        component_id=None,  # Analysis, not component-attached
        created_by="system"  # TODO: Get from current user
    )
    db.add(instance)
    db.flush()  # Get instance ID

    # Add input bindings via relationship (so evaluator sees them immediately)
    for input_name, binding_expr in data.bindings.items():
        parsed = parse_binding_value(binding_expr)

        model_input = ModelInput(input_name=input_name)

        if parsed["type"] == "literal":
            model_input.literal_value = parsed["value"]
        elif parsed["type"] == "value_node":
            # Direct ValueNode binding - enables analysis-to-analysis chaining
            model_input.source_value_node_id = parsed["node_id"]
        elif parsed["type"] in ("lookup", "reference", "expression"):
            model_input.source_lookup = {"expression": parsed.get("expression", binding_expr)}
        else:
            model_input.source_lookup = {"expression": str(binding_expr)}

        instance.inputs.append(model_input)  # Appends to relationship, auto-sets FK

    # Evaluate and create output ValueNodes
    output_nodes = []
    evaluation_error = None
    try:
        result = evaluate_and_attach(instance, db)
        output_nodes = result.get("output_nodes", [])
    except ModelEvaluationError as e:
        evaluation_error = str(e)
        logging.warning(f"Evaluation failed for new analysis: {e}")
    except Exception as e:
        evaluation_error = f"Unexpected error: {str(e)}"
        logging.error(f"Unexpected evaluation error: {e}")

    db.commit()
    db.refresh(instance)

    # Build response
    response_data = {
        "id": instance.id,
        "name": instance.name,
        "description": instance.description,
        "model_version_id": instance.model_version_id,
        "component_id": None,
        "is_analysis": True,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "created_by": instance.created_by,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "computation_status": instance.computation_status.value if instance.computation_status else None,
        "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
        "inputs": [
            {
                "input_name": inp.input_name,
                "literal_value": inp.literal_value,
                "source_lookup": inp.source_lookup,
            }
            for inp in instance.inputs
        ],
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }

    if evaluation_error:
        response_data["evaluation_error"] = evaluation_error

    # Broadcast creation via WebSocket
    import asyncio
    asyncio.create_task(ws_manager.broadcast_analysis_update(
        instance.id, "created", response_data
    ))

    return response_data


@router.get("/analyses")
async def list_analyses(
    db: Session = Depends(get_db)
):
    """
    List all analyses (model instances where component_id IS NULL).

    Analyses are standalone model instances that can be referenced by name.
    """
    from app.models.values import ValueNode

    instances = db.query(ModelInstance).filter(
        ModelInstance.component_id.is_(None)
    ).order_by(ModelInstance.created_at.desc()).all()

    result = []
    for instance in instances:
        # Get output nodes for this instance
        output_nodes = db.query(ValueNode).filter(
            ValueNode.source_model_instance_id == instance.id
        ).all()

        # Get model info and input schema for units
        model_info = None
        input_units = {}  # Map input_name -> unit
        if instance.model_version:
            model_info = {
                "id": instance.model_version.physics_model_id,
                "name": instance.model_version.physics_model.name if instance.model_version.physics_model else None,
                "version": instance.model_version.version,
            }
            # Build unit lookup from model inputs schema
            model_inputs = instance.model_version.inputs or []
            for inp_schema in model_inputs:
                if isinstance(inp_schema, dict):
                    input_units[inp_schema.get("name", "")] = inp_schema.get("unit", "")

        result.append({
            "id": instance.id,
            "name": instance.name,
            "description": instance.description,
            "model_version_id": instance.model_version_id,
            "model": model_info,
            "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
            "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
            "computation_status": instance.computation_status.value if instance.computation_status else None,
            "error_message": instance.error_message,
            "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
            "created_by": instance.created_by,
            "inputs": [
                {
                    "input_name": inp.input_name,
                    "unit": input_units.get(inp.input_name, ""),
                    "literal_value": inp.literal_value,
                    "source_lookup": inp.source_lookup,
                }
                for inp in instance.inputs
            ],
            "output_value_nodes": [
                {
                    "id": node.id,
                    "name": node.source_output_name,
                    "computed_value": node.computed_value,
                    "computed_unit": node.computed_unit_symbol,
                    "computation_status": node.computation_status.value if node.computation_status else None,
                }
                for node in output_nodes
            ],
        })

    return result


@router.get("/analyses/{analysis_id}")
async def get_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a single analysis by ID.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == analysis_id,
        ModelInstance.component_id.is_(None)
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Get output nodes
    output_nodes = db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == analysis_id
    ).all()

    # Get model info and input schema for units
    model_info = None
    input_units = {}  # Map input_name -> unit
    if instance.model_version:
        model_info = {
            "id": instance.model_version.physics_model_id,
            "name": instance.model_version.physics_model.name if instance.model_version.physics_model else None,
            "version": instance.model_version.version,
        }
        # Build unit lookup from model inputs schema
        model_inputs = instance.model_version.inputs or []
        for inp_schema in model_inputs:
            if isinstance(inp_schema, dict):
                input_units[inp_schema.get("name", "")] = inp_schema.get("unit", "")

    return {
        "id": instance.id,
        "name": instance.name,
        "description": instance.description,
        "model_version_id": instance.model_version_id,
        "model": model_info,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "computation_status": instance.computation_status.value if instance.computation_status else None,
        "error_message": instance.error_message,
        "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
        "created_at": instance.created_at.isoformat() if instance.created_at else None,
        "created_by": instance.created_by,
        "inputs": [
            {
                "input_name": inp.input_name,
                "unit": input_units.get(inp.input_name, ""),
                "literal_value": inp.literal_value,
                "source_lookup": inp.source_lookup,
                "source_value_node_id": inp.source_value_node_id,
            }
            for inp in instance.inputs
        ],
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }


@router.patch("/analyses/{analysis_id}")
async def update_analysis(
    analysis_id: int,
    data: AnalysisUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an analysis (name, description, or input bindings).

    If bindings are updated, the model will be re-evaluated.
    Broadcasts update via WebSocket.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == analysis_id,
        ModelInstance.component_id.is_(None)
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Check for name conflicts if name is being changed
    if data.name and data.name != instance.name:
        existing = db.query(ModelInstance).filter(
            ModelInstance.name == data.name,
            ModelInstance.component_id.is_(None),
            ModelInstance.id != analysis_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Analysis with name '{data.name}' already exists"
            )
        instance.name = data.name

    if data.description is not None:
        instance.description = data.description

    # Update bindings if provided
    if data.bindings:
        # Delete existing inputs
        for inp in instance.inputs:
            db.delete(inp)

        # Create new inputs
        for input_name, binding_expr in data.bindings.items():
            parsed = parse_binding_value(binding_expr)

            model_input = ModelInput(
                model_instance_id=analysis_id,
                input_name=input_name
            )

            if parsed["type"] == "literal":
                model_input.literal_value = parsed["value"]
            elif parsed["type"] == "value_node":
                # Direct ValueNode binding - enables analysis-to-analysis chaining
                model_input.source_value_node_id = parsed["node_id"]
            elif parsed["type"] in ("lookup", "reference", "expression"):
                model_input.source_lookup = {"expression": parsed.get("expression", binding_expr)}
            else:
                model_input.source_lookup = {"expression": str(binding_expr)}

            db.add(model_input)

        # Re-evaluate the model
        try:
            evaluate_and_attach(instance, db)
        except ModelEvaluationError as e:
            import logging
            logging.warning(f"Re-evaluation failed for analysis {analysis_id}: {e}")

    db.commit()
    db.refresh(instance)

    # Get output nodes
    output_nodes = db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == analysis_id
    ).all()

    response_data = {
        "id": instance.id,
        "name": instance.name,
        "description": instance.description,
        "model_version_id": instance.model_version_id,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "computation_status": instance.computation_status.value if instance.computation_status else None,
        "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
        "inputs": [
            {
                "input_name": inp.input_name,
                "literal_value": inp.literal_value,
                "source_lookup": inp.source_lookup,
            }
            for inp in instance.inputs
        ],
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }

    # Broadcast update via WebSocket
    import asyncio
    asyncio.create_task(ws_manager.broadcast_analysis_update(
        analysis_id, "updated", response_data
    ))

    return response_data


@router.delete("/analyses/{analysis_id}")
async def delete_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete an analysis.

    Also deletes associated inputs and output ValueNodes.
    Broadcasts deletion via WebSocket.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == analysis_id,
        ModelInstance.component_id.is_(None)
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Delete output ValueNodes
    db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == analysis_id
    ).delete()

    # Delete inputs (cascade should handle this, but be explicit)
    for inp in instance.inputs:
        db.delete(inp)

    # Delete the instance
    db.delete(instance)
    db.commit()

    # Broadcast deletion via WebSocket
    import asyncio
    asyncio.create_task(ws_manager.broadcast_analysis_update(
        analysis_id, "deleted", {"id": analysis_id}
    ))

    return {"deleted": True, "id": analysis_id}


@router.post("/analyses/{analysis_id}/reset-bindings")
async def reset_analysis_bindings(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Reset all input bindings for an analysis.

    Use when model schema has changed and bindings are orphaned/stale.
    Deletes all ModelInputs and output ValueNodes, leaving a clean slate.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == analysis_id,
        ModelInstance.component_id.is_(None)
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Delete all existing inputs
    deleted_inputs = []
    for inp in instance.inputs:
        deleted_inputs.append(inp.input_name)
        db.delete(inp)

    # Delete output ValueNodes (they're now invalid)
    deleted_outputs = db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == analysis_id
    ).delete()

    # Reset computation status
    instance.computation_status = None
    instance.last_computed = None

    db.commit()
    db.refresh(instance)

    # Broadcast update
    import asyncio
    asyncio.create_task(ws_manager.broadcast_analysis_update(
        analysis_id, "bindings_reset", {"id": analysis_id}
    ))

    return {
        "id": analysis_id,
        "reset": True,
        "deleted_inputs": deleted_inputs,
        "deleted_outputs": deleted_outputs,
        "message": "All bindings cleared. Re-bind inputs to evaluate."
    }


@router.post("/analyses/{analysis_id}/evaluate")
async def evaluate_analysis(
    analysis_id: int,
    db: Session = Depends(get_db)
):
    """
    Re-evaluate an analysis and update its output values.

    Useful when dependencies have changed or for manual refresh.
    Broadcasts evaluation result via WebSocket.
    """
    from app.models.values import ValueNode

    instance = db.query(ModelInstance).filter(
        ModelInstance.id == analysis_id,
        ModelInstance.component_id.is_(None)
    ).first()

    if not instance:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Validate bindings match current model schema
    binding_warnings = []
    if instance.model_version:
        expected_inputs = {inp['name'] for inp in (instance.model_version.inputs or [])}
        actual_bindings = {inp.input_name for inp in instance.inputs}

        orphaned = actual_bindings - expected_inputs
        missing = expected_inputs - actual_bindings

        if orphaned:
            binding_warnings.append(f"Orphaned bindings (not in model): {sorted(orphaned)}")
        if missing:
            binding_warnings.append(f"Missing bindings (required by model): {sorted(missing)}")

    # Evaluate the model
    evaluation_error = None
    try:
        evaluate_and_attach(instance, db)
    except ModelEvaluationError as e:
        evaluation_error = str(e)
    except Exception as e:
        evaluation_error = f"Unexpected error: {str(e)}"

    db.commit()
    db.refresh(instance)

    # Get output nodes
    output_nodes = db.query(ValueNode).filter(
        ValueNode.source_model_instance_id == analysis_id
    ).all()

    response_data = {
        "id": instance.id,
        "name": instance.name,
        "model_name": instance.model_version.physics_model.name if instance.model_version and instance.model_version.physics_model else None,
        "model_category": instance.model_version.physics_model.category if instance.model_version and instance.model_version.physics_model else None,
        "computation_status": instance.computation_status.value if instance.computation_status else None,
        "last_computed": instance.last_computed.isoformat() if instance.last_computed else None,
        "output_value_nodes": [
            {
                "id": node.id,
                "name": node.source_output_name,
                "computed_value": node.computed_value,
                "computed_unit": node.computed_unit_symbol,
                "computation_status": node.computation_status.value if node.computation_status else None,
            }
            for node in output_nodes
        ],
    }

    if evaluation_error:
        response_data["evaluation_error"] = evaluation_error

    if binding_warnings:
        response_data["binding_warnings"] = binding_warnings

    # Broadcast evaluation result via WebSocket
    import asyncio
    asyncio.create_task(ws_manager.broadcast_analysis_update(
        analysis_id, "evaluated", response_data
    ))

    return response_data
