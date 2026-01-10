---
title: "Feedback"
description: "Submitting feedback and reporting issues"
---

# Feedback

## Submitting Feedback

Click the purple "?" button (fixed top-right corner) to open the feedback modal.

## Feedback Types

| Type | Badge Color |
|------|-------------|
| Bug | Red |
| Feature | Blue |
| Question | Indigo |

## Urgency Levels

| Urgency | Badge Color |
|---------|-------------|
| Need Now | Orange |
| Nice to Have | Green |

## Feedback Triage

Located in the Reports page, bottom section.

### Features
- Multi-filter table (status, type, urgency)
- Inline status updates via dropdown
- Row expansion for full details
- Resolution workflow
- CSV export

### Status Workflow

```
new (yellow) → reviewed (blue) → in_progress (purple) → resolved (green)
                                                     ↘ wont_fix (gray)
```

### Gotchas
- Resolution notes required when marking resolved or wont_fix
- `resolved_by` and `resolved_at` auto-populated on resolution
