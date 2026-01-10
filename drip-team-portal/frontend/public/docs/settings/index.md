---
title: "Settings"
description: "User preferences and configuration"
---

# Settings

**Route:** `/settings`

User preferences and account settings.

## Profile

### Display Information

- **Name**: Your display name
- **Email**: Login email address
- **Role**: User or Admin

### Profile Picture

Pulled from Auth0 identity provider. To change:
1. Update in your identity provider account
2. Changes sync on next login

## Preferences

### Theme (Planned)

- Light (default)
- Dark
- System preference

### Timezone

- Auto-detect from browser (default)
- Manual selection from dropdown

Affects: time entry timestamps, activity feed, report dates.

### Date Format

- MM/DD/YYYY (US)
- DD/MM/YYYY (International)
- YYYY-MM-DD (ISO)

### Number Format

- Period (1,234.56)
- Comma (1.234,56)

## Integrations

### Linear

If enabled:
- Connection status
- Workspace name
- Sync settings

### Auth0

- Provider name
- Last login time

## Admin Settings

Administrators see additional options:

### User Management

- View all users
- Change user roles
- Deactivate accounts

### System Configuration

- API settings
- Integration configuration
- Feature flags

### Audit Log

View system-wide activity for compliance.

## Saving Changes

Changes save automatically:
- Green confirmation appears
- No "Save" button needed
- Changes apply immediately
