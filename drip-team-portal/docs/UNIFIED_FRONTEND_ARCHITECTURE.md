# Unified Frontend Architecture

## Overview

The DRIP-3D.com frontend is a single React application that serves both the public website and team portal through domain-based routing. This document explains how the unified architecture works.

## Domain-Based Routing

### Implementation

The application uses a custom hook `useIsTeamDomain()` to determine which site to render:

```typescript
// hooks/useDomain.ts
export const useIsTeamDomain = () => {
  return window.location.hostname === 'team.drip-3d.com' || 
         window.location.hostname === 'localhost';
};
```

### Route Structure

```typescript
// App.tsx
function AppRoutes() {
  const isTeamDomain = useIsTeamDomain();
  
  // Company site routes (www.drip-3d.com)
  if (!isTeamDomain) {
    return (
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/progress" element={<ProgressPage />} />
        <Route path="/team" element={<TeamPage />} />
        <Route path="*" element={<Navigate to="/" />} />
      </Routes>
    );
  }
  
  // Team portal routes (team.drip-3d.com)
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<DomainAwareProtectedRoute><Layout /></DomainAwareProtectedRoute>}>
        <Route index element={<Navigate to="/dashboard" />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="components" element={<ComponentRegistry />} />
        // ... more portal routes
      </Route>
    </Routes>
  );
}
```

## Authentication Strategy

### Domain-Aware Authentication

The `DomainAwareAuthProvider` component handles authentication differently based on the domain:

- **Public site (www.drip-3d.com)**: No authentication required
- **Team portal (team.drip-3d.com)**: Auth0 authentication (with dev mode option)

```typescript
// services/auth-domain.tsx
export const DomainAwareAuthProvider = ({ children }) => {
  const isTeamDomain = useIsTeamDomain();
  
  if (!isTeamDomain) {
    // Public site - no auth needed
    return <>{children}</>;
  }
  
  // Team portal - full auth
  return <AuthProvider>{children}</AuthProvider>;
};
```

## Shared Resources

### Assets Structure

All assets are stored in the frontend's public folder and shared between both sites:

```
frontend/public/
├── assets/
│   ├── css/          # Legacy stylesheets (being phased out)
│   └── images/       # Shared images
│       └── system/   # System diagrams
├── team-images/      # Team member photos (renamed from /team/)
└── data/            # JSON data files
    ├── team-data.json   # Team member data
    ├── milestones.json
    └── specs.json
```

### Component Reusability

Common components are shared where possible:
- Navigation components adapt based on domain
- Layout components handle different styling needs
- Utility functions work across both sites

## Build and Deployment

### Single Build Process

Both sites are built from the same codebase:

```bash
npm run build
# Creates a single dist/ folder serving both domains
```

### Railway Configuration

The frontend service in Railway is configured with both custom domains:
- www.drip-3d.com
- team.drip-3d.com

Both domains point to the same service, and the React app handles routing based on the hostname.

## Performance Considerations

### Code Splitting

The application uses dynamic imports to load only necessary code:

```typescript
// Lazy load portal components for team domain
const Dashboard = lazy(() => import('./pages/Dashboard'));
const ComponentRegistry = lazy(() => import('./pages/ComponentRegistry'));

// Lazy load company pages for public domain
const HomePage = lazy(() => import('./pages/company/HomePage'));
const TeamPage = lazy(() => import('./pages/company/TeamPage'));
```

### Shared Dependencies

Common dependencies are loaded once and cached:
- React framework
- Routing libraries
- Utility functions
- CSS frameworks

## Development Workflow

### Local Development

During development, the app defaults to team portal mode (localhost is treated as team domain):

```bash
npm run dev
# Access at http://localhost:5173 - shows team portal
```

To test the public site locally, you can:
1. Modify the `useIsTeamDomain` hook temporarily
2. Use a local hosts file entry
3. Access via a different port with environment variables

### Environment Variables

```bash
# .env.development
VITE_API_URL=http://localhost:8000

# .env.production
VITE_API_URL=https://backend-production-aa29.up.railway.app
```

## Styling Architecture

### Inline Styles Approach

The company pages (HomePage, TeamPage, ProgressPage) use inline styles for:
- Better component encapsulation
- Easier dynamic styling
- Reduced CSS conflicts
- Simplified deployment

### Mobile Responsiveness

Mobile support is implemented through:

```typescript
// hooks/useMobile.tsx
export const useMobile = (breakpoint: number = 768) => {
  const [isMobile, setIsMobile] = useState(false);
  // ... responsive logic
};
```

Key responsive features:
- Navigation collapses to hamburger menu
- Grid layouts stack on mobile
- Font sizes scale appropriately
- Padding/margins adjust for mobile

### Custom Hooks

Company pages utilize several custom hooks:
- `useBodyBackground`: Sets page-specific body colors
- `useFadeInWhenVisible`: Intersection Observer for animations
- `useScrollEasterEgg`: Hidden content on repeated scrolling
- `useMobile`: Responsive design detection

## Migration from Static Site

### What Changed

1. **HTML → React Components**: Static HTML pages converted to React components
2. **Vanilla JS → React Hooks**: Interactive features reimplemented with React patterns
3. **Static Assets → Public Folder**: All assets moved to React public directory
4. **Multiple Files → Single SPA**: Three HTML files became one React app
5. **CSS Files → Inline Styles**: Company pages now use inline styles

### Preserved Features

All original functionality was maintained:
- Animations and transitions
- Responsive design
- Interactive carousels and modals
- Form handling
- Data loading from JSON files

## Future Considerations

### Potential Improvements

1. **SSR/SSG**: Consider Next.js for better SEO on public pages
2. **CDN**: Serve static assets from a CDN
3. **Progressive Enhancement**: Add service worker for offline capability
4. **Analytics**: Separate tracking for each domain

### Maintenance Tips

1. Test both domains when making routing changes
2. Ensure assets work for both sites
3. Keep authentication logic domain-aware
4. Monitor bundle size as features grow

## Troubleshooting

### Common Issues

1. **Wrong site showing**: Check domain detection logic
2. **Assets not loading**: Verify public folder paths
3. **Auth issues**: Ensure auth is only active on team domain
4. **Routing problems**: Check for domain-specific route conflicts

### Debug Commands

```javascript
// Check current domain detection
console.log('Is team domain:', window.location.hostname);

// Force domain mode for testing
localStorage.setItem('forceDomain', 'team'); // or 'public'
```

## Recent Updates (December 2024)

### Company Pages Enhancement
- Added alternating section backgrounds (gray/blue pattern)
- Implemented fade-in animations for content sections
- Created scroll-triggered easter egg on Team page
- Added mobile responsiveness to all company pages

### Infrastructure Changes
- Fixed navigation Link components for proper React Router usage
- Resolved `/team/` directory conflict causing route issues
- Updated nginx configuration for SPA routing
- Enhanced mobile navigation with proper z-index layering

### Known Issues
- Direct URL access to `/team` route fails (see docs/KNOWN_ISSUES.md)
- Workaround: Navigate via homepage and click Team link

---

Last Updated: December 4, 2024