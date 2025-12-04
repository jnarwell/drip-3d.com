# Materials Database API Documentation

## Executive Summary

The DRIP Materials Database system provides comprehensive material property management through a dual approach: a local engineering materials database and integration with the Materials Project (MP) computational database. This enables both practical engineering data and scientifically validated computational properties.

## System Architecture

### Core Components

1. **Local Materials Database** - Curated engineering materials with industry standards
2. **Materials Project Integration** - Access to 140,000+ computational materials
3. **Property Inheritance System** - Automatic property propagation to components
4. **Alloy Standards Service** - Cross-reference between MP and industry specifications

## Database Schema

### Material Model

```python
Material:
  id: int
  name: str                    # e.g., "Aluminum 6061-T6"
  category: str                # e.g., "Aluminum Alloys"
  subcategory: Optional[str]   # e.g., "6xxx Series"
  
  # Identification
  uns_number: Optional[str]    # e.g., "A96061"
  astm_grade: Optional[str]    # e.g., "6061-T6"
  mp_id: Optional[str]         # Materials Project ID
  
  # Metadata
  common_name: Optional[str]   # e.g., "Aerospace Aluminum"
  composition_formula: Optional[str]  # e.g., "Al-Mg-Si"
  data_source: Optional[str]   # e.g., "ASTM B209"
  
  # Relationships
  properties: List[MaterialProperty]
  components: List[Component]  # Many-to-many
```

### Material Property Model

```python
MaterialProperty:
  id: int
  material_id: int
  property_definition_id: int
  
  # Value storage
  value: float
  unit: str
  conditions: Optional[str]    # e.g., "T=20°C"
  is_temperature_dependent: bool
  
  # Metadata
  source: Optional[str]        # e.g., "ASM Handbook"
  reliability: Optional[str]   # e.g., "Verified"
  measurement_method: Optional[str]
  notes: Optional[str]
```

## Materials Project Integration

### Service Architecture

The `MaterialsProjectService` provides intelligent material discovery:

```python
class MaterialsProjectService:
    def search_materials(query: str, search_mode: str):
        """
        Search modes:
        - 'elements': By chemical elements (e.g., "Al Si")
        - 'formula': By chemical formula (e.g., "Al2O3")
        - 'alloy': By engineering name (e.g., "6061")
        """
    
    def calculate_acoustic_properties(material_data):
        """Calculate DRIP-specific properties from MP data"""
    
    def get_material_oxides(elements: List[str]):
        """Analyze oxide formation for base elements"""
```

### Material Mappings

The system includes 200+ engineering alloy mappings:

```python
MATERIAL_NAME_MAPPINGS = {
    # Aluminum Alloys
    "6061": ["Al", "Mg", "Si"],
    "7075": ["Al", "Zn", "Mg", "Cu"],
    
    # Stainless Steels
    "316": ["Fe", "Cr", "Ni", "Mo"],
    "304": ["Fe", "Cr", "Ni"],
    
    # Titanium Alloys
    "Ti-6Al-4V": ["Ti", "Al", "V"],
    "Ti-6-4": ["Ti", "Al", "V"],
}
```

### API Endpoints

#### Search Materials
```
POST /api/v1/materials-project/search
{
  "query": "6061",
  "search_mode": "alloy",
  "limit": 10
}

Response:
{
  "materials": [
    {
      "mp_id": "mp-1234",
      "formula": "Al0.97Mg0.02Si0.01",
      "common_name": "Aluminum 6061",
      "properties": {
        "density": 2700,
        "bulk_modulus": 76.0,
        "shear_modulus": 26.0,
        "acoustic_impedance": 17.1
      },
      "drip_score": 0.85
    }
  ]
}
```

#### Import Material
```
POST /api/v1/materials-project/import
{
  "mp_id": "mp-1234",
  "include_properties": true,
  "calculate_acoustic": true
}

Response:
{
  "material_id": 456,
  "properties_imported": 12,
  "acoustic_properties_calculated": true
}
```

## Alloy Standards Database

### Structure

The alloy standards service manages comprehensive engineering data:

```json
{
  "aluminum_alloys": {
    "6061": {
      "uns": "A96061",
      "composition": {
        "Al": "95.85-98.56",
        "Si": "0.40-0.80",
        "Mg": "0.80-1.20"
      },
      "properties": {
        "density": 2700,
        "tensile_strength": 310,
        "yield_strength": 276,
        "thermal_conductivity": 167
      },
      "applications": ["Aerospace", "Marine", "Structural"]
    }
  }
}
```

### Enhanced Property Management

Temperature-dependent properties:

```
GET /api/v1/materials/123/properties/enhanced?temperature=500

Response:
{
  "properties": [
    {
      "name": "Yield Strength",
      "value": 245,
      "unit": "MPa",
      "temperature": 500,
      "temperature_unit": "K",
      "source": "ASM Handbook interpolated"
    }
  ]
}
```

## Frontend Material Selector

### Component Architecture

The `MaterialSelector` component provides dual-mode selection:

```tsx
interface MaterialSelectorProps {
  onSelect: (material: Material) => void;
  currentMaterialId?: number;
  mode?: 'component' | 'standalone';
}

// Usage
<MaterialSelector
  onSelect={(material) => {
    // Handle material selection
    // Triggers property inheritance
  }}
  currentMaterialId={component.material_id}
/>
```

### Search Modes

1. **Local Database Search**
   - Searches imported materials
   - Shows verification status
   - Displays key properties

2. **Materials Project Search**
   - Direct MP database access
   - Shows computational properties
   - One-click import capability

### Property Inheritance Flow

```
1. User selects material for component
   ↓
2. System identifies inheritable properties
   ↓
3. Old inherited properties removed
   ↓
4. New properties added with source tracking
   ↓
5. UI updates to show inherited values
```

## Property Inheritance System

### Implementation

The `MaterialPropertyManager` handles sophisticated property propagation:

```python
def update_component_material(component_id: int, material_id: int):
    # 1. Clear old inherited properties
    clear_inherited_properties(component_id)
    
    # 2. Get material properties
    material_props = get_material_properties(material_id)
    
    # 3. Create component properties
    for mat_prop in material_props:
        create_inherited_property(
            component_id=component_id,
            property_definition_id=mat_prop.property_definition_id,
            value=mat_prop.value,
            unit=mat_prop.unit,
            inherited_from_material=True,
            source_material_id=material_id
        )
```

### Inheritance Rules

1. **Automatic Propagation**: Material properties automatically flow to components
2. **Override Capability**: Users can override inherited values
3. **Source Tracking**: Clear indication of property origin
4. **Update Cascading**: Material updates can propagate to components

## Integration Examples

### Adding Material with Properties

```python
# Backend service example
material = Material(
    name="Aluminum 7075-T6",
    category="Aluminum Alloys",
    uns_number="A97075",
    composition_formula="Al-Zn-Mg-Cu"
)

# Add properties
properties = [
    MaterialProperty(
        property_definition_id=get_property_def("density"),
        value=2810,
        unit="kg/m³",
        source="ASM Handbook"
    ),
    MaterialProperty(
        property_definition_id=get_property_def("tensile_strength"),
        value=572,
        unit="MPa",
        conditions="T=20°C"
    )
]
```

### Using Materials in Formulas

Materials integrate with the formula system:

```
# Reference material properties in formulas
Stress = #force / (#material.yield_strength * #safety_factor)

# Temperature-dependent calculations
Modulus = #steel.modulus_at_temperature(#operating_temp)
```

### Frontend Integration

```tsx
// Component using material data
function ComponentEditor({ component }: Props) {
  const [material, setMaterial] = useState(component.material);
  
  const handleMaterialChange = async (newMaterial: Material) => {
    // Update component's material
    await updateComponentMaterial(component.id, newMaterial.id);
    
    // Properties automatically inherited
    // UI updates to show new values
  };
  
  return (
    <MaterialSelector
      currentMaterialId={material?.id}
      onSelect={handleMaterialChange}
    />
  );
}
```

## Best Practices

### Material Selection

1. **Start with Standards**: Use pre-defined alloys when possible
2. **Verify Properties**: Check source and reliability ratings
3. **Temperature Conditions**: Note property measurement conditions
4. **Cross-Reference**: Compare MP and handbook values

### Property Management

1. **Source Documentation**: Always document property sources
2. **Condition Tracking**: Record temperature, treatment state
3. **Uncertainty Handling**: Note confidence levels
4. **Version Control**: Track property updates

### Integration Guidelines

1. **Inheritance vs Override**: Use inheritance for standard properties
2. **Custom Properties**: Add component-specific properties as needed
3. **Formula Variables**: Use consistent naming for material properties
4. **Update Strategies**: Decide on cascading update policies

## Performance Considerations

### Caching Strategy

```python
# Material properties are cached
@cache_result(ttl=3600)
def get_material_properties(material_id: int):
    return db.query(MaterialProperty).filter_by(
        material_id=material_id
    ).all()
```

### Query Optimization

- Eager loading for material relationships
- Indexed searches on common fields
- Pagination for large result sets

## Troubleshooting

### Common Issues

1. **Material Not Found in MP**
   - Try alternative names or formulas
   - Check element order in search
   - Use broader search terms

2. **Property Inheritance Not Working**
   - Verify property definitions match
   - Check inheritance flags
   - Ensure material assignment saved

3. **Temperature Dependencies**
   - Verify condition format
   - Check interpolation settings
   - Validate temperature ranges

### Debug Queries

```sql
-- Check material properties
SELECT m.name, p.name, mp.value, mp.unit
FROM materials m
JOIN material_properties mp ON m.id = mp.material_id
JOIN property_definitions p ON mp.property_definition_id = p.id
WHERE m.id = 123;

-- Verify inheritance
SELECT c.name, p.name, cp.value, cp.inherited_from_material
FROM components c
JOIN component_properties cp ON c.id = cp.component_id
JOIN property_definitions p ON cp.property_definition_id = p.id
WHERE cp.source_material_id IS NOT NULL;
```

## Future Enhancements

### Planned Features

1. **Advanced Material Search**
   - Property range filtering
   - Multi-property optimization
   - Similarity matching

2. **Data Sources**
   - NIST integration
   - Matweb connectivity
   - Custom database imports

3. **Property Modeling**
   - Temperature curves
   - Pressure dependencies
   - Fatigue data

4. **Visualization**
   - Property comparison charts
   - Material selection matrices
   - Ashby diagrams

---

*Last Updated: December 2, 2025*
*System Version: 1.0.0*
*Priority: HIGH - Core material data system for engineering calculations*