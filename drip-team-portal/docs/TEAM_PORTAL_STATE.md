# Team Portal State Analysis
**Date**: December 19, 2025

## Current State Overview

The team portal (team.drip-3d.com) is the professional/internal side of the DRIP application, providing project management, component tracking, validation tools, and a reactive value/expression system.

## Codebase Size

| Type | Lines |
|------|-------|
| Python (backend app) | 15,439 |
| TypeScript/TSX (frontend src) | 11,467 |
| **Source code total** | **~27,000** |
| Config/data (JSON, SQL, CSS) | ~25,000 |
| **All files total** | **~52,000** |

## Key Components

### 1. **Authentication**
- **Status**: Working
- **Implementation**: Auth0 with domain-based activation
- **Features**:
  - Only active on team.drip-3d.com
  - Email domain restriction (@drip-3d.com)
  - JWT token-based authentication
  - Dev mode bypass with `x-email` header

### 2. **Value System (NEW - December 2025)**

The core of the property system is now a reactive **Value Node** architecture:

#### ValueNode Types
- **LITERAL**: Direct numeric value with units (e.g., `10 mm`)
- **EXPRESSION**: Mathematical expression with references (e.g., `#FRAME.Height * 2`)
- **REFERENCE**: Points to another ValueNode
- **TABLE_LOOKUP**: Table interpolation (Phase 4 - future)

#### Key Features
- **Universal Property References**: ANY property can reference ANY other property
- **Full Mathematical Expressions**: Complete math support via SymPy (`sqrt(a * b) + c`)
- **Unit-Aware Computation**: Dimensional analysis with 7 SI base dimensions
- **Reactive Dependencies**: Auto-recalculation when source values change
- **Circular Dependency Prevention**: Graph-based detection

#### Expression Syntax
```
#ENTITY_CODE.property_name
```
Examples:
- `#FRAME.Height` - Reference component property
- `#304_STAINLESS_STEEL.Density` - Reference material property
- `sqrt(#HEATBED.Width * #HEATBED.Length)` - Mathematical expression

### 3. **Expression Input Component**

The `ExpressionInput` component provides ghost text autocomplete:

#### Features
- Type `#` to start a reference
- Ghost text shows best matching entity code
- Tab to accept (auto-adds `.` after entity)
- After `.`, shows property name suggestions
- Tab to complete property name

#### Performance Optimizations
- **Client-side caching**: 60-second TTL for search results
- **Pre-fetching**: Warms cache with all entities on mount
- **Race condition handling**: Ref-based query tracking prevents stale updates

### 4. **Unit System**

Dimensional analysis with 7 SI base dimensions:
- Length (m)
- Mass (kg)
- Time (s)
- Current (A)
- Temperature (K)
- Amount (mol)
- Luminous intensity (cd)

#### Architecture (December 2025 Overhaul)
- **SI Base Storage**: All values computed and stored in SI base units internally
- **Backend-driven Preferences**: User preferences stored in database (`user_unit_preferences` table)
- **Display-only Conversion**: Frontend converts from SI to user's preferred unit only for display
- **computed_unit_symbol Field**: ValueNode stores the SI unit symbol (e.g., "m", "Pa") for proper display conversion

#### Features
- Automatic unit computation through expressions
- Unit conversion between compatible units
- Mixed unit expressions (e.g., `100 mm + 1 m` works correctly)
- Dimension tracking through expression evaluation
- User-preferred unit display per quantity type

### 5. **Main Pages**

#### Dashboard (`/dashboard`)
- **Status**: Working
- **Features**: Dashboard stats, recent activity, error boundaries

#### Component Registry (`/components`)
- **Status**: Working
- **Features**:
  - CRUD operations for components
  - Property management with expression support
  - Material property auto-pull
  - Filtering by category, status
  - Search functionality

#### Test Campaign (`/tests`)
- **Status**: Unknown (needs testing)
- **Features**: Test execution and tracking

#### Resources (`/resources`)
- **Status**: Working
- **Sub-pages**:
  - Property Tables
  - Constants
  - Templates

#### Settings (`/settings`)
- **Status**: Working (unit preferences)

## API Endpoints Status

### Core Endpoints
- `/api/v1/components` - Component CRUD
- `/api/v1/auth` - Authentication
- `/api/v1/properties` - Property management with expression support
- `/api/v1/materials` - Material data
- `/api/v1/constants` - System constants
- `/api/v1/templates` - Templates
- `/api/v1/linear` - Linear integration (progress data)
- `/api/v1/linear-enhanced` - Enhanced Linear (team members, projects)
- `/api/v1/reports` - Dashboard stats and activity
- `/api/v1/variables` - Variable management

### New Value System Endpoints
- `/api/v1/units` - Unit definitions and conversions
- `/api/v1/values` - ValueNode CRUD and recalculation
- `/api/v1/search/entities` - Entity autocomplete search
- `/api/v1/search/entities/{code}/properties` - Property autocomplete search

## Data Models

### Value System Models (`/backend/app/models/values.py`)
```python
ValueNode:
  - id, node_type (LITERAL/EXPRESSION/REFERENCE/TABLE_LOOKUP)
  - numeric_value, unit_id (for literals)
  - expression_string, parsed_expression (for expressions)
  - computed_value, computed_unit_id, computed_unit_symbol (cached result)
  - computation_status (VALID/STALE/ERROR/PENDING/CIRCULAR)

ValueDependency:
  - dependent_id, source_id
  - variable_name (how it's referenced in expression)
```

### User Preferences Models (`/backend/app/models/user_preferences.py`)
```python
UserUnitPreference:
  - id, user_id
  - quantity_type (e.g., "length", "pressure", "temperature")
  - preferred_unit_id (FK to units table)
  - precision (display precision, default 0.01)
```

### Unit Models (`/backend/app/models/units.py`)
```python
Unit:
  - symbol, name, quantity_type
  - length_dim, mass_dim, time_dim, current_dim
  - temperature_dim, amount_dim, luminous_dim
  - is_base_unit, multiplier, offset
```

## Services

### ValueEngine (`/backend/app/services/value_engine.py`)
- Expression parsing with SymPy
- Reference resolution (component/material property lookup)
- Unit conversion to SI base units during evaluation
- SI unit symbol tracking (stored in `computed_unit_symbol`)
- Dependency graph building
- Stale detection and recalculation cascade (walks dependents, not dependencies)
- Circular dependency detection

### UnitEngine (`/backend/app/services/unit_engine.py`)
- Unit dimensional analysis
- Unit compatibility checking
- Value conversion between units

## UI/UX State

### Design System
- Tailwind CSS classes throughout
- Consistent color scheme:
  - Primary: Indigo (`indigo-600`)
  - Success: Green (`green-500`)
  - Error: Red (`red-500`)
  - Neutral: Gray shades

### Loading States
- Consistent spinner implementation
- Loading states on all data fetches

### Expression UI
- Ghost text autocomplete (gray overlay text)
- Tab to complete suggestions
- Purple "expr" badge for expression properties
- Computed value display with expression preview

## Data Flow

### State Management
- React Query for server state
- Local state with useState for UI state
- No global state management (Zustand/Redux)

### API Integration
- Axios-based authenticated API client
- Automatic token injection
- Query invalidation on mutations

### Reactive Updates
1. User edits a property value
2. Backend updates ValueNode
3. Backend marks dependents as STALE
4. Backend auto-recalculates stale nodes
5. Frontend invalidates queries
6. UI updates with new computed values

## Known Issues

See `/docs/KNOWN_ISSUES.md` for details:
1. Direct URL access to `/team` route fails
2. Large bundle size (~947 KB)

## Recommendations

### Performance Improvements
1. **Code splitting** - Lazy load routes
2. **Bundle optimization** - Extract vendor chunks
3. **Memoization** - Add React.memo to heavy components

### UX Enhancements
1. **Mobile responsiveness** - Apply same patterns as company pages
2. **Better error messages** - User-friendly error states
3. **Skeleton loaders** - Better perceived performance

### Future Development
1. **Table lookups** - Implement TABLE_LOOKUP node type with interpolation
2. **Testing integration** - Connect test results to value system
3. **Modeling** - Full system modeling, non-dimensional scaling
