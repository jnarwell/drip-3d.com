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

from app.models.formula_isolated import PropertyFormula, PropertyReference, FormulaTemplate, ReferenceType, FormulaStatus
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


@router.post("/create-from-expression")
async def create_formula_from_expression(
    request: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a formula from a simple expression like 'cmp1.length' or '#cmp001.length'"""
    try:
        property_id = request.get("propertyId")
        component_id = request.get("componentId")
        component_db_id = request.get("componentDbId")
        expression = request.get("expression", "").strip()
        property_definition_id = request.get("propertyDefinitionId")
        
        # Keep the original expression with # prefixes for display
        original_expression = expression
        
        logger.info(f"Creating formula from expression: {expression}")
        logger.info(f"Property ID: {property_id}, Component ID: {component_id}, Component DB ID: {component_db_id}")
        
        # Parse the expression and convert variable references
        import re
        
        # Pattern to match variable references like #cmp1.length, #cmp001.length, #steel.density
        # Each variable MUST have a # prefix
        variable_pattern = r'#((cmp\d+|[a-zA-Z]+)\.[a-zA-Z]+)\b'
        
        # Find all variable references
        variables_found = re.findall(variable_pattern, expression)
        
        # Map to store variable name -> actual variable mapping
        variable_map = {}
        references = []
        
        for full_match, prefix in variables_found:
            # Generate a simple variable name for the formula
            var_name = full_match.replace('.', '_')
            variable_map[full_match] = var_name
            
            # Determine reference type and target
            if prefix.startswith('cmp'):
                # Component property reference
                # Extract component number: cmp1 -> 1, cmp001 -> 1
                comp_num_match = re.match(r'cmp(\d+)', prefix)
                if not comp_num_match:
                    raise ValueError(f"Invalid component reference: {prefix}")
                
                comp_num = int(comp_num_match.group(1))
                target_comp_id_str = f"CMP-{comp_num:03d}"
                
                # Find the component
                target_component = db.query(Component).filter(
                    Component.component_id == target_comp_id_str
                ).first()
                
                if not target_component:
                    raise ValueError(f"Component not found: {target_comp_id_str}")
                
                # Extract property name
                prop_name = full_match.split('.')[1]
                # Convert to title case with spaces: length -> Length, youngsModulus -> Young's Modulus
                prop_name = re.sub(r'(?<!^)(?=[A-Z])', ' ', prop_name).title()
                
                # Find property definition
                prop_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name.ilike(prop_name)
                ).first()
                
                if not prop_def:
                    # Try exact match without case conversion
                    prop_def = db.query(PropertyDefinition).filter(
                        PropertyDefinition.name.ilike(full_match.split('.')[1])
                    ).first()
                    
                if not prop_def:
                    # Log available property definitions for debugging
                    all_props = db.query(PropertyDefinition).all()
                    prop_names = [p.name for p in all_props]
                    logger.error(f"Property definition not found: {prop_name}")
                    logger.error(f"Tried: {prop_name} and {full_match.split('.')[1]}")
                    logger.error(f"Available properties: {prop_names}")
                    raise ValueError(f"Property definition not found: {prop_name}")
                
                references.append({
                    "variable_name": var_name,
                    "reference_type": ReferenceType.COMPONENT_PROPERTY.value,
                    "target_component_id": target_component.id,
                    "target_property_definition_id": prop_def.id,
                    "description": f"Reference to {target_comp_id_str}.{prop_name}"
                })
            else:
                # Could be material property or constant
                # For now, assume it's a system constant
                const = db.query(SystemConstant).filter(
                    SystemConstant.symbol.ilike(prefix)
                ).first()
                
                if const:
                    references.append({
                        "variable_name": var_name,
                        "reference_type": ReferenceType.SYSTEM_CONSTANT.value, 
                        "target_constant_symbol": const.symbol,
                        "description": f"System constant: {const.name}"
                    })
                else:
                    # Try material property
                    raise ValueError(f"Unknown reference: {full_match}")
        
        # Replace variable references in expression with simple variable names
        # Need to include the # prefix when replacing
        formula_expression = expression
        for original, var_name in variable_map.items():
            formula_expression = formula_expression.replace('#' + original, var_name)
        
        logger.info(f"Converted expression: {expression} -> {formula_expression}")
        logger.info(f"References: {references}")
        
        # Get property definition for naming
        prop_def = db.query(PropertyDefinition).get(property_definition_id)
        if not prop_def:
            raise ValueError("Property definition not found")
        
        # Create the formula
        formula = PropertyFormula(
            name=f"{prop_def.name} Formula",
            description=f"Formula for calculating {prop_def.name}: {original_expression}",
            property_definition_id=property_definition_id,
            component_id=component_db_id,
            formula_expression=formula_expression,
            created_by=current_user["email"]
        )
        
        db.add(formula)
        db.flush()
        
        # Create references
        for ref_data in references:
            reference = PropertyReference(
                formula_id=formula.id,
                variable_name=ref_data["variable_name"],
                reference_type=ref_data["reference_type"],
                target_component_id=ref_data.get("target_component_id"),
                target_property_definition_id=ref_data.get("target_property_definition_id"),
                target_constant_symbol=ref_data.get("target_constant_symbol"),
                description=ref_data.get("description")
            )
            db.add(reference)
        
        # Flush to ensure references are available for validation
        db.flush()
        
        # Check for self-referencing before validation
        if references:
            for ref in references:
                if (ref.get("reference_type") == ReferenceType.COMPONENT_PROPERTY.value and
                    ref.get("target_component_id") == component_db_id and
                    ref.get("target_property_definition_id") == property_definition_id):
                    formula.validation_status = "error"
                    formula.validation_message = "Formula cannot reference its own property (would create infinite loop)"
                    db.commit()
                    return {
                        "id": formula.id,
                        "name": formula.name,
                        "expression": expression,
                        "formula_expression": formula.formula_expression,
                        "validation_status": formula.validation_status,
                        "validation_message": formula.validation_message
                    }
        
        # Validate the formula
        engine = FormulaEngine(db)
        validation = engine.validate_formula(formula)
        
        formula.validation_status = "valid" if validation.is_valid else "error"
        formula.validation_message = validation.error_message
        
        logger.info(f"Formula validation result: {validation.is_valid}")
        logger.info(f"Formula validation message: {validation.error_message}")
        logger.info(f"Formula references created: {len(references)}")
        
        if validation.is_valid:
            # Update the component property to use this formula
            component_prop = db.query(ComponentProperty).get(property_id)
            if component_prop:
                component_prop.formula_id = formula.id
                component_prop.is_calculated = True
                component_prop.calculation_status = "pending"
                
                # Try to calculate immediately
                logger.info(f"Attempting to calculate formula for property {property_id}")
                calc_result = engine.calculate_property(component_prop)
                if calc_result.success:
                    logger.info(f"Formula calculated successfully: {calc_result.value}")
                    engine._update_property_value(component_prop, calc_result)
                    component_prop.calculation_status = "calculated"
                else:
                    component_prop.calculation_status = "error"
                    logger.error(f"Calculation failed: {calc_result.error_message}")
        
        db.commit()
        
        return {
            "id": formula.id,
            "name": formula.name,
            "expression": expression,
            "formula_expression": formula.formula_expression,
            "validation_status": formula.validation_status,
            "validation_message": formula.validation_message
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating formula from expression: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating formula: {str(e)}"
        )


@router.get("/property/{property_id}/formula")
async def get_property_formula(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the formula expression for a property if it has one"""
    try:
        property = db.query(ComponentProperty).get(property_id)
        if not property or not property.formula_id:
            return {"has_formula": False}
        
        formula = db.query(PropertyFormula).get(property.formula_id)
        if not formula:
            return {"has_formula": False}
        
        # Try to get the original expression from description
        import re
        expression = formula.formula_expression
        if formula.description:
            match = re.search(r"Formula for calculating [^:]+: (.+)$", formula.description)
            if match:
                expression = match.group(1)
        
        return {
            "has_formula": True,
            "formula_id": formula.id,
            "expression": expression,
            "name": formula.name,
            "validation_status": formula.validation_status
        }
    except Exception as e:
        logger.error(f"Error fetching formula for property {property_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching formula: {str(e)}"
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


@router.post("/recalculate-property/{property_id}")
async def recalculate_property_formula(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Manually recalculate a property's formula value"""
    try:
        component_prop = db.query(ComponentProperty).get(property_id)
        if not component_prop:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Property not found"
            )
        
        if not component_prop.is_calculated or not component_prop.formula_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Property is not formula-based"
            )
        
        engine = FormulaEngine(db)
        calc_result = engine.calculate_property(component_prop)
        
        if calc_result.success:
            engine._update_property_value(component_prop, calc_result)
            db.commit()
            
            return {
                "success": True,
                "value": calc_result.value,
                "calculation_time_ms": calc_result.calculation_time_ms
            }
        else:
            return {
                "success": False,
                "error": calc_result.error_message
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recalculating property: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error recalculating property: {str(e)}"
        )


@router.post("/recalculate-dependents/{property_id}")
async def recalculate_dependent_formulas(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Recalculate all formulas that depend on this property"""
    try:
        engine = FormulaEngine(db)
        updated_properties = engine.update_dependent_properties(property_id)
        
        logger.info(f"Updated {len(updated_properties)} dependent properties after change to property {property_id}")
        
        return {
            "success": True,
            "updated_count": len(updated_properties),
            "updated_property_ids": updated_properties
        }
        
    except Exception as e:
        logger.error(f"Error updating dependent properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating dependent properties: {str(e)}"
        )