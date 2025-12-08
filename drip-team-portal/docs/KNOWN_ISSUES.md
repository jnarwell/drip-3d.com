# Known Issues

## 1. Direct URL Access to /team Route Fails

**Issue**: Accessing `https://www.drip-3d.com/team` directly in the browser results in a connection timeout/502 error, but navigating to the Team page via the navigation bar works correctly.

**Status**: Active - Partially Resolved

**Discovered**: 2024-12-04

**Last Updated**: 2024-12-04

**Details**:
- The `/team` route fails when accessed directly via URL
- Client-side navigation (clicking Team link) works perfectly
- Other routes (`/` and `/progress`) work fine with direct URL access
- Console shows the React component is rendering, but the page doesn't display
- Browser extension error: `Invalid frameId for foreground frameId: 0`

**Investigation Summary**:
- Confirmed the issue is not in the React code (component renders in console)
- Not related to custom React hooks (disabling them didn't fix it)
- Found and removed conflicting `/team/` directory in `public/assets/images/team/`
- Issue persists after removing the directory conflict
- Appears to be a deeper Railway routing/deployment issue

**Workaround**: Users can access the Team page by:
1. Going to the homepage first: `https://www.drip-3d.com`
2. Clicking the "Team" link in the navigation bar

**Attempted Fixes**:
1. ✗ Renamed static files to avoid route conflicts
2. ✗ Modified nginx configuration for explicit route handling
3. ✗ Disabled React hooks (scroll easter egg, fade-in animations)
4. ✗ Added backend redirect handlers
5. ✗ Simplified TeamPage component to minimal version
6. ✓ Removed conflicting `/team/` directory (partial fix)

**Root Cause**: Partially identified - there was a conflicting `/team/` directory that has been removed. However, the issue persists, suggesting a deeper Railway infrastructure routing issue.

---

## 2. Large Bundle Size Warning

**Issue**: Frontend build produces a bundle larger than 500KB (936.93 kB)

**Status**: Low Priority

**Details**: The main JavaScript bundle exceeds recommended size. Consider code-splitting for better performance.

**Potential Solutions**:
- Implement dynamic imports for routes
- Use React.lazy() for component code-splitting
- Configure manual chunks in Vite build options