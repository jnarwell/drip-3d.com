---
title: "Components"
description: "Overview of the component registry system"
---

# Components

**Routes:** `/components`, `/components/:componentId`

The Component Registry is the central database for all parts, assemblies, and materials.

## Component Card Fields

- Name
- ID (auto-generated: CMP-001, CMP-002, etc.)
- Category
- Part Number
- Supplier
- Cost
- Status badge (NOT_TESTED, IN_TESTING, VERIFIED, FAILED)
- R&D Phase badge (Phase 1, Phase 2, Phase 3)

## Property Types

Properties are grouped by type:
- Thermal
- Electrical
- Mechanical
- Acoustic
- Material
- Dimensional
- Optical
- Other

## Property Value Types

| Type | Format | Example |
|------|--------|---------|
| SINGLE | `value unit` | `10 mm` |
| RANGE | `min - max unit` | `5 - 15 mm` |
| AVERAGE | `value +/- tolerance unit` | `10 +/- 2 mm` |
| TEXT | Plain text (monospace display) | `Aluminum 6061-T6` |

## Expression System

Reference other properties using expressions:
- Syntax: `#COMPONENT_CODE.property_name`
- Example: `#FRAME.length`, `#MOTOR.rpm`
- Math expressions: `(1/8)*3mm`, `#HEATBED.k * 2`
- Purple "expr" badge indicates expression value
- Yellow "stale" badge indicates dependent value changed

## Related Topics

- [Registry](registry.md) - List view and filtering
- [Detail](detail.md) - Full page component view
- [Properties](properties.md) - Property management
- [Materials](materials.md) - Materials Project integration
