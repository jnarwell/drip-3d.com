---
title: "Constants"
description: "Physical and mathematical constants"
---

# Constants

**Route:** `/resources` → Constants tab

Physical and mathematical constants for use in equations.

## Syntax

Two equivalent syntaxes:

```
#CONST(name)
$name
```

Example: `#CONST(g)` or `$g` for standard gravity.

## Available Constants

| Constant | Symbol | Value | Unit |
|----------|--------|-------|------|
| Standard gravity | g | 9.80665 | m/s² |
| Speed of light | c | 299792458 | m/s |
| Planck constant | h | 6.626e-34 | J·s |
| Boltzmann constant | k_B | 1.38e-23 | J/K |
| Gas constant | R | 8.314 | J/(mol·K) |
| Avogadro number | N_A | 6.022e23 | 1/mol |
| Standard temperature | T_stp | 273.15 | K |
| Standard pressure | P_stp | 101325 | Pa |

## Usage Examples

### Standard Gravity

```
weight = mass * $g
```

### Ideal Gas Law

```
P * V = n * $R * T
```

### Kinetic Energy

```
E = 0.5 * $h * frequency
```

## Greek Letters and Symbols

The equation editor supports Greek letters and math symbols:

- Type `\alpha` for α
- Type `\beta` for β
- Type `\pi` for π
- Type `\mu` for μ
- Type `\omega` for ω

Use Ctrl+, for subscript and Ctrl+. for superscript.

## Display

Constants display:
- Name and symbol
- Value with full precision
- SI unit
- Description

## Adding Constants

Constants are system-managed. Contact admin to request additional constants.
