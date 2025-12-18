"""
Units API - Endpoints for unit management and conversion
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.units import Unit, UnitConversion, UnitAlias
from app.services.unit_engine import UnitEngine
from app.services.seed_units import seed_units

router = APIRouter(prefix="/api/v1/units")
logger = logging.getLogger(__name__)


# ============== Pydantic Schemas ==============

class UnitBase(BaseModel):
    symbol: str
    name: str
    quantity_type: Optional[str] = None
    length_dim: int = 0
    mass_dim: int = 0
    time_dim: int = 0
    current_dim: int = 0
    temperature_dim: int = 0
    amount_dim: int = 0
    luminosity_dim: int = 0
    is_base_unit: bool = False


class UnitCreate(UnitBase):
    pass


class UnitResponse(UnitBase):
    id: int
    display_order: int = 0

    class Config:
        from_attributes = True


class UnitConversionBase(BaseModel):
    from_unit_id: int
    to_unit_id: int
    multiplier: float = 1.0
    offset: float = 0.0


class UnitConversionCreate(UnitConversionBase):
    pass


class UnitConversionResponse(UnitConversionBase):
    id: int
    from_unit: UnitResponse
    to_unit: UnitResponse

    class Config:
        from_attributes = True


class ConvertRequest(BaseModel):
    value: float
    from_symbol: str
    to_symbol: str


class ConvertResponse(BaseModel):
    original_value: float
    converted_value: float
    from_unit: str
    to_unit: str
    success: bool
    error: Optional[str] = None


class DimensionsResponse(BaseModel):
    length_dim: int
    mass_dim: int
    time_dim: int
    current_dim: int
    temperature_dim: int
    amount_dim: int
    luminosity_dim: int
    display: str


class CompatibilityResponse(BaseModel):
    compatible: bool
    unit1: str
    unit2: str
    unit1_dimensions: str
    unit2_dimensions: str


# ============== Unit Endpoints ==============

@router.get("", response_model=List[UnitResponse])
async def list_units(
    quantity_type: Optional[str] = Query(None, description="Filter by quantity type"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all units, optionally filtered by quantity type."""
    query = db.query(Unit)
    if quantity_type:
        query = query.filter(Unit.quantity_type == quantity_type)
    return query.order_by(Unit.display_order, Unit.symbol).all()


@router.get("/quantity-types", response_model=List[str])
async def list_quantity_types(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all unique quantity types."""
    result = db.query(Unit.quantity_type).distinct().filter(Unit.quantity_type.isnot(None)).all()
    return [r[0] for r in result]


@router.get("/{unit_id}", response_model=UnitResponse)
async def get_unit(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a specific unit by ID."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")
    return unit


@router.get("/symbol/{symbol}", response_model=UnitResponse)
async def get_unit_by_symbol(
    symbol: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get a unit by its symbol."""
    engine = UnitEngine(db)
    unit = engine.get_unit_by_symbol(symbol)
    if not unit:
        raise HTTPException(status_code=404, detail=f"Unit '{symbol}' not found")
    return unit


@router.post("", response_model=UnitResponse)
async def create_unit(
    unit_data: UnitCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new unit."""
    # Check for duplicate symbol
    existing = db.query(Unit).filter(Unit.symbol == unit_data.symbol).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Unit with symbol '{unit_data.symbol}' already exists"
        )

    unit = Unit(**unit_data.model_dump())
    db.add(unit)
    db.commit()
    db.refresh(unit)
    return unit


@router.get("/{unit_id}/compatible", response_model=List[UnitResponse])
async def get_compatible_units(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all units that are dimensionally compatible with the given unit."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    engine = UnitEngine(db)
    return engine.get_compatible_units(unit)


# ============== Conversion Endpoints ==============

@router.post("/convert", response_model=ConvertResponse)
async def convert_value(
    request: ConvertRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Convert a value from one unit to another."""
    engine = UnitEngine(db)
    converted, success, error = engine.convert_value_by_symbol(
        request.value,
        request.from_symbol,
        request.to_symbol
    )

    return ConvertResponse(
        original_value=request.value,
        converted_value=converted,
        from_unit=request.from_symbol,
        to_unit=request.to_symbol,
        success=success,
        error=error
    )


@router.get("/check-compatibility", response_model=CompatibilityResponse)
async def check_compatibility(
    unit1: str = Query(..., description="First unit symbol"),
    unit2: str = Query(..., description="Second unit symbol"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Check if two units are dimensionally compatible."""
    engine = UnitEngine(db)

    u1 = engine.get_unit_by_symbol(unit1)
    u2 = engine.get_unit_by_symbol(unit2)

    if not u1:
        raise HTTPException(status_code=404, detail=f"Unit '{unit1}' not found")
    if not u2:
        raise HTTPException(status_code=404, detail=f"Unit '{unit2}' not found")

    dims1 = engine._unit_to_dims(u1)
    dims2 = engine._unit_to_dims(u2)

    return CompatibilityResponse(
        compatible=engine.are_compatible(u1, u2),
        unit1=unit1,
        unit2=unit2,
        unit1_dimensions=engine.dimensions_to_string(dims1),
        unit2_dimensions=engine.dimensions_to_string(dims2)
    )


@router.get("/{unit_id}/dimensions", response_model=DimensionsResponse)
async def get_unit_dimensions(
    unit_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get the dimensional breakdown of a unit."""
    unit = db.query(Unit).filter(Unit.id == unit_id).first()
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found")

    engine = UnitEngine(db)
    dims = engine._unit_to_dims(unit)

    return DimensionsResponse(
        **dims,
        display=engine.dimensions_to_string(dims)
    )


# ============== Conversion Management ==============

@router.get("/conversions", response_model=List[UnitConversionResponse])
async def list_conversions(
    from_unit_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """List all unit conversions, optionally filtered by source unit."""
    query = db.query(UnitConversion)
    if from_unit_id:
        query = query.filter(UnitConversion.from_unit_id == from_unit_id)
    return query.all()


@router.post("/conversions", response_model=UnitConversionResponse)
async def create_conversion(
    conversion: UnitConversionCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Create a new unit conversion."""
    # Verify units exist
    from_unit = db.query(Unit).filter(Unit.id == conversion.from_unit_id).first()
    to_unit = db.query(Unit).filter(Unit.id == conversion.to_unit_id).first()

    if not from_unit:
        raise HTTPException(status_code=404, detail="From unit not found")
    if not to_unit:
        raise HTTPException(status_code=404, detail="To unit not found")

    # Verify dimensional compatibility
    engine = UnitEngine(db)
    if not engine.are_compatible(from_unit, to_unit):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create conversion between dimensionally incompatible units"
        )

    # Check for existing conversion
    existing = db.query(UnitConversion).filter(
        UnitConversion.from_unit_id == conversion.from_unit_id,
        UnitConversion.to_unit_id == conversion.to_unit_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conversion already exists"
        )

    db_conversion = UnitConversion(**conversion.model_dump())
    db.add(db_conversion)
    db.commit()
    db.refresh(db_conversion)
    return db_conversion


# ============== Seeding Endpoint ==============

class SeedResponse(BaseModel):
    success: bool
    units_created: int
    conversions_created: int
    aliases_created: int
    message: str


@router.post("/seed", response_model=SeedResponse)
async def seed_unit_database(
    force: bool = Query(False, description="If true, clear existing units first"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """
    Seed the database with common engineering units.

    This populates units, conversions, and aliases for:
    - SI base units (m, kg, s, A, K, mol, cd)
    - Common derived units (N, Pa, J, W, etc.)
    - Imperial units (in, ft, lb, etc.)
    - Engineering units (thermal conductivity, density, etc.)
    """
    try:
        result = seed_units(db, force=force)
        return SeedResponse(
            success=True,
            units_created=result["units"],
            conversions_created=result["conversions"],
            aliases_created=result["aliases"],
            message=f"Successfully seeded {result['units']} units, {result['conversions']} conversions, {result['aliases']} aliases"
        )
    except Exception as e:
        logger.error(f"Error seeding units: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to seed units: {str(e)}"
        )
