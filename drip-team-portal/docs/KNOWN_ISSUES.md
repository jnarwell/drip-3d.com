# Known Issues

## 1. Direct URL Access to /team Route Fails

**Issue**: Accessing `https://www.drip-3d.com/team` directly in the browser results in a connection timeout/502 error, but navigating to the Team page via the navigation bar works correctly.

**Status**: Active

**Discovered**: 2024-12-04

**Details**:
- The `/team` route fails when accessed directly via URL
- Client-side navigation (clicking Team link) works perfectly
- Other routes (`/` and `/progress`) work fine with direct URL access
- Console shows the React component is rendering, but the page doesn't display
- Browser extension error: `Invalid frameId for foreground frameId: 0`

**Investigation Summary**:
- Confirmed the issue is not in the React code (component renders in console)
- Not related to custom React hooks (disabling them didn't fix it)
- Appears to be a Railway routing/deployment issue
- Possibly related to how Railway handles path-based routing between services

**Workaround**: Users can access the Team page by:
1. Going to the homepage first: `https://www.drip-3d.com`
2. Clicking the "Team" link in the navigation bar

**Attempted Fixes**:
1. ✗ Renamed static files to avoid route conflicts
2. ✗ Modified nginx configuration for explicit route handling
3. ✗ Disabled React hooks (scroll easter egg, fade-in animations)
4. ✗ Added backend redirect handlers
5. ✗ Simplified TeamPage component to minimal version

**Root Cause**: Unknown - likely Railway infrastructure routing issue where `/team` requests are not properly routed to the frontend service.

---

## 2. Large Bundle Size Warning

**Issue**: Frontend build produces a bundle larger than 500KB (936.93 kB)

**Status**: Low Priority

**Details**: The main JavaScript bundle exceeds recommended size. Consider code-splitting for better performance.

**Potential Solutions**:
- Implement dynamic imports for routes
- Use React.lazy() for component code-splitting
- Configure manual chunks in Vite build options