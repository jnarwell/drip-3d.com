---
title: "Component Properties"
description: "Adding and managing component properties"
---

# Component Properties

## Property Types

Properties are organized by type:
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
| TEXT | Plain text (monospace) | `Aluminum 6061-T6` |

## Adding Properties

1. Click "Add Property" dropdown (multi-level menu by property type)
2. Select property type category
3. Fill in value with appropriate format

## Editing Properties

- Click value to edit inline
- Changes save on blur/enter

## Expression Values

Reference other component properties:

```
#FRAME.length
#MOTOR.rpm
#HEATBED.k * 2
(1/8)*3mm
```

### Expression Indicators

- **Purple "expr" badge**: Value is an expression
- **Yellow "stale" badge**: Dependent value changed, needs recalculation

## Unit Storage

All numeric values stored internally in SI units:
- Length: meters
- Mass: kilograms
- Temperature: Kelvin
- etc.

Displayed in user's preferred units from Settings.

## Gotchas

- No undo on property deletion
- Deleting a property referenced by an expression causes stale state
