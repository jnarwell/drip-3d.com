---
title: "Time Tracking"
description: "Overview of the time tracking system"
---

# Time Tracking

**Route:** `/time`

## Timer

- Start/Stop/Pause buttons
- Real-time elapsed display
- Break tracking with optional notes

## Manual Entry

- Date selector (defaults to today)
- Start/End time inputs (HH:MM)
- Break entries (must be within entry range)
- Duration preview

## Categorization

Required on stop:
- Linear issue search (auto-fetches active issues)
- Resource/Document linking (Title, Type, optional URL)
- Description text
- Or mark as N/A

## Entry List

- Grouped by date (descending)
- Shows: time range, duration, breaks, categorization
- Edit/Delete buttons

## Team View

- Active Timers sidebar (green dot = running, yellow = break)
- Team stats row (total hours, entries, avg/person, % of target)
- Project breakdown bar chart
- Issue breakdown bar chart

## Gotchas

- **Starting new timer auto-stops previous timer** (marks it uncategorized)
- Break validation: must fall within entry start/stop times
- Edit reason required to save edits
- Overnight entries: if end < start, assumes next day
- Net duration = gross duration minus breaks

## Related Topics

- [Timer](timer.md) - Real-time tracking
- [Manual Entry](manual.md) - After-the-fact logging
- [Categorization](categorization.md) - Linking entries
- [Team View](team-view.md) - Team-wide data
