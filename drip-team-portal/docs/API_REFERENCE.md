# DRIP API Reference

Base URL: `https://backend-production-aa29.up.railway.app` (production) or `http://localhost:8000` (development)

## Authentication

- **Production**: Bearer token from Auth0
- **Development**: `DEV_MODE=true` bypasses auth

---

## Components

### List Components
```
GET /api/v1/components/
Query: ?skip=0&limit=100
```

### Get Component
```
GET /api/v1/components/{component_id}
```

### Create Component
```
POST /api/v1/components/
{
  "name": "Heat Bed Assembly",
  "code": "HBA001",           // Optional, auto-generated if omitted
  "description": "Main heating surface",
  "category": "Thermal"
}
```

### Update Component
```
PUT /api/v1/components/{component_id}
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

### Delete Component
```
DELETE /api/v1/components/{component_id}
```

---

## Properties

### Get Component Properties
```
GET /api/v1/properties/component/{component_id}
```

Response includes computed values:
```json
{
  "id": 123,
  "property_definition": { "name": "Length", "unit": "mm" },
  "single_value": 100.5,
  "value_node_id": 456,
  "computed_value": 0.1005,         // SI base units
  "computed_unit_symbol": "m",      // For display conversion
  "expression_string": "#CMP001.width * 2"
}
```

### Create Property
```
POST /api/v1/properties/component/{component_id}
{
  "property_definition_id": 1,
  "single_value": 100.5,
  "unit": "mm"
}
```

### Update Property Value
```
PUT /api/v1/properties/{property_id}
{
  "single_value": 150.0,
  "unit": "mm"
}
```

Or set an expression:
```
PUT /api/v1/properties/{property_id}
{
  "expression": "#CMP001.width * 2"
}
```

---

## Values

### Create Value Node
```
POST /api/v1/values/
{
  "node_type": "expression",
  "expression_string": "sqrt(#CMP001.length * 2)",
  "description": "Calculated dimension"
}
```

### Get Value Node
```
GET /api/v1/values/{value_id}
```

### Recalculate Value
```
POST /api/v1/values/{value_id}/recalculate
```

### Search Variables
```
GET /api/v1/variables/search?q=length
```

Returns available references for autocomplete.

---

## Materials

### List Materials
```
GET /api/v1/materials/
Query: ?category=Aluminum Alloys
```

### Get Material
```
GET /api/v1/materials/{material_id}
```

### Create Material
```
POST /api/v1/materials/
{
  "name": "Aluminum 6061-T6",
  "category": "Aluminum Alloys",
  "code": "AL6061T6",
  "uns_number": "A96061"
}
```

### Get Material Properties
```
GET /api/v1/materials/{material_id}/properties
```

---

## Materials Project Integration

### Search Materials Project
```
POST /api/v1/materials-project/search
{
  "query": "6061",
  "search_mode": "alloy",    // "elements", "formula", "alloy"
  "limit": 10
}
```

### Import from Materials Project
```
POST /api/v1/materials-project/import
{
  "mp_id": "mp-1234",
  "include_properties": true,
  "calculate_acoustic": true
}
```

---

## Units

### List Units
```
GET /api/v1/units/
Query: ?dimension=length
```

### Get Unit
```
GET /api/v1/units/{unit_id}
```

### Convert Value
```
POST /api/v1/units/convert
{
  "value": 100,
  "from_unit": "mm",
  "to_unit": "in"
}
```

---

## User Preferences

### Get Unit Preferences
```
GET /api/v1/me/unit-preferences
```

Response:
```json
{
  "preferences": [
    { "quantity_type": "length", "preferred_unit_id": 5, "precision": 0.01 }
  ]
}
```

### Set Unit Preference
```
PUT /api/v1/me/unit-preferences/{quantity_type}
{
  "preferred_unit_id": 5,
  "precision": 0.001
}
```

---

## System Constants

### List Constants
```
GET /api/v1/constants/
Query: ?category=Physics
```

### Get by Symbol
```
GET /api/v1/constants/symbol/{symbol}
Example: GET /api/v1/constants/symbol/g
```

### Create Custom Constant
```
POST /api/v1/constants/
{
  "symbol": "rho_steel",
  "name": "Steel Density",
  "value": 7850,
  "unit": "kg/m³",
  "category": "Engineering"
}
```

---

## Property Tables

### List Tables
```
GET /api/v1/property-tables/
```

### Get Table
```
GET /api/v1/property-tables/{table_id}
```

### Create Table
```
POST /api/v1/property-tables/
{
  "name": "Water Properties",
  "template_id": 1,
  "data": {...},
  "verification_status": "cited",
  "source_citation": "NIST WebBook"
}
```

---

## Linear Integration

### Get Progress Data
```
GET /api/v1/linear/progress
Query: ?force_refresh=false
```

### Get Milestones
```
GET /api/v1/linear/milestones
```

### Force Refresh
```
POST /api/v1/linear/refresh
```

---

## Tests

### List Tests
```
GET /api/v1/tests/
```

### Get Test
```
GET /api/v1/tests/{test_id}
```

### Create Test
```
POST /api/v1/tests/
{
  "name": "Steering Force Test",
  "category": "Acoustic",
  "component_id": 123
}
```

---

## Health Check

```
GET /health
```

Response:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common status codes:
- `400` - Bad request (validation error)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not found
- `422` - Unprocessable entity (invalid data)
- `500` - Internal server error

---

## OpenAPI Documentation

Full interactive API documentation available at:
- **Swagger UI**: `/docs`
- **ReDoc**: `/redoc`
- **OpenAPI JSON**: `/openapi.json`

---

*Last Updated: December 19, 2025*
