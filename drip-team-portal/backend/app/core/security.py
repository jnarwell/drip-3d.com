from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import httpx
import json

security = HTTPBearer()

class Auth0:
    def __init__(self):
        self.domain = settings.AUTH0_DOMAIN
        self.audience = settings.AUTH0_API_AUDIENCE
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET
        self.algorithm = "RS256"
        self._jwks_client = None
    
    async def get_jwks(self):
        if not self._jwks_client:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"https://{self.domain}/.well-known/jwks.json")
                self._jwks_client = response.json()
        return self._jwks_client
    
    async def verify_token(self, token: str) -> Dict[str, Any]:
        try:
            jwks = await self.get_jwks()
            
            unverified_header = jwt.get_unverified_header(token)
            rsa_key = {}
            
            for key in jwks["keys"]:
                if key["kid"] == unverified_header["kid"]:
                    rsa_key = {
                        "kty": key["kty"],
                        "kid": key["kid"],
                        "use": key["use"],
                        "n": key["n"],
                        "e": key["e"]
                    }
            
            if not rsa_key:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Unable to find appropriate key"
                )
            
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=[self.algorithm],
                audience=self.audience,
                issuer=f"https://{self.domain}/"
            )
            
            return payload
            
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Error processing token: {str(e)}"
            )

auth0 = Auth0()

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    token = credentials.credentials
    payload = await auth0.verify_token(token)

    # Get email from custom claim (Auth0 Action), standard claim, or x-email header
    email = (
        payload.get("https://drip-3d.com/email") or
        payload.get("email") or
        request.headers.get("x-email", "")
    )

    if not email.endswith(settings.ALLOWED_EMAIL_DOMAIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access restricted to {settings.ALLOWED_EMAIL_DOMAIN} email addresses"
        )

    return {
        "email": email,
        "name": payload.get("name", ""),
        "sub": payload.get("sub", ""),
        "permissions": payload.get("permissions", []),
    }

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt