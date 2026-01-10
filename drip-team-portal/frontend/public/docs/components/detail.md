---
title: "Component Detail"
description: "Full page component view"
---

# Component Detail

**Route:** `/components/:componentId`

Full page layout with header (name, part number, back button).

## Property List

- Grouped by property type
- Collapsible sections
- Inline editing (click value to edit)

## Expression Support

Property values can be expressions:
- Syntax: `#COMPONENT_CODE.property_name`
- Math: `(1/8)*3mm`, `#HEATBED.k * 2`
- Purple "expr" badge on expression values
- Yellow "stale" badge when dependencies change

## Material Selector

- 220k+ materials from Materials Project API
- Search and select materials
- Inherits material properties automatically
- Inherited properties marked "From material:" in notes

## Unit Conversion

- All numeric values stored in SI units (meters, kg, etc.)
- Displayed in user's preferred units

## Gotchas

- Collapsed section state persists to localStorage
- All numeric values stored in SI units internally
- Material inheritance marks properties "From material:" in notes
- No undo on property deletion
