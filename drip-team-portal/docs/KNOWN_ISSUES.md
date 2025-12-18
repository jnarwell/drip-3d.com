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
