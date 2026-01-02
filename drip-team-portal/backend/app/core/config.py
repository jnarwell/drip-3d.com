from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

# Find the .env file - check current dir, parent dirs, and common locations
def find_env_file():
    current = Path.cwd()

    # Check current dir and up to 3 levels up
    check_dir = current
    for _ in range(4):
        env_path = check_dir / ".env"
        if env_path.exists():
            return str(env_path)
        check_dir = check_dir.parent

    # Check common subdirectories (for when running from parent dir)
    for subdir in ["drip-team-portal", "backend", "drip-team-portal/backend"]:
        env_path = current / subdir / ".env"
        if env_path.exists():
            return str(env_path)

    # Check relative to this file's location
    config_dir = Path(__file__).parent  # app/core/
    backend_dir = config_dir.parent.parent  # backend/
    portal_dir = backend_dir.parent  # drip-team-portal/

    for check_dir in [backend_dir, portal_dir]:
        env_path = check_dir / ".env"
        if env_path.exists():
            return str(env_path)

    return ".env"  # Fallback to default

class Settings(BaseSettings):
    PROJECT_NAME: str = "DRIP Team Portal"
    VERSION: str = "1.0.0"
    
    DATABASE_URL: str = None
    REDIS_URL: str = "redis://localhost:6379"
    
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    AUTH0_DOMAIN: str
    AUTH0_API_AUDIENCE: str
    AUTH0_CLIENT_ID: str
    AUTH0_CLIENT_SECRET: str

    # Google OAuth for Drive access
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "https://team.drip-3d.com/oauth/google/callback"

    LINEAR_API_KEY: str = ""
    LINEAR_WEBHOOK_SECRET: str = ""
    DRIP_TEAM_ID: str = ""
    VALIDATION_PROJECT_ID: str = ""
    
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "https://drip-3d.com",
        "https://www.drip-3d.com",
        "https://team.drip-3d.com",
        "https://frontend-production-31b1.up.railway.app"
    ]
    
    ALLOWED_EMAIL_DOMAIN: str = "@drip-3d.com"
    
    class Config:
        env_file = find_env_file()
        extra = "ignore"  # Ignore extra fields from .env (like VITE_* frontend vars)

settings = Settings()