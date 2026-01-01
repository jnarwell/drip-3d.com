# Time Tracking System

## Overview

The Time Tracking system enables team members to log work sessions with categorization and symmetric visibility. The system integrates with Linear for issue tracking and links to the Resources knowledge base.

### Core Principles

1. **Symmetric Visibility**: All team members can see each other's time entries, enabling coordination and awareness
2. **Categorization Required**: Stopped entries must be categorized (Linear issue, resource, description, or N/A)
3. **Linear Integration**: Direct linking to Linear issues for project tracking alignment
4. **Resource Linking**: Time can be logged against knowledge base resources (docs, papers, etc.)

---

## Entry Modes

### Timer Mode

Click Start to begin tracking. Timer runs continuously until stopped.

**Features:**
- **Break button**: Start/end breaks while timer runs (timer keeps running, break noted)
- Multiple breaks supported per entry
- Visual indicator when on break

### Manual Entry Mode

Enter time ranges directly for past work.

**Fields:**
- Date
- Start time
- End time
- Breaks (optional, multiple allowed)
- Categorization (Linear issue, resource, or description)

---

## Breaks

Breaks are tracked separately from the main entry:
- Timer continues running during breaks (all breaks paid)
- Each break has start time, end time, and optional note
- Total break time shown on entry
- Multiple breaks per entry supported

**Break data:**

| Field | Description |
|-------|-------------|
| `started_at` | When break started |
| `stopped_at` | When break ended |
| `note` | Optional description (e.g., "lunch", "coffee") |

---

## Edit History

All edits are tracked for transparency:
- Edit reason required (dropdown with common reasons + custom option)
- Full history preserved: who changed what, when, and why
- Edited entries marked with `[edited]` indicator
- Click to expand and see full edit history

**Preset edit reasons:**
- Forgot to stop timer
- Started earlier than recorded
- Ended earlier than recorded
- Wrong categorization
- Adding break time
- Other (custom text)

---

## Clickable Links

Entry list displays clickable links:
- **Linear issues**: Opens Linear in new tab
- **Resource URLs**: Opens document/folder in new tab

---

## Core Concepts

### Time Entries

A `TimeEntry` represents a single work session:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `user_id` | string | User email (e.g., "jamie@drip-3d.com") |
| `started_at` | datetime | When work began (UTC) |
| `stopped_at` | datetime | When work ended (NULL if running) |
| `duration_seconds` | int | Computed duration (NULL if running) |
| `linear_issue_id` | string | Linear issue ID (e.g., "DRP-156") |
| `linear_issue_title` | string | Cached issue title for display |
| `resource_id` | int | FK to Resource |
| `description` | text | Free-text description |
| `is_uncategorized` | bool | N/A flag for uncategorizable work |
| `component_id` | int | Optional context component |
| `edit_history` | JSON | Array of edit records (see Edit History) |

**Entry States:**
- **Running**: `stopped_at` is NULL, timer actively counting
- **Completed**: `stopped_at` and `duration_seconds` populated

### Resources

A `Resource` represents knowledge base items:

| Field | Type | Description |
|-------|------|-------------|
| `id` | int | Primary key |
| `title` | string | Resource title |
| `resource_type` | string | doc, folder, image, link, paper, video, spreadsheet |
| `url` | string | Link to resource |
| `added_by` | string | User who added it |
| `added_at` | datetime | When added |
| `tags` | JSON | Array of tags (e.g., ["thermal", "phase-1"]) |
| `notes` | text | Additional notes |

**Resource Associations:**
- `resource_components`: Many-to-many with Components
- `resource_physics_models`: Many-to-many with PhysicsModels
- `time_entries`: One-to-many with TimeEntries

---

## User Flows

### Starting Work

1. User clicks "Start Timer" in the dashboard
2. Optionally selects a component context
3. Optionally pre-links to a Linear issue
4. Timer begins counting

```
POST /api/v1/time/start
{
  "component_id": 5,           // Optional
  "linear_issue_id": "DRP-156" // Optional
}
```

### Stopping Work

1. User clicks "Stop Timer"
2. Modal prompts for categorization:
   - **Linear Issue**: Search/select from assigned issues
   - **Resource**: Select from knowledge base
   - **Description**: Free-text entry
   - **N/A**: Mark as uncategorizable
3. Entry saved with duration computed

```
POST /api/v1/time/stop
{
  "linear_issue_id": "DRP-156",
  "linear_issue_title": "Fix thermal calculation bug"
}
```

### Team Visibility

All team members see:
- Who is currently working (active timers)
- Recent time entries across the team
- Time summaries by user, issue, or component

This symmetric visibility enables:
- Awareness of who's working on what
- Coordination on shared tasks
- Workload visibility

---

## API Reference

See [API_REFERENCE.md#time-tracking](API_REFERENCE.md#time-tracking) for full endpoint documentation.

**Key Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/time/start` | Start a new timer |
| POST | `/api/v1/time/stop` | Stop active timer with categorization |
| GET | `/api/v1/time/active` | Get current user's running timer |
| GET | `/api/v1/time/entries` | List time entries (filterable) |
| GET | `/api/v1/time/summary` | Aggregated time summaries |
| PATCH | `/api/v1/time/entries/{id}` | Edit entry (requires edit_reason) |
| POST | `/api/v1/time/entries/{id}/breaks` | Start a break |
| POST | `/api/v1/time/entries/{id}/breaks/{break_id}/stop` | Stop a break |

**Resource Endpoints:**
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/resources` | List resources (filterable) |
| POST | `/api/v1/resources` | Create resource with associations |
| GET | `/api/v1/resources/{id}` | Get single resource |
| PUT | `/api/v1/resources/{id}` | Update resource |
| DELETE | `/api/v1/resources/{id}` | Delete resource |

---

## Database Schema

### TimeBreak Table

```sql
CREATE TABLE time_breaks (
    id SERIAL PRIMARY KEY,
    time_entry_id INTEGER NOT NULL REFERENCES time_entries(id) ON DELETE CASCADE,
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMP WITH TIME ZONE,
    note VARCHAR(200)
);

CREATE INDEX ix_time_breaks_entry_id ON time_breaks(time_entry_id);
```

### TimeEntry Table

```sql
CREATE TABLE time_entries (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(200) NOT NULL,

    -- Timing
    started_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    stopped_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INTEGER,

    -- Categorization (at least one, or is_uncategorized)
    linear_issue_id VARCHAR(50),
    linear_issue_title VARCHAR(500),
    resource_id INTEGER REFERENCES resources(id),
    description TEXT,
    is_uncategorized BOOLEAN DEFAULT FALSE,

    -- Context
    component_id INTEGER REFERENCES components(id),

    -- Edit tracking
    edit_history JSONB DEFAULT '[]',

    -- Meta
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX ix_time_entries_user_id ON time_entries(user_id);
CREATE INDEX ix_time_entries_linear_issue_id ON time_entries(linear_issue_id);
CREATE INDEX ix_time_entries_component_id ON time_entries(component_id);
CREATE INDEX ix_time_entries_user_started ON time_entries(user_id, started_at);
CREATE INDEX ix_time_entries_active ON time_entries(user_id, stopped_at);
```

**Edit History Record Structure:**

```json
{
  "field": "stopped_at",
  "old_value": "2025-12-31T18:00:00Z",
  "new_value": "2025-12-31T17:30:00Z",
  "reason": "Forgot to stop timer",
  "edited_at": "2025-12-31T17:35:00Z",
  "edited_by": "jamie@drip-3d.com"
}
```

### Resource Table

```sql
CREATE TABLE resources (
    id SERIAL PRIMARY KEY,
    title VARCHAR(300) NOT NULL,
    resource_type VARCHAR(50) NOT NULL,
    url VARCHAR(2000),
    added_by VARCHAR(200) NOT NULL,
    added_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tags JSONB,
    notes TEXT
);

-- Association tables
CREATE TABLE resource_components (
    resource_id INTEGER REFERENCES resources(id) PRIMARY KEY,
    component_id INTEGER REFERENCES components(id) PRIMARY KEY
);

CREATE TABLE resource_physics_models (
    resource_id INTEGER REFERENCES resources(id) PRIMARY KEY,
    physics_model_id INTEGER REFERENCES physics_models(id) PRIMARY KEY
);
```

---

## Integration Points

### Linear Integration

Time entries can link directly to Linear issues:
- `linear_issue_id`: The Linear issue identifier (e.g., "DRP-156")
- `linear_issue_title`: Cached for display without API calls
- Used for time tracking against project tasks

### Component Context

Optional `component_id` provides context:
- Which component was being worked on
- Enables time filtering by component
- Links time to the Component Registry

### Physics Models

Resources can be linked to PhysicsModels:
- Documentation for model design decisions
- Reference papers for equations
- Validation test results

### Dashboard Integration

The Dashboard displays:
- Current user's active timer (if any)
- Team activity feed with recent entries
- Quick-start timer button

---

## Categorization Requirements

When stopping a timer, at least one must be provided:

| Option | Field | Use Case |
|--------|-------|----------|
| Linear Issue | `linear_issue_id` | Work tracked against project tasks |
| Resource | `resource_id` | Work on documentation, research |
| Description | `description` | Ad-hoc work not fitting other categories |
| N/A | `is_uncategorized: true` | Meetings, admin, breaks |

**Validation:** The API returns 400 if no categorization is provided.

---

## Future Enhancements

- [ ] Real-time timer sync via WebSocket
- [x] Time entry editing (adjust start/stop times) - v2
- [x] Break tracking - v2
- [x] Edit history with reasons - v2
- [ ] Recurring time entries (templates)
- [ ] Time budgets and alerts
- [ ] Export to timesheet formats
- [ ] Linear webhook for auto-categorization

---

*Last Updated: December 31, 2025*
