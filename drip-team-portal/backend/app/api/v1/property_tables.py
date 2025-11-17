"""API endpoints for Property Tables"""
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
from app.models.resources import PropertyTable, TableType
from app.schemas.resources import (
    PropertyTable as PropertyTableSchema,
    PropertyTableCreate,
    PropertyTableUpdate
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/property-tables")


@router.get("/", response_model=List[PropertyTableSchema])
async def list_property_tables(
    table_type: Optional[TableType] = Query(None, description="Filter by table type"),
    material_id: Optional[int] = Query(None, description="Filter by material ID"),
    component_id: Optional[int] = Query(None, description="Filter by component ID"),
    search: Optional[str] = Query(None, description="Search in name or description"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all property tables with optional filtering"""
    # For now, return empty list as per instructions
    logger.info(f"User {current_user['email']} requested property tables list")
    return []


@router.get("/{table_id}", response_model=PropertyTableSchema)
async def get_property_table(
    table_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific property table by ID"""
    # For now, return 404 as no tables exist
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Property table with id {table_id} not found"
    )


@router.post("/", response_model=PropertyTableSchema)
async def create_property_table(
    table_data: PropertyTableCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new property table"""
    # For now, return error message as per instructions
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Property table creation will be implemented in a future update"
    )