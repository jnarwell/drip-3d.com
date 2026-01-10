---
title: "Getting Started"
description: "Quick start guide for Drip Team Portal"
---

# Getting Started

## Authentication

- Auth0 authentication with @drip-3d.com domain restriction
- Dev mode on localhost bypasses auth

## Dashboard Overview

After login, you land on the Dashboard which displays:

- **System Validation Progress**: Components verified count, tests complete count, physics validation status
- **Test Protocol Status**: Active protocols, runs in progress, passed/failed counts
- **Test Campaign Progress**: 30-day line chart (completed vs planned tests)
- **Component Status**: Pie/donut chart by status
- **Critical Path**: Scrollable list of tests blocking progress
- **Risk Assessment**: Scrollable list with severity badges (high/medium/low)
- **Recent Activity**: Audit log (user, action, timestamp, type)
- **Active Timers Bar**: Team members currently tracking time (conditionally rendered)

**Auto-refresh**: 30 seconds for stats, on-focus only for activity feed

## Navigation

Header tabs in order:
- Dashboard
- Components
- Models
- Analysis
- Time
- Testing
- Reports
- Resources

User dropdown (top right): email with chevron → Settings, Main Page, Logout

## Global UI Elements

### Feedback Button
- Position: Fixed top-right corner, z-40
- Appearance: 40x40px purple circle with white "?"
- Opens feedback modal on click

### Error Handling
TeamPortalErrorBoundary catches React errors and shows:
- Expandable error details
- "Refresh Page" button
- "Go to Dashboard" button

## Dashboard Gotchas

- Physics Validation shows "Complete" if ANY single result has physics_validated=true, not all
- Test Protocol card doesn't render if no protocols exist
- Recent Activity doesn't auto-refresh like other stats
