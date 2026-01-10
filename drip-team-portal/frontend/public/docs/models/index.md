---
title: "Physics Models"
description: "Overview of the physics modeling system"
---

# Physics Models

**Routes:** `/models`, `/models/new`, `/models/:modelId/edit`

Reusable calculation templates defining inputs, outputs, and equations.

## List View

Table with columns:
- Name/Description
- Category (color badge)
- Variables (X inputs, Y outputs)
- Version
- Actions

### Category Filtering

Filter by physics domain.

### Delete Protection

Cannot delete models with analysis instances attached.

## Categories

| Category | Badge Color |
|----------|-------------|
| thermal | orange |
| mechanical | blue |
| acoustic | purple |
| electrical | yellow |
| fluid | cyan |
| structural | green |
| electromagnetic | pink |
| optical | indigo |
| multiphysics | gray |
| other | gray |

## Model Builder

4-step wizard:
1. Define Model (name, category, description)
2. Inputs & Outputs (variables with units)
3. Equations (per-output expressions)
4. Validate & Create (review and save)

## Related Topics

- [Creating Models](creating.md) - Step-by-step wizard
- [Equations](equations.md) - Syntax and functions
- [Versioning](versioning.md) - Version management
