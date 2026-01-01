# DRIP Backend API

FastAPI backend for the DRIP Team Portal providing materials engineering data management, property calculations, and value system operations.

## Quick Start

```bash
# Development (with auth bypass)
DEV_MODE=true PYTHONPATH=. uvicorn app.main:app --reload --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, middleware, CORS
│   ├── api/v1/              # API endpoints (22 routers)
│   │   ├── components.py    # Component CRUD
│   │   ├── properties.py    # Properties with values/expressions
│   │   ├── values.py        # Value nodes and dependencies
│   │   ├── materials.py     # Materials database
│   │   ├── materials_project.py  # Materials Project API integration
│   │   ├── constants.py     # System constants
│   │   ├── units.py         # Unit definitions and conversions
│   │   ├── user_preferences.py  # User unit preferences
│   │   ├── linear.py        # Linear integration for progress
│   │   └── ...              # More endpoints
│   ├── models/              # SQLAlchemy ORM models
│   │   ├── component.py     # Component model
│   │   ├── property.py      # Property, PropertyDefinition
│   │   ├── values.py        # ValueNode, ValueDependency
│   │   ├── units.py         # Unit, UnitConversion
│   │   └── ...              # More models
│   ├── services/            # Business logic services
│   │   ├── value_engine.py  # Expression evaluation with SymPy
│   │   ├── model_evaluation.py  # Physics model evaluation
│   │   ├── materials_project.py # MP API client
│   │   └── ...              # More services
│   ├── db/
│   │   └── database.py      # PostgreSQL connection
│   └── core/
│       └── config.py        # Environment configuration
├── requirements.txt
└── README.md
```

## Key Systems

### Value System
Properties can have:
- **Literal values**: `42.5 mm`
- **Expressions**: `#CMP001.length * 2` (references other properties)

Value nodes are stored in `value_nodes` table with automatic dependency tracking.

### Expression Syntax
```
#ENTITY.property_name
```
- `ENTITY` = Component ID (e.g., `CMP001`) or system constant prefix
- Uses SymPy for mathematical evaluation
- Auto-updates when dependencies change

### Unit System
- All values stored in SI base units
- 170+ units seeded with conversion factors
- User display preferences stored per-user, per-dimension

## Environment Variables

```bash
DATABASE_URL=postgresql://...     # PostgreSQL connection
DEV_MODE=true                     # Bypass auth (development only)
LINEAR_API_KEY=lin_api_...        # Linear integration
MP_API_KEY=...                    # Materials Project API
```

## API Documentation

When running locally: http://localhost:8000/docs

See [docs/](../docs/) for full system documentation.
