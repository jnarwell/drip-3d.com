---
title: "Creating Analyses"
description: "Analysis creator wizard"
---

# Creating Analyses

**Route:** `/analysis/new`

4-step wizard for creating analysis instances.

## Step 1: Name and Description

- Analysis name (required)
- Description (optional)

## Step 2: Select Model

- Browse available physics models
- Model is **locked after creation** (cannot be changed)
- Shows model version that will be pinned

## Step 3: Bind Inputs

For each model input, specify a binding:

### Binding Types

| Type | Syntax | Example |
|------|--------|---------|
| Literal | number | `25.5`, `1.5e-4` |
| Analysis reference | `#REF:{id}` or `#NODE:{id}` | `#REF:42` |
| System constant | `$CONST.PI` or `#CONST.g` | `$g` |
| Component property | `#CODE.property` | `#FRAME.length`, `#MOTOR.rpm` |
| Free expression | math | `#MOTOR.torque * 0.95` |

### Validation

- All required model inputs must have bindings
- Circular dependency detection on #REF chains

## Step 4: Review Configuration

- Summary of all bindings
- Model version confirmation
- Click "Create Analysis" to save

## After Creation

Analysis appears in list with:
- Initial computed outputs
- VALID status (if successful)
- ERROR status with message (if failed)

## Gotchas

- Model cannot be changed after creation (version pinned)
- Analysis doesn't auto-recalculate unless explicitly triggered
