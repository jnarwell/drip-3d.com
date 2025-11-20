"""API endpoints for System Constants"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.resources import SystemConstant
from app.schemas.resources import (
    SystemConstant as SystemConstantSchema,
    SystemConstantCreate,
    SystemConstantUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/constants")


@router.get("/", response_model=List[SystemConstantSchema])
async def list_constants(
    category: Optional[str] = Query(None, description="Filter by category"),
    search: Optional[str] = Query(None, description="Search in symbol, name, or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all system constants with optional filtering"""
    query = db.query(SystemConstant)
    
    if category:
        query = query.filter(SystemConstant.category == category)
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (SystemConstant.symbol.ilike(search_pattern)) |
            (SystemConstant.name.ilike(search_pattern)) |
            (SystemConstant.description.ilike(search_pattern))
        )
    
    # Order by category, then name
    query = query.order_by(SystemConstant.category, SystemConstant.name)
    
    total = query.count()
    constants = query.offset(skip).limit(limit).all()
    
    logger.info(f"User {current_user['email']} listed {len(constants)} constants (total: {total})")
    return constants


@router.get("/categories", response_model=List[str])
async def get_categories(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all unique constant categories"""
    categories = db.query(SystemConstant.category).distinct().order_by(SystemConstant.category).all()
    return [cat[0] for cat in categories]


@router.get("/{constant_id}", response_model=SystemConstantSchema)
async def get_constant(
    constant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific constant by ID"""
    constant = db.query(SystemConstant).filter(SystemConstant.id == constant_id).first()
    if not constant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constant with id {constant_id} not found"
        )
    return constant


@router.get("/symbol/{symbol}", response_model=SystemConstantSchema)
async def get_constant_by_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific constant by symbol"""
    constant = db.query(SystemConstant).filter(SystemConstant.symbol == symbol).first()
    if not constant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constant with symbol '{symbol}' not found"
        )
    return constant


@router.post("/", response_model=SystemConstantSchema)
async def create_constant(
    constant_data: SystemConstantCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new custom constant"""
    # Check if symbol already exists
    existing = db.query(SystemConstant).filter(SystemConstant.symbol == constant_data.symbol).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Constant with symbol '{constant_data.symbol}' already exists"
        )
    
    # Only allow creating editable constants
    constant = SystemConstant(
        **constant_data.dict(),
        is_editable=True,
        created_by=current_user["email"]
    )
    
    db.add(constant)
    db.commit()
    db.refresh(constant)
    
    logger.info(f"User {current_user['email']} created constant '{constant.symbol}'")
    return constant


@router.patch("/{constant_id}", response_model=SystemConstantSchema)
async def update_constant(
    constant_id: int,
    constant_update: SystemConstantUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Update a custom constant (only editable constants can be updated)"""
    constant = db.query(SystemConstant).filter(SystemConstant.id == constant_id).first()
    if not constant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constant with id {constant_id} not found"
        )
    
    if not constant.is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify system-defined constants"
        )
    
    # Update fields
    update_data = constant_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(constant, field, value)
    
    db.commit()
    db.refresh(constant)
    
    logger.info(f"User {current_user['email']} updated constant '{constant.symbol}'")
    return constant


@router.delete("/{constant_id}")
async def delete_constant(
    constant_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Delete a custom constant (only editable constants can be deleted)"""
    constant = db.query(SystemConstant).filter(SystemConstant.id == constant_id).first()
    if not constant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Constant with id {constant_id} not found"
        )
    
    if not constant.is_editable:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete system-defined constants"
        )
    
    symbol = constant.symbol
    db.delete(constant)
    db.commit()
    
    logger.info(f"User {current_user['email']} deleted constant '{symbol}'")
    return {"message": f"Constant '{symbol}' deleted successfully"}