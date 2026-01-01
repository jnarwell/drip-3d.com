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

### Search Entities (for autocomplete)
```
GET /api/v1/search/entities?q=FRAME
```

Returns entity codes matching the query for expression autocomplete.

### Get Entity Properties (for autocomplete)
```
GET /api/v1/search/entities/{entity_code}/properties?q=len
```

Returns properties for an entity, for expression autocomplete after typing `#CODE.`

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

### Unit Format

Units should use caret notation for exponents:
- `m/s^2` (correct)
- `kg/m^3` (correct)
- `m/s²` (Unicode superscripts not recommended)

The API normalizes common Unicode superscripts (², ³, ⁻¹) to caret notation, but caret notation is preferred for consistency.

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

## Physics Models

### List Physics Models
```
GET /api/v1/physics-models
Query: ?category=thermal
```

Response:
```json
[
  {
    "id": 1,
    "name": "Thermal Expansion",
    "description": "Calculates thermal expansion for materials",
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

Returns full model with all versions.

### Validate Physics Model
```
POST /api/v1/physics-models/validate
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

Response:
```json
{
  "valid": true,
  "errors": [],
  "dimensional_analysis": {
    "expansion": {"valid": true, "message": "Dimensions valid"}
  },
  "latex_preview": {
    "expansion": "L \\cdot \\alpha \\cdot \\Delta T"
  }
}
```

### Create Physics Model
```
POST /api/v1/physics-models
{
  "name": "Thermal Expansion",
  "description": "Calculates thermal expansion",
  "category": "thermal",
  "inputs": [...],
  "outputs": [...],
  "equations": [...]
}
```

### List Categories
```
GET /api/v1/physics-models/categories
```

Returns available model categories (thermal, mechanical, fluid, etc.).

### Get Physics Model by Name
```
GET /api/v1/physics-models/by-name/{model_name}
```

Retrieve a physics model by its name (case-insensitive). Used internally by the `MODEL()` expression function for fast model lookup.

**Parameters:**
- `model_name` (path) - Name of the model (case-insensitive match)

**Example:**
```
GET /api/v1/physics-models/by-name/Thermal%20Expansion
GET /api/v1/physics-models/by-name/thermal%20expansion   # Also works (case-insensitive)
```

**Response:**
```json
{
  "id": 1,
  "name": "Thermal Expansion",
  "description": "Linear thermal expansion calculator",
  "category": "thermal",
  "created_at": "2025-12-27T00:00:00Z",
  "current_version": {
    "id": 1,
    "version": 1,
    "inputs": [
      {"name": "CTE", "unit": "1/K", "dimension": "thermal_expansion", "required": true},
      {"name": "delta_T", "unit": "K", "dimension": "temperature_difference", "required": true},
      {"name": "L0", "unit": "m", "dimension": "length", "required": true}
    ],
    "outputs": [
      {"name": "delta_L", "unit": "m", "dimension": "length"}
    ],
    "equations": {
      "delta_L": "CTE * delta_T * L0"
    },
    "equation_ast": {
      "delta_L": {...}
    },
    "equation_latex": "{\"delta_L\": \"\\\\alpha \\\\cdot \\\\Delta T \\\\cdot L_0\"}"
  }
}
```

**Error Responses:**
- `404` - Model not found
```json
{
  "detail": "Model 'NonExistent' not found"
}
```

---

## Model Instances

### Create Model Instance
```
POST /api/v1/model-instances
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

Response:
```json
{
  "id": 1,
  "name": "Steel Rod Expansion",
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

---

## Analyses (Named Model Instances)

Named analyses are model instances visible team-wide on the Analysis dashboard. They exist independently of components (`component_id = NULL`).

### List Analyses
```
GET /api/v1/analyses
```

List all analyses (named model instances).

**Query Parameters:** None

**Response:**
```json
[
  {
    "id": 14,
    "name": "Frame Expansion",
    "description": "Calculates thermal expansion of frame",
    "model_version_id": 1,
    "model": {
      "id": 1,
      "name": "Thermal Expansion",
      "version": 1
    },
    "computation_status": "valid",
    "last_computed": "2025-12-28T12:00:00Z",
    "created_at": "2025-12-28T11:00:00Z",
    "created_by": "user@example.com",
    "inputs": [
      {
        "input_name": "CTE",
        "literal_value": 2.3e-5,
        "source_lookup": null
      },
      {
        "input_name": "L0",
        "literal_value": null,
        "source_lookup": "#FRAME.Length"
      }
    ],
    "output_value_nodes": [
      {
        "id": 89,
        "name": "delta_L",
        "computed_value": 6.9e-6,
        "unit": "m",
        "status": "valid"
      }
    ]
  }
]
```

**Notes:**
- Returns array directly (not wrapped in object)
- Sorted by `created_at` descending (newest first)
- Response includes full `model` object, `inputs` array, and `output_value_nodes` array
- `computation_status` values: `valid`, `stale`, `error`, `pending`

---

### Create Analysis
```
POST /api/v1/analyses
{
  "name": "Frame Expansion",
  "description": "Calculates thermal expansion of aluminum frame",
  "model_version_id": 1,
  "bindings": {
    "CTE": "2.3e-5",
    "delta_T": "100",
    "L0": "#FRAME.Length"
  }
}
```

**Request Fields:**
- `name` (required): Unique analysis name
- `description` (optional): What this analysis calculates
- `model_version_id` (required): Physics model version to use
- `bindings` (required): Input bindings as key-value pairs
  - Literal values: `"100"` or `"2.3e-5"`
  - Component references: `"#FRAME.Length"` (see #REF format below)

**Response:**
```json
{
  "id": 14,
  "name": "Frame Expansion",
  "description": "Calculates thermal expansion of aluminum frame",
  "model_version_id": 1,
  "component_id": null,
  "is_analysis": true,
  "created_by": "user@example.com",
  "created_at": "2025-12-28T11:00:00Z",
  "computation_status": "valid",
  "last_computed": "2025-12-28T12:00:00Z",
  "inputs": [...],
  "output_value_nodes": [...],
  "evaluation_error": null
}
```

**Notes:**
- `is_analysis` is always `true` for analyses
- `component_id` is always `null` for analyses
- `evaluation_error` contains error message if computation failed

**Errors:**
- `400`: Name already exists, invalid bindings, missing required fields
- `404`: Model version not found

#### #REF Binding Format

Analyses can bind inputs to component properties using `#ComponentCode.PropertyName` syntax:

```
#<ComponentCode>.<PropertyName>
```

**Examples:**
```json
{
  "bindings": {
    "L0": "#FRAME.Length",
    "power": "#TRANSDUCER.Max_Power",
    "temp": "#CHAMBER.Temperature"
  }
}
```

When a #REF binding is used:
- System looks up component by code
- Finds property's ValueNode
- Links analysis input to that ValueNode (creates dependency)
- When component property updates → analysis auto-recalculates

---

### Get Analysis
```
GET /api/v1/analyses/{analysis_id}
```

Get details of a specific analysis.

**Path Parameters:**
- `analysis_id`: Analysis ID

**Response:**
```json
{
  "id": 14,
  "name": "Frame Expansion",
  "description": "Calculates thermal expansion of frame",
  "model_version_id": 1,
  "model": {"id": 1, "name": "Thermal Expansion", "version": 1},
  "computation_status": "valid",
  "last_computed": "2025-12-28T12:00:00Z",
  "created_at": "2025-12-28T11:00:00Z",
  "created_by": "user@example.com",
  "inputs": [
    {
      "input_name": "L0",
      "literal_value": null,
      "source_lookup": "#FRAME.Length",
      "source_value_node_id": 45
    }
  ],
  "output_value_nodes": [...]
}
```

**Notes:**
- Single analysis includes `source_value_node_id` in inputs (resolved ValueNode ID)
- `source_value_node_id` is `null` for literal bindings

**Errors:**
- `404`: Analysis not found

---

### Update Analysis
```
PATCH /api/v1/analyses/{id}
{
  "name": "New Name",
  "description": "Updated description",
  "bindings": {"CTE": "2.5e-5", "L0": "#FRAME.Length"}
}
```

**Request Fields:** (all optional)
- `name`: New analysis name
- `description`: Updated description
- `bindings`: Updated input bindings

**Response:**
```json
{
  "id": 14,
  "name": "New Name",
  "description": "Updated description",
  "model_version_id": 1,
  "computation_status": "valid",
  "last_computed": "2025-12-28T12:30:00Z",
  "inputs": [...],
  "output_value_nodes": [...]
}
```

**Notes:**
- Response is a subset of GET response (no `model`, `created_at`, `created_by`)
- Re-evaluates automatically if bindings changed
- Status will be `pending` during evaluation, then `valid` or `error`
- Broadcasts `instance_updated` via WebSocket

---

### Delete Analysis
```
DELETE /api/v1/analyses/{id}
```

Removes analysis, inputs, and output ValueNodes. Broadcasts `instance_deleted` via WebSocket.

**Response:**
```json
{
  "deleted": true,
  "id": 14
}
```

---

### Force Re-Evaluation
```
POST /api/v1/analyses/{id}/evaluate
```

Immediately re-evaluates outputs and updates `last_computed`. Broadcasts `instance_evaluated` via WebSocket.

**Response:**
```json
{
  "id": 14,
  "name": "Frame Expansion",
  "computation_status": "valid",
  "last_computed": "2025-12-28T12:35:00Z",
  "output_value_nodes": [...],
  "evaluation_error": null
}
```

**Notes:**
- `evaluation_error` contains error message if computation failed
- Useful for forcing recalculation after upstream changes

---

## WebSocket: Analysis Updates

Real-time updates for the Analysis dashboard.

### Endpoint
```
ws://localhost:8000/ws/analysis?token=<jwt>
```

**Authentication:** JWT token in query parameter

### Message Types

| Type | Description |
|------|-------------|
| `connected` | Connection established |
| `instance_created` | New analysis created |
| `instance_updated` | Analysis modified |
| `instance_deleted` | Analysis removed |
| `instance_evaluated` | Outputs recalculated |

**Example message:**
```json
{
  "type": "instance_updated",
  "data": {
    "id": 5,
    "name": "Updated Analysis",
    "computation_status": "valid",
    "outputs": [...]
  }
}
```

See [PHYSICS_MODELS.md](PHYSICS_MODELS.md#real-time-collaboration-websocket) for full WebSocket documentation.

### Error Handling

**Connection Errors:**
- `401 Unauthorized`: Invalid or missing JWT token
- `403 Forbidden`: Token expired
- Connection close with code 1008 (Policy Violation) for auth failures

**Reconnection Strategy:**
```javascript
// Frontend automatically handles reconnection
// Retry delays: 1s, 2s, 4s, 8s, 16s (exponential backoff)
// After 5 failed attempts, stops and shows "Disconnected" indicator
```

**Handling Disconnection:**
- UI shows connection status indicator
- On disconnect: "Live updates paused" message
- On reconnect: "Live updates resumed" + automatic data refetch

**Message Errors:**
- Malformed messages are logged and ignored
- Invalid message types return error in WebSocket message
- Broadcast failures are logged server-side (client unaffected)

---

## Time Tracking

Time tracking allows team members to log work sessions with categorization.

### Start Timer
```
POST /api/v1/time/start
```

Request:
```json
{
  "component_id": 5,           // Optional: context component
  "linear_issue_id": "DRP-156" // Optional: pre-link to Linear issue
}
```

Response:
```json
{
  "id": 1,
  "user_id": "jamie@drip-3d.com",
  "started_at": "2025-12-31T10:00:00Z",
  "stopped_at": null,
  "duration_seconds": null,
  "linear_issue_id": "DRP-156",
  "linear_issue_title": null,
  "resource_id": null,
  "description": null,
  "is_uncategorized": false,
  "component_id": 5
}
```

### Stop Timer
```
POST /api/v1/time/stop
```

Stops the active timer and requires categorization.

Request:
```json
{
  "linear_issue_id": "DRP-156",     // Option 1: Link to Linear issue
  "linear_issue_title": "Fix bug",  // Optional: cached title
  "resource_id": 12,                 // Option 2: Link to resource
  "description": "Research work",    // Option 3: Free-text
  "is_uncategorized": false          // Option 4: Mark as N/A
}
```

At least one categorization field must be provided (or `is_uncategorized: true`).

Response:
```json
{
  "id": 1,
  "user_id": "jamie@drip-3d.com",
  "started_at": "2025-12-31T10:00:00Z",
  "stopped_at": "2025-12-31T11:30:00Z",
  "duration_seconds": 5400,
  "linear_issue_id": "DRP-156",
  "linear_issue_title": "Fix bug",
  "resource_id": null,
  "description": null,
  "is_uncategorized": false,
  "component_id": 5
}
```

### Get Active Timer
```
GET /api/v1/time/active
```

Returns the current user's running timer, or `null` if none.

Response:
```json
{
  "id": 1,
  "user_id": "jamie@drip-3d.com",
  "started_at": "2025-12-31T10:00:00Z",
  "stopped_at": null,
  "duration_seconds": null,
  "component_id": 5
}
```

### List Time Entries
```
GET /api/v1/time/entries
Query: ?user_id=jamie@drip-3d.com&start_date=2025-12-01&end_date=2025-12-31&limit=100
```

**Query Parameters:**
- `user_id` (optional): Filter by user
- `start_date` (optional): ISO date, inclusive
- `end_date` (optional): ISO date, inclusive
- `linear_issue_id` (optional): Filter by Linear issue
- `component_id` (optional): Filter by component
- `limit` (optional): Max results (default 100)
- `offset` (optional): Pagination offset

Response:
```json
[
  {
    "id": 1,
    "user_id": "jamie@drip-3d.com",
    "started_at": "2025-12-31T10:00:00Z",
    "stopped_at": "2025-12-31T11:30:00Z",
    "duration_seconds": 5400,
    "linear_issue_id": "DRP-156",
    "linear_issue_title": "Fix bug",
    "component_id": 5
  }
]
```

### Get Time Summary
```
GET /api/v1/time/summary
Query: ?group_by=user&start_date=2025-12-01&end_date=2025-12-31
```

**Query Parameters:**
- `group_by` (required): `user`, `linear_issue`, `component`, or `day`
- `start_date` (optional): ISO date
- `end_date` (optional): ISO date
- `user_id` (optional): Filter by specific user

Response (group_by=user):
```json
{
  "summary": [
    {
      "user_id": "jamie@drip-3d.com",
      "total_seconds": 28800,
      "entry_count": 5
    }
  ],
  "period": {
    "start": "2025-12-01",
    "end": "2025-12-31"
  }
}
```

---

### Edit Time Entry
```
PATCH /api/v1/time/entries/{id}
```

Edit an existing time entry. **Requires `edit_reason`** for audit trail.

Request:
```json
{
  "stopped_at": "2025-12-31T17:30:00Z",
  "edit_reason": "Forgot to stop timer"
}
```

**Editable fields:** `started_at`, `stopped_at`, `linear_issue_id`, `linear_issue_title`, `resource_id`, `description`, `is_uncategorized`, `component_id`

**Preset edit reasons:**
- Forgot to stop timer
- Started earlier than recorded
- Ended earlier than recorded
- Wrong categorization
- Adding break time
- Other (custom text)

Response:
```json
{
  "id": 1,
  "user_id": "jamie@drip-3d.com",
  "started_at": "2025-12-31T10:00:00Z",
  "stopped_at": "2025-12-31T17:30:00Z",
  "duration_seconds": 27000,
  "edit_history": [
    {
      "field": "stopped_at",
      "old_value": "2025-12-31T18:00:00Z",
      "new_value": "2025-12-31T17:30:00Z",
      "reason": "Forgot to stop timer",
      "edited_at": "2025-12-31T17:35:00Z",
      "edited_by": "jamie@drip-3d.com"
    }
  ]
}
```

**Notes:**
- Entries with edits show `[edited]` indicator in UI
- Full edit history preserved and viewable
- Duration auto-recalculated on time changes

---

## Time Tracking - Breaks

Breaks allow tracking pauses within a work session. Timer continues running during breaks (paid breaks).

### Start Break
```
POST /api/v1/time/entries/{id}/breaks
```

Start a break on an active time entry.

Request:
```json
{
  "note": "lunch"
}
```

Response:
```json
{
  "id": 1,
  "time_entry_id": 5,
  "started_at": "2025-12-31T12:00:00Z",
  "stopped_at": null,
  "note": "lunch"
}
```

### Stop Break
```
POST /api/v1/time/entries/{id}/breaks/{break_id}/stop
```

End an active break.

Response:
```json
{
  "id": 1,
  "time_entry_id": 5,
  "started_at": "2025-12-31T12:00:00Z",
  "stopped_at": "2025-12-31T12:30:00Z",
  "duration_seconds": 1800,
  "note": "lunch"
}
```

### List Breaks
```
GET /api/v1/time/entries/{id}/breaks
```

Get all breaks for a time entry.

Response:
```json
[
  {
    "id": 1,
    "started_at": "2025-12-31T12:00:00Z",
    "stopped_at": "2025-12-31T12:30:00Z",
    "duration_seconds": 1800,
    "note": "lunch"
  },
  {
    "id": 2,
    "started_at": "2025-12-31T15:00:00Z",
    "stopped_at": "2025-12-31T15:15:00Z",
    "duration_seconds": 900,
    "note": "coffee"
  }
]
```

---

## Resources

Knowledge base resources linked to components and physics models.

### List Resources
```
GET /api/v1/resources
Query: ?resource_type=doc&component_id=5&tag=research
```

**Query Parameters:**
- `resource_type` (optional): `doc`, `folder`, `image`, `link`, `paper`, `video`, `spreadsheet`
- `component_id` (optional): Filter by linked component
- `physics_model_id` (optional): Filter by linked model
- `tag` (optional): Filter by tag
- `added_by` (optional): Filter by user

Response:
```json
[
  {
    "id": 1,
    "title": "Thermal Analysis Report",
    "resource_type": "doc",
    "url": "https://docs.google.com/...",
    "added_by": "jamie@drip-3d.com",
    "added_at": "2025-12-31T10:00:00Z",
    "tags": ["thermal", "phase-1"],
    "notes": "Key findings from thermal testing",
    "component_ids": [5, 12],
    "physics_model_ids": [3]
  }
]
```

### Get Resource
```
GET /api/v1/resources/{resource_id}
```

### Create Resource
```
POST /api/v1/resources
```

Request:
```json
{
  "title": "Thermal Analysis Report",
  "resource_type": "doc",
  "url": "https://docs.google.com/...",
  "tags": ["thermal", "phase-1"],
  "notes": "Key findings from thermal testing",
  "component_ids": [5, 12],
  "physics_model_ids": [3]
}
```

Response:
```json
{
  "id": 1,
  "title": "Thermal Analysis Report",
  "resource_type": "doc",
  "url": "https://docs.google.com/...",
  "added_by": "jamie@drip-3d.com",
  "added_at": "2025-12-31T10:00:00Z",
  "tags": ["thermal", "phase-1"],
  "notes": "Key findings from thermal testing",
  "component_ids": [5, 12],
  "physics_model_ids": [3]
}
```

### Update Resource
```
PUT /api/v1/resources/{resource_id}
```

Request:
```json
{
  "title": "Updated Title",
  "tags": ["thermal", "phase-2"],
  "component_ids": [5, 12, 18]
}
```

### Delete Resource
```
DELETE /api/v1/resources/{resource_id}
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

*Last Updated: December 31, 2025*
