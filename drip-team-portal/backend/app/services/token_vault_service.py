"""
Token Vault Service - Exchange Auth0 tokens for Google tokens.

Uses Auth0's Token Vault (federated token exchange) to get Google access tokens
on-demand, without requiring custom claims in the JWT.
"""

import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class TokenVaultService:
    """Service to exchange Auth0 access tokens for Google access tokens via Token Vault."""

    def __init__(self):
        self.auth0_domain = settings.AUTH0_DOMAIN
        self.client_id = settings.AUTH0_CLIENT_ID
        self.client_secret = settings.AUTH0_CLIENT_SECRET

    async def get_google_token(self, auth0_access_token: str) -> str | None:
        """
        Exchange Auth0 access token for Google token via Token Vault.

        Args:
            auth0_access_token: The Auth0 access token from the Authorization header

        Returns:
            Google access token if successful, None otherwise
        """
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"https://{self.auth0_domain}/oauth/token",
                    json={
                        "grant_type": "urn:auth0:params:oauth:grant-type:token-exchange:federated-connection-access-token",
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                        "subject_token": auth0_access_token,
                        "subject_token_type": "urn:ietf:params:oauth:token-type:access_token",
                        "requested_token_type": "http://auth0.com/oauth/token-type/federated-connection-access-token",
                        "connection": "google-oauth2"
                    },
                    headers={"Content-Type": "application/json"},
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    token = data.get("access_token")
                    if token:
                        logger.debug("Token Vault exchange successful")
                        return token
                    logger.warning("Token Vault response missing access_token")
                    return None
                else:
                    logger.warning(
                        f"Token Vault exchange failed: {response.status_code} - {response.text}"
                    )
                    return None

            except httpx.TimeoutException:
                logger.error("Token Vault request timed out")
                return None
            except Exception as e:
                logger.error(f"Token Vault exchange error: {e}")
                return None


def get_token_vault_service() -> TokenVaultService:
    """Factory function to get TokenVaultService instance."""
    return TokenVaultService()
