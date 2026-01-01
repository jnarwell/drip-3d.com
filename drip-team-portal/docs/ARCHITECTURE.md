# DRIP System Architecture

## Overview

DRIP is a materials engineering platform deployed on Railway with a React frontend, FastAPI backend, and PostgreSQL database. The frontend serves two domains from a single codebase: the public website (www.drip-3d.com) and the team portal (team.drip-3d.com).

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         Railway Platform                        │
├───────────────────────┬────────────────────┬───────────────────┤
│  Frontend Service     │  Backend Service   │  PostgreSQL       │
│  (React + TypeScript) │  (FastAPI + Python)│                   │
│                       │                    │                   │
│  ┌─────────────────┐  │  ┌──────────────┐  │  ┌─────────────┐  │
│  │ www.drip-3d.com │  │  │ API Routers  │  │  │ Components  │  │
│  │ (Public Site)   │──┼──│ 17 routers   │──┼──│ Properties  │  │
│  └─────────────────┘  │  └──────────────┘  │  │ Materials   │  │
│  ┌─────────────────┐  │  ┌──────────────┐  │  │ ValueNodes  │  │
│  │team.drip-3d.com │  │  │ Services     │  │  │ Units       │  │
│  │ (Team Portal)   │──┼──│ 17 services  │──┼──│ Tests       │  │
│  └─────────────────┘  │  └──────────────┘  │  │ Users       │  │
│                       │                    │  └─────────────┘  │
└───────────────────────┴────────────────────┴───────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │ Linear API  │   │ Materials   │   │ CoolProp    │
     │ (Progress)  │   │ Project API │   │ (Thermo)    │
     └─────────────┘   └─────────────┘   └─────────────┘
```

## Domain-Based Routing

The frontend uses hostname detection to serve different experiences:

```typescript
// hooks/useDomain.ts
if (hostname.includes('team.')) return 'team';     // Team portal
if (hostname === 'localhost')   return 'team';     // Dev mode
return 'company';                                   // Public site
```

| Domain | Routes | Auth |
|--------|--------|------|
| www.drip-3d.com | `/`, `/progress`, `/team` | None |
| team.drip-3d.com | `/dashboard`, `/components`, `/tests`, `/resources`, etc. | Auth0 |
| localhost | Team portal routes | Mock auth (dev) |

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, middleware
│   ├── api/v1/                 # API routers (19 total)
│   │   ├── auth.py             # Authentication endpoints
│   │   ├── components.py       # Component CRUD
│   │   ├── constants.py        # System constants
│   │   ├── engineering_properties.py  # Eng properties API
│   │   ├── linear.py           # Linear progress integration
│   │   ├── linear_enhanced.py  # Enhanced Linear features
│   │   ├── materials.py        # Materials database
│   │   ├── materials_project.py# MP API integration
│   │   ├── physics_models.py   # Physics models + analyses API
│   │   ├── properties.py       # Properties with values
│   │   ├── reports.py          # PDF report generation
│   │   ├── search.py           # Global search
│   │   ├── tests.py            # Test campaign management
│   │   ├── units.py            # Unit management
│   │   ├── user_preferences.py # User settings persistence
│   │   ├── values.py           # Value system endpoints
│   │   ├── webhooks.py         # External webhooks
│   │   └── websocket.py        # WebSocket for real-time updates
│   ├── models/                 # SQLAlchemy ORM (14 models)
│   │   ├── audit.py            # Audit logging
│   │   ├── component.py        # Component, ComponentProperty
│   │   ├── material.py         # Material, MaterialProperty
│   │   ├── physics_model.py    # PhysicsModel, ModelVersion, ModelInstance, ModelInput
│   │   ├── property.py         # PropertyDefinition
│   │   ├── resources.py        # Resource definitions
│   │   ├── test.py             # TestCampaign, TestResult
│   │   ├── units.py            # Unit, UnitConversion
│   │   ├── user.py             # User accounts
│   │   ├── user_preferences.py # User preferences
│   │   └── values.py           # ValueNode, ValueDependency
│   ├── services/               # Business logic (20+ services)
│   │   ├── alloy_standards.py  # Alloy lookup
│   │   ├── code_generator.py   # Code generation
│   │   ├── dimensional_analysis.py  # 32 dimensions, 197 units
│   │   ├── linear.py           # Linear GraphQL client
│   │   ├── material_property_manager.py  # Material properties
│   │   ├── materials_project.py# MP API client
│   │   ├── model_evaluation.py # Physics model evaluation
│   │   ├── nist_webbook.py     # NIST property lookup
│   │   ├── physics.py          # Physics calculations
│   │   ├── reports.py          # Report generation
│   │   ├── seed_units.py       # Unit seeding
│   │   ├── unit_calculator.py  # Unit math
│   │   ├── unit_engine.py      # Unit conversions
│   │   ├── value_engine.py     # Expression evaluation
│   │   ├── equation_engine/    # Equation parsing/evaluation subsystem
│   │   │   ├── parser.py       # SymPy-based equation parser
│   │   │   ├── evaluator.py    # AST tree walker
│   │   │   ├── latex_generator.py  # LaTeX output
│   │   │   └── exceptions.py   # Custom exceptions
│   │   └── properties/         # Engineering properties subsystem
│   │       ├── router.py       # LOOKUP dispatcher
│   │       ├── registry.py     # YAML source loader
│   │       ├── schemas.py      # Pydantic models
│   │       └── backends/
│   │           ├── table.py    # Static table lookups
│   │           ├── equation.py # Equation-based calculations
│   │           └── coolprop.py # CoolProp integration
│   └── db/
│       └── database.py         # PostgreSQL connection
├── data/                       # Engineering data (35 YAML files)
│   ├── electrical/             # Wire gauges
│   ├── fasteners/              # Threads, torque specs
│   ├── finishes/               # Surface finishes
│   ├── material/               # Temperature-dependent materials
│   ├── mechanical/             # O-rings, pipes, keyways
│   ├── process/                # Steam, refrigerants, gases
│   ├── structural/             # Structural shapes
│   └── tolerances/             # ISO tolerances
```

### Key Services

| Service | Purpose |
|---------|---------|
| `value_engine.py` | Expression parsing, evaluation, LOOKUP(), dependency management |
| `unit_engine.py` | Unit conversions, dimensional analysis |
| `equation_engine/` | Physics model equation parsing (SymPy), evaluation, LaTeX generation |
| `dimensional_analysis.py` | SI dimensional validation (32 dimensions, 197 unit mappings) |
| `model_evaluation.py` | Physics model instance evaluation, input resolution |
| `properties/` | Engineering properties LOOKUP system (35 data sources) |
| `materials_project.py` | Materials Project API integration |
| `linear.py` | Linear GraphQL client for progress tracking |
| `reports.py` | PDF report generation |
| `physics.py` | Physics calculations and validations |

### Engineering Properties System

The `properties/` service provides standardized engineering data lookups with 35 verified data sources:

```
backend/app/services/properties/
├── __init__.py          # Public API exports
├── router.py            # LOOKUP dispatcher, input validation
├── registry.py          # YAML source loader, view generator
├── schemas.py           # Pydantic models for sources
└── backends/
    ├── table.py         # Static table lookups
    ├── equation.py      # Equation-based calculations
    └── coolprop.py      # CoolProp library integration
```

**Data Sources (backend/data/):**

| Category | Count | Tables | Source Standards |
|----------|-------|--------|------------------|
| `fasteners` | 9 | bolt_torque, metric_bolt_torque, api6a_flange_torque, unc_threads, unf_threads, metric_threads_coarse, metric_threads_fine, npt_threads, metric_bolt_dimensions | SAE J-429, ISO 898-1, API 6A, ASME B1.1, ASME B1.20.1, ISO 68-1 |
| `electrical` | 1 | wire_gauge_awg | ASTM B258 |
| `mechanical` | 3 | oring_as568, pipe_schedules, keyway_sizes | SAE AS568, ASME B36.10 |
| `process` | 6 | gas_properties (25 gases), steam, steam_temperature, steam_pressure, r134a, r134a_temperature | CoolProp (NIST REFPROP), IAPWS-IF97 |
| `tolerances` | 2 | iso_286_tolerance, surface_roughness | ISO 286-1 |
| `finishes` | 1 | surface_roughness | ISO 1302 |
| `material` | 14 | Temperature-dependent materials (al_6061_t6, ss_304, ss_316, steel_4140, ti_6al_4v, etc.) | CoolProp, literature |

**Key Features:**
- YAML-based property source definitions with verified data sources
- Case-insensitive discrete input matching
- CoolProp integration for thermodynamic properties (IAPWS-IF97)
- Temperature unit conversion in LOOKUP() inputs (°C, °F → K)
- `lookup_source_id` pattern for unified LOOKUP across display views
- SI unit storage with frontend conversion via UnitContext
- All values stored in SI base units (m, kg, s, Pa, K, etc.)

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── pages/
│   ├── company/                # Public site pages
│   │   ├── HomePage.tsx
│   │   ├── ProgressPage.tsx
│   │   ├── TeamPage.tsx
│   │   └── useBodyBackground.tsx
│   ├── resources/              # Engineering resources
│   │   ├── Constants.tsx       # System constants browser
│   │   └── PropertyTables.tsx  # Engineering tables viewer
│   ├── ModelBuilder/           # Physics model creation wizard
│   │   ├── index.tsx           # 4-step wizard container
│   │   ├── StepDefineModel.tsx # Step 1: Name, category
│   │   ├── StepInputsOutputs.tsx # Step 2: Variables
│   │   ├── StepEquations.tsx   # Step 3: Equations
│   │   ├── StepValidate.tsx    # Step 4: Validation
│   │   └── types.ts            # TypeScript types
│   ├── InstanceCreator/        # Model instantiation wizard
│   │   ├── index.tsx           # 4-step wizard container
│   │   ├── StepSelectModel.tsx # Step 1: Select model
│   │   ├── StepBindInputs.tsx  # Step 2: Bind inputs
│   │   ├── StepAttachComponent.tsx # Step 3: Attach
│   │   └── StepReview.tsx      # Step 4: Review
│   ├── analysis/               # Analysis dashboard (named instances)
│   │   ├── Analysis.tsx        # List all analyses
│   │   └── AnalysisCreator.tsx # Create/edit analysis wizard
│   ├── ModelsList.tsx          # Physics models list
│   ├── Dashboard.tsx           # Team portal home
│   ├── ComponentRegistry.tsx   # Component list
│   ├── ComponentDetailPage.tsx # Component editor
│   ├── Login.tsx               # Auth0 login
│   ├── Reports.tsx             # Report generation
│   ├── Resources.tsx           # Resources hub
│   ├── Settings.tsx            # User preferences
│   └── TestCampaign.tsx        # Test management
├── components/                 # Reusable components
│   ├── ComponentDetailModal.tsx
│   ├── PropertyValue.tsx       # Expression input
│   └── ...
├── hooks/                      # Custom hooks
│   ├── useDomain.ts            # Domain detection
│   ├── useUnitPreferences.ts   # User unit prefs
│   ├── useLinearData.tsx       # Linear API hooks
│   └── useAnalysisWebSocket.ts # WebSocket for Analysis real-time updates
├── contexts/
│   └── UnitContext.tsx         # Unit system context
├── utils/
│   └── unitConversion.ts       # Unit conversion functions
└── services/
    └── auth-domain.tsx         # Domain-aware auth
```

### Team Portal Pages

| Page | Purpose | Key Features |
|------|---------|--------------|
| Dashboard | Portal home | Recent activity, quick stats |
| ComponentRegistry | Component list | Search, filter, CRUD |
| ComponentDetailPage | Component editor | Properties, values, materials |
| ModelsList | Physics models | List, create, instantiate models |
| ModelBuilder | Model creation | 4-step wizard: Define → I/O → Equations → Validate |
| InstanceCreator | Model instantiation | 4-step wizard: Select → Bind → Attach → Review |
| Analysis | Named instances | Team-wide analyses with WebSocket updates |
| AnalysisCreator | Create/edit analysis | 4-step wizard: Name → Model → Bindings → Review |
| TestCampaign | Test management | Create, track, report tests |
| Resources | Engineering hub | Constants, tables, references |
| Reports | Report generation | PDF export, templates |
| Settings | User preferences | Unit system, display prefs |
| Login | Authentication | Auth0 integration |

### State Management

- **React Query** for server state (API data)
- **React Context** for global state (units, auth)
- **Local state** for component-specific state

### Unit System

The frontend handles unit display preferences while the backend stores all values in SI:

```typescript
// UnitContext.tsx - Dimension detection
UNIT_TO_DIMENSION = {
  'K': 'temperature', '°C': 'temperature', '°F': 'temperature',
  'm': 'length', 'mm': 'length', 'in': 'length', 'ft': 'length',
  'Pa': 'pressure', 'psi': 'pressure', 'MPa': 'pressure',
  // ... 100+ unit mappings
}

// Temperature conversion with offset handling
convertTemperature(value, fromUnit, toUnit)  // Special case for °C, °F
convertUnit(value, fromUnit, toUnit)         // Multiplicative conversions
```

### Modal Pattern (React Portal)

All modals use React Portal to render at `document.body` level, ensuring proper z-index stacking above the navbar:

```typescript
import { createPortal } from 'react-dom';

// Modal rendered via portal
{isOpen && createPortal(
  <div className="fixed inset-0 z-[100] bg-black bg-opacity-50 ...">
    <div className="modal-content">...</div>
  </div>,
  document.body
)}
```

Key files using this pattern:
- `components/ComponentDetailModal.tsx`
- `pages/resources/PropertyTables.tsx` (fullscreen mode)
- `pages/TestCampaign.tsx` (create/edit/result modals)

## Data Models

### Core Entities

```
Component ──────────────┬────────────────── Material
    │                   │                       │
    │ has many          │ references            │ has many
    ▼                   ▼                       ▼
ComponentProperty ──► ValueNode ◄── MaterialProperty
    │                   │
    │ uses              │ depends on
    ▼                   ▼
PropertyDefinition  ValueDependency
    │
    │ has
    ▼
   Unit
```

### All Models

| Model | Purpose |
|-------|---------|
| `Component` | Engineering components with properties |
| `ComponentProperty` | Property values for components |
| `Material` | Material definitions |
| `MaterialProperty` | Material property values |
| `PropertyDefinition` | Property type definitions |
| `ValueNode` | Expression-based values |
| `ValueDependency` | Value dependency tracking |
| `PhysicsModel` | Physics model template identity |
| `PhysicsModelVersion` | Versioned model with equations |
| `ModelInstance` | Bound model with input sources |
| `ModelInput` | Single input binding |
| `Unit` | Unit definitions |
| `UnitConversion` | Unit conversion factors |
| `TestCampaign` | Test management |
| `TestResult` | Test results |
| `User` | User accounts |
| `UserPreference` | User settings |
| `AuditLog` | Change tracking |

### Key Relationships

1. **Component → Properties**: Each component has multiple properties
2. **Property → ValueNode**: Every property value is a ValueNode
3. **ValueNode → Dependencies**: Expressions reference other nodes
4. **Material → Properties**: Materials have inheritable properties
5. **TestCampaign → Components**: Tests validate component properties

## Value System Flow

```
User Input: "12mm + #CMP001.length"
           │
           ▼
    ┌──────────────┐
    │ Parse Input  │  Extract references, literals, units
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Resolve Refs │  Look up #CMP001.length → ValueNode
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Convert Units│  12mm → 0.012m, 100°C → 373.15K
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Evaluate     │  SymPy math evaluation
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Store Result │  computed_value (SI), computed_unit_symbol
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Mark Stale   │  Cascade to dependents
    └──────────────┘
```

### LOOKUP() Function

```python
# Table lookup
LOOKUP("unc_threads", "pitch_mm", size="#4")  # → 0.635

# CoolProp thermodynamic lookup with temperature conversion
LOOKUP("steam", "h", T=100°C, P=101325Pa)  # T converted to K internally

# Material property lookup
LOOKUP("al_6061_t6", "E", T=373.15K)  # Young's modulus at temperature
```

## Authentication

| Environment | Method | Details |
|-------------|--------|---------|
| Production (team) | Auth0 | @drip-3d.com emails only |
| Production (public) | None | Public access |
| Development | Mock | Auto-authenticated as dev user |

## External Integrations

### Linear API
- **Purpose**: Project progress tracking
- **Data**: Initiatives, projects, milestones
- **Cache**: 5-minute TTL
- **Routers**: `linear.py`, `linear_enhanced.py`

### Materials Project
- **Purpose**: Computational materials database
- **Data**: Material properties, crystal structures
- **Features**: Search, import to local DB

### CoolProp
- **Purpose**: Thermodynamic property calculations
- **Data**: Steam tables, refrigerants, gas properties
- **Standard**: IAPWS-IF97, NIST REFPROP

## Deployment

### Railway Services

| Service | Build | Health Check |
|---------|-------|--------------|
| Frontend | `npm run build` | HTTP 200 on `/` |
| Backend | `uvicorn app.main:app` | `/health` endpoint |
| PostgreSQL | Managed | Auto |

### Environment Variables

```bash
# Backend
DATABASE_URL=postgresql://...
DEV_MODE=true/false
LINEAR_API_KEY=lin_api_...
MP_API_KEY=...

# Frontend
VITE_API_URL=https://backend-production-aa29.up.railway.app
```

## Documentation Index

| Document | Description |
|----------|-------------|
| [VALUE_SYSTEM.md](VALUE_SYSTEM.md) | Expression engine, dependency tracking |
| [PHYSICS_MODELS.md](PHYSICS_MODELS.md) | Physics models system (equations, dimensions, evaluation) |
| [CONSTANTS_TEMPLATES_TABLES.md](CONSTANTS_TEMPLATES_TABLES.md) | System constants, 35 property tables |
| [MATERIALS_DATABASE.md](MATERIALS_DATABASE.md) | Materials system, MP integration |
| [UNIFIED_FRONTEND_ARCHITECTURE.md](UNIFIED_FRONTEND_ARCHITECTURE.md) | Domain routing, styling |
| [RAILWAY_INTEGRATION.md](RAILWAY_INTEGRATION.md) | Deployment, troubleshooting |
| [LINEAR_INTEGRATION.md](LINEAR_INTEGRATION.md) | Progress tracking |
| [API_REFERENCE.md](API_REFERENCE.md) | API endpoints |
| [ROADMAP_FEATURES.md](ROADMAP_FEATURES.md) | Future features |

---

*Last Updated: December 27, 2025*
