---
title: "Versioning"
description: "Model version management"
---

# Versioning

Models are versioned to maintain calculation integrity.

## Version Behavior

- v1: Initial creation
- v2, v3, etc.: Subsequent edits

### When Version Increments

- Edit creates new version **if structure changes**
- Metadata-only edits don't bump version

## Analysis Binding

When creating an analysis:
1. Model version ID is recorded
2. Analysis is bound to that specific version
3. Future model edits don't affect existing analyses

```
Model: Thermal Resistance (v3)
├── Analysis: "Main Heatsink" → bound to v3
├── Analysis: "Secondary Heatsink" → bound to v3
└── [Model edited to v4]
    └── Analysis: "New Design" → bound to v4
```

## Delete Protection

Models with analysis instances attached cannot be deleted.

To delete:
1. Delete all referencing analyses first
2. Then delete the model

## Gotchas

- Model cannot be changed after analysis creation (version pinned)
- ValueNodes persist and update in-place to preserve FK references
