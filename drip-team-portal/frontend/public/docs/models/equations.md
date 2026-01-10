---
title: "Equations"
description: "Equation syntax and functions"
---

# Equations

Equations compute outputs from inputs.

## Syntax

```
output_name = expression
```

## Operators

| Operator | Description |
|----------|-------------|
| `+` | Addition |
| `-` | Subtraction |
| `*` | Multiplication |
| `/` | Division |
| `^` | Exponentiation |
| `( )` | Grouping |

## Functions

| Function | Description |
|----------|-------------|
| `sqrt(x)` | Square root |
| `sin(x)` | Sine |
| `cos(x)` | Cosine |
| `tan(x)` | Tangent |
| `log(x)` | Natural log |
| `ln(x)` | Natural log (alias) |
| `exp(x)` | Exponential |
| `abs(x)` | Absolute value |

## Constants

| Constant | Value |
|----------|-------|
| `pi` | 3.141592653589793 |
| `e` | 2.718281828459045 |

## LOOKUP Syntax

Reference property table values:

```
LOOKUP("table_name", "column_name", condition1=value1, condition2=value2)
```

### Examples

```
LOOKUP("steam", "enthalpy", T=373, P=1)
LOOKUP("metric_bolt_dimensions", "thread_pitch_coarse", size=M8)
LOOKUP("pipe_schedules", "od", nps=2, schedule=40)
```

## Dimensional Analysis

The system validates unit consistency:
- Adding/subtracting requires same units
- Output unit must match computed unit

## Example

```
stress = force / area
power = voltage * current
thermal_resistance = thickness / (conductivity * area)
```
