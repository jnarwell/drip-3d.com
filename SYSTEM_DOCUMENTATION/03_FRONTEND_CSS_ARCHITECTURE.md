# Frontend CSS Architecture Documentation

## Executive Summary

The DRIP frontend currently employs a hybrid CSS architecture combining legacy modular CSS, Tailwind utilities, and React component styles. This creates complexity but provides a complete design system. This document explains the current state and provides guidance for working within this system.

## Current Architecture Overview

### The "CSS Nightmare" Explained

The frontend has three parallel CSS systems:

1. **Legacy Modular CSS** (1,665 lines)
   - Located in `public/assets/css/`
   - Loaded via `<link>` tags in index.html
   - Complete design system from static site

2. **Tailwind CSS**
   - Configured in `tailwind.config.js`
   - Imported via `src/index.css`
   - Used primarily in team portal components

3. **React Component CSS**
   - `src/App.css` and component-specific styles
   - Mixed approach with some CSS-in-JS patterns

## CSS File Structure

### Design Tokens (`variables.css`)

```css
/* Color System */
--steel-dark: #2C3E50;       /* Primary brand color */
--steel-mid: #34495E;        /* Secondary UI elements */
--steel-light: #7F8C8D;      /* Disabled states */
--ceramic-white: #ECF0F1;    /* Main background */
--ceramic-dark: #BDC3C7;     /* Borders, dividers */
--thermal-orange: #E67E22;   /* Accent, warnings */
--acoustic-blue: #3498DB;    /* Links, CTAs */

/* Typography Scale (1.25 ratio) */
--text-xs: 0.875rem;    /* 14px */
--text-sm: 0.9375rem;   /* 15px */
--text-base: 1rem;      /* 16px */
--text-lg: 1.25rem;     /* 20px */
--text-xl: 1.5625rem;   /* 25px */
--text-2xl: 1.875rem;   /* 30px */
--text-3xl: 2.5rem;     /* 40px */
--text-4xl: 3.75rem;    /* 60px */

/* Spacing Scale */
--space-xs: 0.25rem;    /* 4px */
--space-sm: 0.5rem;     /* 8px */
--space-md: 1rem;       /* 16px */
--space-lg: 1.5rem;     /* 24px */
--space-xl: 2rem;       /* 32px */
--space-2xl: 3rem;      /* 48px */
--space-3xl: 4rem;      /* 64px */
--space-4xl: 6rem;      /* 96px */

/* Breakpoints */
--mobile: 0px;
--tablet: 768px;
--desktop: 1024px;
--wide: 1440px;
```

### Layout System (`layout.css`)

```css
/* Container System */
.container {
  max-width: var(--container-width);
  margin: 0 auto;
  padding: 0 var(--container-padding);
}

.container--content {
  max-width: 48rem; /* 768px - prose width */
}

.container--wide {
  max-width: 80rem; /* 1280px */
}

/* Grid System */
.grid {
  display: grid;
  gap: var(--space-lg);
}

.grid--2 { /* Auto-responsive 2 column */
  grid-template-columns: repeat(auto-fit, minmax(20rem, 1fr));
}

.grid--3 { /* Auto-responsive 3 column */
  grid-template-columns: repeat(auto-fit, minmax(18rem, 1fr));
}

/* Section Spacing */
.section {
  padding: var(--space-3xl) 0;
}

@media (min-width: 768px) {
  .section {
    padding: var(--space-4xl) 0;
  }
}
```

### Component Styles (`components.css`)

Key components styled in legacy CSS:

#### Navigation
```css
.header {
  position: fixed;
  top: 0;
  width: 100%;
  background: white;
  transition: transform 0.3s ease;
  z-index: 1000;
}

.header--hidden {
  transform: translateY(-100%);
}

.header--scrolled {
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}
```

#### Cards
```css
.card {
  background: white;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  padding: var(--space-xl);
  transition: transform 0.3s ease;
}

.card:hover {
  transform: translateY(-0.25rem);
  box-shadow: var(--shadow-lg);
}
```

#### Modals
```css
.modal {
  position: fixed;
  inset: 0;
  display: none;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000;
}

.modal--open {
  display: flex;
}

.modal__content {
  background: white;
  border-radius: var(--radius-lg);
  max-width: 40rem;
  max-height: 90vh;
  overflow-y: auto;
}
```

### Animation System (`animations.css`)

#### Keyframes
```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(2rem);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes scaleIn {
  from {
    opacity: 0;
    transform: scale(0.9);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}
```

#### Reveal Classes
```css
.reveal {
  opacity: 0;
  transition: opacity 0.8s ease;
}

.reveal.active {
  opacity: 1;
}

.reveal-left {
  opacity: 0;
  transform: translateX(-2rem);
  transition: all 0.8s ease;
}

.reveal-left.active {
  opacity: 1;
  transform: translateX(0);
}

/* Staggered animations */
.stagger-1 { transition-delay: 0.1s; }
.stagger-2 { transition-delay: 0.2s; }
.stagger-3 { transition-delay: 0.3s; }
```

### Page-Specific Styles (`pages.css`)

#### Hero Sections
```css
.section--hero {
  min-height: 100vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.hero__content {
  position: relative;
  z-index: 1;
}

.hero__title {
  font-size: var(--text-4xl);
  font-weight: 600;
  line-height: 1.2;
  margin-bottom: var(--space-lg);
}
```

#### Company Pages Integration

**HomePage Carousel:**
```css
.carousel {
  position: relative;
  overflow: hidden;
}

.carousel__track {
  display: flex;
  transition: transform 0.5s ease;
}

.carousel__slide {
  flex: 0 0 100%;
  padding: 0 var(--space-md);
}
```

**Team Page Cards:**
```css
.team-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.team-card:hover {
  transform: translateY(-0.5rem);
}

.team-card__photo {
  aspect-ratio: 1;
  object-fit: cover;
  border-radius: 50%;
}
```

**Progress Page Phases:**
```css
.phase {
  border: 1px solid var(--ceramic-dark);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.phase__header {
  padding: var(--space-lg);
  cursor: pointer;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.phase--expanded .phase__content {
  max-height: 100rem;
  padding: var(--space-lg);
}
```

## React Integration Patterns

### Using Legacy CSS in React Components

```tsx
// Correct usage in company pages
<section className="section section--hero">
  <div className="container">
    <div className="hero__content animate-fade-in-up">
      <h1 className="hero__title">
        Drop Resonance Induction Printing
      </h1>
    </div>
  </div>
</section>
```

### Mixing with Tailwind (Portal Components)

```tsx
// Team portal components use Tailwind
<div className="flex items-center justify-between p-4 border-b">
  <h2 className="text-xl font-semibold">Dashboard</h2>
</div>
```

### Animation Integration

```tsx
// Using the scroll animation hook
import { useScrollAnimation } from '@/hooks/useScrollAnimation';

function HomePage() {
  useScrollAnimation(); // Activates .reveal classes
  
  return (
    <div className="reveal-left stagger-1">
      Content appears with animation
    </div>
  );
}
```

## Common Patterns and Solutions

### Problem: Style Conflicts

When Tailwind and legacy CSS conflict:

```tsx
// ❌ Avoid mixing systems
<div className="card p-4"> {/* Conflict! */}

// ✅ Use one system
<div className="card"> {/* Legacy CSS handles padding */}
// OR
<div className="bg-white rounded-lg shadow-md p-4"> {/* Pure Tailwind */}
```

### Problem: Responsive Design

```css
/* Legacy CSS responsive utilities */
.mobile-only {
  display: block;
}

.desktop-only {
  display: none;
}

@media (min-width: 768px) {
  .mobile-only { display: none; }
  .desktop-only { display: block; }
}
```

### Problem: Dynamic Styling

```tsx
// Use CSS classes for states
<div className={`phase ${isExpanded ? 'phase--expanded' : ''}`}>

// Or use inline styles for truly dynamic values
<div style={{ transform: `translateX(${offset}px)` }}>
```

## Performance Optimization

### Current Issues

1. **Duplicate Loading**: CSS loaded both via HTML and React
2. **Large Bundle**: 100KB+ of CSS, much unused
3. **Runtime Calculations**: Heavy DOM manipulation

### Optimization Strategies

#### 1. CSS Loading Order
```html
<!-- index.html - Current order -->
<link rel="stylesheet" href="/assets/css/reset.css">
<link rel="stylesheet" href="/assets/css/variables.css">
<link rel="stylesheet" href="/assets/css/layout.css">
<link rel="stylesheet" href="/assets/css/components.css">
<link rel="stylesheet" href="/assets/css/pages.css">
<link rel="stylesheet" href="/assets/css/animations.css">
```

#### 2. Conditional Loading
```tsx
// Load page-specific CSS only when needed
useEffect(() => {
  if (!isTeamDomain) {
    import('/assets/css/pages.css');
  }
}, [isTeamDomain]);
```

#### 3. CSS Purging
Configure Tailwind to purge unused styles:
```js
// tailwind.config.js
module.exports = {
  content: ['./src/**/*.{js,jsx,ts,tsx}'],
  // Safelist legacy CSS classes
  safelist: [
    'reveal',
    'reveal-left',
    'animate-fade-in-up',
    // ... other legacy classes
  ]
}
```

## Migration Path

### Short Term (Working within current system)

1. **Document Usage**: Comment which CSS system each component uses
2. **Avoid Mixing**: Use either legacy OR Tailwind per component
3. **Extract Constants**: Move magic numbers to CSS variables

### Medium Term

1. **Component Library**: Build React components for legacy styles
2. **CSS Modules**: Isolate styles per component
3. **Remove Duplicates**: Consolidate common styles

### Long Term

1. **Single System**: Choose Tailwind OR styled-components
2. **Design Tokens**: Unified token system across all components
3. **Type Safety**: CSS-in-JS with TypeScript

## Quick Reference

### Essential Classes

**Layout:**
- `.container`, `.container--content`, `.container--wide`
- `.grid`, `.grid--2`, `.grid--3`, `.grid--4`
- `.section`, `.section--hero`, `.section--dark`

**Components:**
- `.card`, `.button`, `.button--primary`, `.button--ghost`
- `.modal`, `.modal--open`, `.modal__content`
- `.header`, `.header--scrolled`, `.header--hidden`

**Animations:**
- `.reveal`, `.reveal-left`, `.reveal-right`, `.reveal-scale`
- `.animate-fade-in-up`, `.animate-fade-in-down`
- `.stagger-1` through `.stagger-6`

**Utilities:**
- `.text-center`, `.text-gradient`
- `.mobile-only`, `.desktop-only`
- `.sr-only` (screen reader only)

## Debugging Tips

### Chrome DevTools

1. **Find Style Source**: 
   - Computed tab → trace style origin
   - Identify if legacy CSS or Tailwind

2. **Animation Debugging**:
   - Slow down animations: DevTools → More → Rendering → Slow animations

3. **Responsive Testing**:
   - Device toolbar for breakpoint testing
   - Watch for CSS conflicts at different sizes

### Common Issues

1. **Animation Not Triggering**
   - Check if `useScrollAnimation()` is called
   - Verify element has `.reveal` class
   - Check intersection observer threshold

2. **Style Not Applying**
   - Check specificity conflicts
   - Verify CSS file is loaded
   - Look for typos in class names

3. **Modal/Carousel Issues**
   - Ensure JavaScript is loaded
   - Check for event listener conflicts
   - Verify DOM structure matches CSS expectations

---

*Last Updated: December 2, 2025*
*System Version: 1.0.0*
*Status: Transitional - Hybrid CSS architecture in migration phase*