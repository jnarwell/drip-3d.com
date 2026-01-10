---
title: "Bindings"
description: "Input binding syntax"
---

# Bindings

Connect analysis inputs to values using various binding types.

## Binding Types

### Literal Values

Direct numeric values:
```
25.5
1.5e-4
-273.15
```

### Analysis References

Use outputs from other analyses:
```
#REF:{id}
#NODE:{id}
```

Where `{id}` is the value node ID.

### System Constants

Reference global constants:
```
$CONST.PI
#CONST.g
$g
```

Available constants:

| Symbol | Name | Value | Unit |
|--------|------|-------|------|
| g | Gravitational acceleration | 9.80665 | m/s² |
| c | Speed of light | 299792458 | m/s |
| h | Planck constant | 6.626e-34 | J·s |
| k_B | Boltzmann constant | 1.38e-23 | J/K |
| R | Gas constant | 8.314 | J/(mol·K) |
| N_A | Avogadro's number | 6.022e23 | 1/mol |
| T_stp | STP temperature | 273.15 | K |
| P_stp | STP pressure | 101325 | Pa |

### Component Properties

Reference component property values:
```
#FRAME.length
#MOTOR.rpm
#HEATBED.k
```

### Free Expressions

Mathematical operations:
```
#MOTOR.torque * 0.95
(#COMP.length + #COMP.width) / 2
#REF:42 + #REF:43
```

## Inline Editing

From the Analysis list:
1. Expand analysis row
2. Double-click a binding value
3. Edit the value
4. Press Enter to save, Escape to cancel

## Gotchas

- Circular dependency detection on #REF chains
- All required model inputs must have bindings
- Analysis doesn't auto-recalculate unless explicitly triggered
