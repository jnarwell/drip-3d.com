---
title: "Component Registry"
description: "Managing the component list"
---

# Component Registry

**Route:** `/components`

## Display

Responsive card grid (1-3 columns based on viewport).

## Card Fields

Each card shows:
- Name
- ID (auto-generated: CMP-001, CMP-002, etc.)
- Category
- Part Number
- Supplier
- Cost
- Status badge
- R&D Phase badge

## Filtering

- **Category dropdown**: Filter by category
- **Status dropdown**: Filter by status (NOT_TESTED, IN_TESTING, VERIFIED, FAILED)
- **Text search**: Search across name, ID, description, part number

## Actions

| Action | Description |
|--------|-------------|
| Add Component | Modal form with validation |
| Export to CSV | Downloads `components_YYYY-MM-DD.csv` |
| Edit | Per-card button, opens edit modal |
| Delete | Per-card button, requires confirmation |
| Quick Status Toggle | Click status badge to toggle |

## CSV Export Fields

- Component ID
- Name
- Category
- Status
- Part Number
- Supplier
- Unit Cost

## Gotchas

- **Status toggle only cycles NOT_TESTED and VERIFIED**, not all 4 states
- Delete uses confirm() dialog, no undo
- Filters don't persist in URL
