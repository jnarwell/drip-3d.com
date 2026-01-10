---
title: "Manual Entry"
description: "After-the-fact time logging"
---

# Manual Entry

Log time for work already completed.

## Form Fields

- **Date selector**: Defaults to today
- **Start time**: HH:MM format
- **End time**: HH:MM format
- **Breaks**: Must be within entry range
- **Duration preview**: Calculated in real-time

## Duration Calculation

```
Net duration = (End - Start) - Total breaks
```

## Overnight Entries

If end time < start time, assumes next day.

## After Submit

Categorization modal opens (same as stopping timer).

## Gotchas

- Break validation: must fall within entry start/stop times
- Overnight entries: if end < start, assumes next day
- Net duration = gross duration minus breaks
