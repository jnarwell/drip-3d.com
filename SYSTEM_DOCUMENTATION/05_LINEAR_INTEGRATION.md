# Linear Integration Documentation

## Executive Summary

The DRIP system integrates with Linear (project management tool) for two primary purposes: displaying project progress on the public website and synchronizing test results/component tracking between the team portal and Linear issues. This provides real-time visibility into project status and maintains a single source of truth for project management.

## Integration Architecture

### Two-Way Integration

1. **Website Progress Display** (Read-only)
   - Fetches initiatives and projects from Linear
   - Transforms data for public consumption
   - Caches results for performance

2. **Team Portal Sync** (Read/Write)
   - Creates Linear issues for test results
   - Updates issue status based on test outcomes
   - Syncs comments and updates bidirectionally

## Linear API Configuration

### Environment Variables
```bash
LINEAR_API_KEY=lin_api_xxxxxxxxxxxxxxxxxxxx
LINEAR_TEAM_ID=team_id_here
LINEAR_PROJECT_ID=project_id_here
```

### GraphQL Client Setup
```python
# Using GQL library for GraphQL operations
transport = AIOHTTPTransport(
    url="https://api.linear.app/graphql",
    headers={"Authorization": LINEAR_API_KEY}
)
client = Client(transport=transport, fetch_schema_from_transport=True)
```

## Website Progress Integration

### Overview

The `/api/v1/linear/progress` endpoint provides transformed Linear data for the public progress page.

### Data Flow

```
Linear Initiatives → API Transform → Website Format → Cache → Frontend
```

### GraphQL Query

```graphql
query {
  initiatives {
    nodes {
      id
      name
      description
      targetDate
      projects(first: 10) {
        nodes {
          id
          name
          description
          progress      # 0-1 scale
          targetDate
          health       # "onTrack", "atRisk", "offTrack"
          lead {
            name
          }
        }
      }
    }
  }
}
```

### Data Transformation

Linear initiatives are transformed to website phases:

```python
def transform_linear_data_to_website_format(initiatives_data):
    # Extract phase number from initiative title
    # e.g., "Phase 1: Design & Planning" → phase: 1
    
    # Calculate average progress across projects
    total_progress = sum(project.progress for project in projects)
    average_progress = round(total_progress / len(projects))
    
    # Format dates for display
    # ISO format → "Jan 15, 2025"
    
    return {
        "phase": phase_number,
        "title": initiative.name,
        "progress": average_progress,
        "projects": transformed_projects
    }
```

### Caching Strategy

```python
_cache = {
    "data": None,
    "last_updated": None,
    "cache_duration": 300  # 5 minutes
}

# Cache is refreshed when:
# - Data is older than 5 minutes
# - force_refresh parameter is true
# - Manual refresh endpoint is called
```

### API Endpoints

#### Get Progress Data
```
GET /api/v1/linear/progress?force_refresh=false

Response:
{
  "lastUpdated": "2025-12-02T10:00:00Z",
  "phases": [
    {
      "phase": 1,
      "title": "Design & Planning",
      "progress": 75,
      "targetDate": "Dec 15, 2025",
      "projects": [...]
    }
  ]
}
```

#### Get Upcoming Milestones
```
GET /api/v1/linear/milestones

Response:
{
  "milestones": [
    {
      "id": "project_123",
      "name": "Acoustic System Completion",
      "date": "Dec 22, 2025",  # Target + 7 days
      "progress": 0.8,
      "lead": { "name": "Jamie Marwell" }
    }
  ]
}
```

#### Force Refresh
```
POST /api/v1/linear/refresh

Response:
{
  "message": "Data refreshed successfully",
  "lastUpdated": "2025-12-02T10:05:00Z",
  "phases_count": 5
}
```

## Team Portal Integration

### Test Result Synchronization

#### Creating Test Issues

When a test is completed in the DRIP portal:

```python
async def create_test_issue(test_data):
    mutation = gql("""
        mutation CreateIssue($input: IssueCreateInput!) {
            issueCreate(input: $input) {
                success
                issue { id, identifier, title, url }
            }
        }
    """)
    
    # Priority mapping
    # FAIL → Urgent (1)
    # PARTIAL → High (2)
    # PASS → Normal (3)
    
    variables = {
        "input": {
            "title": f"Test {test_data['test_id']}: {test_data['name']}",
            "description": format_test_description(test_data),
            "teamId": LINEAR_TEAM_ID,
            "projectId": LINEAR_PROJECT_ID,
            "priority": priority_map[test_data['result']],
            "labelIds": get_test_labels(test_data)
        }
    }
```

#### Test Issue Description Format

```markdown
## Test Information
- **Test ID**: ST-001
- **Category**: Steering Force
- **Result**: PASS
- **Engineer**: Jamie Marwell
- **Date**: 2025-12-02

## Test Results
- **Steering Force**: 125.3 μN
- **DRIP Number**: 0.456

## Notes
Test performed under standard conditions...
```

### Component Tracking

Components can be linked to Linear issues for tracking:

```python
async def create_component_issue(component_data):
    return await linear.issueCreate(
        title=f"Component: {component_data['name']}",
        description=format_component_description(component_data),
        labels=["DRIP-COMPONENT", component_data['category']]
    )
```

### Bidirectional Sync

#### DRIP → Linear
- Test results create/update issues
- Status changes reflected in Linear
- Comments added to issues

#### Linear → DRIP
- Issue state changes update test status
- Comments sync back to portal
- Custom fields map to test data

### Webhook Integration

Linear webhooks notify DRIP of changes:

```python
@router.post("/api/v1/webhooks/linear")
async def handle_linear_webhook(payload: dict):
    event_type = payload.get("type")
    
    if event_type == "Issue":
        action = payload.get("action")
        if action in ["create", "update"]:
            await sync_issue_to_drip(payload["data"])
```

## Data Models

### Linear Issue Mapping

```python
# DRIP Test → Linear Issue
{
    "test_id": "ST-001",          → Issue Title
    "result": "PASS",             → Priority & Labels
    "drip_number": 0.456,         → Custom Field
    "notes": "...",               → Description
    "engineer": "Jamie"           → Assignee
}

# Linear Issue → DRIP Update
{
    "state": "Done",              → test.status = "COMPLETED"
    "comments": [...],            → test.comments
    "customFields": {
        "drip_number": 0.456      → test.drip_number
    }
}
```

### Label System

Standard labels for categorization:
- `DRIP-TEST` - All test-related issues
- `STEERING-RESULTS` - Steering force tests
- `BONDING-RESULTS` - Bonding strength tests
- `THERMAL-TEST` - Thermal control tests
- `DRIP-COMPONENT` - Component tracking

## Frontend Integration

### Progress Page

The public progress page fetches Linear data:

```typescript
// Fetch progress data
const response = await fetch('/api/v1/linear/progress');
const data = await response.json();

// Display phases with projects
data.phases.forEach(phase => {
    renderPhase(phase);
    phase.projects.forEach(project => {
        renderProject(project);
    });
});
```

### Auto-refresh

Progress data refreshes every 5 minutes:

```typescript
useEffect(() => {
    const interval = setInterval(() => {
        fetchProgressData();
    }, 5 * 60 * 1000); // 5 minutes
    
    return () => clearInterval(interval);
}, []);
```

## Performance Optimization

### Caching

- 5-minute cache for progress data
- Stale-while-revalidate pattern
- Force refresh option available

### Query Optimization

- Limit project fetching (first: 10)
- Select only required fields
- Batch operations where possible

### Error Handling

```python
try:
    data = await refresh_cache()
except Exception as e:
    # Return cached data if available
    if _cache["data"]:
        return _cache["data"]
    # Otherwise propagate error
    raise HTTPException(500, f"Linear sync failed: {e}")
```

## Security Considerations

### API Key Management

- Store in environment variables
- Never expose in frontend code
- Rotate keys periodically

### Data Filtering

- Filter sensitive project data
- Only expose public-safe information
- Validate webhook signatures

## Troubleshooting

### Common Issues

1. **API Key Invalid**
   ```
   Error: "Linear API key not configured"
   Solution: Check LINEAR_API_KEY environment variable
   ```

2. **Cache Not Updating**
   ```
   Check: /api/v1/linear/health
   Solution: Force refresh with POST /api/v1/linear/refresh
   ```

3. **Webhook Not Firing**
   ```
   Verify: Webhook URL in Linear settings
   Check: Webhook signature validation
   ```

### Debug Endpoints

```bash
# Check Linear connectivity
GET /api/v1/linear/health

# View cache status
{
  "status": "healthy",
  "linear_api": "connected",
  "cache_status": "valid",
  "last_cache_update": "2025-12-02T10:00:00Z"
}
```

## Enhanced Linear API (Team Members & Projects)

### Overview

The enhanced Linear API (`/api/v1/linear-enhanced/`) provides additional endpoints for fetching team member data and project assignments. This is used for displaying team-specific information on both the company Team page and the team portal.

### Available Endpoints

#### Get Team Members with Projects
```
GET /api/v1/linear-enhanced/team-members?force_refresh=false

Response:
{
  "lastUpdated": "2025-12-14T10:00:00Z",
  "members": [
    {
      "id": "lead",
      "linearId": "user_abc123",
      "name": "Jamie Marwell",
      "email": "jamie@drip-3d.com",
      "avatarUrl": "https://...",
      "isAdmin": true,
      "activeProjects": ["Acoustic System", "Documentation"],
      "leadProjects": [...],
      "memberProjects": [...]
    }
  ]
}
```

#### Get Member's Project Details
```
GET /api/v1/linear-enhanced/member/{member_id}/projects

Response:
{
  "memberId": "lead",
  "leadProjects": [
    {
      "projectName": "Acoustic System Design",
      "projectId": "proj_123",
      "phase": 1,
      "progress": 0.75,
      "health": "onTrack"
    }
  ],
  "memberProjects": [...],
  "lastUpdated": "2025-12-14T10:00:00Z"
}
```

#### Force Refresh All Caches
```
POST /api/v1/linear-enhanced/refresh-all

Response:
{
  "message": "All caches refreshed successfully",
  "results": {
    "initiatives": { "refreshed": true, ... },
    "team_members": { "refreshed": true, ... },
    "projects_by_member": { "refreshed": true, ... }
  }
}
```

### Frontend Hooks

```typescript
// Available in frontend/src/hooks/useLinearData.tsx

// Fetch progress phases (used by ProgressPage)
const { phases, loading, error, refetch } = useLinearProgress();

// Fetch team members with projects (for TeamPage - planned)
const { members, loading, error, refetch } = useLinearTeam();

// Fetch specific member's projects
const { leadProjects, memberProjects, loading } = useLinearMemberProjects(memberId);
```

### Team Member ID Mapping

The system maps Linear users to internal team member IDs:

| Linear Name | Team ID | Role |
|-------------|---------|------|
| Jamie Marwell | `lead` | Lead Engineer |
| Emma Blemaster | `chemical` | Chemical |
| Addison Prarie | `software` | Software/Simulation |
| Ryota Sato | `acoustics` | Acoustics |
| Weston Keller | `electrical` | Power Systems |
| Pierce Thompson | `mechanical` | Mechanical |

### Planned Integration

The enhanced API hooks exist but are not yet connected to the Team pages. Future work:
1. Connect `useLinearTeam()` to TeamPage component cards
2. Show project assignments per team member
3. Display lead/member roles with progress indicators

---

## Best Practices

### Issue Creation

1. **Descriptive Titles**: Include test ID and name
2. **Structured Descriptions**: Use markdown formatting
3. **Appropriate Labels**: Categorize for filtering
4. **Priority Mapping**: Reflect test urgency

### Data Synchronization

1. **Batch Updates**: Group multiple changes
2. **Conflict Resolution**: Last-write-wins
3. **Error Recovery**: Queue failed syncs
4. **Audit Trail**: Log all operations

### Progress Display

1. **Cache Appropriately**: Balance freshness vs performance
2. **Handle Failures**: Show stale data with warning
3. **Progressive Enhancement**: Basic info first
4. **Responsive Updates**: Real-time where needed

## Future Enhancements

### Planned Features

1. **Advanced Sync**
   - Real-time updates via websockets
   - Conflict resolution UI
   - Bulk operations

2. **Enhanced Mapping**
   - Custom field configuration
   - Workflow automation
   - Template issues

3. **Analytics**
   - Test completion rates
   - Issue cycle times
   - Progress trends

4. **Integration Expansion**
   - Slack notifications
   - Email digests
   - Calendar sync

---

*Last Updated: December 14, 2025*
*System Version: 1.1.0*
*Priority: MEDIUM - Project visibility and coordination system*