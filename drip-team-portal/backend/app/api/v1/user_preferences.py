"""
User Unit Preferences API

Endpoints for managing user's preferred display units per quantity type.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging
import os

from app.db.database import get_db
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.user import User
from app.models.user_preferences import UserUnitPreference
from app.models.units import Unit

router = APIRouter(prefix="/api/v1/me")
logger = logging.getLogger(__name__)


# ============== Pydantic Schemas ==============

class UnitPreferenceBase(BaseModel):
    quantity_type: str
    unit_symbol: str
    precision: float = 0.01


class UnitPreferenceCreate(UnitPreferenceBase):
    pass


class UnitPreferenceResponse(BaseModel):
    id: int
    quantity_type: str
    unit_symbol: str
    unit_name: str
    unit_id: int
    precision: float

    class Config:
        from_attributes = True


class UnitPreferencesResponse(BaseModel):
    preferences: List[UnitPreferenceResponse]


class BulkPreferenceUpdate(BaseModel):
    preferences: List[UnitPreferenceCreate]


# ============== Helper Functions ==============

def get_or_create_user(db: Session, auth_user: dict) -> User:
    """Get user from database or create if doesn't exist."""
    auth0_id = auth_user.get("sub", "")
    email = auth_user.get("email", "unknown@drip-3d.com")
    name = auth_user.get("name", "Unknown User")

    user = db.query(User).filter(User.auth0_id == auth0_id).first()
    if not user:
        user = User(
            auth0_id=auth0_id,
            email=email,
            name=name
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# ============== Endpoints ==============

@router.get("/unit-preferences", response_model=List[UnitPreferenceResponse])
async def get_unit_preferences(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all unit preferences for the current user.

    Returns a list of preferences with quantity_type, unit symbol, and precision.
    """
    user = get_or_create_user(db, current_user)

    preferences = db.query(UserUnitPreference).filter(
        UserUnitPreference.user_id == user.id
    ).all()

    result = []
    for pref in preferences:
        unit = db.query(Unit).filter(Unit.id == pref.preferred_unit_id).first()
        if unit:
            result.append(UnitPreferenceResponse(
                id=pref.id,
                quantity_type=pref.quantity_type,
                unit_symbol=unit.symbol,
                unit_name=unit.name,
                unit_id=unit.id,
                precision=pref.precision
            ))

    return result


@router.get("/unit-preferences/{quantity_type}", response_model=UnitPreferenceResponse)
async def get_unit_preference(
    quantity_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get user's preferred unit for a specific quantity type."""
    user = get_or_create_user(db, current_user)

    pref = db.query(UserUnitPreference).filter(
        UserUnitPreference.user_id == user.id,
        UserUnitPreference.quantity_type == quantity_type
    ).first()

    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No preference set for quantity type '{quantity_type}'"
        )

    unit = db.query(Unit).filter(Unit.id == pref.preferred_unit_id).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Preferred unit not found"
        )

    return UnitPreferenceResponse(
        id=pref.id,
        quantity_type=pref.quantity_type,
        unit_symbol=unit.symbol,
        unit_name=unit.name,
        unit_id=unit.id,
        precision=pref.precision
    )


@router.put("/unit-preferences/{quantity_type}", response_model=UnitPreferenceResponse)
async def set_unit_preference(
    quantity_type: str,
    preference: UnitPreferenceCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Set user's preferred unit for a quantity type.

    Creates a new preference if one doesn't exist, or updates the existing one.
    """
    user = get_or_create_user(db, current_user)

    # Find the unit by symbol
    unit = db.query(Unit).filter(Unit.symbol == preference.unit_symbol).first()
    if not unit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unit '{preference.unit_symbol}' not found"
        )

    # Check if preference already exists
    existing = db.query(UserUnitPreference).filter(
        UserUnitPreference.user_id == user.id,
        UserUnitPreference.quantity_type == quantity_type
    ).first()

    if existing:
        # Update existing preference
        existing.preferred_unit_id = unit.id
        existing.precision = preference.precision
        db.commit()
        db.refresh(existing)
        pref = existing
    else:
        # Create new preference
        pref = UserUnitPreference(
            user_id=user.id,
            quantity_type=quantity_type,
            preferred_unit_id=unit.id,
            precision=preference.precision
        )
        db.add(pref)
        db.commit()
        db.refresh(pref)

    return UnitPreferenceResponse(
        id=pref.id,
        quantity_type=pref.quantity_type,
        unit_symbol=unit.symbol,
        unit_name=unit.name,
        unit_id=unit.id,
        precision=pref.precision
    )


@router.delete("/unit-preferences/{quantity_type}")
async def delete_unit_preference(
    quantity_type: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete user's preference for a quantity type.

    After deletion, the system will use the default unit for that quantity type.
    """
    user = get_or_create_user(db, current_user)

    pref = db.query(UserUnitPreference).filter(
        UserUnitPreference.user_id == user.id,
        UserUnitPreference.quantity_type == quantity_type
    ).first()

    if not pref:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No preference set for quantity type '{quantity_type}'"
        )

    db.delete(pref)
    db.commit()

    return {"message": f"Preference for '{quantity_type}' deleted"}


@router.put("/unit-preferences", response_model=List[UnitPreferenceResponse])
async def bulk_set_unit_preferences(
    data: BulkPreferenceUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Set multiple unit preferences at once.

    Useful for the Settings page to save all preferences in one request.
    """
    user = get_or_create_user(db, current_user)
    results = []

    for pref_data in data.preferences:
        # Find the unit by symbol
        unit = db.query(Unit).filter(Unit.symbol == pref_data.unit_symbol).first()
        if not unit:
            logger.warning(f"Unit '{pref_data.unit_symbol}' not found, skipping")
            continue

        # Check if preference already exists
        existing = db.query(UserUnitPreference).filter(
            UserUnitPreference.user_id == user.id,
            UserUnitPreference.quantity_type == pref_data.quantity_type
        ).first()

        if existing:
            existing.preferred_unit_id = unit.id
            existing.precision = pref_data.precision
            pref = existing
        else:
            pref = UserUnitPreference(
                user_id=user.id,
                quantity_type=pref_data.quantity_type,
                preferred_unit_id=unit.id,
                precision=pref_data.precision
            )
            db.add(pref)

        db.flush()
        results.append(UnitPreferenceResponse(
            id=pref.id,
            quantity_type=pref.quantity_type,
            unit_symbol=unit.symbol,
            unit_name=unit.name,
            unit_id=unit.id,
            precision=pref.precision
        ))

    db.commit()
    return results
