# DRIP System Documentation Overview

## Introduction

This documentation provides comprehensive technical documentation for the DRIP (Drop Resonance Induction Printing) platform's core systems. Following Anthropic's principles for effective AI-assisted development, each system is documented with clear interfaces, usage examples, and integration points.

## Core Systems

### 1. [Variable Formula System](./01_VARIABLE_FORMULA_SYSTEM.md) 🔢 **[HIGHEST PRIORITY]**

The mathematical foundation of DRIP, enabling dynamic property calculations through expressions with variable references.

**Key Features:**
- Mathematical expression parsing with SymPy
- Variable reference system with `#prefix` syntax
- Automatic unit calculation and validation
- Dependency management and circular reference detection
- Real-time evaluation with caching

**Quick Example:**
```
Stress = #force / (#pi * (#diameter/2)^2)
```

---

### 2. [Constants, Templates & Tables System](./02_CONSTANTS_TEMPLATES_TABLES_SYSTEM.md) 📊

Comprehensive data management for engineering constants, property tables, and reusable templates.

**Key Features:**
- System constants (physics, math, engineering)
- Property table templates with interpolation
- Verification system (🟢 Verified, 🟡 Cited, 🔴 Unverified)
- Document import with OCR support
- Source tracking and quality assurance

**Quick Access:**
- Constants: `#g`, `#pi`, `#k_B`
- Custom constants with Unicode support
- Temperature-dependent properties

---

### 3. [Frontend CSS Architecture](./03_FRONTEND_CSS_ARCHITECTURE.md) 🎨

Documentation of the hybrid CSS system managing the company website styling.

**Current State:**
- Legacy modular CSS (1,665 lines)
- Tailwind CSS integration
- React component styles
- "CSS Nightmare" - three parallel systems

**Key Components:**
- Design tokens in CSS variables
- Animation system with reveal effects
- Responsive grid layouts
- Component-based BEM naming

---

### 4. [Materials Database API](./04_MATERIALS_DATABASE_API.md) 🧪

Dual-source material property system integrating local engineering data with Materials Project.

**Key Features:**
- 200+ engineering alloy mappings
- Materials Project integration (140,000+ materials)
- Property inheritance to components
- Industry standards cross-reference (UNS, ASTM)
- Acoustic property calculations for DRIP

**Integration Points:**
- Formula variables: `#steel.density`
- Automatic property propagation
- Temperature-dependent lookups

---

### 5. [Linear Integration](./05_LINEAR_INTEGRATION.md) 📈

Project management integration for progress tracking and test result synchronization.

**Two-Way Integration:**
1. **Website Progress** (Read-only)
   - Initiative/project display
   - 5-minute caching
   - Public milestone tracking

2. **Team Portal Sync** (Read/Write)
   - Test result → Linear issues
   - Component tracking
   - Bidirectional updates

---

## System Integration Map

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │Company Pages│  │ Team Portal  │  │ Material UI   │  │
│  │  (Legacy CSS)│  │  (Tailwind)  │  │  Components   │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
└────────────────────────┬────────────────────────────────┘
                         │ API Calls
┌────────────────────────▼────────────────────────────────┐
│                   Backend (FastAPI)                      │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐  │
│  │  Formula    │  │  Materials   │  │   Constants   │  │
│  │   Engine    │◄─┤   Database   │◄─┤   & Tables    │  │
│  └─────────────┘  └──────────────┘  └───────────────┘  │
│         ▲                 ▲                              │
│         └─────────────────┴──────────────┐              │
│                                          │              │
│  ┌─────────────────────────────┐  ┌─────▼──────────┐  │
│  │      Linear Integration      │  │  Variable      │  │
│  │   (Progress & Test Sync)     │  │  Resolution    │  │
│  └─────────────────────────────┘  └────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Quick Reference

### Variable Types
- Component properties: `#cmp1.length`
- System constants: `#g`, `#pi`
- Material properties: `#steel.density`
- Functions: `sqrt()`, `sin()`, `log()`

### API Endpoints

**Formula System:**
```
POST /api/v1/formulas/create-from-expression
POST /api/v1/formulas/{id}/calculate
GET  /api/v1/variables/search?q=mass
```

**Materials:**
```
POST /api/v1/materials-project/search
POST /api/v1/materials-project/import
GET  /api/v1/materials/{id}/properties/enhanced
```

**Constants & Tables:**
```
GET  /api/v1/constants/
POST /api/v1/enhanced/property-tables/import-from-document
```

**Linear:**
```
GET  /api/v1/linear/progress
POST /api/v1/linear/refresh
```

## Development Guidelines

### Adding New Features

1. **Check Integration Points**: Review system documentation for dependencies
2. **Follow Patterns**: Use established patterns from existing systems
3. **Document Interfaces**: Create clear API documentation
4. **Consider Performance**: Check caching and optimization strategies
5. **Test Integration**: Verify cross-system functionality

### Debugging Tips

1. **Formula Issues**: Check variable resolution and unit consistency
2. **Material Properties**: Verify inheritance flags and source tracking
3. **CSS Conflicts**: Identify which system (legacy/Tailwind) is active
4. **Linear Sync**: Check cache status and API connectivity
5. **Constants**: Ensure proper categorization and symbol uniqueness

## System Priorities

1. **🔴 Critical**: Variable Formula System - Core calculation engine
2. **🟠 High**: Materials Database - Essential engineering data
3. **🟠 High**: Constants/Tables - Reference data foundation
4. **🟡 Medium**: Linear Integration - Project coordination
5. **🟡 Medium**: CSS Architecture - UI consistency

## Documentation Principles

Following Anthropic's guidelines:

1. **Clear Interfaces**: Each system has well-defined boundaries
2. **Usage Examples**: Real code examples throughout
3. **Integration Points**: Clear documentation of system interactions
4. **Edge Cases**: Common issues and solutions documented
5. **Performance Notes**: Optimization strategies included

## Getting Help

When working with these systems:

1. **Start with Overview**: Read this document first
2. **Deep Dive**: Use specific system docs for implementation
3. **Check Integration**: Review how systems connect
4. **Follow Examples**: Use provided code samples
5. **Debug Systematically**: Use troubleshooting guides

---

*Last Updated: December 2, 2025*
*Documentation Version: 1.0.0*
*Platform: DRIP Acoustic Manufacturing System*

## Documentation Requirements

### 📋 [Documentation Requirements Guide](./DOCUMENTATION_REQUIREMENTS.md) **[MANDATORY]**

**All contributors MUST follow these documentation requirements:**

- **Pre-Change Review**: Search, read, and understand existing docs
- **File Management**: Check redundancy, ensure proper placement, legacy old files
- **Update Requirements**: Keep all documentation current with changes
- **Red Flags**: Clear conditions when to STOP work immediately
- **Quality Standards**: Checklist for documentation completeness

**Core Workflow:**
```
STOP → SEARCH → READ → PLAN → DOCUMENT → CODE
```

---

## Future Documentation

Planned additions:
- Authentication & Security System
- Test Campaign Management
- Report Generation System
- Component Registry Details
- Deployment & DevOps Procedures