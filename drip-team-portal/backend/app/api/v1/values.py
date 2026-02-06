"""
Values API - Endpoints for value node management and computation

Handles:
- Creating/updating value nodes (literals, expressions, references)
- Computing values with unit propagation
- Dependency graph queries
- Bulk recalculation
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.values import ValueNode, ValueDependency, NodeType, ComputationStatus
from app.models.units import Unit
from app.models.user import User
from app.services.value_engine import ValueEngine, ExpressionError, CircularDependencyError

router = APIRouter(prefix="/api/v1/values")
logger = logging.getLogger(__name__)


def _get_user_id(db: Session, current_user: dict) -> Optional[int]:
    """Get database user ID from auth context."""
    auth0_id = current_user.get("sub", "")
    if not auth0_id:
        return None
    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    return user.id if user else None


# ============== Pydantic Schemas ==============

class UnitBrief(BaseModel):
    """Brief unit info for responses."""
    id: int
    symbol: str
    name: str

    class Config:
        from_attributes = True


class ValueNodeBase(BaseModel):
    """Base value node schema."""
    description: Optional[str] = None


class LiteralCreate(ValueNodeBase):
    """Create a literal value."""
    value: float
    unit_id: Optional[int] = None


class ExpressionCreate(ValueNodeBase):
    """Create an expression value."""
    expression: str = Field(..., description="Expression string, e.g., 'sqrt(#cmp001.length * 2)'")


class ReferenceCreate(ValueNodeBase):
    """Create a reference to another value."""
    reference_node_id: int


class ValueNodeResponse(BaseModel):
    """Response for a value node."""
    id: int
    node_type: str
    description: Optional[str] = None

    # For literals
    numeric_value: Optional[float] = None
    unit_id: Optional[int] = None
    unit: Optional[UnitBrief] = None

    # For expressions
    expression_string: Optional[str] = None

    # For references
    reference_node_id: Optional[int] = None

    # Computed result
    computed_value: Optional[float] = None
    computed_unit_id: Optional[int] = None
    computed_unit: Optional[UnitBrief] = None
    computation_status: str
    computation_error: Optional[str] = None
    last_computed: Optional[datetime] = None

    # Metadata
    created_at: datetime
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ValueNodeBrief(BaseModel):
    """Brief value node for dependency trees."""
    id: int
    node_type: str
    computed_value: Optional[float] = None
    computation_status: str
    expression_string: Optional[str] = None

    class Config:
        from_attributes = True


class DependencyTreeNode(BaseModel):
    """Node in dependency tree."""
    id: int
    node_type: str
    status: str
    value: Optional[float] = None
    expression: Optional[str] = None
    dependencies: List["DependencyTreeNode"] = []
    truncated: bool = False


class RecalculateResponse(BaseModel):
    """Response from recalculation."""
    success: bool
    value: Optional[float] = None
    unit_symbol: Optional[str] = None
    error: Optional[str] = None
    nodes_recalculated: int = 0


class BulkRecalculateResponse(BaseModel):
    """Response from bulk recalculation."""
    total_nodes: int
    successful: int
    failed: int
    errors: List[Dict[str, Any]] = []


class ExpressionValidateRequest(BaseModel):
    """Request to validate an expression."""
    expression: str


class ExpressionValidateResponse(BaseModel):
    """Response from expression validation."""
    valid: bool
    references: List[str] = []
    error: Optional[str] = None
    parsed_preview: Optional[str] = None


# ============== Value Node CRUD ==============

@router.post("/literal", response_model=ValueNodeResponse)
async def create_literal_value(
    data: LiteralCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a literal value node."""
    # Validate unit if provided
    if data.unit_id:
        unit = db.query(Unit).filter(Unit.id == data.unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    node = engine.create_literal(
        value=data.value,
        unit_id=data.unit_id,
        description=data.description,
        created_by=current_user.get("email", "unknown")
    )
    db.commit()

    return _node_to_response(node, db)


@router.post("/expression", response_model=ValueNodeResponse)
async def create_expression_value(
    data: ExpressionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create an expression value node."""
    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    try:
        node = engine.create_expression(
            expression=data.expression,
            description=data.description,
            created_by=current_user.get("email", "unknown"),
            resolve_references=True
        )

        # Try to compute initial value
        success, error = engine.recalculate(node)
        db.commit()

        return _node_to_response(node, db)

    except ExpressionError as e:
        logger.warning(f"create_expression_value: Expression error for '{data.expression}': {e}")
        error_detail = {
            "message": str(e),
            "expression": data.expression,
        }
        if hasattr(e, 'to_dict'):
            error_detail.update(e.to_dict())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )


@router.post("/reference", response_model=ValueNodeResponse)
async def create_reference_value(
    data: ReferenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a reference value node that points to another node."""
    # Verify referenced node exists
    ref_node = db.query(ValueNode).filter(ValueNode.id == data.reference_node_id).first()
    if not ref_node:
        raise HTTPException(status_code=404, detail="Referenced node not found")

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    node = engine.create_reference(
        reference_node_id=data.reference_node_id,
        description=data.description,
        created_by=current_user.get("email", "unknown")
    )

    # Compute initial value
    success, error = engine.recalculate(node)
    db.commit()

    return _node_to_response(node, db)


@router.get("", response_model=List[ValueNodeResponse])
async def list_values(
    node_type: Optional[str] = Query(None, description="Filter by node type"),
    status: Optional[str] = Query(None, description="Filter by computation status"),
    limit: int = Query(100, le=1000),
    offset: int = Query(0),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List value nodes with optional filters."""
    query = db.query(ValueNode)

    if node_type:
        try:
            nt = NodeType(node_type)
            query = query.filter(ValueNode.node_type == nt)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid node_type. Must be one of: {[t.value for t in NodeType]}"
            )

    if status:
        try:
            cs = ComputationStatus(status)
            query = query.filter(ValueNode.computation_status == cs)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in ComputationStatus]}"
            )

    nodes = query.order_by(ValueNode.created_at.desc()).offset(offset).limit(limit).all()
    return [_node_to_response(n, db) for n in nodes]


@router.get("/{node_id}", response_model=ValueNodeResponse)
async def get_value(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a value node by ID."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    return _node_to_response(node, db)


@router.delete("/{node_id}")
async def delete_value(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a value node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    # Check if other nodes depend on this one
    dependents = db.query(ValueDependency).filter(
        ValueDependency.source_id == node_id
    ).count()

    if dependents > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot delete: {dependents} other value(s) depend on this node"
        )

    # Delete dependencies where this node is the dependent
    db.query(ValueDependency).filter(
        ValueDependency.dependent_id == node_id
    ).delete()

    db.delete(node)
    db.commit()

    return {"success": True, "message": f"Value node {node_id} deleted"}


# ============== Computation Endpoints ==============

@router.post("/{node_id}/recalculate", response_model=RecalculateResponse)
async def recalculate_value(
    node_id: int,
    cascade: bool = Query(False, description="Also recalculate stale dependents"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Force recalculation of a value node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    try:
        success, error = engine.recalculate(node)
        nodes_recalculated = 1

        if cascade and success:
            recalculated = engine.recalculate_stale(node)
            nodes_recalculated += len(recalculated)

        db.commit()

        unit_symbol = None
        if node.computed_unit_id:
            unit = db.query(Unit).filter(Unit.id == node.computed_unit_id).first()
            if unit:
                unit_symbol = unit.symbol

        return RecalculateResponse(
            success=success,
            value=node.computed_value,
            unit_symbol=unit_symbol,
            error=error,
            nodes_recalculated=nodes_recalculated
        )

    except CircularDependencyError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Circular dependency detected: {str(e)}"
        )


@router.post("/recalculate-all", response_model=BulkRecalculateResponse)
async def recalculate_all_stale(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Recalculate all stale value nodes."""
    stale_nodes = db.query(ValueNode).filter(
        ValueNode.computation_status.in_([
            ComputationStatus.STALE,
            ComputationStatus.PENDING
        ])
    ).all()

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    successful = 0
    failed = 0
    errors = []

    for node in stale_nodes:
        try:
            success, error = engine.recalculate(node)
            if success:
                successful += 1
            else:
                failed += 1
                errors.append({"node_id": node.id, "error": error})
        except Exception as e:
            failed += 1
            errors.append({"node_id": node.id, "error": str(e)})

    db.commit()

    return BulkRecalculateResponse(
        total_nodes=len(stale_nodes),
        successful=successful,
        failed=failed,
        errors=errors[:20]  # Limit errors returned
    )


# ============== Dependency Endpoints ==============

@router.get("/{node_id}/dependencies", response_model=DependencyTreeNode)
async def get_dependencies(
    node_id: int,
    depth: int = Query(5, le=20, description="Maximum depth to traverse"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the dependency tree for a value node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    tree = engine.get_dependency_tree(node, depth=depth)

    return tree


@router.get("/{node_id}/dependents", response_model=List[ValueNodeBrief])
async def get_dependents(
    node_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all nodes that depend on this node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    # Get direct dependents
    deps = db.query(ValueDependency).filter(
        ValueDependency.source_id == node_id
    ).all()

    dependent_nodes = [dep.dependent_node for dep in deps]

    return [
        ValueNodeBrief(
            id=n.id,
            node_type=n.node_type.value,
            computed_value=n.computed_value,
            computation_status=n.computation_status.value,
            expression_string=n.expression_string
        )
        for n in dependent_nodes
    ]


# ============== Expression Utilities ==============

@router.post("/validate-expression", response_model=ExpressionValidateResponse)
async def validate_expression(
    data: ExpressionValidateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate an expression without creating a node."""
    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    try:
        parsed = engine._parse_expression(data.expression)
        references = engine._extract_references(data.expression)

        return ExpressionValidateResponse(
            valid=True,
            references=references,
            parsed_preview=parsed.get("sympy_repr", "")
        )

    except ExpressionError as e:
        logger.debug(f"validate_expression: Expression validation failed for '{data.expression}': {e}")
        # Include detailed error info if available
        error_msg = str(e)
        if hasattr(e, 'expression') and e.expression:
            error_msg = f"{e.args[0] if e.args else 'Parse error'}"
        return ExpressionValidateResponse(
            valid=False,
            error=error_msg
        )


# ============== Update Endpoints ==============

@router.put("/{node_id}/literal", response_model=ValueNodeResponse)
async def update_literal_value(
    node_id: int,
    data: LiteralCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a literal value node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    if node.node_type != NodeType.LITERAL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update literal values with this endpoint"
        )

    # Validate unit if provided
    if data.unit_id:
        unit = db.query(Unit).filter(Unit.id == data.unit_id).first()
        if not unit:
            raise HTTPException(status_code=404, detail="Unit not found")

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)
    engine.update_literal(node, data.value, data.unit_id)
    # Auto-recalculate all stale dependents
    engine.recalculate_stale(node)

    if data.description is not None:
        node.description = data.description

    db.commit()

    return _node_to_response(node, db)


@router.put("/{node_id}/expression", response_model=ValueNodeResponse)
async def update_expression_value(
    node_id: int,
    data: ExpressionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an expression value node."""
    node = db.query(ValueNode).filter(ValueNode.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Value node not found")

    if node.node_type != NodeType.EXPRESSION:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only update expression values with this endpoint"
        )

    user_id = _get_user_id(db, current_user)
    engine = ValueEngine(db, user_id=user_id)

    try:
        engine.update_expression(node, data.expression)

        if data.description is not None:
            node.description = data.description

        # Recalculate this node and all stale dependents
        success, error = engine.recalculate(node)
        if success:
            engine.recalculate_stale(node)
        db.commit()

        return _node_to_response(node, db)

    except ExpressionError as e:
        db.rollback()
        logger.warning(f"update_expression_value: Expression error for node {node_id}: {e}")
        error_detail = {
            "message": str(e),
            "expression": data.expression,
            "node_id": node_id,
        }
        if hasattr(e, 'to_dict'):
            error_detail.update(e.to_dict())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_detail
        )


# ============== Helper Functions ==============

def _node_to_response(node: ValueNode, db: Session) -> ValueNodeResponse:
    """Convert a ValueNode to response schema."""
    unit = None
    if node.unit_id:
        u = db.query(Unit).filter(Unit.id == node.unit_id).first()
        if u:
            unit = UnitBrief(id=u.id, symbol=u.symbol, name=u.name)

    computed_unit = None
    if node.computed_unit_id:
        cu = db.query(Unit).filter(Unit.id == node.computed_unit_id).first()
        if cu:
            computed_unit = UnitBrief(id=cu.id, symbol=cu.symbol, name=cu.name)

    return ValueNodeResponse(
        id=node.id,
        node_type=node.node_type.value,
        description=node.description,
        numeric_value=node.numeric_value,
        unit_id=node.unit_id,
        unit=unit,
        expression_string=node.expression_string,
        reference_node_id=node.reference_node_id,
        computed_value=node.computed_value,
        computed_unit_id=node.computed_unit_id,
        computed_unit=computed_unit,
        computation_status=node.computation_status.value,
        computation_error=node.computation_error,
        last_computed=node.last_computed,
        created_at=node.created_at,
        created_by=node.created_by
    )
