"""
Google Drive API - List and access user's Drive files.

Uses Auth0 Token Vault to exchange the user's Auth0 token for a Google access token.
This allows access to the user's Google Drive without storing tokens.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from typing import Optional, List
from pydantic import BaseModel
import os
import httpx
import logging

from app.services.token_vault_service import get_token_vault_service, TokenVaultService

logger = logging.getLogger(__name__)

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/drive", tags=["drive"])


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
    has_token: bool
    token_preview: Optional[str] = None
    message: str


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def extract_auth0_token(request: Request) -> str:
    """Extract the Auth0 access token from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]  # Remove "Bearer " prefix
    return auth_header


async def get_google_token_from_vault(
    request: Request,
    token_vault: TokenVaultService = Depends(get_token_vault_service)
) -> Optional[str]:
    """Get Google token via Token Vault exchange."""
    auth0_token = extract_auth0_token(request)
    if not auth0_token:
        return None
    return await token_vault.get_google_token(auth0_token)


# =============================================================================
# TEST ENDPOINT - Verify token exchange
# =============================================================================

@router.get("/test", response_model=DriveTokenStatus)
async def test_drive_token(
    request: Request,
    current_user: dict = Depends(get_current_user),
    token_vault: TokenVaultService = Depends(get_token_vault_service)
):
    """
    Test endpoint to verify Token Vault exchange is working.

    Returns whether a Google token can be obtained via Token Vault.
    Use this to verify the Auth0 Token Vault is correctly configured.
    """
    auth0_token = extract_auth0_token(request)
    google_token = await token_vault.get_google_token(auth0_token)

    if google_token:
        preview = f"{google_token[:20]}..." if len(google_token) > 20 else google_token
        return DriveTokenStatus(
            has_token=True,
            token_preview=preview,
            message="Token Vault exchange successful - Google token obtained"
        )
    else:
        return DriveTokenStatus(
            has_token=False,
            token_preview=None,
            message="Token Vault exchange failed. Ensure user logged in via Google and Token Vault is enabled."
        )


# =============================================================================
# FILE ENDPOINTS
# =============================================================================

@router.get("/files", response_model=DriveListResponse)
async def list_drive_files(
    request: Request,
    page_token: Optional[str] = Query(None, description="Token for pagination"),
    page_size: int = Query(25, ge=1, le=100, description="Number of files per page"),
    query: Optional[str] = Query(None, description="Search query (Drive search syntax)"),
    mime_type: Optional[str] = Query(None, description="Filter by MIME type"),
    current_user: dict = Depends(get_current_user),
    token_vault: TokenVaultService = Depends(get_token_vault_service)
):
    """
    List files from user's Google Drive.

    Supports pagination via page_token and filtering by:
    - query: Google Drive search syntax (e.g., "name contains 'report'")
    - mime_type: Filter by file type (e.g., "application/pdf")

    Returns file metadata including name, type, links, and modification time.
    """
    auth0_token = extract_auth0_token(request)
    google_token = await token_vault.get_google_token(auth0_token)

    if not google_token:
        raise HTTPException(
            status_code=401,
            detail="Could not obtain Google token. Please ensure you're logged in with Google."
        )

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
            headers={"Authorization": f"Bearer {google_token}"}
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
    request: Request,
    current_user: dict = Depends(get_current_user),
    token_vault: TokenVaultService = Depends(get_token_vault_service)
):
    """
    Get metadata for a single Drive file.

    Returns detailed file information including permissions and sharing status.
    """
    auth0_token = extract_auth0_token(request)
    google_token = await token_vault.get_google_token(auth0_token)

    if not google_token:
        raise HTTPException(
            status_code=401,
            detail="Could not obtain Google token. Please ensure you're logged in with Google."
        )

    fields = "id,name,mimeType,webViewLink,iconLink,thumbnailLink,modifiedTime,createdTime,size,owners,shared,permissions"

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"https://www.googleapis.com/drive/v3/files/{file_id}",
            params={"fields": fields},
            headers={"Authorization": f"Bearer {google_token}"}
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
    q: str,
    request: Request,
    page_size: int = Query(25, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
    token_vault: TokenVaultService = Depends(get_token_vault_service)
):
    """
    Search for files in Google Drive.

    Simple search endpoint that wraps the name contains query.
    For advanced queries, use /files with the query parameter.
    """
    auth0_token = extract_auth0_token(request)
    google_token = await token_vault.get_google_token(auth0_token)

    if not google_token:
        raise HTTPException(
            status_code=401,
            detail="Could not obtain Google token. Please ensure you're logged in with Google."
        )

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
            headers={"Authorization": f"Bearer {google_token}"}
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
