from pydantic_settings import BaseSettings
from typing import List

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
        env_file = ".env"

settings = Settings()