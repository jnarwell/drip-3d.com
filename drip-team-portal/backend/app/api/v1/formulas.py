"""API endpoints for Property Formula management"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging
from datetime import datetime

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

from app.models.formula import PropertyFormula, PropertyReference, FormulaTemplate, ReferenceType, FormulaStatus
from app.models.property import PropertyDefinition, ComponentProperty
from app.models.component import Component
from app.models.resources import SystemConstant
from app.services.formula_engine import FormulaEngine, CalculationResult, ValidationResult

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/formulas")


# Pydantic schemas for API
from pydantic import BaseModel, Field
from typing import Dict, Any


class PropertyReferenceCreate(BaseModel):
    variable_name: str = Field(..., description="Variable name in formula (e.g., 'k', 'rho')")
    reference_type: ReferenceType
    target_component_id: Optional[int] = None
    target_property_definition_id: Optional[int] = None
    target_constant_symbol: Optional[str] = None
    literal_value: Optional[float] = None
    function_name: Optional[str] = None
    function_args: Optional[List[float]] = None
    description: Optional[str] = None
    units_expected: Optional[str] = None
    default_value: Optional[float] = None


class PropertyReferenceResponse(PropertyReferenceCreate):
    id: int
    formula_id: int
    
    class Config:
        from_attributes = True


class PropertyFormulaCreate(BaseModel):
    name: str = Field(..., description="Human-readable formula name")
    description: Optional[str] = None
    property_definition_id: int = Field(..., description="Property this formula calculates")
    component_id: Optional[int] = Field(None, description="Specific component (null = applies to all)")
    formula_expression: str = Field(..., description="Mathematical expression")
    references: List[PropertyReferenceCreate] = Field([], description="Variable references")


class PropertyFormulaUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    formula_expression: Optional[str] = None
    is_active: Optional[bool] = None


class PropertyFormulaResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    property_definition_id: int
    component_id: Optional[int]
    formula_expression: str
    is_active: bool
    validation_status: FormulaStatus
    validation_message: Optional[str]
    calculation_order: int
    version: int
    created_at: datetime
    updated_at: datetime
    created_by: str
    
    # Relationships
    references: List[PropertyReferenceResponse] = []
    property_definition: Optional[Dict] = None
    component: Optional[Dict] = None
    
    class Config:
        from_attributes = True


class FormulaValidationResponse(BaseModel):
    is_valid: bool
    error_message: Optional[str] = None
    variables_found: Optional[List[str]] = None
    dependencies: Optional[List[int]] = None


class CalculationResponse(BaseModel):
    success: bool
    value: Optional[float] = None
    error_message: Optional[str] = None
    input_values: Optional[Dict[str, Any]] = None
    calculation_time_ms: Optional[float] = None


@router.get("/", response_model=List[PropertyFormulaResponse])
async def list_formulas(
    property_definition_id: Optional[int] = Query(None, description="Filter by property definition"),
    component_id: Optional[int] = Query(None, description="Filter by component"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all property formulas with optional filtering"""
    query = db.query(PropertyFormula)
    
    if property_definition_id is not None:
        query = query.filter(PropertyFormula.property_definition_id == property_definition_id)
    
    if component_id is not None:
        query = query.filter(PropertyFormula.component_id == component_id)
    
    if is_active is not None:
        query = query.filter(PropertyFormula.is_active == is_active)
    
    formulas = query.offset(skip).limit(limit).all()
    
    logger.info(f"User {current_user['email']} retrieved {len(formulas)} formulas")
    return formulas


@router.get("/{formula_id}", response_model=PropertyFormulaResponse)
async def get_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific formula by ID"""
    formula = db.query(PropertyFormula).filter(PropertyFormula.id == formula_id).first()
    
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formula with id {formula_id} not found"
        )
    
    return formula


@router.post("/", response_model=PropertyFormulaResponse)
async def create_formula(
    formula_data: PropertyFormulaCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new property formula"""
    try:
        # Validate that property definition exists
        prop_def = db.query(PropertyDefinition).get(formula_data.property_definition_id)
        if not prop_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property definition not found"
            )
        
        # Validate component if specified
        if formula_data.component_id:
            component = db.query(Component).get(formula_data.component_id)
            if not component:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Component not found"
                )
        
        # Create formula
        formula = PropertyFormula(
            name=formula_data.name,
            description=formula_data.description,
            property_definition_id=formula_data.property_definition_id,
            component_id=formula_data.component_id,
            formula_expression=formula_data.formula_expression,
            created_by=current_user["email"]
        )
        
        db.add(formula)
        db.flush()  # Get the ID
        
        # Create references
        for ref_data in formula_data.references:
            reference = PropertyReference(
                formula_id=formula.id,
                variable_name=ref_data.variable_name,
                reference_type=ref_data.reference_type,
                target_component_id=ref_data.target_component_id,
                target_property_definition_id=ref_data.target_property_definition_id,
                target_constant_symbol=ref_data.target_constant_symbol,
                literal_value=ref_data.literal_value,
                function_name=ref_data.function_name,
                function_args=ref_data.function_args,
                description=ref_data.description,
                units_expected=ref_data.units_expected,
                default_value=ref_data.default_value
            )
            db.add(reference)
        
        # Validate the formula
        engine = FormulaEngine(db)
        validation = engine.validate_formula(formula)
        
        formula.validation_status = FormulaStatus.VALID if validation.is_valid else FormulaStatus.ERROR
        formula.validation_message = validation.error_message
        
        db.commit()
        
        logger.info(f"User {current_user['email']} created formula '{formula.name}' (ID: {formula.id})")
        return formula
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating formula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating formula: {str(e)}"
        )


@router.put("/{formula_id}", response_model=PropertyFormulaResponse)
async def update_formula(
    formula_id: int,
    formula_data: PropertyFormulaUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update an existing formula"""
    formula = db.query(PropertyFormula).filter(PropertyFormula.id == formula_id).first()
    
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formula with id {formula_id} not found"
        )
    
    try:
        # Update fields
        if formula_data.name is not None:
            formula.name = formula_data.name
        if formula_data.description is not None:
            formula.description = formula_data.description
        if formula_data.formula_expression is not None:
            formula.formula_expression = formula_data.formula_expression
        if formula_data.is_active is not None:
            formula.is_active = formula_data.is_active
        
        formula.updated_at = datetime.utcnow()
        
        # Re-validate if expression changed
        if formula_data.formula_expression is not None:
            engine = FormulaEngine(db)
            validation = engine.validate_formula(formula)
            formula.validation_status = FormulaStatus.VALID if validation.is_valid else FormulaStatus.ERROR
            formula.validation_message = validation.error_message
        
        db.commit()
        
        logger.info(f"User {current_user['email']} updated formula {formula_id}")
        return formula
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating formula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating formula: {str(e)}"
        )


@router.delete("/{formula_id}")
async def delete_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a formula"""
    formula = db.query(PropertyFormula).filter(PropertyFormula.id == formula_id).first()
    
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formula with id {formula_id} not found"
        )
    
    try:
        # Check if any properties are using this formula
        dependent_props = db.query(ComponentProperty).filter(
            ComponentProperty.formula_id == formula_id
        ).count()
        
        if dependent_props > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete formula - {dependent_props} properties are using it"
            )
        
        db.delete(formula)
        db.commit()
        
        logger.info(f"User {current_user['email']} deleted formula {formula_id}")
        return {"message": "Formula deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting formula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting formula: {str(e)}"
        )


@router.post("/{formula_id}/validate", response_model=FormulaValidationResponse)
async def validate_formula(
    formula_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Validate a formula expression and dependencies"""
    formula = db.query(PropertyFormula).filter(PropertyFormula.id == formula_id).first()
    
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formula with id {formula_id} not found"
        )
    
    try:
        engine = FormulaEngine(db)
        validation = engine.validate_formula(formula)
        
        return FormulaValidationResponse(
            is_valid=validation.is_valid,
            error_message=validation.error_message,
            variables_found=validation.variables_found,
            dependencies=validation.dependencies
        )
        
    except Exception as e:
        logger.error(f"Error validating formula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error validating formula: {str(e)}"
        )


@router.post("/{formula_id}/calculate/{component_id}", response_model=CalculationResponse)
async def calculate_formula(
    formula_id: int,
    component_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Calculate a formula for a specific component"""
    formula = db.query(PropertyFormula).filter(PropertyFormula.id == formula_id).first()
    
    if not formula:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Formula with id {formula_id} not found"
        )
    
    component = db.query(Component).get(component_id)
    if not component:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Component not found"
        )
    
    try:
        engine = FormulaEngine(db)
        result = engine._evaluate_formula(formula, component_id)
        
        return CalculationResponse(
            success=result.success,
            value=result.value,
            error_message=result.error_message,
            input_values=result.input_values,
            calculation_time_ms=result.calculation_time_ms
        )
        
    except Exception as e:
        logger.error(f"Error calculating formula: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error calculating formula: {str(e)}"
        )


@router.get("/references/available", response_model=Dict[str, List[Dict]])
async def get_available_references(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all available references for formula variables"""
    
    # Property definitions
    property_defs = db.query(PropertyDefinition).all()
    properties = [
        {
            "id": prop.id,
            "name": prop.name,
            "property_type": prop.property_type.value,
            "unit": prop.unit,
            "description": prop.description
        }
        for prop in property_defs
    ]
    
    # System constants
    constants = db.query(SystemConstant).all()
    constants_list = [
        {
            "symbol": const.symbol,
            "name": const.name,
            "value": const.value,
            "unit": const.unit,
            "description": const.description,
            "category": const.category
        }
        for const in constants
    ]
    
    # Components
    components = db.query(Component).all()
    components_list = [
        {
            "id": comp.id,
            "component_id": comp.component_id,
            "name": comp.name,
            "category": comp.category.value
        }
        for comp in components
    ]
    
    return {
        "properties": properties,
        "constants": constants_list,
        "components": components_list,
        "functions": list(FormulaEngine(db).parser.ALLOWED_FUNCTIONS),
        "math_constants": list(FormulaEngine(db).parser.CONSTANTS.keys())
    }