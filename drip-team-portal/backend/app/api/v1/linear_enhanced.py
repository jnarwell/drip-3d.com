"""
Enhanced Linear API integration for company pages.
Provides endpoints for fetching initiatives, projects, and team member data.
"""

import os
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import httpx

from app.db.database import get_db

import os as _os
if _os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/linear-enhanced", tags=["linear-enhanced"])

# Linear API configuration
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_API_URL = "https://api.linear.app/graphql"

# Enhanced cache for different data types
_enhanced_cache = {
    "initiatives": {"data": None, "last_updated": None},
    "team_members": {"data": None, "last_updated": None},
    "projects_by_member": {"data": None, "last_updated": None},
    "cache_duration": 300  # 5 minutes
}

class EnhancedLinearClient:
    """Enhanced client for Linear GraphQL API with team member support"""
    
    def __init__(self):
        self.api_key = LINEAR_API_KEY
        self.api_url = LINEAR_API_URL
    
    async def make_graphql_request(self, query: str, variables: Dict = None) -> Dict:
        """Make a GraphQL request to Linear API"""
        if not self.api_key:
            raise HTTPException(status_code=500, detail="Linear API key not configured")
        
        if variables is None:
            variables = {}
        
        payload = {
            "query": query,
            "variables": variables
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": self.api_key
        }
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    self.api_url,
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json()
                
                if "errors" in data:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Linear API Error: {data['errors']}"
                    )
                
                return data.get("data", {})
                
            except httpx.TimeoutException:
                raise HTTPException(status_code=504, detail="Linear API timeout")
            except httpx.RequestError as e:
                raise HTTPException(status_code=503, detail=f"Linear API request failed: {str(e)}")
    
    async def fetch_team_members(self) -> Dict:
        """Fetch all team members and their project assignments"""
        query = """
            query {
                users {
                    nodes {
                        id
                        name
                        email
                        displayName
                        avatarUrl
                        isActive
                        admin
                        assignedIssues(first: 50, filter: { 
                            state: { type: { nin: ["completed", "canceled"] } }
                        }) {
                            nodes {
                                id
                                title
                                project {
                                    id
                                    name
                                    state
                                }
                            }
                        }
                        teamMemberships {
                            nodes {
                                team {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """
        return await self.make_graphql_request(query)
    
    async def fetch_initiatives_with_leads(self) -> Dict:
        """Fetch initiatives with project leads and member assignments"""
        query = """
            query {
                initiatives {
                    nodes {
                        id
                        name
                        description
                        targetDate
                        projects(first: 20) {
                            nodes {
                                id
                                name
                                description
                                progress
                                targetDate
                                health
                                state
                                lead {
                                    id
                                    name
                                    email
                                    displayName
                                }
                                members {
                                    nodes {
                                        id
                                        name
                                        email
                                    }
                                }
                                issues(first: 100) {
                                    nodes {
                                        assignee {
                                            id
                                            name
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """
        return await self.make_graphql_request(query)

def map_linear_user_to_team_member(linear_user: Dict[str, Any]) -> Optional[str]:
    """Map Linear user to our team member IDs"""
    # Mapping based on names (case insensitive)
    name_to_id_map = {
        "jamie marwell": "lead",
        "emma blemaster": "chemical",
        "addison prarie": "software",
        "addison prairie": "software",  # Alternative spelling
        "ryota sato": "acoustics",
        "weston keller": "electrical",
        "pierce thompson": "mechanical"
    }
    
    user_name = linear_user.get("name", "").lower()
    display_name = linear_user.get("displayName", "").lower()
    
    # Try exact match first
    if user_name in name_to_id_map:
        return name_to_id_map[user_name]
    if display_name in name_to_id_map:
        return name_to_id_map[display_name]
    
    # Try partial match
    for known_name, team_id in name_to_id_map.items():
        if known_name in user_name or known_name in display_name:
            return team_id
        # Check if all parts of known name are in user name
        name_parts = known_name.split()
        if all(part in user_name or part in display_name for part in name_parts):
            return team_id
    
    return None

def transform_team_members_data(users_data: Dict) -> List[Dict[str, Any]]:
    """Transform Linear users to team member format with project assignments"""
    users = users_data.get("users", {}).get("nodes", [])
    
    team_members = []
    for user in users:
        if not user.get("isActive", False):
            continue
        
        team_member_id = map_linear_user_to_team_member(user)
        if not team_member_id:
            continue
        
        # Extract projects the member is working on
        assigned_projects = set()
        for issue in user.get("assignedIssues", {}).get("nodes", []):
            project = issue.get("project")
            if project and project.get("state") != "canceled":
                assigned_projects.add(project["name"])
        
        team_member_data = {
            "id": team_member_id,
            "linearId": user["id"],
            "name": user["name"],
            "email": user.get("email"),
            "avatarUrl": user.get("avatarUrl"),
            "isAdmin": user.get("admin", False),
            "activeProjects": list(assigned_projects),
            "teams": [
                team["team"]["name"] 
                for team in user.get("teamMemberships", {}).get("nodes", [])
            ]
        }
        
        team_members.append(team_member_data)
    
    return team_members

def transform_initiatives_for_progress(initiatives_data: Dict) -> List[Dict[str, Any]]:
    """Transform Linear initiatives data for Progress page display"""
    initiatives = initiatives_data.get("initiatives", {}).get("nodes", [])
    
    def extract_phase_number(title: str) -> int:
        """Extract phase number from title"""
        import re
        match = re.search(r'Phase (\d+)', title)
        return int(match.group(1)) if match else 999
    
    def format_date(date_string: str) -> str:
        """Format date for display"""
        if not date_string:
            return "TBD"
        try:
            date_obj = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
            return date_obj.strftime("%b %d, %Y")
        except:
            return "TBD"
    
    phases = []
    for idx, initiative in enumerate(initiatives):
        phase_number = extract_phase_number(initiative.get("name", ""))
        projects = initiative.get("projects", {}).get("nodes", [])
        
        # Calculate overall progress
        total_progress = sum(project.get("progress", 0) for project in projects)
        average_progress = round(total_progress / len(projects)) if projects else 0
        
        # Transform projects with team member data
        transformed_projects = []
        for project in projects:
            # Get unique assignees from issues
            assignees = set()
            for issue in project.get("issues", {}).get("nodes", []):
                assignee = issue.get("assignee")
                if assignee:
                    member_id = map_linear_user_to_team_member(assignee)
                    if member_id:
                        assignees.add(member_id)
            
            # Get lead info
            lead_data = None
            if project.get("lead"):
                lead_member_id = map_linear_user_to_team_member(project["lead"])
                if lead_member_id:
                    lead_data = {
                        "id": lead_member_id,
                        "name": project["lead"].get("name"),
                        "email": project["lead"].get("email")
                    }
            
            transformed_projects.append({
                "id": project.get("id"),
                "name": project.get("name", ""),
                "description": project.get("description", ""),
                "status": "active" if project.get("state") != "canceled" else "canceled",
                "progress": project.get("progress", 0),
                "targetDate": format_date(project.get("targetDate")),
                "health": project.get("health"),
                "lead": lead_data,
                "teamMembers": list(assignees),
                "memberCount": len(assignees)
            })
        
        phase_data = {
            "phase": phase_number if phase_number != 999 else idx + 1,
            "title": initiative.get("name", ""),
            "description": initiative.get("description"),
            "targetDate": format_date(initiative.get("targetDate")),
            "progress": average_progress,
            "projects": transformed_projects
        }
        
        phases.append(phase_data)
    
    # Sort phases by phase number
    phases.sort(key=lambda x: x["phase"])
    
    return phases

def is_cache_valid(cache_key: str) -> bool:
    """Check if specific cache is still valid"""
    cache_data = _enhanced_cache.get(cache_key, {})
    if not cache_data.get("data") or not cache_data.get("last_updated"):
        return False
    
    cache_age = datetime.now() - cache_data["last_updated"]
    return cache_age.total_seconds() < _enhanced_cache["cache_duration"]

async def refresh_cache(cache_key: str) -> Dict[str, Any]:
    """Refresh specific cache based on key"""
    client = EnhancedLinearClient()
    
    try:
        if cache_key == "initiatives":
            data = await client.fetch_initiatives_with_leads()
            processed_data = {
                "lastUpdated": datetime.now().isoformat(),
                "phases": transform_initiatives_for_progress(data)
            }
        
        elif cache_key == "team_members":
            data = await client.fetch_team_members()
            processed_data = {
                "lastUpdated": datetime.now().isoformat(),
                "members": transform_team_members_data(data)
            }
        
        elif cache_key == "projects_by_member":
            # Get both initiatives and team data
            initiatives_data = await client.fetch_initiatives_with_leads()
            team_data = await client.fetch_team_members()
            
            # Build project assignments by member
            member_projects = {}
            for phase in transform_initiatives_for_progress(initiatives_data):
                for project in phase["projects"]:
                    # Add project to lead's list
                    if project.get("lead"):
                        lead_id = project["lead"]["id"]
                        if lead_id not in member_projects:
                            member_projects[lead_id] = {"lead": [], "member": []}
                        member_projects[lead_id]["lead"].append({
                            "projectName": project["name"],
                            "projectId": project["id"],
                            "phase": phase["phase"],
                            "progress": project["progress"],
                            "health": project["health"]
                        })
                    
                    # Add project to team members' lists
                    for member_id in project.get("teamMembers", []):
                        if member_id not in member_projects:
                            member_projects[member_id] = {"lead": [], "member": []}
                        member_projects[member_id]["member"].append({
                            "projectName": project["name"],
                            "projectId": project["id"],
                            "phase": phase["phase"],
                            "progress": project["progress"],
                            "health": project["health"]
                        })
            
            processed_data = {
                "lastUpdated": datetime.now().isoformat(),
                "memberProjects": member_projects
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Invalid cache key: {cache_key}")
        
        # Update cache
        _enhanced_cache[cache_key]["data"] = processed_data
        _enhanced_cache[cache_key]["last_updated"] = datetime.now()
        
        return processed_data
        
    except Exception as e:
        # If refresh fails and we have cached data, return it
        if _enhanced_cache[cache_key].get("data"):
            return _enhanced_cache[cache_key]["data"]
        raise e

@router.get("/progress-data")
async def get_enhanced_progress_data(force_refresh: bool = False):
    """
    Get comprehensive progress data with team member assignments.
    
    Returns:
    - Phases with projects
    - Team member assignments per project
    - Project health and progress metrics
    """
    try:
        cache_key = "initiatives"
        
        if not force_refresh and is_cache_valid(cache_key):
            return JSONResponse(content=_enhanced_cache[cache_key]["data"])
        
        progress_data = await refresh_cache(cache_key)
        return JSONResponse(content=progress_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress data: {str(e)}")

@router.get("/team-members")
async def get_team_members_with_projects(force_refresh: bool = False):
    """
    Get team members with their Linear data and project assignments.
    
    Returns:
    - Team member Linear profiles
    - Active project assignments
    - Leadership roles
    """
    try:
        # Get team members data
        if not force_refresh and is_cache_valid("team_members"):
            members_data = _enhanced_cache["team_members"]["data"]
        else:
            members_data = await refresh_cache("team_members")
        
        # Get project assignments
        if not force_refresh and is_cache_valid("projects_by_member"):
            projects_data = _enhanced_cache["projects_by_member"]["data"]
        else:
            projects_data = await refresh_cache("projects_by_member")
        
        # Combine data
        members = members_data["members"]
        member_projects = projects_data["memberProjects"]
        
        for member in members:
            member_id = member["id"]
            if member_id in member_projects:
                member["leadProjects"] = member_projects[member_id]["lead"]
                member["memberProjects"] = member_projects[member_id]["member"]
            else:
                member["leadProjects"] = []
                member["memberProjects"] = []
        
        return JSONResponse(content={
            "lastUpdated": members_data["lastUpdated"],
            "members": members
        })
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch team data: {str(e)}")

@router.get("/member/{member_id}/projects")
async def get_member_projects(member_id: str):
    """
    Get detailed project information for a specific team member.
    
    Parameters:
    - member_id: Team member ID (e.g., "lead", "chemical", "software")
    """
    try:
        # Refresh project data if needed
        if not is_cache_valid("projects_by_member"):
            await refresh_cache("projects_by_member")
        
        projects_data = _enhanced_cache["projects_by_member"]["data"]
        member_projects = projects_data["memberProjects"].get(member_id, {
            "lead": [],
            "member": []
        })
        
        return JSONResponse(content={
            "memberId": member_id,
            "leadProjects": member_projects.get("lead", []),
            "memberProjects": member_projects.get("member", []),
            "lastUpdated": projects_data["lastUpdated"]
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch member projects: {str(e)}")

@router.post("/refresh-all")
async def force_refresh_all_data():
    """
    Force refresh all Linear data caches.
    Useful for ensuring all data is synchronized.
    """
    try:
        results = {}
        
        for cache_key in ["initiatives", "team_members", "projects_by_member"]:
            data = await refresh_cache(cache_key)
            results[cache_key] = {
                "refreshed": True,
                "lastUpdated": data.get("lastUpdated"),
                "recordCount": len(data.get(list(data.keys())[1], []))  # Get the main data array
            }
        
        return JSONResponse(content={
            "message": "All caches refreshed successfully",
            "results": results
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh all data: {str(e)}")


@router.get("/issues")
async def get_linear_issues(
    state: str = "active",
    project_id: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 50
):
    """
    Get Linear issues for time tracking dropdown.

    Parameters:
    - state: "active" (default), "completed", "all"
    - project_id: Filter by Linear project ID
    - search: Search in issue title
    - limit: Max issues to return (default 50)

    Returns issues sorted by updated date (most recent first).
    Returns empty array with configured=false when API key not set.
    """
    # Graceful degradation when Linear not configured
    if not LINEAR_API_KEY:
        return {"issues": [], "count": 0, "configured": False}

    try:
        client = EnhancedLinearClient()

        # Build filter based on state
        if state == "active":
            state_filter = '{ type: { nin: ["completed", "canceled"] } }'
        elif state == "completed":
            state_filter = '{ type: { eq: "completed" } }'
        else:
            state_filter = '{}'

        # Build project filter
        project_filter = f', project: {{ id: {{ eq: "{project_id}" }} }}' if project_id else ""

        # Build search filter
        search_filter = f', title: {{ containsIgnoreCase: "{search}" }}' if search else ""

        query = f"""
            query {{
                issues(
                    first: {limit},
                    filter: {{ state: {state_filter}{project_filter}{search_filter} }},
                    orderBy: updatedAt
                ) {{
                    nodes {{
                        id
                        identifier
                        title
                        state {{
                            name
                            type
                        }}
                        project {{
                            id
                            name
                        }}
                        assignee {{
                            name
                            email
                        }}
                        updatedAt
                    }}
                }}
            }}
        """

        data = await client.make_graphql_request(query)
        issues = data.get("issues", {}).get("nodes", [])

        return {
            "issues": [
                {
                    "id": issue["id"],
                    "identifier": issue["identifier"],  # "DRP-156"
                    "title": issue["title"],
                    "state": issue.get("state", {}).get("name"),
                    "state_type": issue.get("state", {}).get("type"),
                    "project_id": issue.get("project", {}).get("id") if issue.get("project") else None,
                    "project_name": issue.get("project", {}).get("name") if issue.get("project") else None,
                    "assignee_name": issue.get("assignee", {}).get("name") if issue.get("assignee") else None,
                    "assignee_email": issue.get("assignee", {}).get("email") if issue.get("assignee") else None,
                    "updated_at": issue.get("updatedAt"),
                }
                for issue in issues
            ],
            "count": len(issues),
            "configured": True
        }

    except Exception as e:
        # Log warning but return empty array instead of 500 error
        import logging
        logging.warning(f"Linear issues fetch failed: {e}")
        return {"issues": [], "count": 0, "configured": True, "error": str(e)}


@router.post("/sync-users")
async def sync_linear_users_to_db(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Sync team members from Linear to our User table.

    Creates new users or updates names for existing users.
    Only syncs users with @drip-3d.com email addresses.
    """
    from app.models.user import User

    # Graceful degradation when Linear not configured
    if not LINEAR_API_KEY:
        return {"synced": [], "total": 0, "configured": False}

    try:
        # Get team members from Linear
        if not is_cache_valid("team_members"):
            await refresh_cache("team_members")

        members_data = _enhanced_cache["team_members"]["data"]
        members = members_data.get("members", [])

        synced = []
        for member in members:
            email = member.get("email")
            if not email or not email.endswith("@drip-3d.com"):
                continue

            name = member.get("name")

            existing = db.query(User).filter(User.email == email).first()
            if existing:
                # Update name if changed
                if existing.name != name and name:
                    existing.name = name
                    synced.append({"email": email, "name": name, "action": "updated"})
            else:
                # Create new user
                new_user = User(
                    email=email,
                    name=name,
                    auth0_id=f"linear:{member.get('linearId', email)}",  # Placeholder until first login
                    is_active=True
                )
                db.add(new_user)
                synced.append({"email": email, "name": name, "action": "created"})

        db.commit()

        return {
            "synced": synced,
            "total": len(synced),
            "configured": True
        }

    except Exception as e:
        import logging
        logging.warning(f"Linear users sync failed: {e}")
        return {"synced": [], "total": 0, "configured": True, "error": str(e)}


@router.get("/health")
async def enhanced_linear_health_check():
    """Check enhanced Linear API connectivity and cache status"""
    try:
        client = EnhancedLinearClient()
        
        # Test API connectivity
        test_query = """
            query {
                viewer {
                    id
                    name
                }
            }
        """
        
        viewer_data = await client.make_graphql_request(test_query)
        
        # Check cache status for each type
        cache_status = {}
        for cache_key in ["initiatives", "team_members", "projects_by_member"]:
            cache_data = _enhanced_cache.get(cache_key, {})
            cache_status[cache_key] = {
                "valid": is_cache_valid(cache_key),
                "last_updated": cache_data.get("last_updated").isoformat() if cache_data.get("last_updated") else None
            }
        
        return JSONResponse(content={
            "status": "healthy",
            "linear_api": "connected",
            "cache_status": cache_status,
            "viewer": viewer_data.get("viewer", {})
        })
        
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "linear_api": "disconnected",
                "error": str(e)
            }
        )