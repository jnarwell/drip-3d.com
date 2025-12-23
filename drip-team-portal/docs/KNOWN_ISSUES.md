# Known Issues

## 1. Direct URL Access to /team Route Fails

**Issue**: Accessing `https://www.drip-3d.com/team` directly in the browser results in a connection timeout/502 error, but navigating to the Team page via the navigation bar works correctly.

**Status**: Active - NOT RESOLVED

**Discovered**: 2024-12-04

**Last Updated**: 2025-12-14

**Details**:
- The `/team` route fails when accessed directly via URL
- Client-side navigation (clicking Team link) works perfectly
- Other routes (`/` and `/progress`) work fine with direct URL access

**Workaround**: Users can access the Team page by:
1. Going to the homepage first: `https://www.drip-3d.com`
2. Clicking the "Team" link in the navigation bar

**Root Cause**: Unknown - Suspected Railway infrastructure routing issue.

---

## 2. Large Bundle Size Warning

**Issue**: Frontend build produces a bundle larger than 500KB (~947 kB)

**Status**: Low Priority

**Details**: The main JavaScript bundle exceeds recommended size.

**Potential Solutions**:
- Implement dynamic imports for routes
- Use React.lazy() for component code-splitting
- Configure manual chunks in Vite build options

---

## 3. Expression Autocomplete Initial Delay (RESOLVED)

**Issue**: First keystroke after `#` had ~200-500ms delay before ghost text appeared.

**Status**: RESOLVED (December 17, 2025)

**Solution**:
- Added client-side caching with 60-second TTL
- Pre-fetch all entities on component mount to warm cache
- Subsequent queries are now instant from cache

---

## 4. Ghost Text Race Condition (RESOLVED)

**Issue**: Typing quickly showed partial/incorrect ghost text completions (e.g., "e", "me", "ame" instead of "E" for completing "FRAME").

**Status**: RESOLVED (December 17, 2025)

**Solution**:
- Added ref-based query tracking (`latestEntityQueryRef`, `latestPropertyQueryRef`)
- API responses are ignored if they don't match the current query
- Prevents stale responses from overwriting current state

---

## 5. Stale Dependent Values Not Auto-Recalculating (RESOLVED)

**Issue**: When editing a source property value, dependent expressions stayed in "stale" status and didn't auto-recalculate.

**Status**: RESOLVED (December 18, 2025)

**Root Cause**: The `recalculate_stale()` function was walking upstream (dependencies) instead of downstream (dependents). When a literal is updated, its dependents are marked stale, but walking dependencies wouldn't find them.

**Solution (Two Parts)**:
1. Added `engine.recalculate_stale(node)` calls after update endpoints
2. Fixed the graph traversal direction in `value_engine.py`:
   - `recalculate_stale()` now walks `node.dependents` (downstream)
   - Added `_collect_stale_dependents()` to recursively find stale nodes
   - Added `_sort_by_dependency_order()` to ensure correct calculation order
- Dependent values now automatically recalculate when source changes

---

## 6. Expression Results Showing Wrong Units (RESOLVED)

**Issue**: Expression results computed in SI base units (e.g., 0.4 meters) were displayed with the wrong unit symbol (e.g., "0.4 mm" instead of "0.4 m"), causing values to appear 1000x incorrect.

**Status**: RESOLVED (December 19, 2025)

**Root Cause**: The API wasn't returning the SI unit symbol for the computed value. The frontend needs to know the *actual* computed unit to convert properly for display.

**Solution (Three Parts)**:
1. Added `computed_unit_symbol` field to ValueNode model (stores "m", "Pa", etc.)
2. Updated `value_engine.py` to track and store SI unit symbol during expression evaluation
3. Updated `properties.py` API to return `computed_unit_symbol` in the response

**Key Files**:
- `backend/app/models/values.py` - Added `computed_unit_symbol` column
- `backend/app/services/value_engine.py` - Unit tracking during evaluation
- `backend/app/api/v1/properties.py` - Return `computed_unit_symbol` in response

**Architecture Note**: All values are computed and stored in SI base units. The `computed_unit_symbol` tells the frontend which SI unit to convert FROM when displaying in the user's preferred unit.

---

## 7. Literal Values Display Bug After Reload (RESOLVED)

**Issue**: When entering a value like "10mm", it displayed correctly initially but showed "0.001 mm" after page reload.

**Status**: RESOLVED (December 20, 2025)

**Root Cause**: Inconsistency between literal and expression storage:
- Expressions were evaluated and stored in SI units (e.g., 0.01 meters)
- Literals were stored in the property definition's unit (e.g., 10 mm)
- Display code assumed everything was in SI, causing wrong conversions

**Solution (Two Parts)**:
1. **Frontend (PropertyValue.tsx)**: Updated `handleSave` to convert literal values to SI before sending to backend, matching expression behavior
2. **Frontend (PropertyValue.tsx)**: Fixed display to convert FROM SI base unit (`BASE_UNITS[dimension]`) instead of from property definition unit

**Key Change**: Both literals and expressions now stored consistently in SI base units.

---

## 8. Node Replacement Breaks Dependencies (RESOLVED)

**Issue**: When changing a property from expression to literal (or vice versa), dependent expressions would stop updating because they were linked to the OLD ValueNode ID.

**Status**: RESOLVED (December 20, 2025)

**Root Cause**: Creating a new ValueNode for the replacement didn't transfer the dependency links from the old node.

**Solution**:
- Added `transfer_dependents(old_node, new_node)` method to ValueEngine
- Called during node replacement to update all `ValueDependency.source_id` references
- Marks transferred dependents as stale for recalculation

**Key Files**:
- `backend/app/services/value_engine.py` - New `transfer_dependents()` method
- `backend/app/api/v1/properties.py` - Calls transfer on node replacement

---

## 9. Cascade Recalculation Only One Level Deep (RESOLVED)

**Issue**: With dependency chain A → B → C (C depends on B, B depends on A), changing A would recalculate B but not C.

**Status**: RESOLVED (December 20, 2025)

**Root Cause**: The stale marking and collection wasn't fully recursive through all downstream dependency levels.

**Solution (Three Parts)**:
1. Added `_mark_node_and_dependents_stale()` helper that recursively marks ALL downstream nodes
2. Updated `transfer_dependents()` to use recursive marking
3. Updated `recalculate_stale()` to call `mark_dependents_stale()` before collecting

**Result**: Infinite cascade recalculation now works - changing a value cascades through unlimited dependency levels (A → B → C → D → ...).

---

## 10. Cross-Component Updates Not Showing (RESOLVED)

**Issue**: When updating a value in Component A, dependent expressions in Component B wouldn't refresh in the UI even though they were recalculated in the backend.

**Status**: RESOLVED (December 20, 2025)

**Root Cause**: Frontend only invalidated queries for the current component (`['component-properties', componentId]`), not for other components.

**Solution**: Changed `updateProperty` mutation's `onSuccess` to invalidate ALL component-properties queries:
```typescript
queryClient.invalidateQueries({ queryKey: ['component-properties'] });
```

**Key File**: `frontend/src/components/PropertyValue.tsx`

---

## 11. Expression Update Doesn't Cascade to Cross-Component Dependents (RESOLVED)

**Issue**: When directly editing an expression (e.g., B on Frame), cross-component dependents (e.g., C on Heatbed referencing B) would get stuck on "calculating..." and never update. However, if a literal upstream of B was changed, the cascade worked correctly.

**Status**: RESOLVED (December 20, 2025)

**Root Cause**: The expression update path was missing `recalculate_stale()` call. Literal updates had it, but expression updates didn't cascade to dependents.

**Solution**: Added `engine.recalculate_stale(existing_node)` after updating an existing expression node in `properties.py`:
```python
if existing_node and existing_node.node_type.value == "expression":
    engine.update_expression(existing_node, expression)
    engine.recalculate(existing_node)
    engine.recalculate_stale(existing_node)  # Added this line
```

**Key File**: `backend/app/api/v1/properties.py`

---

## 12. Imperial Units Not Recognized in Expressions (RESOLVED)

**Issue**: Using imperial length units in expressions (e.g., `#FRAME.Height - 2ft` or `5in + 3cm`) caused a 400 Bad Request error.

**Status**: RESOLVED (December 23, 2025)

**Root Cause**: The `LITERAL_WITH_UNIT_PATTERN` regex in `value_engine.py` was missing `in` and `ft` from the length units pattern.

**Solution**: Added imperial length units to the regex pattern:
```python
LITERAL_WITH_UNIT_PATTERN = re.compile(
    r'(?<![a-zA-Z0-9_])(-?\d+\.?\d*)\s*'
    r'(nm|μm|mm|cm|m|km|in|ft|'  # Added in|ft| for imperial
    # ... rest of pattern
)
```

**Key File**: `backend/app/services/value_engine.py`

**Note**: Mixed metric/imperial expressions (e.g., `1m + 2ft`) now work correctly - all values are converted to SI base units during evaluation.
