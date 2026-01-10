---
title: "Expression Syntax"
description: "Reference for expressions, bindings, and lookups"
---

# Expression Syntax

Expressions allow binding analysis inputs to properties, referencing other analyses, and using constants.

## Property References

Reference component properties:

```
#FRAME.length
#MOTOR.rpm
#SENSOR.voltage
```

Structure: `#` + component code + `.` + property name.

## Analysis References

### Output References

Reference another analysis output by ID:

```
#REF:{id}
```

Example: `#REF:42` references the output of analysis with ID 42.

### Node References

Reference specific nodes in analysis chains:

```
#NODE:{id}
```

Used for chaining analyses together.

## Constants

Two equivalent syntaxes:

```
$CONST.PI
#CONST.g
$g
```

Available constants:
- `g` - Standard gravity (9.80665 m/s²)
- `c` - Speed of light (299792458 m/s)
- `h` - Planck constant (6.626e-34 J·s)
- `k_B` - Boltzmann constant (1.38e-23 J/K)
- `R` - Gas constant (8.314 J/(mol·K))
- `N_A` - Avogadro number (6.022e23)
- `T_stp` - Standard temperature (273.15 K)
- `P_stp` - Standard pressure (101325 Pa)

## LOOKUP Function

Query property tables:

```
LOOKUP("table_name", "column_name", condition=value)
```

### Examples

```
LOOKUP("unc_threads", "pitch", size="1/4")
LOOKUP("bolt_torque", "torque_nm", size="M8", grade="8.8")
LOOKUP("oring_as568", "id_mm", dash_number="210")
```

## Mathematical Operators

| Operator | Description |
|----------|-------------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `()` | Parentheses |

## Expression Examples

### Basic Property

```
#FRAME.mass
```

### Calculated Volume

```
#BOX.length * #BOX.width * #BOX.height
```

### With Constant

```
#OBJECT.mass * $g
```

### Chained Analysis

```
#REF:42 + #REF:43
```

### Complex Expression

```
(#HEATER.power * 3600) / (#TANK.volume * #FLUID.density * #FLUID.specific_heat)
```

## Autocomplete

Expression inputs support autocomplete:
1. Type `#` to start reference
2. Begin typing component code
3. Ghost text shows match
4. Press Tab to accept
5. Continue with property name
6. Press Enter to submit

## Unit Handling

- Units convert automatically to match expected unit
- Dimensional analysis validates compatibility
- Incompatible units cause errors

## Validation Errors

| Error | Cause |
|-------|-------|
| "Entity not found" | Component doesn't exist |
| "Property not found" | Property not on component |
| "Invalid syntax" | Malformed expression |
| "Unit mismatch" | Incompatible units |
| "Circular reference" | Analysis references itself |
