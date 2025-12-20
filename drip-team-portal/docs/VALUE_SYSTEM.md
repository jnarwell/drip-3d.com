# Value System Documentation

## Executive Summary

The DRIP Value System is a reactive, expression-based calculation engine that powers all property values in the platform. Every value is a `ValueNode` that can be a literal number, an expression referencing other values, or a direct reference to another node.

## Core Concepts

### Value Types

| Type | Description | Example |
|------|-------------|---------|
| `LITERAL` | Direct numeric value with optional unit | `42.5 mm` |
| `EXPRESSION` | Mathematical expression with references | `sqrt(#CMP001.length * 2)` |
| `REFERENCE` | Points to another ValueNode | Reference to material property |
| `TABLE_LOOKUP` | Table interpolation (planned) | `#steam_table[T: 100]` |

### Reference Syntax

All value references use the `#` prefix:
```
#ENTITY_CODE.property_name
```

**Examples:**
- `#CMP001.length` - Component property by code
- `#FRAME.Height` - Component property by generated code from name
- `#304_STAINLESS_STEEL_001.Density` - Material property

**Code Generation:**
If an entity doesn't have an explicit `code`, one is generated from the name:
- `Heat Bed Assembly` → `HEAT_BED_ASSEMBLY`
- `304 Stainless Steel` → `304_STAINLESS_STEEL`

## Data Models

### ValueNode

The core value container stored in `value_nodes` table:

```python
ValueNode:
    id: int
    node_type: NodeType (LITERAL, EXPRESSION, REFERENCE, TABLE_LOOKUP)

    # For LITERAL nodes
    numeric_value: float          # The raw number
    unit_id: int                  # Reference to units table

    # For EXPRESSION nodes
    expression_string: str        # "sqrt(#CMP001.length * 2)"
    parsed_expression: JSON       # Parsed AST with placeholders

    # Computed/cached result
    computed_value: float         # Result in SI base units
    computed_unit_id: int         # Unit of result
    computed_unit_symbol: str     # SI symbol for display (e.g., "m", "Pa")
    computation_status: enum      # VALID, STALE, ERROR, PENDING, CIRCULAR
    computation_error: str        # Error message if failed
    last_computed: datetime

    # Relationships
    dependencies: List[ValueDependency]   # What this node uses
    dependents: List[ValueDependency]     # What uses this node
```

### ValueDependency

Tracks the dependency graph for reactive updates:

```python
ValueDependency:
    dependent_id: int      # The node that uses another value
    source_id: int         # The node being used
    variable_name: str     # Reference path (e.g., "CMP001.length")
```

### Computation Status

| Status | Meaning |
|--------|---------|
| `VALID` | Computed value is current |
| `STALE` | Dependencies changed, needs recalculation |
| `ERROR` | Computation failed (see error message) |
| `PENDING` | Not yet computed |
| `CIRCULAR` | Circular dependency detected |

## ValueEngine

The core service in `backend/app/services/value_engine.py`:

### Key Capabilities

1. **Expression Parsing** (via SymPy)
   - Supports: `+`, `-`, `*`, `/`, `^`, `**`
   - Functions: `sqrt`, `sin`, `cos`, `tan`, `log`, `exp`, `abs`
   - Constants: `pi`, `e`

2. **Unit Conversion**
   - All values converted to SI base units during evaluation
   - Stored `computed_unit_symbol` enables frontend display conversion
   - Supports 50+ unit types across 19 dimensions

3. **Literal Values with Units**
   - Inline syntax: `12mm`, `5 m`, `100Pa`, `3.14 kg`
   - Automatically converted to SI for storage
   - Both literals and expressions stored consistently in SI base units

4. **Dependency Management**
   - Automatic tracking via `ValueDependency` table
   - **Infinite cascade recalculation**: A → B → C → D... all update automatically
   - **Cross-component updates**: Changes cascade globally across all components
   - Circular dependency detection and prevention

5. **Node Replacement**
   - Seamlessly switch between literal and expression types
   - Dependencies automatically transferred to new node
   - Dependents marked stale and recalculated

### API Usage

**Create Literal:**
```python
engine = ValueEngine(db)
node = engine.create_literal(value=10.5, unit_id=meter_unit_id)
```

**Create Expression:**
```python
node = engine.create_expression(
    expression="sqrt(#CMP001.length * 2)",
    description="Calculated dimension"
)
# Dependencies are automatically extracted and linked
```

**Recalculate:**
```python
success, error = engine.recalculate(node)
# Updates computed_value, computed_unit_id, computed_unit_symbol
```

**Mark Dependents Stale:**
```python
engine.mark_dependents_stale(source_node)
# All nodes depending on source_node are marked STALE (recursively)
```

**Transfer Dependents (Node Replacement):**
```python
engine.transfer_dependents(old_node, new_node)
# Moves all dependencies from old_node to new_node
# Used when replacing literal ↔ expression
# Automatically marks transferred dependents as stale
```

**Recalculate Stale Dependents:**
```python
recalculated = engine.recalculate_stale(source_node)
# Recursively finds and recalculates all stale downstream nodes
# Returns list of recalculated nodes
```

## Unit Propagation

### SI Base Units

All computed values are stored in SI base units:

| Dimension | SI Base Unit |
|-----------|-------------|
| Length | m |
| Area | m² |
| Volume | m³ |
| Mass | kg |
| Force | N |
| Pressure | Pa |
| Temperature | K |
| Time | s |

### Conversion Flow

**Expressions:**
```
User Input: "12 mm + #CMP001.length"
                    ↓
Parse & Convert:   0.012 m + (looked up, converted to m)
                    ↓
Evaluate:          Result in meters (SI)
                    ↓
Store:             computed_value=X, computed_unit_symbol="m"
                    ↓
Display:           Convert from SI to user's preferred unit
```

**Literals:**
```
User Input: "10 mm"
                    ↓
Frontend converts to SI: 0.01 m
                    ↓
Store:             computed_value=0.01, computed_unit_symbol="m"
                    ↓
Display:           Convert from SI to user's preferred unit
```

**Key Principle:** All values (literals AND expressions) are stored consistently in SI base units. The frontend handles conversion both ways.

## Reactive Updates

When a source value changes, the system performs **infinite cascade recalculation** across all components:

```
1. User updates #CMP001.length
        ↓
2. Engine recursively marks ALL downstream dependents as STALE
   (A → B → C → D... infinite levels)
        ↓
3. Stale nodes collected by walking downstream dependency graph
        ↓
4. Sorted by dependency order (sources first)
        ↓
5. Each node recalculated in order
        ↓
6. New values stored, status → VALID
        ↓
7. Frontend invalidates ALL component queries for cross-component refresh
```

### Node Replacement Behavior

When switching between literal and expression (or vice versa):

```
1. New ValueNode created with new type
        ↓
2. transfer_dependents() moves all dependencies to new node
        ↓
3. Transferred dependents marked STALE (recursively)
        ↓
4. New node recalculated
        ↓
5. Cascade recalculation runs for all stale dependents
```

This ensures expressions that referenced the old node continue working seamlessly.

## Integration Points

### Property System
- `ComponentProperty.value_node_id` links to ValueNode
- `MaterialProperty.value_node_id` for material properties
- Enables expressions on any property

### Frontend
- Property input accepts both literals and expressions
- `#` prefix triggers autocomplete suggestions
- Display converts SI → user preferred units

### API Endpoints

```
POST /api/v1/values/              # Create value node
GET  /api/v1/values/{id}          # Get node with computed value
PUT  /api/v1/values/{id}          # Update (recalculates)
GET  /api/v1/variables/search     # Search available references
POST /api/v1/values/{id}/recalculate  # Force recalculation
```

## Best Practices

### Expression Design

**Do:**
```
#CMP001.length * 2                   # Clear reference
sqrt(#beam.width * #beam.height)     # Standard functions
12mm + #part.offset                  # Inline units
```

**Don't:**
```
#cmp1.len                            # Abbreviated names
#CMP001.length + #CMP001.length      # Circular (same property)
12 + #pressure                       # Unit mismatch (dimensionless + pressure)
```

### Dependency Management

1. Keep dependency chains shallow (max ~10 levels)
2. Avoid circular dependencies (engine detects but prevents)
3. Use meaningful entity codes for readability
4. Document complex expressions with property descriptions

## Error Handling

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| "Circular dependency detected" | A → B → A | Review expression chain |
| "Referenced node not found" | Invalid entity/property | Check entity code and property name |
| "Invalid expression" | Syntax error | Verify expression syntax |
| "Dependency failed" | Source has error | Fix source node first |

### Debugging

Check the dependency tree:
```python
tree = engine.get_dependency_tree(node)
# Returns nested structure showing all dependencies
```

---

*Last Updated: December 20, 2025*
*System Version: 2.1.0*
*Replaces: 01_VARIABLE_FORMULA_SYSTEM.md (deprecated)*

**Version 2.1.0 Changes:**
- Infinite cascade recalculation (A → B → C → D... unlimited levels)
- Cross-component reactive updates
- Node replacement with dependency transfer
- Consistent SI storage for both literals and expressions
