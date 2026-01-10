---
title: "Analysis"
description: "Overview of the analysis system"
---

# Analysis

**Routes:** `/analysis`, `/analysis/new`, `/analysis/:analysisId/edit`

Named instances of physics models with bound inputs and computed outputs.

## List View

Table with expandable rows showing:
- Analysis name
- Model name and category
- Primary output value
- Status badge
- Actions (Refresh, Edit, Delete)

### Features

- Real-time WebSocket status indicator
- Inline editing of input bindings (double-click to edit)
- Status filtering (VALID, STALE, ERROR, PENDING)
- Manual re-evaluate button per analysis
- Delete confirmation modal

### Status Badges

| Status | Color | Meaning |
|--------|-------|---------|
| VALID | Green | All inputs resolved, outputs computed |
| STALE | Yellow | Dependency changed, needs re-evaluation |
| ERROR | Red | Computation failed |
| PENDING | Gray | Computation in progress |

## Analysis Creator

4-step wizard:
1. Name and description
2. Select model (locked in edit mode)
3. Bind inputs with expressions
4. Review configuration

## Input Binding Types

| Type | Syntax | Example |
|------|--------|---------|
| Literal | number | `25.5`, `1.5e-4` |
| Analysis reference | `#REF:{id}` or `#NODE:{id}` | `#REF:42` |
| System constant | `$CONST.PI`, `#CONST.g` | `$g` |
| Component property | `#CODE.property` | `#FRAME.length` |
| Free expression | math | `#MOTOR.rpm * 0.95` |

## Gotchas

- Model cannot be changed after creation (version pinned)
- Circular dependency detection on #REF chains
- All required model inputs must have bindings
- Analysis doesn't auto-recalculate unless explicitly triggered
- ValueNodes persist and update in-place to preserve FK references

## Related Topics

- [Creating Analyses](creating.md) - Wizard walkthrough
- [Bindings](bindings.md) - Input binding syntax
- [Chaining](chaining.md) - Linking analyses together
