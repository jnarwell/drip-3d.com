from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.property import PropertyDefinition, ComponentProperty, PropertyType
from app.models.component import Component
from app.models.values import ValueNode
from app.models.units import Unit
from app.models.user import User
from app.services.value_engine import ValueEngine, ExpressionError
from app.schemas.property import (
    PropertyDefinitionCreate,
    PropertyDefinitionUpdate,
    PropertyDefinitionResponse,
    ComponentPropertyCreate,
    ComponentPropertyUpdate,
    ComponentPropertyResponse,
    ValueNodeBrief
)

router = APIRouter(prefix="/api/v1")
logger = logging.getLogger(__name__)


def _get_user_id(db: Session, current_user: dict) -> Optional[int]:
    """Get database user ID from auth context."""
    auth0_id = current_user.get("sub", "")
    if not auth0_id:
        return None
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    return user.id if user else None


# ==================== Helper Functions ====================

def _property_to_response(prop: ComponentProperty, db: Session) -> Dict[str, Any]:
    """Convert ComponentProperty to response dict with value_node info."""
    response = {
        "id": prop.id,
        "component_id": prop.component_id,
        "property_definition_id": prop.property_definition_id,
        "property_definition": prop.property_definition,
        "single_value": prop.single_value,
        "min_value": prop.min_value,
        "max_value": prop.max_value,
        "average_value": prop.average_value,
        "tolerance": prop.tolerance,
        "text_value": prop.text_value,
        "notes": prop.notes,
        "source": prop.source,
        "conditions": prop.conditions,
        "updated_at": prop.updated_at,
        "updated_by": prop.updated_by,
        "value_node_id": prop.value_node_id,
        "value_node": None
    }

    # Add value_node info if linked
    if prop.value_node_id:
        value_node = db.query(ValueNode).filter(ValueNode.id == prop.value_node_id).first()
        if value_node:
            # Use the computed_unit_symbol stored directly on the ValueNode
            # Fall back to looking up from computed_unit_id for backwards compatibility
            computed_unit_symbol = value_node.computed_unit_symbol
            if not computed_unit_symbol and value_node.computed_unit_id:
                unit = db.query(Unit).filter(Unit.id == value_node.computed_unit_id).first()
                if unit:
                    computed_unit_symbol = unit.symbol

            response["value_node"] = {
                "id": value_node.id,
                "node_type": value_node.node_type.value,
                "expression_string": value_node.expression_string,
                "computed_value": value_node.computed_value,
                "computed_unit_symbol": computed_unit_symbol,
                "computation_status": value_node.computation_status.value,
                "computation_error": value_node.computation_error  # Includes dimension warnings
            }

    return response


# ==================== Property Definitions ====================

@router.get("/property-definitions", response_model=List[PropertyDefinitionResponse])
async def get_property_definitions(
    property_type: PropertyType = None,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all property definitions, optionally filtered by type"""
    query = db.query(PropertyDefinition)
    if property_type:
        query = query.filter(PropertyDefinition.property_type == property_type)
    return query.all()


@router.post("/property-definitions", response_model=PropertyDefinitionResponse)
async def create_property_definition(
    property_def: PropertyDefinitionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom property definition"""
    db_property_def = PropertyDefinition(
        **property_def.dict(),
        created_by=current_user["email"]
    )
    db.add(db_property_def)
    db.commit()
    db.refresh(db_property_def)
    return db_property_def


@router.patch("/property-definitions/{definition_id}", response_model=PropertyDefinitionResponse)
async def update_property_definition(
    definition_id: int,
    property_update: PropertyDefinitionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a property definition (only custom properties can be updated)"""
    property_def = db.query(PropertyDefinition).filter(
        PropertyDefinition.id == definition_id
    ).first()
    if not property_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property definition not found"
        )

    # Only allow updating custom properties
    if not property_def.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update built-in property definitions"
        )

    update_data = property_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(property_def, field, value)

    db.commit()
    db.refresh(property_def)
    return property_def


@router.delete("/property-definitions/{definition_id}")
async def delete_property_definition(
    definition_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a property definition (only custom properties can be deleted)"""
    property_def = db.query(PropertyDefinition).filter(
        PropertyDefinition.id == definition_id
    ).first()
    if not property_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property definition not found"
        )

    # Only allow deleting custom properties
    if not property_def.is_custom:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete built-in property definitions"
        )

    # Check if any component properties use this definition
    in_use_count = db.query(ComponentProperty).filter(
        ComponentProperty.property_definition_id == definition_id
    ).count()
    if in_use_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {in_use_count} component(s) use this property"
        )

    db.delete(property_def)
    db.commit()

    return {"status": "success", "message": "Property definition deleted"}


# ==================== Component Properties ====================

@router.get("/components/{component_id}/properties")
async def get_component_properties(
    component_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all properties for a specific component with computed values."""
    logger.info(f"Getting properties for component: {component_id}")

    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    properties = db.query(ComponentProperty).filter(
        ComponentProperty.component_id == component.id
    ).all()

    logger.info(f"Found {len(properties)} properties")

    # Convert to response with value_node info
    return [_property_to_response(p, db) for p in properties]


@router.post("/components/{component_id}/properties")
async def add_component_property(
    component_id: str,
    property_data: ComponentPropertyCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Add a property to a component.

    If single_value is provided, creates a literal ValueNode.
    If expression is provided, creates an expression ValueNode.
    """
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    # Check if property definition exists
    property_def = db.query(PropertyDefinition).filter(
        PropertyDefinition.id == property_data.property_definition_id
    ).first()
    if not property_def:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property definition not found"
        )

    # Check if this property already exists for the component
    existing = db.query(ComponentProperty).filter(
        ComponentProperty.component_id == component.id,
        ComponentProperty.property_definition_id == property_data.property_definition_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This property already exists for the component"
        )

    # Create ValueNode if value or expression provided
    value_node_id = None
    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    # Build description for the value node
    comp_code = component.code or f"COMP_{component.id}"
    value_description = f"{comp_code}.{property_def.name}"

    if property_data.expression:
        # Create expression ValueNode
        try:
            value_node = engine.create_expression(
                expression=property_data.expression,
                description=value_description,
                created_by=current_user["email"],
                resolve_references=True
            )
            # Try to compute - pass property definition unit for validation
            engine.recalculate(value_node, expected_unit=property_def.unit)
            value_node_id = value_node.id
            logger.info(f"Created expression ValueNode {value_node_id} for {value_description}")
        except ExpressionError as e:
            logger.warning(
                f"add_component_property: Expression error for {component_id}.{property_def.name}: "
                f"'{property_data.expression}' - {e}"
            )
            error_detail = {
                "message": str(e),
                "expression": property_data.expression,
                "component_id": component_id,
                "property": property_def.name,
            }
            if hasattr(e, 'to_dict'):
                error_detail.update(e.to_dict())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )

    elif property_data.single_value is not None:
        # Create literal ValueNode
        value_node = engine.create_literal(
            value=property_data.single_value,
            unit_id=property_data.unit_id,
            description=value_description,
            created_by=current_user["email"]
        )
        value_node_id = value_node.id
        logger.info(f"Created literal ValueNode {value_node_id} for {value_description}")

    # Create the property, excluding expression and unit_id which aren't model fields
    property_dict = property_data.dict(exclude={"expression", "unit_id"})
    db_property = ComponentProperty(
        component_id=component.id,
        **property_dict,
        value_node_id=value_node_id,
        updated_by=current_user["email"]
    )

    db.add(db_property)
    db.commit()
    db.refresh(db_property)

    return _property_to_response(db_property, db)


@router.patch("/components/{component_id}/properties/{property_id}")
async def update_component_property(
    component_id: str,
    property_id: int,
    property_update: ComponentPropertyUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Update a component property value.

    If expression is provided, updates/creates an expression ValueNode.
    If single_value is provided, updates/creates a literal ValueNode.
    """
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    update_data = property_update.dict(exclude_unset=True)
    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    # Build description for value node
    comp_code = component.code or f"COMP_{component.id}"
    value_description = f"{comp_code}.{property_value.property_definition.name}"

    # Handle expression update
    if "expression" in update_data and update_data["expression"]:
        expression = update_data.pop("expression")
        unit_id = update_data.pop("unit_id", None)

        try:
            # Get expected unit from property definition for validation
            expected_unit = property_value.property_definition.unit

            if property_value.value_node_id:
                # Update existing value node
                existing_node = db.query(ValueNode).filter(
                    ValueNode.id == property_value.value_node_id
                ).first()
                if existing_node and existing_node.node_type.value == "expression":
                    # Update existing expression node
                    engine.update_expression(existing_node, expression)
                    engine.recalculate(existing_node, expected_unit=expected_unit)
                    # Auto-recalculate all stale dependents
                    engine.recalculate_stale(existing_node)
                else:
                    # Existing node is a literal - create new expression to replace it
                    value_node = engine.create_expression(
                        expression=expression,
                        description=value_description,
                        created_by=current_user["email"],
                        resolve_references=True
                    )
                    # Transfer dependents from old node to new node
                    engine.transfer_dependents(existing_node, value_node)
                    engine.recalculate(value_node, expected_unit=expected_unit)
                    # Recalculate anything that was depending on the old node
                    engine.recalculate_stale(value_node)
                    property_value.value_node_id = value_node.id
            else:
                # Create new expression ValueNode
                value_node = engine.create_expression(
                    expression=expression,
                    description=value_description,
                    created_by=current_user["email"],
                    resolve_references=True
                )
                engine.recalculate(value_node, expected_unit=expected_unit)
                property_value.value_node_id = value_node.id

            logger.info(f"Updated expression for property {property_id}")

        except ExpressionError as e:
            logger.warning(
                f"update_component_property: Expression error for {component_id} property {property_id}: "
                f"'{expression}' - {e}"
            )
            error_detail = {
                "message": str(e),
                "expression": expression,
                "component_id": component_id,
                "property_id": property_id,
            }
            if hasattr(e, 'to_dict'):
                error_detail.update(e.to_dict())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_detail
            )

    # Handle single_value update (literal)
    elif "single_value" in update_data and update_data["single_value"] is not None:
        single_value = update_data["single_value"]
        unit_id = update_data.pop("unit_id", None)

        if property_value.value_node_id:
            # Update existing value node if it's a literal
            existing_node = db.query(ValueNode).filter(
                ValueNode.id == property_value.value_node_id
            ).first()
            if existing_node and existing_node.node_type.value == "literal":
                engine.update_literal(existing_node, single_value, unit_id)
                # Auto-recalculate all stale dependents
                engine.recalculate_stale(existing_node)
            else:
                # Create new literal (replaces expression with literal)
                value_node = engine.create_literal(
                    value=single_value,
                    unit_id=unit_id,
                    description=value_description,
                    created_by=current_user["email"]
                )
                # Transfer dependents from old node to new node
                engine.transfer_dependents(existing_node, value_node)
                # Recalculate anything that was depending on the old node
                engine.recalculate_stale(value_node)
                property_value.value_node_id = value_node.id
        else:
            # Create new literal ValueNode
            value_node = engine.create_literal(
                value=single_value,
                unit_id=unit_id,
                description=value_description,
                created_by=current_user["email"]
            )
            property_value.value_node_id = value_node.id

        logger.info(f"Updated literal value for property {property_id}")

    # Remove unit_id from update_data if still present (not a model field)
    update_data.pop("unit_id", None)
    update_data.pop("expression", None)

    # Update other fields
    for field, value in update_data.items():
        setattr(property_value, field, value)

    property_value.updated_at = datetime.utcnow()
    property_value.updated_by = current_user["email"]

    db.commit()
    db.refresh(property_value)

    return _property_to_response(property_value, db)


@router.delete("/components/{component_id}/properties/{property_id}")
async def delete_component_property(
    component_id: str,
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a component property and its associated ValueNode."""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    # Note: We don't delete the ValueNode here as it might be referenced elsewhere
    # The ValueNode can be orphaned and cleaned up separately if needed

    db.delete(property_value)
    db.commit()

    return {"status": "success", "message": "Property deleted"}


# ==================== Property Recalculation ====================

@router.post("/components/{component_id}/properties/{property_id}/recalculate")
async def recalculate_property(
    component_id: str,
    property_id: int,
    cascade: bool = False,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Force recalculation of a property's ValueNode."""
    component = db.query(Component).filter(Component.component_id == component_id).first()
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Component {component_id} not found"
        )

    property_value = db.query(ComponentProperty).filter(
        ComponentProperty.id == property_id,
        ComponentProperty.component_id == component.id
    ).first()
    if not property_value:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )

    if not property_value.value_node_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property has no associated ValueNode"
        )

    value_node = db.query(ValueNode).filter(
        ValueNode.id == property_value.value_node_id
    ).first()
    if not value_node:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ValueNode not found"
        )

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    success, error = engine.recalculate(value_node)

    nodes_recalculated = 1
    if cascade and success:
        recalculated = engine.recalculate_stale(value_node)
        nodes_recalculated += len(recalculated)

    db.commit()

    return {
        "success": success,
        "error": error,
        "computed_value": value_node.computed_value,
        "nodes_recalculated": nodes_recalculated
    }
