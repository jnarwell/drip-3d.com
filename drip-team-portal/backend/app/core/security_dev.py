# Development security bypass for testing
from typing import Dict, Any

async def get_current_user_dev() -> Dict[str, Any]:
    """Mock user for development testing"""
    return {
        "email": "user@drip-3d.com",
        "name": "Test User",
        "sub": "dev|123456",
        "permissions": []
    }