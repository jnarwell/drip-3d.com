"""
Google Drive API - List and access user's Drive files.

Uses stored OAuth tokens from the database (obtained via /google-oauth endpoints).
Tokens are automatically refreshed when expired using the stored refresh token.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta
import os
import httpx
import logging
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception

from app.db.database import get_db
from app.models.google_token import GoogleToken
from app.core.config import settings

logger = logging.getLogger(__name__)


def _is_retryable_error(exception: Exception) -> bool:
    """Check if the exception is retryable (transient errors)."""
    if isinstance(exception, httpx.HTTPStatusError):
        # Retry on 429 (rate limit), 500, 502, 503, 504 (server errors)
        return exception.response.status_code in (429, 500, 502, 503, 504)
    if isinstance(exception, (httpx.TimeoutException, httpx.ConnectError)):
        return True
    return False

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/drive", tags=["drive"])

# Google OAuth token refresh endpoint
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"


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


class DriveTokenStatus(BaseModel):
    connected: bool
    has_token: bool
    is_expired: Optional[bool] = None
    message: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def refresh_google_token(token: GoogleToken, db: Session) -> str:
    """
    Refresh an expired Google access token using the refresh token.

    Updates the token in the database and returns the new access token.
    """
    if not token.refresh_token:
        raise HTTPException(
            status_code=401,
            detail="Google token expired and no refresh token available. Please reconnect Google Drive."
        )

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "refresh_token": token.refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"Google token refresh failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=401,
                    detail="Failed to refresh Google token. Please reconnect Google Drive."
                )

            data = response.json()

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Google token refresh timed out. Please try again."
            )

    new_access_token = data.get("access_token")
    expires_in = data.get("expires_in", 3600)

    if not new_access_token:
        raise HTTPException(
            status_code=401,
            detail="No access token received from Google. Please reconnect."
        )

    # Update token in database
    token.access_token = new_access_token
    token.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    token.updated_at = datetime.utcnow()
    db.commit()

    logger.debug(f"Refreshed Google token for user: {token.user_email}")

    return new_access_token


async def get_google_token(
    user_email: str,
    db: Session
) -> str:
    """
    Get a valid Google access token for the user.

    Fetches from database and auto-refreshes if expired.
    """
    token = db.query(GoogleToken).filter(GoogleToken.user_email == user_email).first()

    if not token:
        raise HTTPException(
            status_code=401,
            detail={
                "error": "google_not_connected",
                "message": "Google Drive not connected. Please connect your Google account first.",
                "action": "connect_google"
            }
        )

    # Check if token is expired
    if token.is_expired():
        logger.debug(f"Token expired for {user_email}, refreshing...")
        return await refresh_google_token(token, db)

    return token.access_token


# =============================================================================
# TEST ENDPOINT - Verify connection status
# =============================================================================

@router.get("/test", response_model=DriveTokenStatus)
async def test_drive_connection(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Test endpoint to verify Google Drive connection status.

    Returns whether the user has connected Google Drive and token validity.
    """
    user_email = current_user["email"]
    token = db.query(GoogleToken).filter(GoogleToken.user_email == user_email).first()

    if not token:
        return DriveTokenStatus(
            connected=False,
            has_token=False,
            is_expired=None,
            message="Google Drive not connected. Use /google-oauth/auth-url to connect."
        )

    is_expired = token.is_expired()

    if is_expired and not token.refresh_token:
        return DriveTokenStatus(
            connected=False,
            has_token=True,
            is_expired=True,
            message="Google token expired and cannot be refreshed. Please reconnect."
        )

    return DriveTokenStatus(
        connected=True,
        has_token=True,
        is_expired=is_expired,
        message="Google Drive connected" + (" (token will auto-refresh)" if is_expired else "")
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
    drive_id: Optional[str] = Query(None, description="Shared drive ID (optional)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    List files from user's Google Drive.

    Supports pagination via page_token and filtering by:
    - query: Google Drive search syntax (e.g., "name contains 'report'")
    - mime_type: Filter by file type (e.g., "application/pdf")
    - drive_id: Target a specific shared drive

    Returns file metadata including name, type, links, and modification time.
    Includes files from shared drives via supportsAllDrives.
    """
    google_token = await get_google_token(current_user["email"], db)

    # Build Drive API query
    params = {
        "pageSize": page_size,
        "fields": "nextPageToken,files(id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,size,owners,driveId)",
        "orderBy": "modifiedTime desc",
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }

    # Set corpora based on drive_id
    if drive_id:
        params["driveId"] = drive_id
        params["corpora"] = "drive"
    else:
        params["corpora"] = "allDrives"

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
            headers={"Authorization": f"Bearer {google_token}"},
            timeout=15.0
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token invalid. Please reconnect Google Drive."
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
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get metadata for a single Drive file.

    Returns detailed file information including permissions and sharing status.
    """
    google_token = await get_google_token(current_user["email"], db)

    fields = "id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,createdTime,size,owners,shared,permissions"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={
                "fields": fields,
                "supportsAllDrives": "true",
            },
            headers={"Authorization": f"Bearer {google_token}"},
            timeout=15.0
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token invalid. Please reconnect Google Drive."
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
    drive_id: Optional[str] = Query(None, description="Shared drive ID (optional)"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Search for files in Google Drive.

    Simple search endpoint that wraps the name contains query.
    For advanced queries, use /files with the query parameter.
    Includes files from shared drives via supportsAllDrives.
    """
    google_token = await get_google_token(current_user["email"], db)

    # Escape single quotes and backslashes to prevent Drive query injection
    escaped_q = q.replace("\\", "\\\\").replace("'", "\\'")

    params = {
        "pageSize": page_size,
        "fields": "files(id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,driveId)",
        "q": f"name contains '{escaped_q}' and trashed=false",
        "orderBy": "modifiedTime desc",
        "supportsAllDrives": "true",
        "includeItemsFromAllDrives": "true",
    }

    # Set corpora based on drive_id
    if drive_id:
        params["driveId"] = drive_id
        params["corpora"] = "drive"
    else:
        params["corpora"] = "allDrives"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://www.googleapis.com/drive/v3/files",
            params=params,
            headers={"Authorization": f"Bearer {google_token}"},
            timeout=15.0
        )

        if response.status_code == 401:
            raise HTTPException(
                status_code=401,
                detail="Google token invalid. Please reconnect Google Drive."
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
