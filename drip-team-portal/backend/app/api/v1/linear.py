"""
Linear API integration for website progress tracking.
Provides endpoints for fetching Linear initiative and project data.
"""

import os
import asyncio
from typing import Dict, List, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.responses import JSONResponse
import httpx

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/linear", tags=["linear"])

# Linear API configuration
LINEAR_API_KEY = os.getenv("LINEAR_API_KEY")
LINEAR_API_URL = "https://api.linear.app/graphql"

# Cache for Linear data (simple in-memory cache)
_cache = {
    "data": None,
    "last_updated": None,
    "cache_duration": 300  # 5 minutes
}

class LinearClient:
    """Client for interacting with Linear GraphQL API"""
    
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
    
    async def fetch_initiatives(self) -> Dict:
        """Fetch initiatives and their projects from Linear"""
        query = """
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
                                progress
                                targetDate
                                health
                                lead {
                                    name
                                }
                            }
                        }
                    }
                }
            }
        """
        return await self.make_graphql_request(query)

def transform_linear_data_to_website_format(initiatives_data: Dict) -> List[Dict[str, Any]]:
    """Transform Linear data to website progress format"""
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
    
    # Transform each initiative to phase format
    phases = []
    for idx, initiative in enumerate(initiatives):
        phase_number = extract_phase_number(initiative.get("name", ""))
        projects = initiative.get("projects", {}).get("nodes", [])
        
        # Calculate overall progress
        total_progress = sum(project.get("progress", 0) for project in projects)
        average_progress = round(total_progress / len(projects)) if projects else 0
        
        phase_data = {
            "phase": phase_number if phase_number != 999 else idx + 1,
            "title": initiative.get("name", ""),
            "description": initiative.get("description"),
            "targetDate": format_date(initiative.get("targetDate")),
            "progress": average_progress,
            "projects": [
                {
                    "id": project.get("id"),
                    "name": project.get("name", ""),
                    "description": project.get("description", ""),
                    "status": "active",
                    "progress": project.get("progress", 0),
                    "targetDate": format_date(project.get("targetDate")),
                    "health": project.get("health"),
                    "lead": {
                        "name": project.get("lead", {}).get("name") if project.get("lead") else None,
                        "email": None
                    } if project.get("lead") else None
                }
                for project in projects
            ]
        }
        phases.append(phase_data)
    
    # Sort phases by phase number
    phases.sort(key=lambda x: x["phase"])
    
    return phases

def is_cache_valid() -> bool:
    """Check if cached data is still valid"""
    if not _cache["data"] or not _cache["last_updated"]:
        return False
    
    cache_age = datetime.now() - _cache["last_updated"]
    return cache_age.total_seconds() < _cache["cache_duration"]

async def refresh_cache() -> Dict[str, Any]:
    """Refresh the Linear data cache"""
    try:
        client = LinearClient()
        initiatives_data = await client.fetch_initiatives()
        
        phases = transform_linear_data_to_website_format(initiatives_data)
        
        progress_data = {
            "lastUpdated": datetime.now().isoformat(),
            "phases": phases
        }
        
        # Update cache
        _cache["data"] = progress_data
        _cache["last_updated"] = datetime.now()
        
        return progress_data
        
    except Exception as e:
        # If refresh fails and we have cached data, return it
        if _cache["data"]:
            return _cache["data"]
        raise e

@router.get("/progress")
async def get_progress_data(
    force_refresh: bool = False,
):  # Public endpoint - no auth required (used by company website)
    """
    Get Linear progress data for website display.
    Returns cached data if available and fresh, otherwise fetches from Linear API.

    Query Parameters:
    - force_refresh: Set to true to bypass cache and fetch fresh data
    """
    try:
        # Return cached data if valid and not forcing refresh
        if not force_refresh and is_cache_valid():
            return JSONResponse(content=_cache["data"])
        
        # Refresh cache with fresh data from Linear
        progress_data = await refresh_cache()
        
        return JSONResponse(content=progress_data)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch progress data: {str(e)}")

@router.get("/milestones")
async def get_upcoming_milestones(
    current_user: dict = Depends(get_current_user)
):
    """
    Get upcoming project completion milestones.
    Returns the next 3 upcoming project deadlines plus one week for celebration.
    """
    try:
        # Get fresh or cached progress data
        if is_cache_valid():
            progress_data = _cache["data"]
        else:
            progress_data = await refresh_cache()
        
        # Extract projects and calculate milestones
        all_projects = []
        for phase in progress_data.get("phases", []):
            all_projects.extend(phase.get("projects", []))
        
        # Filter incomplete projects (excluding Team Setup)
        upcoming_projects = [
            project for project in all_projects
            if (project.get("progress", 0) < 1 and 
                "team setup" not in project.get("name", "").lower())
        ]
        
        # Sort by target date and take top 3
        def parse_date(date_str):
            try:
                return datetime.strptime(date_str, "%b %d, %Y")
            except:
                return datetime.max
        
        upcoming_projects.sort(key=lambda x: parse_date(x.get("targetDate", "")))
        upcoming_projects = upcoming_projects[:3]
        
        # Add one week to each date for milestone celebration
        milestones = []
        for project in upcoming_projects:
            try:
                target_date = datetime.strptime(project["targetDate"], "%b %d, %Y")
                milestone_date = target_date + timedelta(days=7)
                
                milestones.append({
                    "id": project["id"],
                    "name": f"{project['name']} Completion",
                    "description": f"Milestone celebrating the completion of {project['name'].lower()}",
                    "date": milestone_date.strftime("%b %d, %Y"),
                    "progress": project.get("progress", 0),
                    "lead": project.get("lead")
                })
            except:
                continue
        
        return JSONResponse(content={
            "milestones": milestones,
            "lastUpdated": progress_data.get("lastUpdated")
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch milestones: {str(e)}")

@router.post("/refresh")
async def force_refresh_data(background_tasks: BackgroundTasks):
    """
    Force refresh of Linear data.
    Useful for webhooks or manual updates.
    """
    try:
        progress_data = await refresh_cache()
        
        return JSONResponse(content={
            "message": "Data refreshed successfully",
            "lastUpdated": progress_data.get("lastUpdated"),
            "phases_count": len(progress_data.get("phases", []))
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh data: {str(e)}")

@router.get("/health")
async def linear_health_check(
    current_user: dict = Depends(get_current_user)
):
    """Check Linear API connectivity and cache status"""
    try:
        client = LinearClient()
        
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
        
        return JSONResponse(content={
            "status": "healthy",
            "linear_api": "connected",
            "cache_status": "valid" if is_cache_valid() else "expired",
            "last_cache_update": _cache["last_updated"].isoformat() if _cache["last_updated"] else None,
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