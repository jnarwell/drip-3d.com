---
title: "Property Tables"
description: "Lookup tables for engineering calculations"
---

# Property Tables

**Route:** `/resources` → Property Tables tab

37 lookup tables organized into 8 categories for use in equations.

## Categories

| Category | Tables | Examples |
|----------|--------|----------|
| Fasteners | Bolt specs, thread data | UNC threads, bolt torque |
| Mechanical | Bearings, seals | O-ring sizes, bearing dimensions |
| Material | Material properties | Densities, thermal properties |
| Electrical | Wire specs, components | Wire gauges, resistivity |
| Tolerances | Fits, GD&T | ANSI fits, ISO tolerances |
| Finishes | Surface treatments | Anodizing specs, plating |
| Process/Fluids | Gas and fluid data | Gas properties, viscosity |
| Structural | Beam profiles | I-beam dimensions, tube sizes |

## Using Tables in Equations

### LOOKUP Syntax

```
LOOKUP("table_name", "column_name", condition1=value1)
```

### Examples

```
LOOKUP("unc_threads", "pitch", size="1/4")
```
Returns the pitch for 1/4" UNC thread.

```
LOOKUP("bolt_torque", "torque_nm", size="M8", grade="8.8")
```
Returns torque value for M8 grade 8.8 bolt.

```
LOOKUP("oring_as568", "id_mm", dash_number="210")
```
Returns inner diameter for AS568-210 O-ring.

## Template Generation

When viewing a table:
1. Click column header
2. System generates LOOKUP template
3. Copy to clipboard
4. Paste into equation

## Table View

- **Fullscreen modal**: Expand for large tables
- **Column sorting**: Click headers to sort
- **Search**: Filter rows by any column
- **Export**: Download as CSV

## Adding Tables

Tables are system-managed. Contact admin to request new tables or modifications.

## Common Tables

### Fasteners

| Table | Key Columns |
|-------|-------------|
| unc_threads | size, tpi, pitch, major_dia |
| bolt_torque | size, grade, torque_nm, torque_ftlb |

### Mechanical

| Table | Key Columns |
|-------|-------------|
| oring_as568 | dash_number, id_mm, cs_mm |
| bearing_sizes | designation, bore, od, width |

### Electrical

| Table | Key Columns |
|-------|-------------|
| metric_wire | awg, diameter_mm, resistance_per_m |
| resistivity | material, resistivity_ohm_m |

### Tolerances

| Table | Key Columns |
|-------|-------------|
| ansi_fits | class, hole_tol, shaft_tol |
| gdt_zones | feature, tolerance_zone |
