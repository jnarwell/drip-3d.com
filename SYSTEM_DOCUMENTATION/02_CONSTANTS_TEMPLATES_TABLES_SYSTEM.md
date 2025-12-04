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

### 2. Property Table Templates

#### Overview
Templates define reusable structures for engineering data tables without containing actual data.

#### Table Types

**SINGLE_VAR_LOOKUP**
- One independent variable (e.g., temperature)
- Multiple dependent properties
- Example: Water properties vs. temperature

**MULTI_VAR_LOOKUP**
- Two or more independent variables
- 2D/3D property surfaces
- Example: Steam properties vs. pressure and temperature

**RANGE_BASED_LOOKUP**
- Property varies within ranges
- Step functions or correlations
- Example: Heat transfer coefficients by Reynolds number

**REFERENCE_ONLY**
- Documentation tables
- No interpolation
- Example: Material composition tables

#### Data Model
```python
PropertyTableTemplate:
  name: str
  description: str
  table_type: enum
  independent_vars: JSON  # {"temperature": {"unit": "K", "min": 273, "max": 373}}
  dependent_vars: JSON    # {"density": {"unit": "kg/m³"}, "viscosity": {"unit": "Pa⋅s"}}
  interpolation_type: enum  # LINEAR, LOGARITHMIC, POLYNOMIAL
  extrapolation_allowed: bool
  require_monotonic: bool
  usage_count: int
  scope: enum  # PUBLIC, WORKSPACE, PRIVATE
```

#### Template Creation Process

1. **Manual Definition**
   - Define variables and units
   - Set interpolation rules
   - Configure validation

2. **Document Analysis**
   ```
   POST /api/v1/property-table-templates/analyze-document
   {
     "file": <PDF/Excel file>,
     "analysis_hints": {
       "table_location": "page 5",
       "expected_vars": ["temperature", "pressure"]
     }
   }
   ```

### 3. Property Tables

#### Overview
Property tables contain actual engineering data with comprehensive verification and source tracking.

#### Verification System

**🟢 Verified**
- Imported from authoritative sources
- IAPWS, NIST, ASME standards
- Automated validation passed

**🟡 Cited**
- Manual entry with source
- Peer-reviewed publications
- Industry handbooks

**🔴 Unverified**
- No source documentation
- Internal measurements
- Preliminary data

#### Data Model
```python
PropertyTable:
  template_id: ForeignKey
  name: str
  data: JSON  # Actual table data
  material_id: Optional[int]
  component_id: Optional[int]
  
  # Import tracking
  import_method: enum  # MANUAL, API, DOCUMENT
  extracted_via_ocr: bool
  ocr_confidence: float
  manual_corrections: int
  
  # Verification
  verification_status: enum
  source_citation: str
  source_authority: str  # IAPWS, NIST, ASME, etc.
  source_url: Optional[str]
  data_quality: str  # A-F rating
  
  # Metadata
  temperature_range: Optional[JSON]
  pressure_range: Optional[JSON]
  notes: str
```

#### Import Methods

**Document Import**
```python
POST /api/v1/enhanced/property-tables/import-from-document
{
  "file": <PDF/Excel>,
  "template_id": 123,
  "extraction_settings": {
    "ocr_enabled": true,
    "page_range": "5-7",
    "table_detection": "automatic"
  }
}
```

**API Import** (Future)
```python
POST /api/v1/enhanced/property-tables/import-from-api
{
  "source": "NIST_WEBBOOK",
  "query": {
    "material": "water",
    "property": "density",
    "conditions": "1atm"
  }
}
```

### 4. Integration with Formula System

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

*Last Updated: December 2, 2025*
*System Version: 1.0.0*
*Priority: HIGH - Core data foundation for engineering calculations*