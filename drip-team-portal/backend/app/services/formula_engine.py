"""Formula evaluation engine for property calculations"""
import re
import math
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from sqlalchemy.orm import Session
import sympy as sp
from sympy.parsing.sympy_parser import parse_expr
from sympy.core.sympify import SympifyError

from app.models.formula_isolated import PropertyFormula, PropertyReference, ReferenceType, FormulaStatus
from app.models.property import ComponentProperty, PropertyDefinition
from app.models.component import Component
from app.models.resources import SystemConstant

logger = logging.getLogger(__name__)


@dataclass
class CalculationResult:
    """Result of formula calculation"""
    success: bool
    value: Optional[float] = None
    error_message: Optional[str] = None
    input_values: Optional[Dict[str, Any]] = None
    calculation_time_ms: Optional[float] = None


@dataclass
class ValidationResult:
    """Result of formula validation"""
    is_valid: bool
    error_message: Optional[str] = None
    variables_found: Optional[List[str]] = None
    dependencies: Optional[List[int]] = None  # Formula IDs this depends on


class FormulaParser:
    """Parses and validates mathematical expressions"""
    
    # Supported functions
    ALLOWED_FUNCTIONS = {
        'sqrt', 'log', 'ln', 'log10', 'exp', 'pow',
        'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
        'sinh', 'cosh', 'tanh',
        'abs', 'ceil', 'floor', 'round',
        'min', 'max', 'sum'
    }
    
    # Mathematical constants
    CONSTANTS = {
        'pi': math.pi,
        'e': math.e,
        'tau': 2 * math.pi,
    }
    
    @classmethod
    def parse_expression(cls, expression: str) -> Tuple[sp.Basic, ValidationResult]:
        """Parse mathematical expression and extract variables"""
        try:
            # Clean the expression
            cleaned = cls._clean_expression(expression)
            
            # Parse with sympy
            parsed = parse_expr(cleaned, transformations='all')
            
            # Extract variables
            variables = [str(var) for var in parsed.free_symbols]
            
            # Validate functions
            validation = cls._validate_functions(parsed)
            if not validation.is_valid:
                return None, validation
                
            return parsed, ValidationResult(
                is_valid=True,
                variables_found=variables
            )
            
        except SympifyError as e:
            return None, ValidationResult(
                is_valid=False,
                error_message=f"Invalid mathematical expression: {str(e)}"
            )
        except Exception as e:
            return None, ValidationResult(
                is_valid=False,
                error_message=f"Parse error: {str(e)}"
            )
    
    @classmethod
    def _clean_expression(cls, expression: str) -> str:
        """Clean and normalize expression for parsing"""
        # Remove extra whitespace
        cleaned = re.sub(r'\s+', ' ', expression.strip())
        
        # Replace common patterns
        replacements = {
            '√': 'sqrt',
            '²': '**2',
            '³': '**3',
            '×': '*',
            '÷': '/',
            'π': 'pi',
        }
        
        for old, new in replacements.items():
            cleaned = cleaned.replace(old, new)
            
        return cleaned
    
    @classmethod
    def _validate_functions(cls, parsed_expr: sp.Basic) -> ValidationResult:
        """Validate that only allowed functions are used"""
        # Get all function calls
        functions_used = set()
        
        # Walk through the expression tree to find function applications
        for expr in sp.preorder_traversal(parsed_expr):
            # Skip symbols and numbers - they're not functions
            if isinstance(expr, (sp.Symbol, sp.Number)):
                continue
                
            # Check if this is a function application
            if hasattr(expr, 'func') and hasattr(expr.func, '__name__'):
                func_name = expr.func.__name__
                # Skip built-in sympy types that aren't actual function calls
                if func_name in ['Add', 'Mul', 'Pow', 'Symbol', 'Integer', 'Float', 'Rational', 
                                 'Div', 'Sub', 'Neg', 'Abs', 'Sign', 'Mod']:
                    continue
                    
                # Check if it's an allowed function
                if func_name not in cls.ALLOWED_FUNCTIONS and func_name not in cls.CONSTANTS:
                    functions_used.add(func_name)
        
        if functions_used:
            return ValidationResult(
                is_valid=False,
                error_message=f"Unsupported functions: {', '.join(functions_used)}"
            )
        
        return ValidationResult(is_valid=True)


class FormulaEngine:
    """Main engine for formula evaluation and dependency management"""
    
    def __init__(self, db: Session):
        self.db = db
        self.parser = FormulaParser()
        self._dependency_cache: Dict[int, List[int]] = {}
        
    def validate_formula(self, formula: PropertyFormula) -> ValidationResult:
        """Validate a formula expression and check dependencies"""
        try:
            # Parse the expression
            parsed_expr, validation = self.parser.parse_expression(formula.formula_expression)
            if not validation.is_valid:
                return validation
            
            # Check that all variables have references
            missing_refs = []
            logger.info(f"Checking references for formula {formula.id}")
            logger.info(f"Variables found in expression: {validation.variables_found}")
            
            for var in validation.variables_found:
                ref = self.db.query(PropertyReference).filter(
                    PropertyReference.formula_id == formula.id,
                    PropertyReference.variable_name == var
                ).first()
                
                if not ref:
                    missing_refs.append(var)
                    # Log what references we do have
                    all_refs = self.db.query(PropertyReference).filter(
                        PropertyReference.formula_id == formula.id
                    ).all()
                    ref_names = [r.variable_name for r in all_refs]
                    logger.error(f"Missing reference for variable '{var}'")
                    logger.error(f"Available references: {ref_names}")
            
            if missing_refs:
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Missing variable references: {', '.join(missing_refs)}"
                )
            
            # Check for circular dependencies
            dependencies = self._get_formula_dependencies(formula.id)
            if self._has_circular_dependency(formula.id, dependencies):
                return ValidationResult(
                    is_valid=False,
                    error_message="Circular dependency detected"
                )
            
            return ValidationResult(
                is_valid=True,
                variables_found=validation.variables_found,
                dependencies=dependencies
            )
            
        except Exception as e:
            logger.error(f"Formula validation error: {e}")
            return ValidationResult(
                is_valid=False,
                error_message=f"Validation error: {str(e)}"
            )
    
    def calculate_property(self, component_property: ComponentProperty) -> CalculationResult:
        """Calculate property value using its formula"""
        if not component_property.formula_id or not component_property.is_calculated:
            return CalculationResult(
                success=False,
                error_message="Property is not formula-based"
            )
        
        formula = self.db.query(PropertyFormula).get(component_property.formula_id)
        if not formula:
            return CalculationResult(
                success=False,
                error_message="Formula not found"
            )
        
        return self._evaluate_formula(formula, component_property.component_id)
    
    def _evaluate_formula(self, formula: PropertyFormula, component_id: int) -> CalculationResult:
        """Evaluate a formula for a specific component"""
        import time
        start_time = time.time()
        
        try:
            # Parse the expression
            parsed_expr, validation = self.parser.parse_expression(formula.formula_expression)
            if not validation.is_valid:
                return CalculationResult(
                    success=False,
                    error_message=validation.error_message
                )
            
            # Resolve all variable values
            variable_values, resolve_error = self._resolve_variables(formula, component_id)
            if resolve_error:
                return CalculationResult(
                    success=False,
                    error_message=resolve_error,
                    input_values=variable_values
                )
            
            # Substitute values into expression
            substituted = parsed_expr.subs(variable_values)
            
            # Evaluate the result
            result = float(substituted.evalf())
            
            calculation_time = (time.time() - start_time) * 1000  # ms
            
            return CalculationResult(
                success=True,
                value=result,
                input_values=variable_values,
                calculation_time_ms=calculation_time
            )
            
        except Exception as e:
            logger.error(f"Formula evaluation error: {e}")
            return CalculationResult(
                success=False,
                error_message=str(e),
                calculation_time_ms=(time.time() - start_time) * 1000
            )
    
    def _resolve_variables(self, formula: PropertyFormula, component_id: int) -> Tuple[Dict[str, float], Optional[str]]:
        """Resolve all variable values for a formula"""
        variable_values = {}
        
        references = self.db.query(PropertyReference).filter(
            PropertyReference.formula_id == formula.id
        ).all()
        
        for ref in references:
            value, error = self._resolve_single_variable(ref, component_id)
            if error:
                return variable_values, f"Error resolving '{ref.variable_name}': {error}"
            
            variable_values[ref.variable_name] = value
        
        return variable_values, None
    
    def _resolve_single_variable(self, reference: PropertyReference, component_id: int) -> Tuple[Optional[float], Optional[str]]:
        """Resolve a single variable reference to a numeric value"""
        try:
            if reference.reference_type == ReferenceType.LITERAL_VALUE.value:
                return reference.literal_value, None
                
            elif reference.reference_type == ReferenceType.SYSTEM_CONSTANT.value:
                constant = self.db.query(SystemConstant).filter(
                    SystemConstant.symbol == reference.target_constant_symbol
                ).first()
                
                if not constant:
                    return reference.default_value, f"System constant '{reference.target_constant_symbol}' not found"
                
                return constant.value, None
                
            elif reference.reference_type == ReferenceType.COMPONENT_PROPERTY.value:
                # Determine which component to look at
                target_component_id = reference.target_component_id or component_id
                
                logger.info(f"Looking for component property: component_id={target_component_id}, property_def_id={reference.target_property_definition_id}")
                
                component_prop = self.db.query(ComponentProperty).filter(
                    ComponentProperty.component_id == target_component_id,
                    ComponentProperty.property_definition_id == reference.target_property_definition_id
                ).first()
                
                if not component_prop:
                    logger.error(f"Component property not found for component_id={target_component_id}, property_def_id={reference.target_property_definition_id}")
                    return reference.default_value, f"Component property not found"
                
                # If the property is also calculated, evaluate it first
                if component_prop.is_calculated and component_prop.formula_id:
                    calc_result = self.calculate_property(component_prop)
                    if not calc_result.success:
                        return reference.default_value, f"Failed to calculate dependent property: {calc_result.error_message}"
                    return calc_result.value, None
                
                # Otherwise use the stored value
                value = self._extract_property_value(component_prop)
                logger.info(f"Extracted property value: {value} from property {component_prop.id}")
                if value is None:
                    return reference.default_value, "Property value is null"
                
                return value, None
                
            elif reference.reference_type == ReferenceType.FUNCTION_CALL.value:
                # Handle built-in function calls
                return self._evaluate_function(reference), None
                
            else:
                return reference.default_value, f"Unsupported reference type: {reference.reference_type}"
                
        except Exception as e:
            logger.error(f"Variable resolution error: {e}")
            return reference.default_value, str(e)
    
    def _extract_property_value(self, component_prop: ComponentProperty) -> Optional[float]:
        """Extract the appropriate value from a ComponentProperty based on its type"""
        prop_def = component_prop.property_definition
        
        if prop_def.value_type.value == "single":
            return component_prop.single_value
        elif prop_def.value_type.value == "average":
            return component_prop.average_value
        elif prop_def.value_type.value == "range":
            # For ranges, use the average of min and max
            if component_prop.min_value is not None and component_prop.max_value is not None:
                return (component_prop.min_value + component_prop.max_value) / 2
            return component_prop.min_value or component_prop.max_value
        
        return None
    
    def _evaluate_function(self, reference: PropertyReference) -> float:
        """Evaluate built-in function calls"""
        func_name = reference.function_name
        args = reference.function_args or []
        
        # Map function names to Python functions
        func_map = {
            'sqrt': math.sqrt,
            'log': math.log,
            'log10': math.log10,
            'exp': math.exp,
            'sin': math.sin,
            'cos': math.cos,
            'tan': math.tan,
            'abs': abs,
            'min': min,
            'max': max,
        }
        
        if func_name in func_map:
            return func_map[func_name](*args)
        
        raise ValueError(f"Unknown function: {func_name}")
    
    def _get_formula_dependencies(self, formula_id: int) -> List[int]:
        """Get list of formula IDs that this formula depends on"""
        if formula_id in self._dependency_cache:
            return self._dependency_cache[formula_id]
        
        dependencies = []
        
        # Get all component property references for this formula
        references = self.db.query(PropertyReference).filter(
            PropertyReference.formula_id == formula_id,
            PropertyReference.reference_type == ReferenceType.COMPONENT_PROPERTY.value
        ).all()
        
        for ref in references:
            # Find formulas that calculate the referenced properties
            dependent_props = self.db.query(ComponentProperty).filter(
                ComponentProperty.property_definition_id == ref.target_property_definition_id,
                ComponentProperty.is_calculated == True,
                ComponentProperty.formula_id.isnot(None)
            ).all()
            
            for prop in dependent_props:
                if prop.formula_id not in dependencies:
                    dependencies.append(prop.formula_id)
        
        self._dependency_cache[formula_id] = dependencies
        return dependencies
    
    def _has_circular_dependency(self, formula_id: int, dependencies: List[int], visited: Optional[List[int]] = None) -> bool:
        """Check for circular dependencies in formula chain"""
        if visited is None:
            visited = []
        
        if formula_id in visited:
            return True
        
        visited = visited + [formula_id]
        
        for dep_id in dependencies:
            dep_dependencies = self._get_formula_dependencies(dep_id)
            if self._has_circular_dependency(dep_id, dep_dependencies, visited):
                return True
        
        return False
    
    def update_dependent_properties(self, changed_property_id: int) -> List[int]:
        """Update all properties that depend on the changed property"""
        updated_properties = []
        
        # Find all formulas that reference this property
        prop = self.db.query(ComponentProperty).get(changed_property_id)
        if not prop:
            return updated_properties
        
        dependent_refs = self.db.query(PropertyReference).filter(
            PropertyReference.reference_type == ReferenceType.COMPONENT_PROPERTY.value,
            PropertyReference.target_property_definition_id == prop.property_definition_id
        ).all()
        
        for ref in dependent_refs:
            # Find properties using this formula
            dependent_props = self.db.query(ComponentProperty).filter(
                ComponentProperty.formula_id == ref.formula_id,
                ComponentProperty.is_calculated == True
            ).all()
            
            for dep_prop in dependent_props:
                calc_result = self.calculate_property(dep_prop)
                if calc_result.success:
                    # Update the property value
                    self._update_property_value(dep_prop, calc_result)
                    updated_properties.append(dep_prop.id)
                    self.db.commit()
        
        return updated_properties
    
    def _update_property_value(self, component_prop: ComponentProperty, calc_result: CalculationResult):
        """Update a ComponentProperty with calculated values"""
        from datetime import datetime
        
        prop_def = component_prop.property_definition
        
        # Clear existing values
        component_prop.single_value = None
        component_prop.min_value = None  
        component_prop.max_value = None
        component_prop.average_value = None
        component_prop.tolerance = None
        
        # Set value based on property type
        if prop_def.value_type.value == "single":
            component_prop.single_value = calc_result.value
        elif prop_def.value_type.value == "average":
            component_prop.average_value = calc_result.value
            component_prop.tolerance = 0  # Could be calculated from uncertainty propagation
        elif prop_def.value_type.value == "range":
            # For calculated values, assume no range unless specified
            component_prop.min_value = calc_result.value
            component_prop.max_value = calc_result.value
        
        # Update calculation metadata
        component_prop.last_calculated = datetime.utcnow()
        component_prop.calculation_inputs = calc_result.input_values
        component_prop.calculation_status = "calculated"
        component_prop.source = "Formula calculation"