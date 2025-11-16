"""API endpoints for enhanced alloy data with NIST temperature-dependent properties"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging

from app.db.database import get_db
from app.core.security import get_current_user
from app.services.alloy_standards import AlloyStandardsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize service
alloy_service = AlloyStandardsService()

@router.get("/alloys/{alloy_name}/enhanced")
async def get_enhanced_alloy_data(
    alloy_name: str,
    include_nist: bool = Query(True, description="Include NIST temperature-dependent data"),
    current_user: dict = Depends(get_current_user)
):
    """Get enhanced alloy data including NIST temperature-dependent properties"""
    logger.info(f"🔍 Getting enhanced data for alloy: {alloy_name}")
    
    enhanced_data = alloy_service.get_enhanced_alloy_data(alloy_name, include_nist_data=include_nist)
    
    if not enhanced_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alloy {alloy_name} not found"
        )
    
    return {
        "alloy_name": alloy_name,
        "enhanced_data": enhanced_data,
        "nist_enhanced": enhanced_data.get("nist_enhanced", False),
        "temperature_dependent_properties": enhanced_data.get("temperature_dependent_properties", {})
    }

@router.get("/alloys/{alloy_name}/property-at-temperature")
async def get_property_at_temperature(
    alloy_name: str,
    property_name: str = Query(..., description="Property name (e.g., 'thermal_conductivity')"),
    temperature: float = Query(..., description="Temperature in Kelvin"),
    current_user: dict = Depends(get_current_user)
):
    """Get specific property value at given temperature"""
    logger.info(f"🌡️ Getting {property_name} for {alloy_name} at {temperature}K")
    
    property_value = alloy_service.get_property_at_temperature(alloy_name, property_name, temperature)
    
    if property_value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property {property_name} not available for {alloy_name} at {temperature}K"
        )
    
    return {
        "alloy_name": alloy_name,
        "property_name": property_name,
        "temperature": temperature,
        "temperature_unit": "K",
        "value": property_value,
        "calculated_at": "now"
    }

@router.get("/alloys/{alloy_name}/temperature-curve")
async def get_temperature_curve(
    alloy_name: str,
    property_name: str = Query(..., description="Property name"),
    temp_min: float = Query(273, description="Minimum temperature (K)"),
    temp_max: float = Query(1273, description="Maximum temperature (K)"),
    num_points: int = Query(50, description="Number of points in curve"),
    current_user: dict = Depends(get_current_user)
):
    """Generate temperature curve for a specific property"""
    logger.info(f"📈 Generating {property_name} curve for {alloy_name} ({temp_min}-{temp_max}K)")
    
    curve_points = alloy_service.generate_temperature_curve(
        alloy_name, property_name, temp_min, temp_max, num_points
    )
    
    if not curve_points:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Temperature curve for {property_name} not available for {alloy_name}"
        )
    
    return {
        "alloy_name": alloy_name,
        "property_name": property_name,
        "temperature_range": {"min": temp_min, "max": temp_max},
        "temperature_unit": "K",
        "curve_points": curve_points,
        "num_points": len(curve_points)
    }

@router.post("/alloys/bulk-enhance")
async def bulk_enhance_alloys(
    categories: Optional[List[str]] = Query(None, description="Material categories to enhance"),
    current_user: dict = Depends(get_current_user)
):
    """Bulk enhance multiple alloys with NIST data"""
    logger.info(f"🚀 Starting bulk enhancement for categories: {categories}")
    
    try:
        results = alloy_service.bulk_enhance_alloys_with_nist(categories)
        
        return {
            "status": "completed",
            "summary": {
                "total_processed": results["total_processed"],
                "enhanced_count": len(results["enhanced"]),
                "failed_count": len(results["failed"]),
                "skipped_count": len(results["skipped"])
            },
            "enhanced": results["enhanced"],
            "failed": results["failed"],
            "skipped": results["skipped"]
        }
        
    except Exception as e:
        logger.error(f"❌ Bulk enhancement failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Bulk enhancement failed: {str(e)}"
        )

@router.get("/alloys/available-properties")
async def get_available_temperature_properties(
    current_user: dict = Depends(get_current_user)
):
    """Get list of available temperature-dependent properties"""
    return {
        "temperature_dependent_properties": [
            {
                "name": "thermal_conductivity",
                "unit": "W/m·K",
                "description": "Thermal conductivity vs temperature"
            },
            {
                "name": "density", 
                "unit": "kg/m³",
                "description": "Density vs temperature"
            },
            {
                "name": "dynamic_viscosity",
                "unit": "Pa·s", 
                "description": "Dynamic viscosity vs temperature (for liquid phases)"
            },
            {
                "name": "specific_heat",
                "unit": "J/kg·K",
                "description": "Specific heat capacity vs temperature"
            }
        ],
        "static_properties": [
            "yield_strength", "ultimate_tensile_strength", "youngs_modulus",
            "shear_modulus", "poisson_ratio", "brinell_hardness", "melting_point"
        ]
    }

@router.get("/alloys/categories/enhanced")
async def get_enhanced_categories_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get summary of which categories have enhanced data available"""
    summary = {
        "categories": [],
        "total_alloys": 0,
        "enhanced_alloys": 0
    }
    
    for category, alloys in alloy_service.standards_data.items():
        category_info = {
            "name": category,
            "total_alloys": len(alloys),
            "enhanced_count": 0,
            "sample_alloys": []
        }
        
        # Check first few alloys to see if enhancement is available
        sample_count = 0
        for alloy_code, alloy_data in alloys.items():
            if sample_count >= 3:
                break
            category_info["sample_alloys"].append({
                "code": alloy_code,
                "name": alloy_data.get("common_name", "")
            })
            sample_count += 1
        
        summary["categories"].append(category_info)
        summary["total_alloys"] += len(alloys)
    
    return summary

@router.get("/alloys/{alloy_name}/nist-status")
async def get_nist_enhancement_status(
    alloy_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Check NIST enhancement status for a specific alloy"""
    enhanced_data = alloy_service.get_enhanced_alloy_data(alloy_name, include_nist_data=False)
    
    if not enhanced_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alloy {alloy_name} not found"
        )
    
    # Try to enhance with NIST data to see what's available
    try:
        from app.services.nist_webbook import nist_service
        enhanced_with_nist = nist_service.enhance_alloy_with_nist_data(enhanced_data)
        
        return {
            "alloy_name": alloy_name,
            "base_properties": list(enhanced_data.get("thermal", {}).keys()) + list(enhanced_data.get("mechanical", {}).keys()),
            "nist_enhanced": enhanced_with_nist.get("nist_enhanced", False),
            "temperature_dependent_properties": list(enhanced_with_nist.get("temperature_dependent_properties", {}).keys()),
            "enhancement_possible": enhanced_with_nist.get("nist_enhanced", False)
        }
        
    except Exception as e:
        logger.warning(f"Could not check NIST status for {alloy_name}: {e}")
        return {
            "alloy_name": alloy_name,
            "nist_enhanced": False,
            "error": str(e),
            "enhancement_possible": False
        }

@router.get("/alloys/{alloy_name}/sources")
async def get_property_source_info(
    alloy_name: str,
    current_user: dict = Depends(get_current_user)
):
    """Get source and temperature dependency information for an alloy's properties"""
    source_info = alloy_service.get_property_source_info(alloy_name)
    
    if not source_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alloy {alloy_name} not found"
        )
    
    return source_info

@router.get("/database/sources-summary")
async def get_database_sources_summary(
    current_user: dict = Depends(get_current_user)
):
    """Get comprehensive summary of all data sources in the database"""
    return alloy_service.get_all_sources_summary()