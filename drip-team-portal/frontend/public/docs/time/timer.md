---
title: "Timer"
description: "Real-time time tracking"
---

# Timer

Real-time tracking with Start/Stop/Pause controls.

## Features

- Start/Stop/Pause buttons
- Real-time elapsed display
- Break tracking with optional notes

## Active Timer Bar

When a timer is running:
- Green dot = timer running
- Yellow dot = on break

Visible in main navigation.

## Break Tracking

Add breaks while timer is running:
- Breaks must fall within entry start/stop times
- Break time deducted from total

## Stopping

On stop, categorization modal opens:
- Link to Linear issue, Resource, or Component
- Add description
- Or mark as N/A

## Gotchas

- **Starting new timer auto-stops previous timer** (marks it uncategorized)
- Break validation: must fall within entry start/stop times
- Net duration = gross duration minus breaks
