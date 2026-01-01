"""
Google Drive API Service

Uses OAuth2 access token from Auth0 (passed through from Google social login)
to interact with Google Drive API.
"""

from typing import Optional, List, Dict, Any
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logger = logging.getLogger(__name__)


class DriveService:
    """Service for interacting with Google Drive API."""

    # Common MIME types for filtering
    MIME_TYPES = {
        'folder': 'application/vnd.google-apps.folder',
        'document': 'application/vnd.google-apps.document',
        'spreadsheet': 'application/vnd.google-apps.spreadsheet',
        'presentation': 'application/vnd.google-apps.presentation',
        'pdf': 'application/pdf',
    }

    def __init__(self, access_token: str):
        """
        Initialize DriveService with a Google OAuth2 access token.

        Args:
            access_token: Google OAuth2 access token from Auth0
        """
        self.access_token = access_token
        self._service = None

    @property
    def service(self):
        """Lazy-load the Drive API service."""
        if self._service is None:
            credentials = Credentials(token=self.access_token)
            self._service = build('drive', 'v3', credentials=credentials)
        return self._service

    async def list_files(
        self,
        query: Optional[str] = None,
        page_size: int = 20,
        page_token: Optional[str] = None,
        order_by: str = "modifiedTime desc",
        fields: str = "nextPageToken, files(id, name, mimeType, modifiedTime, webViewLink, iconLink, owners, shared)"
    ) -> Dict[str, Any]:
        """
        List files from Google Drive.

        Args:
            query: Optional Drive API query string (e.g., "name contains 'report'")
            page_size: Number of results per page (max 100)
            page_token: Token for pagination
            order_by: Sort order (default: most recently modified first)
            fields: Fields to return in response

        Returns:
            Dict with 'files' list and optional 'nextPageToken'
        """
        try:
            # Build request parameters
            params = {
                'pageSize': min(page_size, 100),
                'orderBy': order_by,
                'fields': fields,
            }

            if query:
                params['q'] = query

            if page_token:
                params['pageToken'] = page_token

            # Execute request (synchronous, but we're in async context)
            result = self.service.files().list(**params).execute()

            return {
                'files': result.get('files', []),
                'nextPageToken': result.get('nextPageToken'),
            }

        except HttpError as e:
            logger.error(f"Drive API error listing files: {e}")
            raise DriveAPIError(f"Failed to list files: {e.reason}", status_code=e.resp.status)
        except Exception as e:
            logger.error(f"Unexpected error listing files: {e}")
            raise DriveAPIError(f"Failed to list files: {str(e)}")

    async def get_file(self, file_id: str) -> Dict[str, Any]:
        """
        Get metadata for a specific file.

        Args:
            file_id: Google Drive file ID

        Returns:
            File metadata dict
        """
        try:
            result = self.service.files().get(
                fileId=file_id,
                fields="id, name, mimeType, modifiedTime, createdTime, webViewLink, iconLink, owners, shared, description, size"
            ).execute()

            return result

        except HttpError as e:
            logger.error(f"Drive API error getting file {file_id}: {e}")
            if e.resp.status == 404:
                raise DriveAPIError(f"File not found: {file_id}", status_code=404)
            raise DriveAPIError(f"Failed to get file: {e.reason}", status_code=e.resp.status)
        except Exception as e:
            logger.error(f"Unexpected error getting file: {e}")
            raise DriveAPIError(f"Failed to get file: {str(e)}")

    async def search_files(
        self,
        name_contains: Optional[str] = None,
        mime_type: Optional[str] = None,
        in_folder: Optional[str] = None,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        Search for files with common filters.

        Args:
            name_contains: Search for files containing this in the name
            mime_type: Filter by MIME type (can use keys from MIME_TYPES)
            in_folder: Folder ID to search within
            page_size: Number of results

        Returns:
            Dict with 'files' list
        """
        query_parts = []

        if name_contains:
            # Escape single quotes in search term
            escaped = name_contains.replace("'", "\\'")
            query_parts.append(f"name contains '{escaped}'")

        if mime_type:
            # Allow using shorthand like 'folder' or full MIME type
            actual_mime = self.MIME_TYPES.get(mime_type, mime_type)
            query_parts.append(f"mimeType = '{actual_mime}'")

        if in_folder:
            query_parts.append(f"'{in_folder}' in parents")

        # Exclude trashed files
        query_parts.append("trashed = false")

        query = " and ".join(query_parts) if query_parts else None

        return await self.list_files(query=query, page_size=page_size)

    async def list_folders(self, page_size: int = 50) -> Dict[str, Any]:
        """List all folders the user has access to."""
        return await self.list_files(
            query=f"mimeType = '{self.MIME_TYPES['folder']}' and trashed = false",
            page_size=page_size
        )


class DriveAPIError(Exception):
    """Custom exception for Drive API errors."""

    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)
