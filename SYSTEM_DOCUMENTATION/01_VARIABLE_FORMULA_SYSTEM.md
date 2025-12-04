# Variable Formula System Documentation

## Executive Summary

The DRIP Variable Formula System enables dynamic property calculations through mathematical expressions with variable references. This system is fundamental to the DRIP platform, allowing engineers to define complex relationships between component properties, material characteristics, and physical constants.

## Core Concepts

### Variable Reference Syntax

All variables use the `#` prefix notation:
- Component properties: `#cmp1.length`, `#cmp001.width`
- System constants: `#g` (gravity), `#pi` (π)
- Material properties: `#steel.density`, `#aluminum.youngsModulus`

### Example Formula
```
Force = #mass * #g
Stress = #force / (#pi * (#diameter/2)^2)
```

## System Architecture

### Backend Components

#### 1. Data Models (`backend/app/models/formula_isolated.py`)

```python
PropertyFormula:
  - expression: str (e.g., "#mass * #g")
  - result_value: float (calculated)
  - result_unit: str (derived)
  - validation_status: enum
  - calculation_order: int
  - version: int

PropertyReference:
  - reference_type: enum (COMPONENT_PROPERTY, SYSTEM_CONSTANT, etc.)
  - reference_path: str (e.g., "cmp1.length")
  - resolved_value: float
  - resolved_unit: str
```

#### 2. Formula Engine (`backend/app/services/formula_engine.py`)

**Key Capabilities:**
- Expression parsing using SymPy
- Variable resolution across multiple data sources
- Circular dependency detection
- Automatic unit calculation
- Real-time evaluation

**Supported Operations:**
- Basic: `+`, `-`, `*`, `/`, `^`
- Functions: `sqrt`, `log`, `sin`, `cos`, `tan`, `exp`, `abs`, `min`, `max`
- Constants: `pi`, `e`, `tau`

#### 3. API Endpoints (`backend/app/api/v1/formulas.py`)

```
POST   /api/v1/formulas/                    # Create formula
GET    /api/v1/formulas/{id}               # Get formula details
PUT    /api/v1/formulas/{id}               # Update formula
DELETE /api/v1/formulas/{id}               # Delete formula
POST   /api/v1/formulas/create-from-expression  # Create from expression
POST   /api/v1/formulas/{id}/validate      # Validate formula
POST   /api/v1/formulas/{id}/calculate     # Calculate result
```

### Frontend Components

#### 1. FormulaInput Component
- Real-time variable suggestions
- Tab completion for variables
- Syntax validation
- Unit preview

#### 2. FormulaEditor Component
- Full formula creation interface
- Variable reference management
- Expression builder
- Preview calculations

#### 3. Variable Resolution Utilities
- Client-side parsing
- Variable detection
- Expression validation

## Usage Patterns

### Creating a Formula

#### Via API:
```json
POST /api/v1/formulas/create-from-expression
{
  "property_id": 123,
  "expression": "#mass * #g",
  "description": "Calculate weight from mass"
}
```

#### Via UI:
1. Open property editor
2. Select "Formula" mode
3. Type expression with `#` variables
4. System suggests matching variables
5. Preview calculation result
6. Save formula

### Variable Resolution Process

1. **User types**: `#m`
2. **System searches**:
   - Component properties starting with 'm'
   - System constants (matches none)
   - Material properties containing 'm'
3. **Suggestions shown**:
   - `#mass` (component property)
   - `#modulus` (material property)
   - `#steel.modulus` (specific material)
4. **User selects**: Tab to complete

### Unit Calculation

The system automatically derives units from operations:

```
#force [N] / #area [m²] = result [N/m²] or [Pa]
#velocity [m/s] * #time [s] = result [m]
#energy [J] / #mass [kg] = result [m²/s²]
```

## Best Practices

### Formula Design

1. **Use Descriptive Variables**
   ```
   Good:  #beam.length * #beam.width * #beam.height
   Poor:  #l * #w * #h
   ```

2. **Include Units in Variable Names When Ambiguous**
   ```
   #pressure_MPa instead of #pressure
   #temperature_K instead of #temperature
   ```

3. **Break Complex Formulas into Steps**
   ```
   Step 1: #area = #pi * (#diameter/2)^2
   Step 2: #stress = #force / #area
   ```

### Error Handling

Common errors and solutions:

1. **Circular Dependency**
   - Error: "Formula creates circular dependency"
   - Solution: Review formula chain, ensure no property references itself

2. **Unit Mismatch**
   - Error: "Cannot add [m] and [kg]"
   - Solution: Check formula logic, ensure dimensional consistency

3. **Undefined Variable**
   - Error: "Variable #xyz not found"
   - Solution: Verify variable exists and is accessible

## Advanced Features

### Formula Templates

Pre-defined formulas for common calculations:

```python
# Stress calculation template
template = FormulaTemplate(
    name="Tensile Stress",
    expression="#force / #cross_sectional_area",
    required_variables=["force", "cross_sectional_area"],
    expected_unit="Pa"
)
```

### Dependency Management

The system tracks formula dependencies:

```
Property A: #b + #c
Property B: #d * 2
Property C: constant
Property D: #e / #f

Dependency tree:
A → [B, C]
B → [D]
D → [E, F]
```

### Calculation History

Every calculation is logged:
```json
{
  "formula_id": 123,
  "timestamp": "2025-12-02T10:30:00Z",
  "input_values": {"mass": 10, "g": 9.81},
  "result": 98.1,
  "unit": "N",
  "calculation_time_ms": 15
}
```

## Integration Points

### With Component System
- Properties can have formula-based values
- Changes propagate through dependency chain
- Validation ensures consistency

### With Materials Database
- Direct access to material properties
- Automatic unit conversion
- Temperature-dependent properties supported

### With Unit System
- Automatic unit derivation
- Unit consistency validation
- Custom unit definitions

## Performance Considerations

### Optimization Strategies

1. **Caching**: Calculated values cached until dependencies change
2. **Batch Processing**: Multiple formulas evaluated in single pass
3. **Lazy Evaluation**: Formulas only calculated when accessed
4. **Dependency Ordering**: Optimal calculation sequence

### Limits

- Max formula length: 1000 characters
- Max dependencies: 50 per formula
- Max calculation depth: 20 levels
- Timeout: 5 seconds per calculation

## Troubleshooting Guide

### Common Issues

1. **Formula Not Updating**
   - Check dependency chain
   - Verify all variables resolved
   - Look for circular dependencies

2. **Incorrect Units**
   - Review unit definitions
   - Check for implicit conversions
   - Verify base unit consistency

3. **Performance Issues**
   - Reduce formula complexity
   - Check for calculation loops
   - Enable caching

## Future Roadmap

### Planned Enhancements

1. **Advanced Functions**
   - Statistical functions (mean, std)
   - Engineering functions (beam calculations)
   - Material-specific functions

2. **Visual Formula Builder**
   - Drag-drop interface
   - Visual dependency graph
   - Step-by-step debugger

3. **Formula Optimization**
   - Automatic simplification
   - Common subexpression elimination
   - Parallel evaluation

4. **Extended Variable Types**
   - Array/matrix support
   - Time-series data
   - Conditional expressions

## API Reference

### Key Endpoints

```typescript
// Get available variables
GET /api/v1/variables/search?q=mass

// Create formula from expression
POST /api/v1/formulas/create-from-expression
{
  "property_id": 123,
  "expression": "#mass * #g"
}

// Validate formula
POST /api/v1/formulas/{id}/validate

// Calculate result
POST /api/v1/formulas/{id}/calculate
{
  "context": {
    "component_id": 456
  }
}
```

## Code Examples

### Python (Backend)

```python
# Create and evaluate formula
formula = FormulaEngine.create_formula(
    property_id=123,
    expression="#mass * #g"
)
result = FormulaEngine.evaluate(formula, context)
print(f"Result: {result.value} {result.unit}")
```

### TypeScript (Frontend)

```typescript
// Use formula in component
const formula = useFormula(propertyId);
const result = formula.calculate({
  variables: {
    mass: 10,
    g: 9.81
  }
});
```

---

*Last Updated: December 2, 2025*
*System Version: 1.0.0*
*Priority: HIGHEST - Core mathematical foundation for DRIP platform*