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
│  │ (Public Site)   │──┼──│ 22 routes    │──┼──│ Properties  │  │
│  └─────────────────┘  │  └──────────────┘  │  │ Materials   │  │
│  ┌─────────────────┐  │  ┌──────────────┐  │  │ ValueNodes  │  │
│  │team.drip-3d.com │  │  │ Services     │  │  │ Units       │  │
│  │ (Team Portal)   │──┼──│ 13 services  │──┼──│ Users       │  │
│  └─────────────────┘  │  └──────────────┘  │  └─────────────┘  │
└───────────────────────┴────────────────────┴───────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
     ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
     │ Linear API  │   │ Materials   │   │ NIST        │
     │ (Progress)  │   │ Project API │   │ WebBook     │
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
| team.drip-3d.com | `/dashboard`, `/components`, `/tests`, etc. | Auth0 |
| localhost | Team portal routes | Mock auth (dev) |

## Backend Architecture

### Directory Structure

```
backend/
├── app/
│   ├── main.py                 # FastAPI app, CORS, middleware
│   ├── api/v1/                 # API routers
│   │   ├── components.py       # Component CRUD
│   │   ├── properties.py       # Properties with values
│   │   ├── materials.py        # Materials database
│   │   ├── materials_project.py# MP API integration
│   │   ├── values.py           # Value system endpoints
│   │   ├── units.py            # Unit management
│   │   ├── constants.py        # System constants
│   │   ├── linear.py           # Linear progress integration
│   │   └── ...                 # 14 more routers
│   ├── models/                 # SQLAlchemy ORM
│   │   ├── component.py
│   │   ├── property.py
│   │   ├── values.py           # ValueNode, ValueDependency
│   │   ├── units.py            # Unit, UnitConversion
│   │   └── ...
│   ├── services/               # Business logic
│   │   ├── value_engine.py     # Expression evaluation
│   │   ├── unit_engine.py      # Unit calculations
│   │   ├── materials_project.py# MP API client
│   │   └── ...
│   └── db/
│       └── database.py         # PostgreSQL connection
```

### Key Services

| Service | Purpose |
|---------|---------|
| `value_engine.py` | Expression parsing, evaluation, dependency management |
| `unit_engine.py` | Unit conversions, dimensional analysis |
| `properties/` | Engineering properties LOOKUP system |
| `materials_project.py` | Materials Project API integration |
| `linear.py` | Linear GraphQL client for progress tracking |
| `nist_webbook.py` | NIST material property lookup |

### Engineering Properties System

The `properties/` service provides standardized engineering data lookups:

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

**Key Features:**
- YAML-based property source definitions in `backend/data/`
- Case-insensitive discrete input matching
- CoolProp integration for thermodynamic properties (IAPWS-IF97)
- `lookup_source_id` pattern for unified LOOKUP across display views
- Unit conversion for grid display values

## Frontend Architecture

### Directory Structure

```
frontend/src/
├── pages/
│   ├── company/                # Public site pages
│   │   ├── HomePage.tsx
│   │   ├── ProgressPage.tsx
│   │   └── TeamPage.tsx
│   ├── Dashboard.tsx           # Team portal
│   ├── ComponentRegistry.tsx
│   ├── ComponentDetailPage.tsx
│   └── Settings.tsx
├── components/                 # Reusable components
├── hooks/                      # Custom hooks
│   ├── useDomain.ts            # Domain detection
│   ├── useUnitPreferences.ts   # User unit prefs
│   └── useLinearData.tsx       # Linear API hooks
├── contexts/
│   └── UnitContext.tsx         # Unit system context
└── services/
    └── auth-domain.tsx         # Domain-aware auth
```

### State Management

- **React Query** for server state (API data)
- **React Context** for global state (units, auth)
- **Local state** for component-specific state

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

### Key Relationships

1. **Component → Properties**: Each component has multiple properties
2. **Property → ValueNode**: Every property value is a ValueNode
3. **ValueNode → Dependencies**: Expressions reference other nodes
4. **Material → Properties**: Materials have inheritable properties

## Value System Flow

```
User Input: "12mm + #CMP001.length"
           │
           ▼
    ┌──────────────┐
    │ Parse Input  │  Extract references, literals
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Resolve Refs │  Look up #CMP001.length → ValueNode
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Convert Units│  12mm → 0.012m (SI)
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Evaluate     │  SymPy math evaluation
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Store Result │  computed_value, computed_unit_symbol
    └──────┬───────┘
           │
           ▼
    ┌──────────────┐
    │ Mark Stale   │  Cascade to dependents
    └──────────────┘
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

### Materials Project
- **Purpose**: Computational materials database
- **Data**: Material properties, crystal structures
- **Features**: Search, import to local DB

### NIST WebBook
- **Purpose**: Authoritative property data
- **Data**: Thermodynamic properties

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
| [CONSTANTS_TEMPLATES_TABLES.md](CONSTANTS_TEMPLATES_TABLES.md) | System constants, property tables |
| [MATERIALS_DATABASE.md](MATERIALS_DATABASE.md) | Materials system, MP integration |
| [UNIFIED_FRONTEND_ARCHITECTURE.md](UNIFIED_FRONTEND_ARCHITECTURE.md) | Domain routing, styling |
| [RAILWAY_INTEGRATION.md](RAILWAY_INTEGRATION.md) | Deployment, troubleshooting |
| [LINEAR_INTEGRATION.md](LINEAR_INTEGRATION.md) | Progress tracking |
| [API_REFERENCE.md](API_REFERENCE.md) | API endpoints |

---

*Last Updated: December 24, 2025*
