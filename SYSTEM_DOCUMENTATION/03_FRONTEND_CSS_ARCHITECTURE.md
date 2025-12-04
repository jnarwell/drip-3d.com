# Frontend CSS Architecture Documentation

## Executive Summary

The DRIP frontend has evolved from a hybrid CSS architecture to a more streamlined approach for company pages. While the team portal maintains Tailwind utilities, the company pages (Home, Progress, Team) now use React inline styles for consistency and maintainability. This document reflects the current architecture after the December 2025 rebuild.

## Current Architecture Overview

### Two Distinct Approaches

1. **Company Pages (www.drip-3d.com)**
   - React inline styles (CSS-in-JS)
   - No external CSS dependencies
   - Design tokens as JavaScript constants
   - Component-based styling

2. **Team Portal (team.drip-3d.com)**
   - Tailwind CSS utilities
   - Component-specific CSS files
   - Traditional CSS approach

## Company Pages Architecture (NEW)

### Design System Constants

```typescript
// Color Palette
const colors = {
  blue: '#354857',      // Primary brand color (drip blue)
  gray: '#ebf0f1',      // Light gray background
  white: '#ffffff',     // Pure white
  darkGray: '#666666',  // Text gray
  borderGray: '#e9ecef' // Border color
};

// Typography
const typography = {
  fontFamily: 'Roboto, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  h1: {
    fontSize: '48px',
    fontWeight: 'bold'
  },
  h2: {
    fontSize: '36px',
    fontWeight: 'bold'
  },
  h3: {
    fontSize: '24px',
    fontWeight: 'bold'
  },
  body: {
    fontSize: '16px',
    lineHeight: '1.8'
  }
};

// Spacing
const spacing = {
  section: '60px 21px', // Reduced horizontal padding
  container: '1200px',  // Max width
  cardPadding: '40px 30px'
};
```

### Component Styling Patterns

#### Navigation Component
```tsx
const Navigation: React.FC<NavigationProps> = ({ activePage }) => {
  return (
    <nav style={{ 
      backgroundColor: colors.blue,
      padding: '12px 24px 12px 24px', // Specific padding requirements
      display: 'flex',
      justifyContent: 'space-between',
      alignItems: 'center'
    }}>
      {/* Logo with 32px height */}
      <img src="/drip-logo-white.svg" style={{ height: '32px' }} />
      
      {/* Navigation links */}
      <div style={{ display: 'flex', gap: '24px' }}>
        {navItems.map(item => (
          <a style={{
            color: colors.white,
            textDecoration: 'none',
            fontSize: '16px',
            borderBottom: activePage === item.key ? '2px solid #ffffff' : 'none'
          }}>
            {item.label}
          </a>
        ))}
      </div>
    </nav>
  );
};
```

#### Section Backgrounds (Alternating Pattern)
```tsx
// All pages follow this pattern
<section style={{ backgroundColor: colors.gray }}>  {/* Section 1 */}
<section style={{ backgroundColor: colors.blue }}>  {/* Section 2 */}
<section style={{ backgroundColor: colors.gray }}>  {/* Section 3 */}
```

#### Card Components
```tsx
const Card = ({ children }) => (
  <div style={{
    backgroundColor: colors.white,
    borderRadius: '8px',
    padding: spacing.cardPadding,
    boxShadow: '0 2px 4px rgba(0,0,0,0.05)'
  }}>
    {children}
  </div>
);
```

### Animation System

#### Fade-in When Visible Hook
```tsx
// useFadeInWhenVisible.tsx
export const useFadeInWhenVisible = () => {
  const ref = useRef<HTMLElement>(null);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        // Only trigger when 100% visible
        if (entry.isIntersecting && entry.intersectionRatio >= 1) {
          setIsVisible(true);
        }
      },
      { threshold: 1.0 }
    );

    if (ref.current) {
      observer.observe(ref.current);
    }

    return () => observer.disconnect();
  }, []);

  return { ref, isVisible };
};

// Usage
const section = useFadeInWhenVisible();
<div ref={section.ref} style={{
  opacity: section.isVisible ? 1 : 0,
  transition: 'opacity 0.4s ease-in-out'
}}>
```

### Responsive Design

```tsx
// Mobile detection and responsive styling
const [isMobile, setIsMobile] = useState(false);

useEffect(() => {
  const checkMobile = () => setIsMobile(window.innerWidth < 768);
  checkMobile();
  window.addEventListener('resize', checkMobile);
  return () => window.removeEventListener('resize', checkMobile);
}, []);

// Conditional styling
<div style={{
  display: isMobile ? 'block' : 'flex',
  padding: isMobile ? '20px' : '40px'
}}>
```

## Page-Specific Implementations

### HomePage
- Title: "Acoustic Deposition Manufacturing"
- L1 System Capabilities cards (Temperature, Steering, Production)
- How It Works section with specifications table
- Grid layout with 100px gap

### ProgressPage
- Linear API integration for real-time data
- Expandable phase dropdowns
- Progress bars with percentage calculations
- Project cards sorted by end date

### TeamPage
- Team member cards in responsive grid
- Easter egg: 15 rapid scrolls reveal FGM roadmap
- Contact form with 60% width
- Image handling with objectPosition: 'center top'

## Legacy System (Archived)

The previous hybrid CSS system has been moved to `/legacy/static-site/`. It included:

- 1,665 lines of modular CSS
- Six separate CSS files
- Complex BEM naming conventions
- jQuery-based animations

This system is no longer actively used for company pages but remains for reference.

## Team Portal CSS (Unchanged)

The team portal continues to use:

```tsx
// Tailwind utilities
<div className="flex items-center justify-between p-4">
  <h2 className="text-xl font-semibold">Dashboard</h2>
</div>

// With proper Tailwind configuration
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        'drip-blue': '#354857',
        'drip-gray': '#ebf0f1'
      }
    }
  }
}
```

## Performance Optimizations

### Current Implementation

1. **No External CSS**: Inline styles eliminate CSS file loading
2. **Minimal JavaScript**: React handles all animations
3. **Lazy Loading**: Components load as needed
4. **Optimized Images**: Team photos in public directory

### Body Background Handling
```tsx
// useBodyBackground hook
export const useBodyBackground = (color: string) => {
  useEffect(() => {
    const originalColor = document.body.style.backgroundColor;
    document.body.style.backgroundColor = color;
    
    return () => {
      document.body.style.backgroundColor = originalColor;
    };
  }, [color]);
};
```

## Migration Benefits

### From Hybrid to Inline Styles

**Before (Legacy CSS):**
```html
<div class="card card--hover reveal-left stagger-1">
```

**After (Inline Styles):**
```tsx
<div style={{
  backgroundColor: '#ffffff',
  borderRadius: '8px',
  padding: '40px 30px',
  opacity: isVisible ? 1 : 0,
  transition: 'opacity 0.4s ease-in-out'
}}>
```

**Benefits:**
1. No CSS specificity conflicts
2. Component styles colocated with logic
3. Dynamic styling without class manipulation
4. Easier to understand and maintain
5. Better TypeScript support

## Common Patterns

### Centering Content
```tsx
style={{
  maxWidth: '1200px',
  margin: '0 auto'
}}
```

### Grid Layouts
```tsx
style={{
  display: 'grid',
  gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
  gap: '30px'
}}
```

### Hover Effects
```tsx
onMouseEnter={(e) => {
  e.currentTarget.style.transform = 'translateY(-2px)';
}}
onMouseLeave={(e) => {
  e.currentTarget.style.transform = 'translateY(0)';
}}
```

### Tables
```tsx
style={{
  width: '100%',
  borderCollapse: 'collapse',
  backgroundColor: '#ffffff',
  borderRadius: '8px',
  overflow: 'hidden'
}}
```

## Best Practices

### Do's
1. Use design system constants
2. Keep styles close to components
3. Use hooks for reusable behavior
4. Maintain consistent spacing
5. Test responsive behavior

### Don'ts
1. Don't mix CSS approaches on company pages
2. Don't use magic numbers - use constants
3. Don't forget mobile responsiveness
4. Don't inline complex calculations
5. Don't duplicate style objects

## Debugging

### Common Issues

1. **Styles Not Applying**
   - Check style object syntax
   - Verify camelCase property names
   - Look for typos

2. **Animation Issues**
   - Verify ref is attached
   - Check intersection observer threshold
   - Test transition property

3. **Responsive Problems**
   - Use browser DevTools device mode
   - Check media query logic
   - Test at exact breakpoint (768px)

### Chrome DevTools Tips

1. **Inspect Inline Styles**: Elements panel → Styles → element.style
2. **Test Animations**: Rendering tab → Slow animations
3. **Mobile Testing**: Toggle device toolbar
4. **Performance**: Lighthouse audit for optimization

## Future Considerations

### Potential Improvements

1. **Style Objects**: Extract common styles to reusable objects
2. **Theme Context**: Centralized theme management
3. **CSS Variables**: For truly dynamic theming
4. **Component Library**: Shared UI components
5. **Style Type Safety**: TypeScript style definitions

### Maintenance Guidelines

1. Document style changes in components
2. Update design constants when colors change
3. Test across browsers for consistency
4. Monitor performance impact
5. Keep animations smooth (60 FPS)

---

*Last Updated: December 4, 2025*
*System Version: 2.0.0*
*Status: Production - Inline styles architecture for company pages*