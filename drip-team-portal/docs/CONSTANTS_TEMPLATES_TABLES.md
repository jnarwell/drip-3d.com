# Constants, Templates, and Tables System Documentation

## Executive Summary

The Constants, Templates, and Tables system provides the foundation for engineering data management in DRIP. It enables storage, verification, and utilization of physical constants, engineering property tables, and reusable data templates with comprehensive source tracking and quality assurance.

## System Components

### 1. System Constants

#### Overview
System constants provide reliable physical, mathematical, and engineering values for use in formulas and calculations.

#### Data Model
```python
SystemConstant:
  symbol: str          # Unique identifier (e.g., "g", "k_B")
  name: str           # Full name (e.g., "Gravitational acceleration")
  value: float        # Numerical value (e.g., 9.80665)
  unit: str           # Units (e.g., "m/s²")
  description: str    # Detailed description
  category: str       # Physics, Chemistry, Engineering, Mathematics
  is_editable: bool   # false for system, true for user-defined
```

#### Categories

**Physics Constants:**
- `g` = 9.80665 m/s² (Standard gravity)
- `c` = 299792458 m/s (Speed of light)
- `h` = 6.62607015e-34 J⋅s (Planck constant)
- `k_B` = 1.380649e-23 J/K (Boltzmann constant)
- `N_A` = 6.02214076e23 1/mol (Avogadro constant)

**Mathematics Constants:**
- `pi` = 3.14159265358979323846
- `e` = 2.71828182845904523536
- `tau` = 6.28318530717958647692

**Engineering Constants:**
- `sigma` = 5.670374419e-8 W/(m²⋅K⁴) (Stefan-Boltzmann)
- `R` = 8.314462618 J/(mol⋅K) (Universal gas constant)

#### API Endpoints
```
GET    /api/v1/constants/              # List all constants
GET    /api/v1/constants/categories    # Get unique categories
GET    /api/v1/constants/{id}         
GET    /api/v1/constants/symbol/{sym}  # Get by symbol (e.g., "g")
POST   /api/v1/constants/              # Create custom constant
PATCH  /api/v1/constants/{id}          # Update (custom only)
DELETE /api/v1/constants/{id}          # Delete (custom only)
```

### 2. Engineering Reference Tables (YAML-based)

#### Overview
Engineering reference tables provide standardized property lookups for calculations. Data is defined in YAML files in `backend/data/` and exposed via the Engineering Properties API.

#### Source Types

**table**
- Static lookup tables with discrete inputs
- Example: ISO 286 tolerance grades, metric bolt dimensions

**equation**
- Mathematical expressions with continuous inputs
- Example: Material stress-strain relationships

**library**
- External library integration (CoolProp for thermodynamic properties)
- Example: Steam/water properties via IAPWS-IF97

#### YAML Data Model

```yaml
id: iso_286_tolerance
name: "ISO 286 Tolerance Grades"
category: tolerances
description: "Standard tolerance grades IT01-IT18"
source: "ISO 286-1:2010"
source_url: "https://www.iso.org/standard/53987.html"
type: table  # table | equation | library

inputs:
  - name: grade
    unit: "none"
    type: discrete
    values: ["IT01", "IT0", "IT1", ...]
  - name: size_range
    unit: "mm"
    type: discrete
    values: ["0-3", "3-6", ...]

outputs:
  - name: tolerance_um
    unit: µm
    description: "Tolerance in micrometers"

resolution:
  type: table
  data:
    IT01:
      "0-3": {tolerance_um: 0.3, tolerance_mm: 0.0003}
      ...

views:
  - id: default
    name: "ISO Tolerance Grades"
    grid:
      grade: {type: list, values: [...]}
      size_range: {type: list, values: [...]}
    columns:
      - output: tolerance_um
        header: "Tolerance"
        unit: "µm"
```

#### Categories

| Category | Examples |
|----------|----------|
| `tolerances` | ISO 286 tolerance grades |
| `fasteners` | Metric bolt dimensions |
| `finishes` | Surface finish Ra values |
| `process` | Steam tables (CoolProp) |
| `material` | Material property lookups |

#### API Endpoints

```
GET  /api/v1/eng-properties/sources              # List all sources
GET  /api/v1/eng-properties/sources/{id}         # Get source metadata
GET  /api/v1/eng-properties/sources/{id}/views/{view}  # Get table view data
POST /api/v1/eng-properties/lookup              # LOOKUP() function resolution
```

#### Using in Expressions

```
# LOOKUP syntax
LOOKUP("source_id", "output_name", input1=value1, input2=value2)

# Examples
LOOKUP("iso_286_tolerance", "tolerance_mm", grade="IT7", size_range="10-18")
LOOKUP("metric_bolt_dimensions", "tap_drill_coarse", size="M8")
LOOKUP("steam", "h", T=373.15, Q=1)  # Saturated steam enthalpy
```

#### Case-Insensitive Inputs

Discrete string inputs are matched case-insensitively:

```
# Both work - internally normalized to canonical "M8"
LOOKUP("metric_bolt_dimensions", "tap_drill_coarse", size="M8")
LOOKUP("metric_bolt_dimensions", "tap_drill_coarse", size="m8")
```

#### Unified Sources with lookup_source_id

Some tables have separate display views (e.g., steam by temperature, steam by pressure) but use a unified source for LOOKUP:

```yaml
# steam_temperature.yaml
id: steam_temperature
name: "Steam — Temperature"
lookup_source_id: steam  # LOOKUP uses unified "steam" source

# steam_pressure.yaml
id: steam_pressure
name: "Steam — Pressure"
lookup_source_id: steam  # Same unified source

# steam.yaml (no views, LOOKUP only)
id: steam
inputs: [T, P, Q]  # All optional, supports any combination
views: []  # Display only via steam_temperature and steam_pressure
```

This pattern allows:
- Different display views indexed by different variables
- Single LOOKUP syntax: `LOOKUP("steam", "h", T=373, Q=1)`

#### Frontend Display

The PropertyTables page (`/resources/tables`) displays:
- Source list with category filtering
- Type badges (table, equation, library)
- Interactive data grid with fullscreen mode
- Snake_case values auto-formatted to Title Case

### 3. Integration with Formula System

#### Constant References in Formulas

Constants are directly accessible in formulas using the `#` prefix:

```
# Basic usage
Force = #mass * #g

# Mathematical operations
Area = #pi * (#radius)^2

# Complex calculations
Reynolds = #density * #velocity * #diameter / #viscosity
```

#### Property Table Lookups (In Development)

Future formula syntax for table interpolation:

```
# Single variable lookup
density = #water_properties[temperature: #T]

# Multi-variable lookup
enthalpy = #steam_tables[pressure: #P, temperature: #T]

# Range-based lookup
heat_coefficient = #correlation_table[reynolds: #Re]
```

## Frontend Implementation

### Constants Management UI

**Features:**
- Greek letter input support
- Subscript/superscript formatting
- Real-time search
- Category filtering
- Custom constant creation

**Keyboard Shortcuts:**
- `Ctrl+,` - Convert to subscript
- `Ctrl+.` - Convert to superscript
- `Alt+G` - Greek letter palette

### Property Tables Interface

**List View:**
- Verification badges (🟢🟡🔴)
- Source authority display
- Import method icons
- Quick search/filter

**Detail View:**
- Interactive data grid
- Interpolation preview
- Source documentation
- Edit history

### Templates Management

**Template Builder:**
- Variable definition
- Unit configuration
- Interpolation settings
- Validation rules

**Document Analyzer:**
- PDF/Excel upload
- Table detection preview
- Variable extraction
- Template suggestion

## Best Practices

### Constant Management

1. **Naming Conventions**
   - Use standard symbols (g, c, h)
   - Include units in description
   - Categorize appropriately

2. **Custom Constants**
   - Document source/derivation
   - Use descriptive names
   - Avoid duplicating system constants

### Table Creation

1. **Source Documentation**
   - Always cite sources
   - Include page/table numbers
   - Note any modifications

2. **Data Quality**
   - Verify OCR extractions
   - Check unit consistency
   - Validate ranges

3. **Template Design**
   - Make templates reusable
   - Define clear variable names
   - Document interpolation limits

## Quality Assurance

### Verification Workflow

1. **Import Stage**
   - Document source verification
   - OCR confidence check
   - Initial data validation

2. **Review Stage**
   - Manual inspection
   - Cross-reference with sources
   - Unit verification

3. **Approval Stage**
   - Authority confirmation
   - Final validation
   - Status assignment

### Data Integrity

**Automatic Checks:**
- Unit consistency
- Range validation
- Monotonicity (if required)
- Interpolation stability

**Manual Reviews:**
- Source accuracy
- Transcription errors
- Edge case handling

## API Usage Examples

### Creating a Custom Constant

```python
POST /api/v1/constants/
{
  "symbol": "rho_steel",
  "name": "Steel Density",
  "value": 7850,
  "unit": "kg/m³",
  "description": "Density of carbon steel at room temperature",
  "category": "Engineering"
}
```

### Importing a Property Table

```python
# Step 1: Analyze document
response = analyze_document("steam_tables.pdf")
template_suggestion = response.suggested_template

# Step 2: Create/select template
template_id = create_or_select_template(template_suggestion)

# Step 3: Import data
table = import_from_document(
  file="steam_tables.pdf",
  template_id=template_id,
  source_citation="ASME Steam Tables, 7th Edition, Table 3",
  source_authority="ASME"
)
```

### Using Constants in Formulas

```python
# Backend formula engine
formula = FormulaEngine.create_formula(
  expression="#force / (#pi * (#diameter/2)^2)",
  property_id=stress_property_id
)

# Frontend component
const StressCalculator = () => {
  const formula = useFormula(stressPropertyId);
  const constants = useConstants(['pi']);
  // Component logic
};
```

## Performance Considerations

### Caching Strategy

1. **Constants**: Cached on application startup
2. **Templates**: Cached on first use
3. **Table Data**: LRU cache for frequently accessed tables

### Optimization Tips

- Use template IDs instead of names in formulas
- Batch constant lookups
- Enable table data compression for large datasets
- Index frequently searched fields

## Future Enhancements

### Planned Features

1. **External API Integration**
   - NIST WebBook connection
   - Materials Project integration
   - Industry database APIs

2. **Advanced Interpolation**
   - Spline interpolation
   - Machine learning models
   - Uncertainty quantification

3. **Collaborative Features**
   - Table sharing workspace
   - Verification workflows
   - Community constants library

4. **Formula Integration**
   - Direct table lookups in formulas
   - Automatic unit conversion
   - Temperature/pressure corrections

---

*Last Updated: December 24, 2025*
*System Version: 2.0.0*
*Priority: HIGH - Core data foundation for engineering calculations*