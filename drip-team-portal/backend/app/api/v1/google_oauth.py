"""
Google OAuth API - Direct OAuth flow for Google Drive access.

Provides endpoints for users to connect their Google Drive via OAuth,
storing tokens in the database for later use by the Drive API.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta
from urllib.parse import urlencode
import httpx
import os
import logging

from app.db.database import get_db
from app.models.google_token import GoogleToken
from app.core.config import settings
from app.core.rate_limit import limiter

logger = logging.getLogger(__name__)

if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/google-oauth", tags=["google-oauth"])

# Google OAuth endpoints
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"

# Scopes for Google Drive read-only access
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/userinfo.email",
]


# =============================================================================
# PYDANTIC SCHEMAS
# =============================================================================

class AuthUrlResponse(BaseModel):
    auth_url: str
    message: str


class CallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None


class CallbackResponse(BaseModel):
    success: bool
    message: str


class StatusResponse(BaseModel):
    connected: bool
    expires_at: Optional[str] = None
    is_expired: Optional[bool] = None
    message: str


# =============================================================================
# ENDPOINTS
# =============================================================================

@router.get("/auth-url", response_model=AuthUrlResponse)
async def get_auth_url(
    current_user: dict = Depends(get_current_user)
):
    """
    Get the Google OAuth authorization URL.

    The user should be redirected to this URL to authorize Google Drive access.
    After authorization, Google will redirect back to our callback URL.
    """
    if not settings.GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured. GOOGLE_CLIENT_ID is missing."
        )

    # Use user email as state for CSRF protection
    state = current_user["email"]

    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",  # Request refresh token
        "prompt": "consent",  # Force consent to get refresh token
        "state": state,
    }

    auth_url = f"{GOOGLE_AUTH_URL}?{urlencode(params)}"

    return AuthUrlResponse(
        auth_url=auth_url,
        message="Redirect user to this URL to authorize Google Drive access"
    )


@router.post("/callback", response_model=CallbackResponse)
@limiter.limit("10/minute")
async def handle_callback(
    request: Request,
    data: CallbackRequest,
    db: Session = Depends(get_db)
):
    """
    Handle the OAuth callback from Google.

    This endpoint is PUBLIC (no auth required) because it's called during
    the OAuth flow. The user email comes from the 'state' parameter which
    was set when the flow started.

    Exchanges the authorization code for access and refresh tokens,
    then stores them in the database.

    Rate limited: 10 requests/minute per IP
    """
    # Get user email from state parameter (set when OAuth flow started)
    user_email = data.state

    # Validate email is present and belongs to our domain
    if not user_email:
        raise HTTPException(
            status_code=400,
            detail="Missing state parameter. Please try again."
        )

    if not user_email.endswith(settings.ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(
            status_code=403,
            detail=f"Access restricted to {settings.ALLOWED_EMAIL_DOMAIN} email addresses"
        )

    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=500,
            detail="Google OAuth not configured."
        )

    # Exchange code for tokens
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "code": data.code,
                    "grant_type": "authorization_code",
                    "redirect_uri": settings.GOOGLE_REDIRECT_URI,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=10.0
            )

            if response.status_code != 200:
                logger.error(f"Google token exchange failed: {response.status_code} - {response.text}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to exchange authorization code: {response.text}"
                )

            token_data = response.json()

        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="Google token exchange timed out. Please try again."
            )

    access_token = token_data.get("access_token")
    refresh_token = token_data.get("refresh_token")
    expires_in = token_data.get("expires_in", 3600)  # Default 1 hour

    if not access_token:
        raise HTTPException(
            status_code=400,
            detail="No access token received from Google."
        )

    # Calculate expiration time
    expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

    # Store or update tokens in database
    existing = db.query(GoogleToken).filter(GoogleToken.user_email == user_email).first()

    if existing:
        existing.access_token = access_token
        if refresh_token:  # Only update refresh token if provided
            existing.refresh_token = refresh_token
        existing.expires_at = expires_at
        existing.updated_at = datetime.utcnow()
    else:
        new_token = GoogleToken(
            user_email=user_email,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
        )
        db.add(new_token)

    db.commit()

    logger.info(f"Google Drive connected for user: {user_email}")

    return CallbackResponse(
        success=True,
        message="Google Drive connected successfully!"
    )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Check if the current user has connected Google Drive.

    Returns connection status and token expiration info.
    """
    user_email = current_user["email"]

    token = db.query(GoogleToken).filter(GoogleToken.user_email == user_email).first()

    if not token:
        return StatusResponse(
            connected=False,
            expires_at=None,
            is_expired=None,
            message="Google Drive not connected. Click 'Connect' to authorize access."
        )

    is_expired = token.is_expired()

    if is_expired and not token.refresh_token:
        return StatusResponse(
            connected=False,
            expires_at=token.expires_at.isoformat() if token.expires_at else None,
            is_expired=True,
            message="Google Drive token expired. Please reconnect."
        )

    return StatusResponse(
        connected=True,
        expires_at=token.expires_at.isoformat() if token.expires_at else None,
        is_expired=is_expired,
        message="Google Drive connected" + (" (token will auto-refresh)" if is_expired else "")
    )


@router.delete("/disconnect", response_model=CallbackResponse)
async def disconnect(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Disconnect Google Drive by removing stored tokens.

    This revokes the user's Google Drive access from our application.
    """
    user_email = current_user["email"]

    token = db.query(GoogleToken).filter(GoogleToken.user_email == user_email).first()

    if not token:
        return CallbackResponse(
            success=True,
            message="Google Drive was not connected."
        )

    # Optionally revoke the token with Google
    if token.access_token:
        try:
            async with httpx.AsyncClient() as client:
                await client.post(
                    "https://oauth2.googleapis.com/revoke",
                    params={"token": token.access_token},
                    timeout=5.0
                )
        except Exception as e:
            logger.warning(f"Failed to revoke Google token: {e}")
            # Continue anyway - we'll delete from our database

    db.delete(token)
    db.commit()

    logger.info(f"Google Drive disconnected for user: {user_email}")

    return CallbackResponse(
        success=True,
        message="Google Drive disconnected successfully."
    )
