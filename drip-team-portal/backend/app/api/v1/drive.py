"""
Google Drive API - List and access user's Drive files.

Uses the Google access token from JWT claims to access the user's Drive.
The Google token is passed through from Auth0 via a custom claim set by an Auth0 Action.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, List
from pydantic import BaseModel
from jose import jwt
import os
import httpx
import logging

logger = logging.getLogger(__name__)

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/drive", tags=["drive"])
security = HTTPBearer()

# Custom claim namespace for Google token (configured in Auth0 Action)
GOOGLE_TOKEN_CLAIM = "https://drip-3d.com/google_access_token"


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class DriveFile(BaseModel):
    id: str
    name: str
    mimeType: str
    webViewLink: Optional[str] = None
    iconLink: Optional[str] = None
    thumbnailLink: Optional[str] = None
    modifiedTime: Optional[str] = None
    size: Optional[str] = None
    owners: Optional[List[dict]] = None


class DriveListResponse(BaseModel):
    files: List[DriveFile]
    nextPageToken: Optional[str] = None


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def extract_google_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[str]:
    """
    Extract Google access token from the Auth0 JWT claims.

    The token is injected as a custom claim by an Auth0 Action when
    the user logs in via Google social connection.
    """
    auth0_token = credentials.credentials

    try:
        # Decode without verification just to read claims
        # (The main get_current_user already verified the token)
        unverified = jwt.get_unverified_claims(auth0_token)

        # Check for Google token in custom claim
        google_token = unverified.get(GOOGLE_TOKEN_CLAIM)

        if google_token:
            logger.debug("Found Google token in JWT claims")
            return google_token

        # Fallback: check header (for testing/dev)
        header_token = request.headers.get("x-google-token")
        if header_token:
            logger.debug("Found Google token in x-google-token header")
            return header_token

        return None

    except Exception as e:
        logger.warning(f"Error extracting Google token: {e}")
        return None


def require_google_token(google_token: Optional[str] = Depends(extract_google_token)) -> str:
    """Dependency that requires a valid Google token."""
    if not google_token:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "google_token_required",
                "message": "Google Drive access requires Google authentication. Please re-login with Google.",
                "hint": "Ensure Auth0 Action is configured to pass through Google token."
            }
        )
    return google_token


def get_google_token(current_user: dict) -> str:
    """Extract Google access token from current user claims (legacy helper)."""
    token = current_user.get("google_access_token")
    if not token:
        raise HTTPException(
            status_code=401,
            detail="Google access token not available. Please re-authenticate with Google."
        )
    return token


# =============================================================================
# TEST ENDPOINT - Verify token extraction
# =============================================================================

class DriveTokenStatus(BaseModel):
    has_token: bool
    token_preview: Optional[str] = None
    message: str


@router.get("/test", response_model=DriveTokenStatus)
async def test_drive_token(
    google_token: Optional[str] = Depends(extract_google_token)
):
    """
    Test endpoint to verify Google token extraction.

    Returns whether a Google token is available and a preview of the first 20 chars.
    Use this to verify the Auth0 Action is correctly passing the Google token.
    """
    if google_token:
        preview = f"{google_token[:20]}..." if len(google_token) > 20 else google_token
        return DriveTokenStatus(
            has_token=True,
            token_preview=preview,
            message="Google token found in JWT claims"
        )
    else:
        return DriveTokenStatus(
            has_token=False,
            token_preview=None,
            message="No Google token found. Ensure Auth0 Action is configured to pass Google token in claim: " + GOOGLE_TOKEN_CLAIM
        )


# =============================================================================
# FILE ENDPOINTS
# =============================================================================

@router.get("/files", response_model=DriveListResponse)
async def list_drive_files(
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    page_size: int = Query(25, ge=1, le=100, description="Number of files per page"),
    query: Optional[str] = Query(None, description="Search query (Drive search syntax)"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    current_user: dict = Depends(get_current_user)
):
    """
    List files from user's Google Drive.

    Supports pagination via page_token and filtering by:
    - query: Google Drive search syntax (e.g., "name contains 'report'")
    - mime_type: Filter by file type (e.g., "application/pdf")

    Returns file metadata including name, type, links, and modification time.
    """
    token = get_google_token(current_user)

    # Build Drive API query
    params = {
        "pageSize": page_size,
        "fields": "nextPageToken,files(id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,size,owners)",
        "orderBy": "modifiedTime desc",
    }

    if page_token:
        params["pageToken"] = page_token

    # Build q parameter for filtering
    q_parts = []
    if query:
        q_parts.append(query)
    if mime_type:
        q_parts.append(f"mimeType='{mime_type}'")
    # Exclude trashed files
    q_parts.append("trashed=false")

    if q_parts:
        params["q"] = " and ".join(q_parts)

    # Call Google Drive API
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token expired or invalid. Please re-authenticate."
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Google Drive API error: {response.text}"
            )

        data = response.json()

    return DriveListResponse(
        files=[DriveFile(**f) for f in data.get("files", [])],
        nextPageToken=data.get("nextPageToken")
    )


@router.get("/files/{file_id}")
async def get_drive_file(
    file_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Get metadata for a single Drive file.

    Returns detailed file information including permissions and sharing status.
    """
    token = get_google_token(current_user)

    fields = "id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,createdTime,size,owners,shared,permissions"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"fields": fields},
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token expired or invalid. Please re-authenticate."
            )

        if response.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail="File not found or you don't have access."
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Google Drive API error: {response.text}"
            )

        return response.json()


@router.get("/search")
async def search_drive_files(
    q: str = Query(..., description="Search term"),
    page_size: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for files in Google Drive.

    Simple search endpoint that wraps the name contains query.
    For advanced queries, use /files with the query parameter.
    """
    token = get_google_token(current_user)

    params = {
        "pageSize": page_size,
        "fields": "files(id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime)",
        "q": f"name contains '{q}' and trashed=false",
        "orderBy": "modifiedTime desc",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
            headers={"Authorization": f"Bearer {token}"}
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token expired or invalid. Please re-authenticate."
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Google Drive API error: {response.text}"
            )

        data = response.json()

    return {
        "files": data.get("files", []),
        "query": q
    }
