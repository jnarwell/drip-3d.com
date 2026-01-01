# Physics Models System Documentation

## Overview

The Physics Models system enables creation of reusable physics/engineering calculation templates that integrate with the DRIP Team Portal's reactive value system. Models define mathematical relationships between inputs and outputs with full dimensional analysis validation.

**Built**: December 26-27, 2025 (parallel development across 6 instances in ~30 minutes)

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Physics Models System                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐      │
│  │  Model Builder  │    │Instance Creator │    │  Models List    │      │
│  │  (4-step wizard)│    │ (4-step wizard) │    │   (/models)     │      │
│  └────────┬────────┘    └────────┬────────┘    └─────────────────┘      │
│           │                      │                                       │
│  ─────────┴──────────────────────┴───────────────────────────────────── │
│                              REST API                                    │
│  ───────────────────────────────────────────────────────────────────── │
│           │                      │                                       │
│  ┌────────┴────────┐    ┌────────┴────────┐                             │
│  │ Equation Engine │    │  Dimensional    │                             │
│  │ - Parser        │    │  Analysis       │                             │
│  │ - Evaluator     │    │ (32 dimensions) │                             │
│  │ - LaTeX Gen     │    │ (197 units)     │                             │
│  └────────┬────────┘    └────────┬────────┘                             │
│           │                      │                                       │
│  ─────────┴──────────────────────┴───────────────────────────────────── │
│                           Model Evaluation                               │
│  ───────────────────────────────────────────────────────────────────── │
│           │                                                              │
│  ┌────────┴────────┐    ┌─────────────────┐                             │
│  │ PhysicsModel    │    │   ValueNode     │                             │
│  │ ModelVersion    │───>│ (output values) │                             │
│  │ ModelInstance   │    │ source_model_   │                             │
│  │ ModelInput      │    │ instance_id     │                             │
│  └─────────────────┘    └─────────────────┘                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Concepts

| Concept | Description |
|---------|-------------|
| **PhysicsModel** | Template identity (e.g., "Thermal Expansion Calculator") |
| **PhysicsModelVersion** | Specific version with inputs, outputs, and equations |
| **ModelInstance** | Binding of a model version to concrete input sources |
| **ModelInput** | Single input binding (to ValueNode, LOOKUP, Constant, or Literal) |
| **Output ValueNode** | Computed results with `source_model_instance_id` tracking |

---

## Database Models

### PhysicsModel

Template identity that survives version changes.

```python
# Table: physics_models

id: int                    # Primary key
name: str(200)             # "Thermal Expansion Calculator"
description: text          # Full description
category: str(50)          # "thermal", "mechanical", "fluid", "electrical"
created_by: str(100)       # User email
created_at: datetime
updated_at: datetime

# Relationships
versions: List[PhysicsModelVersion]
```

**Categories**:
- `thermal` - Heat transfer, thermal expansion
- `mechanical` - Stress, strain, deformation
- `fluid` - Flow, pressure drop
- `electrical` - Circuits, resistance
- `acoustic` - Sound, vibration
- `optical` - Light, refraction

### PhysicsModelVersion

Specific version containing equations and schemas.

```python
# Table: physics_model_versions

id: int                    # Primary key
physics_model_id: int      # FK → physics_models.id
version: int               # Version number (1, 2, 3...)
is_current: bool           # True for active version
changelog: text            # What changed

# Schema definitions (JSONB)
inputs: List[dict]         # Input variable definitions
outputs: List[dict]        # Output variable definitions
equations: dict            # {output_name: expression}

# Cached representations
equation_ast: dict         # Pre-parsed AST for fast evaluation
equation_latex: text       # LaTeX rendering for display

created_by: str(100)
created_at: datetime

# Relationships
physics_model: PhysicsModel
instances: List[ModelInstance]

# Constraints
UNIQUE(physics_model_id, version)
```

**Input Schema Format**:
```json
[
  {
    "name": "length",
    "unit": "m",
    "required": true,
    "description": "Initial length"
  },
  {
    "name": "CTE",
    "unit": "1/K",
    "required": true,
    "description": "Coefficient of thermal expansion"
  }
]
```

**Output Schema Format**:
```json
[
  {
    "name": "expansion",
    "unit": "m",
    "expression": "length * CTE * delta_T",
    "description": "Calculated expansion"
  }
]
```

### ModelInstance

Binding of a model version to concrete inputs.

```python
# Table: model_instances

id: int                    # Primary key
model_version_id: int      # FK → physics_model_versions.id
component_id: int          # FK → components.id (optional)
name: str(200)             # Friendly name for this instance

created_by: str(100)
created_at: datetime
last_computed: datetime    # When outputs were last calculated
computation_status: enum   # VALID, STALE, ERROR, PENDING, CIRCULAR

# Relationships
model_version: PhysicsModelVersion
component: Component       # Optional attachment
inputs: List[ModelInput]
```

### ModelInput

Single input binding for a ModelInstance.

```python
# Table: model_inputs

id: int                    # Primary key
model_instance_id: int     # FK → model_instances.id
input_name: str(100)       # Must match schema input name

# Source binding - ONE of these should be set:
source_value_node_id: int  # FK → value_nodes.id (Component Property)
source_lookup: dict        # LOOKUP expression {"table": "...", "conditions": {...}}
literal_value: float       # Direct constant value
literal_unit_id: int       # FK → units.id (for literal)

# Relationships
model_instance: ModelInstance
source_value_node: ValueNode
literal_unit: Unit
```

**Binding Types**:

| Type | Field(s) Used | Example |
|------|---------------|---------|
| Component Property | `source_value_node_id` | Reference to `#SYSTEM.length` |
| LOOKUP | `source_lookup` | `{"table": "steam", "key": "h", "conditions": {"T": 373}}` |
| Constant | `literal_value`, `literal_unit_id` | System constant like `g` |
| Literal | `literal_value`, `literal_unit_id` | User-entered `0.003` |

### ValueNode Extension

The existing ValueNode model was extended to track physics model outputs:

```python
# Added to value_nodes table

source_model_instance_id: int  # FK → model_instances.id (optional)
source_output_name: str(100)   # Which output this represents (e.g., "expansion")
```

When a ModelInstance computes, it creates ValueNodes with these fields set. This enables:
- Querying all outputs for an instance
- Reference in expressions: `#COMPONENT.thermal_expansion`
- Integration with reactive dependency system

---

## Equation Engine

Location: `backend/app/services/equation_engine/`

### Module Structure

```
equation_engine/
├── __init__.py          # Public API exports
├── parser.py            # SymPy to AST converter
├── evaluator.py         # AST tree walker
├── latex_generator.py   # AST to LaTeX converter
└── exceptions.py        # Custom exception classes
```

### Supported Operators

| Operator | Syntax | Example |
|----------|--------|---------|
| Addition | `+` | `a + b` |
| Subtraction | `-` | `a - b` |
| Multiplication | `*` | `a * b` |
| Division | `/` | `a / b` |
| Power | `**` or `^` | `a ** 2`, `a^2` |

### Supported Functions

| Function | Syntax | Notes |
|----------|--------|-------|
| Square root | `sqrt(x)` | x must be non-negative |
| Sine | `sin(x)` | x in radians |
| Cosine | `cos(x)` | x in radians |
| Tangent | `tan(x)` | x in radians, not at asymptotes |
| Exponential | `exp(x)` | e^x |
| Natural log | `ln(x)` or `log(x)` | x must be positive |
| Absolute value | `abs(x)` | |

### Supported Constants

| Constant | Value | Notes |
|----------|-------|-------|
| `pi` | 3.14159... | Circle ratio |
| `e` | 2.71828... | Euler's number |

### Parser API

```python
from app.services.equation_engine import parse_equation, EquationParseError, UnknownInputError

# Parse an equation
parsed = parse_equation(
    "length * CTE * delta_T",
    allowed_inputs=["length", "CTE", "delta_T"]
)

# Returns:
{
    "original": "length * CTE * delta_T",
    "ast": {
        "type": "mul",
        "operands": [
            {"type": "input", "name": "length"},
            {"type": "input", "name": "CTE"},
            {"type": "input", "name": "delta_T"}
        ]
    },
    "inputs": ["CTE", "delta_T", "length"],  # Sorted
    "sympy_expr": <SymPy expression object>
}
```

### AST Node Types

```python
# Constant value
{"type": "const", "value": 3.14}
{"type": "const", "value": 3.14159, "name": "pi"}  # Named constant

# Input variable
{"type": "input", "name": "length"}

# Binary operations
{"type": "add", "operands": [...]}
{"type": "mul", "operands": [...]}
{"type": "div", "numerator": {...}, "denominator": {...}}
{"type": "pow", "base": {...}, "exponent": {...}}

# Unary operations
{"type": "neg", "operand": {...}}
{"type": "func", "name": "sqrt", "arg": {...}}
{"type": "func", "name": "sin", "arg": {...}}
```

### Evaluator API

```python
from app.services.equation_engine import evaluate_equation, evaluate_with_result

# Evaluate AST with input values
result = evaluate_equation(
    parsed["ast"],
    {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
)
# Returns: 0.00001215

# Structured result with error handling
result = evaluate_with_result(parsed, input_values)
# Returns:
{
    "success": True,
    "value": 0.00001215,
    "inputs_used": {"length": 0.003, "CTE": 8.1e-6, "delta_T": 500}
}
# Or on error:
{
    "success": False,
    "error": "Division by zero",
    "error_type": "EvaluationError"
}
```

### LaTeX Generator API

```python
from app.services.equation_engine import generate_latex, SYMBOL_LATEX_MAP

# Generate LaTeX from parsed equation
latex = generate_latex(parsed)
# Returns: "L \cdot \alpha \cdot \Delta T"

# Custom symbol mapping
custom_map = {"my_var": r"\xi"}
latex = generate_latex(parsed, symbol_map=custom_map)
```

### Symbol to LaTeX Mapping

The generator includes automatic symbol beautification:

| Input Symbol | LaTeX Output | Display |
|-------------|--------------|---------|
| `delta_T` | `\Delta T` | ΔT |
| `delta_x` | `\Delta x` | Δx |
| `CTE` | `\alpha` | α |
| `length` | `L` | L |
| `width` | `W` | W |
| `height` | `H` | H |
| `area` | `A` | A |
| `volume` | `V` | V |
| `rho` | `\rho` | ρ |
| `sigma` | `\sigma` | σ |
| `Cp` | `C_p` | Cₚ |
| `T1`, `T2` | `T_1`, `T_2` | T₁, T₂ |

### Exception Types

```python
from app.services.equation_engine import (
    EquationParseError,   # Invalid syntax
    UnknownInputError,    # References undefined input
    EvaluationError       # Runtime math error
)

# UnknownInputError includes context:
except UnknownInputError as e:
    print(e.input_name)      # "undefined_var"
    print(e.allowed_inputs)  # ["length", "CTE", "delta_T"]
```

---

## Dimensional Analysis System

Location: `backend/app/services/dimensional_analysis.py`

### SI Base Dimensions

The system uses 7 SI base dimensions for physical quantity tracking:

| Symbol | Dimension | SI Unit |
|--------|-----------|---------|
| L | Length | meter (m) |
| M | Mass | kilogram (kg) |
| T | Time | second (s) |
| Θ | Temperature | kelvin (K) |
| I | Electric Current | ampere (A) |
| N | Amount of Substance | mole (mol) |
| J | Luminous Intensity | candela (cd) |

### Dimension Class

```python
from app.services.dimensional_analysis import Dimension

# Immutable, hashable dataclass
@dataclass(frozen=True)
class Dimension:
    length: int = 0       # L exponent
    mass: int = 0         # M exponent
    time: int = 0         # T exponent
    temperature: int = 0  # Θ exponent
    current: int = 0      # I exponent
    amount: int = 0       # N exponent
    luminosity: int = 0   # J exponent
```

### Dimension Arithmetic

```python
# Multiplication (add exponents)
FORCE = MASS * ACCELERATION
# M·L·T⁻² = M × L·T⁻²

# Division (subtract exponents)
VELOCITY = LENGTH / TIME
# L·T⁻¹ = L / T

# Power (multiply exponents)
AREA = LENGTH ** 2
# L² = L^2

# Check compatibility
dim1.is_compatible_with(dim2)  # True if equal
dim.is_dimensionless()          # True if all exponents are 0
```

### Predefined Dimensions (32 total)

**Base Dimensions**:
```python
DIMENSIONLESS = Dimension()
LENGTH = Dimension(length=1)
MASS = Dimension(mass=1)
TIME = Dimension(time=1)
TEMPERATURE = Dimension(temperature=1)
CURRENT = Dimension(current=1)
AMOUNT = Dimension(amount=1)
LUMINOSITY = Dimension(luminosity=1)
```

**Derived Geometric**:
```python
AREA = Dimension(length=2)                    # L²
VOLUME = Dimension(length=3)                  # L³
```

**Mechanical**:
```python
VELOCITY = Dimension(length=1, time=-1)                      # L·T⁻¹
ACCELERATION = Dimension(length=1, time=-2)                  # L·T⁻²
FORCE = Dimension(mass=1, length=1, time=-2)                 # M·L·T⁻²
PRESSURE = Dimension(mass=1, length=-1, time=-2)             # M·L⁻¹·T⁻²
ENERGY = Dimension(mass=1, length=2, time=-2)                # M·L²·T⁻²
POWER = Dimension(mass=1, length=2, time=-3)                 # M·L²·T⁻³
TORQUE = Dimension(mass=1, length=2, time=-2)                # M·L²·T⁻²
FREQUENCY = Dimension(time=-1)                               # T⁻¹
DENSITY = Dimension(mass=1, length=-3)                       # M·L⁻³
VOLUME_FLOW = Dimension(length=3, time=-1)                   # L³·T⁻¹
MASS_FLOW = Dimension(mass=1, time=-1)                       # M·T⁻¹
DYNAMIC_VISCOSITY = Dimension(mass=1, length=-1, time=-1)    # M·L⁻¹·T⁻¹
KINEMATIC_VISCOSITY = Dimension(length=2, time=-1)           # L²·T⁻¹
```

**Electrical**:
```python
VOLTAGE = Dimension(mass=1, length=2, time=-3, current=-1)      # M·L²·T⁻³·I⁻¹
RESISTANCE = Dimension(mass=1, length=2, time=-3, current=-2)   # M·L²·T⁻³·I⁻²
CAPACITANCE = Dimension(mass=-1, length=-2, time=4, current=2)  # M⁻¹·L⁻²·T⁴·I²
INDUCTANCE = Dimension(mass=1, length=2, time=-2, current=-2)   # M·L²·T⁻²·I⁻²
```

**Thermal**:
```python
THERMAL_CONDUCTIVITY = Dimension(mass=1, length=1, time=-3, temperature=-1)  # W/(m·K)
SPECIFIC_HEAT = Dimension(length=2, time=-2, temperature=-1)                  # J/(kg·K)
HEAT_TRANSFER_COEFF = Dimension(mass=1, time=-3, temperature=-1)             # W/(m²·K)
THERMAL_EXPANSION = Dimension(temperature=-1)                                 # 1/K
SPECIFIC_ENERGY = Dimension(length=2, time=-2)                               # J/kg
SPECIFIC_ENTROPY = Dimension(length=2, time=-2, temperature=-1)              # J/(kg·K)
SPECIFIC_VOLUME = Dimension(length=3, mass=-1)                               # m³/kg
```

### Unit to Dimension Mapping (197 units)

The `UNIT_DIMENSIONS` dictionary maps unit symbols to their dimensions:

**Length Units** (12 mappings):
```python
'nm', 'μm', 'mm', 'cm', 'm', 'km',  # Metric
'in', 'ft', 'yd', 'mi', 'mil', 'thou'  # Imperial
```

**Area Units** (10 mappings):
```python
'mm²', 'cm²', 'm²', 'km²', 'ha',  # Metric
'in²', 'ft²', 'yd²', 'mi²', 'acre'  # Imperial
```

**Volume Units** (11 mappings):
```python
'mm³', 'cm³', 'mL', 'L', 'm³', 'km³',  # Metric
'in³', 'ft³', 'gal', 'fl oz', 'bbl'  # Imperial
```

**Pressure Units** (11 mappings):
```python
'Pa', 'kPa', 'MPa', 'GPa', 'bar', 'mbar',  # Metric
'psi', 'ksi', 'psf', 'inHg', 'inH₂O'  # Imperial
```

**Temperature Units** (12 mappings):
```python
'K', 'kelvin', '°C', '℃', 'degC', 'celsius',
'°F', '℉', 'degF', 'fahrenheit', '°R', 'rankine'
```

**Thermal Expansion Units** (8 mappings):
```python
'1/K', '1/°C', 'ppm/K', 'ppm/°C', 'µm/(m·K)',
'1/°F', '1/°R', 'ppm/°F'
```

**Full list**: 197 unit symbols mapped to 32 dimensions.

### Validation Functions

```python
from app.services.dimensional_analysis import (
    validate_equation_dimensions,
    check_dimensional_consistency,
    infer_dimension,
    get_unit_dimension
)

# Get dimension for a unit
dim = get_unit_dimension('Pa')  # Returns PRESSURE

# Validate equation dimensions match expected output
is_valid, error_msg = validate_equation_dimensions(
    equation_ast=parsed['ast'],
    input_dimensions={
        "length": LENGTH,
        "CTE": THERMAL_EXPANSION,
        "delta_T": TEMPERATURE
    },
    expected_output_dimension=LENGTH
)
# Returns: (True, "") for L × Θ⁻¹ × Θ = L

# Check consistency without expected dimension
is_consistent, error_msg, computed_dim = check_dimensional_consistency(
    equation_ast=parsed['ast'],
    input_dimensions=input_dims
)

# Infer dimension from AST
computed_dim = infer_dimension(ast, input_dimensions)
```

### Dimension Rules

**Addition/Subtraction**: Dimensions must match exactly
```python
# Valid: LENGTH + LENGTH = LENGTH
# Invalid: LENGTH + TIME → DimensionError
```

**Multiplication**: Add exponents
```python
# MASS × ACCELERATION = FORCE
# M × L·T⁻² = M·L·T⁻²
```

**Division**: Subtract exponents
```python
# LENGTH / TIME = VELOCITY
# L / T = L·T⁻¹
```

**Power**: Multiply exponents by power
```python
# LENGTH ** 2 = AREA
# L² = L^2
```

**Square Root**: Halve exponents (must be even)
```python
# sqrt(AREA) = LENGTH
# √(L²) = L
```

**Functions (sin, cos, exp, ln)**: Require dimensionless input, return dimensionless
```python
# sin(angle) → Valid (angle is dimensionless)
# sin(length) → DimensionError
```

---

## Model Evaluation Service

Location: `backend/app/services/model_evaluation.py`

### Core Functions

```python
from app.services.model_evaluation import (
    evaluate_model_instance,
    resolve_model_input,
    create_component_properties_for_outputs,
    evaluate_and_attach,
    get_instance_outputs,
    invalidate_instance_outputs,
    ModelEvaluationError
)
```

### evaluate_model_instance()

Main entry point for model evaluation.

```python
def evaluate_model_instance(
    instance: ModelInstance,
    db: Session
) -> List[ValueNode]:
    """
    Evaluate a ModelInstance and create output ValueNodes.

    Flow:
    1. Get model version with equations
    2. Resolve all input bindings to float values
    3. Evaluate each output equation
    4. Create ValueNode for each output with source tracking

    Returns:
        List of created ValueNode objects (one per output)

    Raises:
        ModelEvaluationError: If evaluation fails
    """
```

### resolve_model_input()

Resolves a single input binding to a float value.

```python
def resolve_model_input(model_input: ModelInput, db: Session) -> float:
    """
    Handles:
    - source_value_node_id: Get ValueNode.computed_value
    - literal_value + literal_unit_id: Return literal (assumed SI)
    - source_lookup: Execute LOOKUP (NotImplementedError for now)

    Raises:
        ModelEvaluationError: If input cannot be resolved
    """
```

### evaluate_and_attach()

Convenience function for full evaluation with component attachment.

```python
def evaluate_and_attach(instance: ModelInstance, db: Session) -> Dict[str, Any]:
    """
    1. Evaluates the model instance
    2. Creates component properties for outputs (if attached)
    3. Returns structured result

    Returns:
        {
            "output_nodes": List[ValueNode],
            "properties": List[ComponentProperty],
            "references": ["#SYSTEM.thermal_expansion", ...]
        }
    """
```

### Output ValueNode Creation

When a ModelInstance is evaluated, output ValueNodes are created with:

```python
ValueNode(
    node_type=NodeType.LITERAL,           # Computed results stored as literals
    numeric_value=result,
    computed_value=result,
    computed_unit_symbol=output_unit,
    computation_status=ComputationStatus.VALID,
    last_computed=datetime.utcnow(),
    source_model_instance_id=instance.id,  # Tracks origin
    source_output_name=output_name,        # "expansion"
    description=f"Model output: {output_name}"
)
```

### Invalidation

When input bindings change:

```python
# Mark all outputs as stale
count = invalidate_instance_outputs(instance, db)

# Get existing outputs without re-evaluating
outputs = get_instance_outputs(instance, db)
```

---

## API Endpoints

Location: `backend/app/api/v1/physics_models.py`

### List Physics Models

```
GET /api/v1/physics-models
```

**Query Parameters**:
- `category` (optional): Filter by category

**Response**:
```json
[
  {
    "id": 1,
    "name": "Thermal Expansion",
    "description": "Calculates thermal expansion",
    "category": "thermal",
    "created_at": "2025-12-27T00:00:00Z",
    "current_version": {
      "id": 1,
      "version": 1,
      "inputs": [...],
      "outputs": [...],
      "equations": {"expansion": "length * CTE * delta_T"}
    }
  }
]
```

### Get Physics Model

```
GET /api/v1/physics-models/{model_id}
```

**Response**: Full model with all versions.

### Validate Physics Model

```
POST /api/v1/physics-models/validate
```

Called by Model Builder Step 4 before creation.

**Request Body**:
```json
{
  "inputs": [
    {"name": "length", "unit": "m", "required": true},
    {"name": "CTE", "unit": "1/K", "required": true},
    {"name": "delta_T", "unit": "K", "required": true}
  ],
  "outputs": [
    {"name": "expansion", "unit": "m"}
  ],
  "equations": [
    {"output_name": "expansion", "expression": "length * CTE * delta_T"}
  ]
}
```

**Response**:
```json
{
  "valid": true,
  "errors": [],
  "dimensional_analysis": {
    "expansion": {
      "valid": true,
      "message": "Dimensions valid"
    }
  },
  "latex_preview": {
    "expansion": "L \\cdot \\alpha \\cdot \\Delta T"
  }
}
```

**Error Response** (dimension mismatch):
```json
{
  "valid": false,
  "errors": [
    "Dimension error in 'expansion': Dimension mismatch: equation produces Dimension(L · Θ), but expected Dimension(L)"
  ],
  "dimensional_analysis": {
    "expansion": {
      "valid": false,
      "message": "Dimension mismatch..."
    }
  }
}
```

### Create Physics Model

```
POST /api/v1/physics-models
```

**Request Body**:
```json
{
  "name": "Thermal Expansion",
  "description": "Calculates thermal expansion for materials",
  "category": "thermal",
  "inputs": [...],
  "outputs": [...],
  "equations": [...]
}
```

**Response**:
```json
{
  "id": 1,
  "name": "Thermal Expansion",
  "category": "thermal",
  "current_version": {
    "id": 1,
    "version": 1,
    "equation_latex": "{\"expansion\": \"L \\\\cdot \\\\alpha \\\\cdot \\\\Delta T\"}"
  }
}
```

### Create Model Instance

```
POST /api/v1/model-instances
```

**Request Body**:
```json
{
  "name": "Thermal Expansion Instance",
  "model_version_id": 1,
  "target_component_id": 5,
  "bindings": {
    "length": "0.003",
    "CTE": "8.1e-6",
    "delta_T": "500"
  }
}
```

**Response**:
```json
{
  "id": 1,
  "name": "Thermal Expansion Instance",
  "model_version_id": 1,
  "component_id": 5,
  "bindings": {...},
  "output_value_nodes": []
}
```

### Get Model Instance

```
GET /api/v1/model-instances/{instance_id}
```

### List Categories

```
GET /api/v1/physics-models/categories
```

**Response**:
```json
{
  "categories": [
    {"id": "thermal", "name": "Thermal", "description": "Heat transfer, thermal expansion"},
    {"id": "mechanical", "name": "Mechanical", "description": "Stress, strain, deformation"},
    {"id": "fluid", "name": "Fluid Dynamics", "description": "Flow, pressure drop"},
    {"id": "electrical", "name": "Electrical", "description": "Circuits, resistance"},
    {"id": "acoustic", "name": "Acoustic", "description": "Sound, vibration"},
    {"id": "optical", "name": "Optical", "description": "Light, refraction"}
  ]
}
```

---

## Frontend Routes

### Models List

```
Route: /models
Component: frontend/src/pages/ModelsList.tsx
```

Displays all physics models with:
- Category badges
- Description preview
- "New Model" button
- "Instantiate" button

### Model Builder

```
Route: /models/new
Component: frontend/src/pages/ModelBuilder/index.tsx
```

4-step wizard for creating physics models:

| Step | Component | Purpose |
|------|-----------|---------|
| 1 | StepDefineModel | Name, description, category |
| 2 | StepInputsOutputs | Add inputs and outputs with units |
| 3 | StepEquations | Enter equation for each output |
| 4 | StepValidate | Dimensional validation, LaTeX preview, create |

**Step Flow**:
```
Define Model → Inputs/Outputs → Equations → Validate & Create
```

### Instance Creator

```
Route: /instances/new
Route: /instances/new/:modelId (with pre-selected model)
Component: frontend/src/pages/InstanceCreator/index.tsx
```

4-step wizard for instantiating models:

| Step | Component | Purpose |
|------|-----------|---------|
| 1 | StepSelectModel | Browse and select a model |
| 2 | StepBindInputs | Bind inputs to sources |
| 3 | StepAttachComponent | Optionally attach to component |
| 4 | StepReview | Review and create instance |

**Binding Types in UI**:
- Component Property (selector)
- LOOKUP (expression builder)
- Constant (dropdown of system constants)
- Literal (direct value entry)

### Frontend Types

```typescript
// ModelBuilderData - Wizard state
interface ModelBuilderData {
  name: string;
  description: string;
  category: string;
  inputs: ModelVariable[];
  outputs: ModelVariable[];
  equations: Record<string, string>;
}

// ModelVariable - Input/output definition
interface ModelVariable {
  id: string;           // Temporary UI ID
  name: string;
  unit: string;
  description?: string;
}

// Categories
const MODEL_CATEGORIES = [
  { value: 'thermal', label: 'Thermal' },
  { value: 'mechanical', label: 'Mechanical' },
  { value: 'acoustic', label: 'Acoustic' },
  // ... 10 categories total
];
```

---

## Testing

### Test Files

```
backend/tests/
├── test_equation_engine/
│   ├── test_parser.py        # Equation parsing tests
│   ├── test_evaluator.py     # Evaluation tests
│   └── test_latex.py         # LaTeX generation tests
├── test_dimensional_analysis.py  # Dimension validation tests
├── test_physics_models.py        # API endpoint tests
└── test_integration/
    ├── test_model_creation.py    # Model creation flow
    ├── test_instance_creation.py # Instance creation flow
    ├── test_model_evaluation.py  # Evaluation flow
    └── test_end_to_end.py        # Full workflow tests
```

### Test Coverage Summary

**Equation Engine (105 tests)**:
- Parse valid equations ✓
- Detect syntax errors ✓
- Validate input references ✓
- Evaluate with inputs ✓
- Handle math errors ✓
- Generate LaTeX ✓

**Dimensional Analysis**:
- Unit to dimension lookup ✓
- Dimension arithmetic ✓
- Equation validation ✓
- Error detection ✓

**Integration**:
- Model CRUD ✓
- Instance CRUD ✓
- Evaluation flow ✓
- Component property creation ✓

### Running Tests

```bash
cd backend
pytest tests/test_equation_engine/ -v
pytest tests/test_dimensional_analysis.py -v
pytest tests/test_integration/ -v
```

### Visual Testing

See `VISUAL_TESTING_CHECKLIST.md` for manual UI testing checklist covering:
- Model Builder wizard flow
- Instance Creator wizard flow
- Validation error handling
- LaTeX rendering

---

## Integration with Value System

### Output as ValueNode

When a ModelInstance is evaluated, outputs become ValueNodes with tracking:

```python
# Created by model evaluation
ValueNode(
    source_model_instance_id=instance.id,
    source_output_name="expansion"
)

# Query outputs for an instance
outputs = db.query(ValueNode).filter(
    ValueNode.source_model_instance_id == instance_id
).all()
```

### Reference in Expressions

If attached to a component, outputs can be referenced in expressions:

```python
# Component "SYSTEM" has model instance output "expansion"
# Other expressions can reference:
"#SYSTEM.expansion * 2"
```

### Reactive Updates

When model inputs change:
1. Instance outputs are marked STALE
2. Dependents of outputs are marked STALE
3. Cascade recalculation runs
4. Frontend invalidates queries

---

## MODEL() Expression Function

The `MODEL()` function allows inline physics model evaluation within property expressions, similar to `LOOKUP()` for table lookups.

### Syntax

```
MODEL("Model Name", input1: value1, input2: value2, output: "output_name")
```

**Parameters:**
- `"Model Name"` - Name of the physics model (case-insensitive)
- `input: value` pairs - Bindings for each model input
- `output: "name"` - (Optional) Which output to return for multi-output models

### Examples

**Simple single-output model:**
```
MODEL("Thermal Expansion", CTE: 2.3e-5, delta_T: 100, L0: 1m)
```

**Multi-output model with specific output:**
```
MODEL("Rectangle Calculator", length: 5, width: 3, output: "area")
MODEL("Rectangle Calculator", length: 5, width: 3, output: "perimeter")
```

**With property references:**
```
MODEL("Thermal Expansion", CTE: #MAT.cte, delta_T: #SYSTEM.temp_delta, L0: #PART.length)
```

**Mixed bindings:**
```
#PART.length + MODEL("Thermal Expansion", CTE: 2.3e-5, delta_T: 100, L0: 1m)
```

### Binding Value Types

| Type | Example | Description |
|------|---------|-------------|
| Literal number | `100`, `2.3e-5` | Plain numeric value |
| Literal with unit | `1m`, `25°C`, `100Pa` | Converted to SI before evaluation |
| Property reference | `#MAT.cte` | Resolved from component/material property |
| Expression | `#PART.temp - 273.15` | Evaluated before model evaluation |

### Storage Format

MODEL() calls are stored in the ValueNode's `parsed_expression` JSON:

```json
{
  "original": "#PART.length + MODEL(\"Thermal Expansion\", CTE: 2.3e-5, delta_T: 100, L0: 1m)",
  "modified": "__ref_0__ + __model_0__",
  "placeholders": {
    "__ref_0__": "PART.length"
  },
  "model_calls": {
    "__model_0__": {
      "model_name": "Thermal Expansion",
      "bindings": {
        "CTE": "2.3e-5",
        "delta_T": "100",
        "L0": "1m"
      },
      "output_name": null
    }
  }
}
```

### Evaluation Flow

1. **Parse** - Extract MODEL() calls during expression parsing
2. **Resolve bindings** - Convert each binding to a float value
   - Literals with units → SI conversion
   - Property references → ValueNode lookup
   - Expressions → Evaluate with math context
3. **Find model** - `PhysicsModel.find_by_name(db, model_name)` (case-insensitive)
4. **Get current version** - Use the model's current version equations
5. **Evaluate** - Call `evaluate_inline_model()` with resolved bindings
6. **Substitute** - Replace `__model_N__` placeholder with result
7. **Continue** - Evaluate remaining expression with SymPy

### API Helper

For debugging or direct model lookup:

```
GET /api/v1/physics-models/by-name/{model_name}
```

Returns full model metadata including equations and AST for evaluation.

### Error Handling

| Error | Cause | Message |
|-------|-------|---------|
| Model not found | Invalid model name | `Model 'XYZ' not found` |
| Missing input | Required input not bound | `Missing required inputs: CTE, delta_T` |
| Invalid output | Output name doesn't exist | `Model 'X' has no output 'Y'. Available: a, b` |
| Multi-output ambiguous | No output specified for multi-output model | `Model 'X' has multiple outputs: a, b. Specify which using: output: "name"` |
| Binding error | Can't resolve binding value | `MODEL() binding 'CTE: #INVALID' could not be resolved` |

### vs ModelInstance

| Feature | MODEL() Function | ModelInstance |
|---------|-----------------|---------------|
| Storage | Inline in expression | Separate DB record |
| Outputs | Computed fresh each time | Cached as ValueNodes |
| Dependencies | Tracked via expression refs | Explicit ModelInput records |
| Use case | Ad-hoc calculations | Persistent bindings |
| Component attachment | Via containing property | Direct attachment |

---

## Analysis Dashboard (Named Instances)

### Overview

The Analysis dashboard provides a dedicated interface for creating and monitoring named model instances that exist independently of components. While component-attached instances calculate properties for specific parts, named analyses track system-level metrics visible to the entire team.

### Use Cases

**Named Analysis instances (Analysis dashboard):**
- System-level calculations (e.g., "Achievable Droplet Distance")
- Shared team metrics that multiple engineers reference
- Monitoring values that change as the system evolves
- Calculations that don't belong to a specific component

**Component-attached instances (Instance Creator):**
- Component-specific properties (e.g., Frame thermal expansion)
- Values tied to a particular part's lifecycle
- Properties that are part of component design

**Inline MODEL() calls (Component properties):**
- Quick calculations embedded in expressions
- Ad-hoc evaluations without persistence
- Derived values within property expressions

### Comparison Table

| Feature | Named Analysis | Component Instance | Inline MODEL() |
|---------|---------------|-------------------|----------------|
| **Persistence** | Database record | Database record | Ephemeral (in expression) |
| **Visibility** | Analysis page (team-wide) | Component detail page | Property value only |
| **Component binding** | None | Required (`component_id`) | Via containing property |
| **Naming** | Required, globally unique | Optional | Anonymous |
| **Use case** | System metrics | Component calculations | Ad-hoc inline calcs |
| **Real-time updates** | WebSocket broadcasts | Per-component | Per-evaluation |
| **Created via** | Analysis page | Instance Creator | Property expression |

### Database Schema

Named analyses use the existing `model_instances` table:

```sql
-- Named analysis discriminator
WHERE component_id IS NULL AND name IS NOT NULL

-- Key fields
name VARCHAR(200) NOT NULL UNIQUE  -- Globally unique across team
description TEXT                   -- Optional description
component_id INT NULL              -- NULL for analyses
computation_status ENUM            -- VALID, STALE, ERROR, PENDING
last_computed TIMESTAMP           -- When outputs last calculated
```

**Constraints:**
- `UNIQUE(name) WHERE component_id IS NULL` - Analysis names globally unique
- `CHECK(component_id IS NOT NULL OR name IS NOT NULL)` - Analyses must have names

### API Endpoints

#### List Analyses
```http
GET /api/v1/analyses
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Achievable Distance",
    "description": "Maximum droplet travel distance",
    "model_name": "Acoustic Range",
    "computation_status": "valid",
    "last_computed": "2025-12-27T13:00:00Z",
    "outputs": [
      {
        "name": "distance",
        "computed_value": 0.0032,
        "unit": "m",
        "status": "valid"
      }
    ]
  }
]
```

**Sorted:** Alphabetically by name

#### Update Analysis
```http
PATCH /api/v1/analyses/{id}
```

**Body:**
```json
{
  "name": "New Name",
  "description": "Updated description",
  "bindings": {
    "power": "8.5",
    "frequency": "40000"
  }
}
```

**Effect:** Updates analysis and re-evaluates if bindings changed. Broadcasts update via WebSocket.

#### Delete Analysis
```http
DELETE /api/v1/analyses/{id}
```

**Effect:** Removes analysis, inputs, and output ValueNodes. Broadcasts deletion via WebSocket.

#### Force Evaluation
```http
POST /api/v1/analyses/{id}/evaluate
```

**Effect:** Immediately re-evaluates outputs, updates `last_computed`. Broadcasts evaluation complete via WebSocket.

### Real-Time Collaboration (WebSocket)

#### Connection
```javascript
// Frontend connects to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/analysis?token=<jwt>');
```

**Authentication:** JWT token in query parameter

#### Message Types

**Connection established:**
```json
{
  "type": "connected",
  "message": "Connected to Analysis updates",
  "user": "engineer@drip-3d.com"
}
```

**Instance created:**
```json
{
  "type": "instance_created",
  "data": {
    "id": 5,
    "name": "New Analysis",
    "model_name": "Thermal Stress",
    "computation_status": "VALID",
    "outputs": [...]
  }
}
```

**Instance updated:**
```json
{
  "type": "instance_updated",
  "data": {
    "id": 5,
    "name": "Updated Name",
    "..."
  }
}
```

**Instance deleted:**
```json
{
  "type": "instance_deleted",
  "data": {
    "id": 5,
    "name": "Deleted Analysis"
  }
}
```

**Instance evaluated:**
```json
{
  "type": "instance_evaluated",
  "data": {
    "id": 5,
    "computation_status": "VALID",
    "last_computed": "2025-12-27T13:05:00Z",
    "outputs": [...]
  }
}
```

#### Use Case: Multi-Engineer Collaboration

**Scenario:** Two engineers working on different aspects of the system

1. **Engineer A** creates "System Power Budget" analysis
   - WebSocket broadcasts `instance_created` to all connected clients
   - **Engineer B's** Analysis page updates automatically

2. **Engineer A** updates power input from 8W to 10W
   - WebSocket broadcasts `instance_updated`
   - **Engineer B** sees updated value in real-time

3. **Engineer B** deletes outdated "Old Thermal Test" analysis
   - WebSocket broadcasts `instance_deleted`
   - Removed from **Engineer A's** list instantly

**No page refresh needed.** Changes propagate immediately to all team members.

### Frontend Routes

| Route | Component | Purpose |
|-------|-----------|---------|
| `/analysis` | `Analysis.tsx` | List all analyses, sorted alphabetically |
| `/analysis/new` | `AnalysisCreator.tsx` | 4-step wizard: Name → Model → Bindings → Review |
| `/analysis/:id/edit` | `AnalysisCreator.tsx` | Edit existing analysis (edit mode) |

### Continuous Updates

Analyses update reactively through the existing ValueNode dependency system:

1. **Dependency created:**
   - Analysis input: `power: #TRANSDUCER.Max_Power`
   - Creates `ValueDependency` edge

2. **Source changes:**
   - Engineer updates `TRANSDUCER.Max_Power` from 8W to 10W
   - System marks all dependent analyses as STALE

3. **Re-evaluation:**
   - On next access or manual refresh
   - Outputs recalculated with new input values
   - Status → VALID
   - WebSocket broadcasts `instance_evaluated`

4. **All clients update:**
   - Everyone sees new values in real-time

### Examples

**Example 1: Acoustic Performance**
```
Name: "Achievable Distance"
Model: "Acoustic Range"
Bindings:
  - power: #TRANSDUCER.Max_Power
  - frequency: 40000 (literal)
  - droplet_mass: LOOKUP("aluminum", "density") * VOLUME
Output:
  - distance: 3.2 mm (updates when transducer power changes)
```

**Example 2: System Power Budget**
```
Name: "Total Power Consumption"
Model: "Power Sum"
Bindings:
  - transducer_power: #TRANSDUCER.Max_Power
  - heater_power: #HEATER.Power
  - electronics_power: 2.5 (literal)
Output:
  - total_power: 15.6 W
Status: STALE (heater power changed)
```

**Example 3: Multi-Output Model**
```
Name: "Thermal Envelope"
Model: "Temperature Distribution"
Bindings:
  - ambient_temp: #SENSOR.Ambient
  - power_dissipation: #Total_Power.result
Outputs:
  - max_temp: 85.2°C
  - min_temp: 23.1°C
  - delta_temp: 62.1 K
```

### Error Handling

**Analysis creation errors:**

| Error | Cause | HTTP Code |
|-------|-------|-----------|
| "Analysis name already exists" | Duplicate name | 400 |
| "Missing required inputs" | Required bindings not provided | 400 |
| "Model not found" | Invalid model_version_id | 404 |

**Runtime errors:**

| Status | Meaning | Display |
|--------|---------|---------|
| VALID | Outputs current | Green badge |
| STALE | Inputs changed, needs re-eval | Yellow badge |
| ERROR | Evaluation failed | Red badge with error |
| PENDING | Currently evaluating | Blue badge with spinner |

**WebSocket errors:**
- Connection lost → Auto-reconnect with exponential backoff (max 5 attempts)
- Authentication failed → Close connection, redirect to login
- Invalid message → Log error, continue operation

### Implementation Details

**Code locations:**
- Backend API: `backend/app/api/v1/physics_models.py` (analyses endpoints)
- WebSocket: `backend/app/api/v1/websocket.py`, `backend/app/services/websocket_manager.py`
- Frontend page: `frontend/src/pages/analysis/Analysis.tsx`
- Frontend creator: `frontend/src/pages/analysis/AnalysisCreator.tsx`
- WebSocket hook: `frontend/src/hooks/useAnalysisWebSocket.ts`

**Dependencies:**
- Same evaluation engine as MODEL() and Instance Creator
- Same dependency tracking as ValueNode system
- FastAPI WebSocket support for real-time updates

---

## Example: Thermal Expansion Model

### Model Definition

```json
{
  "name": "Thermal Expansion",
  "category": "thermal",
  "inputs": [
    {"name": "length", "unit": "m", "description": "Initial length"},
    {"name": "CTE", "unit": "1/K", "description": "Coefficient of thermal expansion"},
    {"name": "delta_T", "unit": "K", "description": "Temperature change"}
  ],
  "outputs": [
    {"name": "expansion", "unit": "m", "description": "Calculated expansion"}
  ],
  "equations": {
    "expansion": "length * CTE * delta_T"
  }
}
```

### Dimensional Analysis

```
Input Dimensions:
  length:  L
  CTE:     Θ⁻¹
  delta_T: Θ

Equation: length * CTE * delta_T
  = L × Θ⁻¹ × Θ
  = L × 1
  = L ✓

Expected Output: L (length)
Result: Valid
```

### Instance with Literal Bindings

```json
{
  "name": "Steel Rod Expansion",
  "model_version_id": 1,
  "target_component_id": 5,
  "bindings": {
    "length": "0.003",
    "CTE": "8.1e-6",
    "delta_T": "500"
  }
}
```

### Evaluation Result

```
expansion = 0.003 × 8.1e-6 × 500
         = 0.00001215 m
         = 12.15 μm
```

---

## Future Enhancements

### Planned Features

1. **LOOKUP Input Binding**: Execute LOOKUP expressions from property tables
2. **Version Comparison**: Visual diff between model versions
3. **Template Library**: Pre-built models for common calculations
4. **Bulk Instantiation**: Create multiple instances at once
5. **Export/Import**: Share models between deployments

### Not Yet Implemented

- `source_lookup` binding type (raises NotImplementedError)
- Model versioning (versions are created but not editable)
- Model deletion cascade
- Permission/ownership model

---

*Last Updated: December 31, 2025*
