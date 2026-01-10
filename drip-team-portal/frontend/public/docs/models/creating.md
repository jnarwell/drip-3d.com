---
title: "Creating Models"
description: "Step-by-step model creation wizard"
---

# Creating Models

**Route:** `/models/new`

4-step wizard for creating physics models.

## Step 1: Define Model

| Field | Required | Description |
|-------|----------|-------------|
| Model Name | Yes | Model identifier |
| Category | Yes | Physics domain dropdown |
| Description | No | Textarea for details |

## Step 2: Inputs & Outputs

### Inputs

Dynamic list with per-input fields:
- Name
- Unit (autocomplete with 30+ units)
- Description

### Outputs

Dynamic list with per-output fields:
- Name
- Unit
- Description

**Validation:** At least 1 input and 1 output required.

## Step 3: Equations

For each output:
```
{output_name} = [textarea]
```

### Editor Features

- Quick-insert buttons for variable names
- Operator buttons: `+ - * / ^ ( )`
- Warning if equation empty

## Step 4: Validate & Create

- Summary review of all model details
- API validation call
- Dimensional analysis display (computed vs expected)
- LaTeX preview of equations

Click "Create Model" to save.

## Gotchas

- Edit creates new version if structure changes, metadata-only edits don't bump version
- Validation is optional - if API fails, user can still save
- LaTeX rendering converts symbols (alpha → α, delta_T → ΔT)
