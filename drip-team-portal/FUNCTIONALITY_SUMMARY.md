# DRIP Team Portal - Complete Functionality Summary

**Last Updated:** December 31, 2025

The DRIP Team Portal is a comprehensive engineering platform for the DRIP acoustic 3D printing project. It provides component management, parametric calculations, physics modeling, and real-time collaboration tools.

---

## Table of Contents

1. [Authentication & Access](#authentication--access)
2. [Component Registry](#component-registry)
3. [Value System](#value-system)
4. [Unit System](#unit-system)
5. [Materials Database](#materials-database)
6. [Physics Models](#physics-models)
7. [Analysis Dashboard](#analysis-dashboard)
8. [Engineering Properties](#engineering-properties)
9. [System Constants](#system-constants)
10. [Linear Integration](#linear-integration)
11. [Test Campaign](#test-campaign)
12. [Reports](#reports)
13. [API Overview](#api-overview)

---

## Authentication & Access

### Domain-Based Routing
- **team.drip-3d.com** - Team portal (authenticated)
- **www.drip-3d.com** - Public site (no auth)
- **localhost** - Defaults to team portal

### Authentication
- **Provider:** Auth0
- **Domain restriction:** `@drip-3d.com` emails only
- **Token type:** JWT Bearer tokens
- **Dev mode:** `DEV_MODE=true` bypasses auth with `x-email` header

---

## Component Registry

Central hub for managing engineering components.

### Features
- **CRUD operations** - Create, read, update, delete components
- **Auto-generated codes** - Unique component codes (e.g., `FRAME001`)
- **Categories** - Thermal, Mechanical, Electrical, Acoustic, etc.
- **Status tracking** - Design, Prototype, Production, Obsolete
- **Search & filter** - By name, code, category, status

### Component Properties
- Each component has typed properties with values
- Properties can be:
  - **Literal values** - Direct numeric entry with units
  - **Expressions** - Calculated from other properties
  - **Material-derived** - Auto-pulled from assigned material

### Data Model
```
Component
├── id, name, code, description
├── category, status
├── material_id (optional)
└── properties[] → ComponentProperty → ValueNode
```

---

## Value System

Reactive expression engine powering all calculations.

### ValueNode Types
| Type | Description | Example |
|------|-------------|---------|
| `LITERAL` | Direct numeric value | `100 mm` |
| `EXPRESSION` | Mathematical formula | `#FRAME.Height * 2` |
| `REFERENCE` | Points to another node | Link to material property |
| `TABLE_LOOKUP` | Interpolated lookup | (Future) |

### Expression Syntax
```
#ENTITY_CODE.property_name
```

**Examples:**
- `#FRAME.Height` - Component property
- `#304_STAINLESS.Density` - Material property
- `sqrt(#HEATBED.Width * #HEATBED.Length)` - Math expression
- `#FRAME.Height + 2ft` - Mixed units

### Supported Functions
- **Math:** `sqrt()`, `sin()`, `cos()`, `tan()`, `exp()`, `ln()`, `log10()`, `abs()`
- **Constants:** `pi`, `e`
- **Operators:** `+`, `-`, `*`, `/`, `^` (power)

### Dependency Graph
- Automatic tracking of value dependencies
- Cascade recalculation when source values change
- Circular dependency detection and prevention
- Status tracking: `valid`, `stale`, `error`, `pending`

### Ghost Text Autocomplete
- Type `#` to start a reference
- Tab to accept suggestions
- Auto-completes entity codes and property names

---

## Unit System

Comprehensive dimensional analysis with 7 SI base dimensions.

### SI Base Dimensions
| Dimension | SI Unit | Symbol |
|-----------|---------|--------|
| Length | meter | m |
| Mass | kilogram | kg |
| Time | second | s |
| Current | ampere | A |
| Temperature | kelvin | K |
| Amount | mole | mol |
| Luminous intensity | candela | cd |

### Features
- **35+ quantity types** - Length, pressure, temperature, etc.
- **SI base storage** - All values stored in SI internally
- **User preferences** - Display in preferred units per quantity
- **Automatic conversion** - Mixed unit expressions work correctly
- **Unit validation** - Dimensional analysis catches errors

### Unit Format
```
m/s^2    (correct - caret notation)
kg/m^3   (correct)
m/s²     (works but not recommended)
```

### Supported Units (partial list)
- **Length:** m, mm, cm, km, in, ft, yd, mi
- **Mass:** kg, g, mg, lb, oz
- **Temperature:** K, °C, °F
- **Pressure:** Pa, kPa, MPa, GPa, bar, psi, atm
- **Force:** N, kN, lbf
- **Energy:** J, kJ, MJ, kWh, BTU, cal

---

## Materials Database

Engineering materials with properties.

### Features
- **Material library** - Pre-loaded engineering materials
- **Categories** - Aluminum Alloys, Steels, Polymers, Ceramics, etc.
- **Material properties** - Density, yield strength, thermal conductivity, etc.
- **UNS numbers** - Standard material identifiers
- **Materials Project integration** - Import from MP database

### Material Properties
Properties automatically available when material assigned to component:
- Density
- Young's Modulus
- Poisson's Ratio
- Yield Strength
- Thermal Conductivity
- Coefficient of Thermal Expansion (CTE)
- Specific Heat Capacity

### Materials Project API
```
POST /api/v1/materials-project/search
POST /api/v1/materials-project/import
```

---

## Physics Models

Reusable physics calculation templates with dimensional validation.

### Model Structure
```
PhysicsModel
└── PhysicsModelVersion (versioned)
    ├── inputs[] - Typed input variables with units
    ├── outputs[] - Typed output variables with units
    └── equations{} - Output expressions
```

### Creating Models (4-Step Wizard)
1. **Define Model** - Name, description, category
2. **Inputs & Outputs** - Define variables with units
3. **Equations** - Write output expressions
4. **Validate** - Dimensional analysis check

### Categories
- Thermal
- Mechanical
- Fluid
- Electrical
- Acoustic
- General

### Dimensional Analysis
- **32 predefined dimensions** - SI base + derived
- **197 unit mappings** - Unit to dimension lookup
- **Validation** - Catches physics errors at design time

### Example: Thermal Expansion Model
```json
{
  "name": "Thermal Expansion",
  "inputs": [
    {"name": "L0", "unit": "m"},
    {"name": "CTE", "unit": "1/K"},
    {"name": "delta_T", "unit": "K"}
  ],
  "outputs": [
    {"name": "delta_L", "unit": "m"}
  ],
  "equations": {
    "delta_L": "L0 * CTE * delta_T"
  }
}
```

### Model Instances
Bind model inputs to create calculations:

**Binding Types:**
| Type | Example | Description |
|------|---------|-------------|
| Literal | `"100"` | Direct value |
| Component ref | `"#FRAME.Length"` | Property reference |
| Constant | `"g"` | System constant |

### MODEL() Expression Function
Inline model evaluation in expressions:
```
MODEL("Thermal Expansion", CTE: 2.3e-5, delta_T: 100, L0: #PART.length)
```

---

## Analysis Dashboard

Team-wide named model instances with real-time collaboration.

### Purpose
- System-level calculations visible to all team members
- Calculations that don't belong to a specific component
- Shared metrics that update as the system evolves

### Features
- **List all analyses** - Alphabetically sorted
- **Create/edit wizard** - 3-step process
- **Real-time updates** - WebSocket broadcasts changes
- **Status indicators** - valid (green), stale (yellow), error (red)
- **Filter by status** - Show only valid/stale/error
- **Filter by model** - Show analyses using specific model

### WebSocket Events
| Event | Description |
|-------|-------------|
| `instance_created` | New analysis added |
| `instance_updated` | Analysis modified |
| `instance_deleted` | Analysis removed |
| `instance_evaluated` | Outputs recalculated |

### API Endpoints
```
GET    /api/v1/analyses           - List all
POST   /api/v1/analyses           - Create new
GET    /api/v1/analyses/{id}      - Get single
PATCH  /api/v1/analyses/{id}      - Update
DELETE /api/v1/analyses/{id}      - Delete
POST   /api/v1/analyses/{id}/evaluate - Force recalc
```

---

## Engineering Properties

LOOKUP system for verified engineering data.

### Data Sources (35 total)
Organized in `/backend/data/`:

**Tolerances:**
- `ansi_fits.yaml` - ANSI shaft/hole fits
- `gdt_zones.yaml` - GD&T tolerance zones

**Fasteners:**
- `bolt_torque.yaml` - Bolt torque specs
- `unc_threads.yaml` - UNC thread dimensions

**Electrical:**
- `resistivity.yaml` - Material resistivity
- `metric_wire.yaml` - Wire gauge specs

**Mechanical:**
- `oring_as568.yaml` - O-ring dimensions
- `bearing_sizes.yaml` - Bearing specs

**Process:**
- `gas_properties.yaml` - Gas properties

### LOOKUP() Function
```
LOOKUP("source_name", "parameter", value)
```

**Example:**
```
LOOKUP("aluminum_6061", "yield_strength", 25°C)
```

### Backends
- **Table lookup** - Static table interpolation
- **Equation-based** - Computed from formula
- **CoolProp** - Thermodynamic properties

---

## System Constants

Physical and engineering constants.

### Categories
- Physics (g, c, h, etc.)
- Engineering (common values)
- Custom (user-defined)

### API
```
GET /api/v1/constants/            - List all
GET /api/v1/constants/symbol/{s}  - Get by symbol
POST /api/v1/constants/           - Create custom
```

### Built-in Constants
| Symbol | Name | Value |
|--------|------|-------|
| `g` | Gravitational acceleration | 9.80665 m/s² |
| `c` | Speed of light | 299792458 m/s |
| `pi` | Pi | 3.14159... |
| `e` | Euler's number | 2.71828... |

---

## Linear Integration

Project management integration with Linear.

### Features
- **Progress tracking** - Pull project status from Linear
- **Milestone display** - Show project milestones
- **Team view** - Team member assignments
- **Auto-refresh** - Periodic data sync

### Endpoints
```
GET /api/v1/linear/progress     - Get progress data
GET /api/v1/linear/milestones   - Get milestones
POST /api/v1/linear/refresh     - Force refresh
```

---

## Test Campaign

Test management and tracking.

### Features
- **Test definitions** - Create test specifications
- **Categories** - Acoustic, Thermal, Mechanical, etc.
- **Component linking** - Associate tests with components
- **Result tracking** - Pass/fail/pending status

### API
```
GET  /api/v1/tests/       - List tests
GET  /api/v1/tests/{id}   - Get test
POST /api/v1/tests/       - Create test
```

---

## Reports

Report generation and export.

### Features
- **Dashboard stats** - Component counts, status breakdown
- **Recent activity** - Latest changes
- **PDF export** - Generate reports (planned)

---

## API Overview

### Base URLs
- **Production:** `https://backend-production-aa29.up.railway.app`
- **Development:** `http://localhost:8000`

### Authentication
```
Authorization: Bearer <jwt_token>
```

### Core Endpoints

| Resource | Endpoint | Methods |
|----------|----------|---------|
| Components | `/api/v1/components` | GET, POST, PUT, DELETE |
| Properties | `/api/v1/properties` | GET, POST, PUT |
| Values | `/api/v1/values` | GET, POST |
| Materials | `/api/v1/materials` | GET, POST |
| Units | `/api/v1/units` | GET, POST |
| Constants | `/api/v1/constants` | GET, POST |
| Physics Models | `/api/v1/physics-models` | GET, POST, PATCH |
| Analyses | `/api/v1/analyses` | GET, POST, PATCH, DELETE |
| Tests | `/api/v1/tests` | GET, POST |

### WebSocket
```
ws://host/ws/analysis?token=<jwt>
```

### Documentation
- **Swagger UI:** `/docs`
- **ReDoc:** `/redoc`
- **OpenAPI JSON:** `/openapi.json`

---

## Technology Stack

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Math:** SymPy
- **Deployment:** Railway

### Frontend
- **Framework:** React 18 + TypeScript
- **Build:** Vite
- **Styling:** Tailwind CSS
- **State:** React Query + Context
- **Auth:** Auth0

### Codebase Size
| Component | Lines |
|-----------|-------|
| Python (backend) | ~15,500 |
| TypeScript (frontend) | ~11,500 |
| **Total source** | **~27,000** |

---

## Key Documentation

| Document | Description |
|----------|-------------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System architecture |
| [PHYSICS_MODELS.md](docs/PHYSICS_MODELS.md) | Physics models system |
| [VALUE_SYSTEM.md](docs/VALUE_SYSTEM.md) | Expression engine |
| [API_REFERENCE.md](docs/API_REFERENCE.md) | API endpoints |
| [TEAM_PORTAL_STATE.md](docs/TEAM_PORTAL_STATE.md) | Current state analysis |

---

## Summary

The DRIP Team Portal provides:

1. **Component Management** - Full CRUD with auto-generated codes
2. **Reactive Calculations** - Expression-based properties with auto-recalculation
3. **Physics Modeling** - Reusable templates with dimensional validation
4. **Unit Intelligence** - SI storage, user display, automatic conversion
5. **Materials Database** - Engineering materials with property inheritance
6. **Real-time Collaboration** - WebSocket updates for team visibility
7. **Engineering Data** - 35 verified data sources for lookups
8. **Project Integration** - Linear progress tracking

All features work together through the unified Value System, enabling parametric engineering calculations across the entire system.
