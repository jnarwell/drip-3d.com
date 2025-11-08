from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/api/v1/auth")

@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user information"""
    db_user = db.query(User).filter(User.email == current_user["email"]).first()
    
    if not db_user:
        # Create user if doesn't exist
        db_user = User(
            email=current_user["email"],
            name=current_user.get("name", ""),
            auth0_id=current_user["sub"],
            last_login=datetime.utcnow()
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
    else:
        # Update last login
        db_user.last_login = datetime.utcnow()
        db.commit()
    
    return db_user

@router.post("/logout")
async def logout(current_user: Dict[str, Any] = Depends(get_current_user)):
    """Logout endpoint (handled client-side with Auth0)"""
    return {"message": "Logout successful"}