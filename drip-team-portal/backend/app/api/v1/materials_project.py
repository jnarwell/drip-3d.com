from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.db.database import get_db
import os
if os.getenv("DEV_MODE") == "true":
    from app.core.security_dev import get_current_user_dev as get_current_user
else:
    from app.core.security import get_current_user
from app.models.material import Material, MaterialProperty
from app.models.property import PropertyDefinition, PropertyType, ValueType
from app.services.materials_project import MaterialsProjectService
from app.services.alloy_standards import AlloyStandardsService
import json
from app.schemas.material import MaterialResponse, MaterialPropertyValue
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/materials-project")

# Initialize services
mp_service = MaterialsProjectService()
standards_service = AlloyStandardsService()

class MPSearchRequest(BaseModel):
    query_type: str  # "alloy_system", "elements", "properties"
    alloy_system: Optional[str] = None  # e.g., "Al-Si", "Al-Mg"
    elements_include: Optional[List[str]] = None
    elements_exclude: Optional[List[str]] = None
    min_density: Optional[float] = None
    max_density: Optional[float] = None
    min_melting_point: Optional[float] = None
    limit: Optional[int] = 20

class MPMaterialDetail(BaseModel):
    mp_id: str
    formula: str
    common_name: Optional[str] = None
    density: Optional[float] = None
    formation_energy: Optional[float] = None
    stability: bool = False
    band_gap: Optional[float] = None
    crystal_system: Optional[str] = None
    space_group: Optional[str] = None
    elastic_moduli: Optional[Dict[str, float]] = None
    acoustic_properties: Optional[Dict[str, float]] = None
    lattice: Optional[Dict[str, float]] = None
    mechanical_properties: Optional[Dict[str, Any]] = None
    thermal_properties: Optional[Dict[str, Any]] = None
    applications: Optional[List[str]] = None
    standards: Optional[List[str]] = None
    has_standard: Optional[bool] = None
    data_source: Optional[str] = None
    composition: Optional[Dict[str, str]] = None

class MPImportRequest(BaseModel):
    mp_id: str
    material_name: Optional[str] = None  # Custom name override
    category: Optional[str] = "Metal"

class MPAluminumAlloyCompare(BaseModel):
    alloy_formulas: List[str]  # e.g., ["Al", "Al2O3", "Al-Si", "Al-Mg"]

class MPComparisonResult(BaseModel):
    formula: str
    mp_id: str
    density: Optional[float]
    formation_energy: Optional[float]
    printability_score: Optional[float]
    acoustic_impedance: Optional[float]
    impedance_contrast: Optional[float]

class MPOxideResult(BaseModel):
    mp_id: str
    formula: str
    formation_energy: Optional[float]
    stability: bool
    band_gap: Optional[float]
    density: Optional[float]
    elastic_moduli: Optional[Dict[str, float]]

@router.post("/search", response_model=List[MPMaterialDetail])
async def search_materials_project(
    search_request: MPSearchRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search Materials Project database for materials"""
    try:
        if search_request.query_type == "alloy_system":
            if not search_request.alloy_system:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="alloy_system required for alloy system search"
                )
            
            # Use the new search method with standards fallback
            results = mp_service.search_with_standards_fallback(search_request.alloy_system)
            
        elif search_request.query_type == "elements":
            # Also handle common names in element search
            if search_request.elements_include and len(search_request.elements_include) == 1:
                search_type, elements = mp_service.parse_material_search(search_request.elements_include[0])
                search_request.elements_include = elements
                
            results = mp_service.search_by_properties(
                min_density=search_request.min_density,
                max_density=search_request.max_density,
                min_melting_point=search_request.min_melting_point,
                elements_include=search_request.elements_include,
                elements_exclude=search_request.elements_exclude
            )
        else:
            # Default aluminum search
            results = mp_service.search_aluminum_alloys()
        
        # Limit results
        if search_request.limit:
            results = results[:search_request.limit]
        
        return results
        
    except Exception as e:
        logger.error(f"Error searching Materials Project: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching Materials Project: {str(e)}"
        )


@router.get("/material/{mp_id}", response_model=MPMaterialDetail)
async def get_material_details(
    mp_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed information for a specific Materials Project material"""
    try:
        details = mp_service.get_material_details(mp_id)
        if not details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material {mp_id} not found"
            )
        return details
        
    except Exception as e:
        logger.error(f"Error getting material details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting material details: {str(e)}"
        )


@router.post("/import")
async def import_material_from_mp(
    import_request: MPImportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Import a material from Materials Project into DRIP portal database"""
    try:
        # Check if material already imported by MP ID
        existing = db.query(Material).filter(
            Material.mp_id == import_request.mp_id
        ).first()
        
        if existing:
            # Return existing material instead of error
            return {
                "status": "already_exists",
                "material_id": existing.id,
                "material_name": existing.name,
                "mp_id": existing.mp_id,
                "properties_imported": [],
                "message": f"Material {import_request.mp_id} already exists as '{existing.name}'"
            }
        
        # Get material details from MP (already includes standards cross-correlation)
        mp_details = mp_service.get_material_details(import_request.mp_id)
        if not mp_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material {import_request.mp_id} not found in Materials Project"
            )
        
        # Create material record
        # Use common name if available, otherwise use formula
        if mp_details.get('common_name'):
            material_name = import_request.material_name or f"{mp_details['common_name']} ({mp_details['formula']})"
        else:
            material_name = import_request.material_name or f"{mp_details['formula']} (MP: {mp_details['mp_id']})"
        
        # Check if material name already exists (handle unique constraint)
        existing_by_name = db.query(Material).filter(
            Material.name == material_name
        ).first()
        
        if existing_by_name:
            # Generate a unique name by appending MP ID
            material_name = f"{material_name} [MP: {import_request.mp_id}]"
            
            # Double check this new name doesn't exist either
            final_check = db.query(Material).filter(
                Material.name == material_name
            ).first()
            
            if final_check:
                return {
                    "status": "already_exists",
                    "material_id": final_check.id,
                    "material_name": final_check.name,
                    "mp_id": final_check.mp_id,
                    "properties_imported": [],
                    "message": f"Material with similar name already exists as '{final_check.name}'"
                }
        
        new_material = Material(
            name=material_name,
            category=import_request.category,
            subcategory="Aluminum Alloy" if "Al" in mp_details['formula'] else "Other",
            mp_id=import_request.mp_id,
            data_source="Materials Project",
            source_url=f"https://materialsproject.org/materials/{import_request.mp_id}",
            created_by=current_user["email"]
        )
        db.add(new_material)
        db.flush()  # Get material ID without committing
        
        # Import properties
        properties_imported = []
        
        # Density
        if mp_details.get('density'):
            density_def = db.query(PropertyDefinition).filter(
                PropertyDefinition.name == "Density"
            ).first()
            
            if not density_def:
                density_def = PropertyDefinition(
                    name="Density",
                    property_type=PropertyType.PHYSICAL,
                    unit="g/cm³",
                    value_type=ValueType.SINGLE,
                    created_by=current_user["email"]
                )
                db.add(density_def)
                db.flush()
            
            mat_prop = MaterialProperty(
                material_id=new_material.id,
                property_definition_id=density_def.id,
                value=mp_details['density'],
                source="Materials Project API",
                created_by=current_user["email"]
            )
            db.add(mat_prop)
            properties_imported.append("Density")
        
        # Formation Energy
        if mp_details.get('formation_energy'):
            formation_def = db.query(PropertyDefinition).filter(
                PropertyDefinition.name == "Formation Energy"
            ).first()
            
            if not formation_def:
                formation_def = PropertyDefinition(
                    name="Formation Energy",
                    property_type=PropertyType.THERMAL,
                    unit="eV/atom",
                    value_type=ValueType.SINGLE,
                    created_by=current_user["email"]
                )
                db.add(formation_def)
                db.flush()
            
            mat_prop = MaterialProperty(
                material_id=new_material.id,
                property_definition_id=formation_def.id,
                value=mp_details['formation_energy'],
                source="Materials Project API",
                created_by=current_user["email"]
            )
            db.add(mat_prop)
            properties_imported.append("Formation Energy")
        
        # Elastic Properties
        if mp_details.get('elastic_moduli'):
            elastic = mp_details['elastic_moduli']
            
            # Bulk Modulus
            if elastic.get('bulk_modulus'):
                bulk_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Bulk Modulus"
                ).first()
                
                if not bulk_def:
                    bulk_def = PropertyDefinition(
                        name="Bulk Modulus",
                        property_type=PropertyType.MECHANICAL,
                        unit="GPa",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(bulk_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=bulk_def.id,
                    value=elastic['bulk_modulus'],
                    source="Materials Project API",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Bulk Modulus")
            
            # Shear Modulus
            if elastic.get('shear_modulus'):
                shear_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Shear Modulus"
                ).first()
                
                if not shear_def:
                    shear_def = PropertyDefinition(
                        name="Shear Modulus",
                        property_type=PropertyType.MECHANICAL,
                        unit="GPa",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(shear_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=shear_def.id,
                    value=elastic['shear_modulus'],
                    source="Materials Project API",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Shear Modulus")
            
            # Young's Modulus
            if elastic.get('youngs_modulus'):
                youngs_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Young's Modulus"
                ).first()
                
                if not youngs_def:
                    youngs_def = PropertyDefinition(
                        name="Young's Modulus",
                        property_type=PropertyType.MECHANICAL,
                        unit="GPa",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(youngs_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=youngs_def.id,
                    value=elastic['youngs_modulus'],
                    source="Materials Project API",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Young's Modulus")
            
            # Poisson's Ratio
            if elastic.get('poisson_ratio'):
                poisson_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Poisson's Ratio"
                ).first()
                
                if not poisson_def:
                    poisson_def = PropertyDefinition(
                        name="Poisson's Ratio",
                        property_type=PropertyType.MECHANICAL,
                        unit="",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(poisson_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=poisson_def.id,
                    value=elastic['poisson_ratio'],
                    source="Materials Project API",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Poisson's Ratio")
        
        # Acoustic Properties
        if mp_details.get('acoustic_properties'):
            acoustic = mp_details['acoustic_properties']
            
            # Longitudinal Wave Velocity
            if acoustic.get('longitudinal_velocity'):
                long_vel_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Longitudinal Wave Velocity"
                ).first()
                
                if not long_vel_def:
                    long_vel_def = PropertyDefinition(
                        name="Longitudinal Wave Velocity",
                        property_type=PropertyType.ACOUSTIC,
                        unit="m/s",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(long_vel_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=long_vel_def.id,
                    value=acoustic['longitudinal_velocity'],
                    source="Materials Project API (calculated)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Longitudinal Wave Velocity")
            
            # Acoustic Impedance
            if acoustic.get('longitudinal_impedance'):
                impedance_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Acoustic Impedance"
                ).first()
                
                if not impedance_def:
                    impedance_def = PropertyDefinition(
                        name="Acoustic Impedance",
                        property_type=PropertyType.ACOUSTIC,
                        unit="Rayl",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(impedance_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=impedance_def.id,
                    value=acoustic['longitudinal_impedance'],
                    source="Materials Project API (calculated)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Acoustic Impedance")
        
        # Band Gap
        if mp_details.get('band_gap') is not None:
            bandgap_def = db.query(PropertyDefinition).filter(
                PropertyDefinition.name == "Band Gap"
            ).first()
            
            if not bandgap_def:
                bandgap_def = PropertyDefinition(
                    name="Band Gap",
                    property_type=PropertyType.ELECTRICAL,
                    unit="eV",
                    value_type=ValueType.SINGLE,
                    created_by=current_user["email"]
                )
                db.add(bandgap_def)
                db.flush()
            
            mat_prop = MaterialProperty(
                material_id=new_material.id,
                property_definition_id=bandgap_def.id,
                value=mp_details['band_gap'],
                source="Materials Project API",
                created_by=current_user["email"]
            )
            db.add(mat_prop)
            properties_imported.append("Band Gap")
        
        # Import mechanical properties from standards if available
        if mp_details.get('mechanical_properties'):
            mech_props = mp_details['mechanical_properties']
            
            # Yield Strength
            if mech_props.get('yield_strength'):
                yield_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Yield Strength"
                ).first()
                
                if not yield_def:
                    yield_def = PropertyDefinition(
                        name="Yield Strength",
                        property_type=PropertyType.MECHANICAL,
                        unit="MPa",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(yield_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=yield_def.id,
                    value=mech_props['yield_strength'],
                    source="Industry Standard (via Materials Project)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Yield Strength")
            
            # Ultimate Tensile Strength
            if mech_props.get('ultimate_tensile_strength'):
                uts_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Ultimate Tensile Strength"
                ).first()
                
                if not uts_def:
                    uts_def = PropertyDefinition(
                        name="Ultimate Tensile Strength",
                        property_type=PropertyType.MECHANICAL,
                        unit="MPa",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(uts_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=uts_def.id,
                    value=mech_props['ultimate_tensile_strength'],
                    source="Industry Standard (via Materials Project)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Ultimate Tensile Strength")
            
            # Hardness
            if mech_props.get('brinell_hardness'):
                hardness_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Brinell Hardness"
                ).first()
                
                if not hardness_def:
                    hardness_def = PropertyDefinition(
                        name="Brinell Hardness",
                        property_type=PropertyType.MECHANICAL,
                        unit="HB",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(hardness_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=hardness_def.id,
                    value=mech_props['brinell_hardness'],
                    source="Industry Standard (via Materials Project)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Brinell Hardness")
        
        # Import thermal properties from standards if available
        if mp_details.get('thermal_properties'):
            thermal_props = mp_details['thermal_properties']
            
            # Melting Point
            if thermal_props.get('melting_point'):
                melting_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Melting Point"
                ).first()
                
                if not melting_def:
                    melting_def = PropertyDefinition(
                        name="Melting Point",
                        property_type=PropertyType.THERMAL,
                        unit="°C",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(melting_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=melting_def.id,
                    value=thermal_props['melting_point'],
                    source="Industry Standard (via Materials Project)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Melting Point")
            
            # Thermal Conductivity
            if thermal_props.get('thermal_conductivity'):
                thermal_k_def = db.query(PropertyDefinition).filter(
                    PropertyDefinition.name == "Thermal Conductivity"
                ).first()
                
                if not thermal_k_def:
                    thermal_k_def = PropertyDefinition(
                        name="Thermal Conductivity",
                        property_type=PropertyType.THERMAL,
                        unit="W/m·K",
                        value_type=ValueType.SINGLE,
                        created_by=current_user["email"]
                    )
                    db.add(thermal_k_def)
                    db.flush()
                
                mat_prop = MaterialProperty(
                    material_id=new_material.id,
                    property_definition_id=thermal_k_def.id,
                    value=thermal_props['thermal_conductivity'],
                    source="Industry Standard (via Materials Project)",
                    created_by=current_user["email"]
                )
                db.add(mat_prop)
                properties_imported.append("Thermal Conductivity")
        
        db.commit()
        
        return {
            "status": "success",
            "material_id": new_material.id,
            "material_name": new_material.name,
            "mp_id": new_material.mp_id,
            "properties_imported": properties_imported,
            "message": f"Successfully imported {material_name} with {len(properties_imported)} properties"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing material from Materials Project: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error importing material: {str(e)}"
        )


@router.post("/compare-alloys", response_model=List[MPComparisonResult])
async def compare_aluminum_alloys(
    compare_request: MPAluminumAlloyCompare,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Compare multiple aluminum alloys for DRIP printing suitability"""
    try:
        comparison = mp_service.compare_alloys(compare_request.alloy_formulas)
        return comparison
        
    except Exception as e:
        logger.error(f"Error comparing alloys: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing alloys: {str(e)}"
        )


@router.get("/oxide-analysis/{base_element}", response_model=List[MPOxideResult])
async def analyze_oxide_formation(
    base_element: str = "Al",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Analyze oxide formation for a base element (default: Al)"""
    try:
        oxides = mp_service.analyze_oxide_formation(base_element)
        return oxides
        
    except Exception as e:
        logger.error(f"Error analyzing oxide formation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing oxide formation: {str(e)}"
        )


@router.get("/test-thermal-properties")
async def test_thermal_properties(
    material_id: str = Query("mp-1234", description="Material ID to test"),
    db: Session = Depends(get_db),
    mp_service: MaterialsProjectService = Depends(lambda: MaterialsProjectService()),
    current_user: dict = Depends(get_current_user)
):
    """Test endpoint to check what thermal properties are available from Materials Project"""
    try:
        result = mp_service.get_available_thermal_properties(material_id)
        if result is None:
            return {"error": "No data returned"}
        return result
    except Exception as e:
        logger.error(f"Error testing thermal properties: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/batch-import")
async def batch_import_materials(
    mp_ids: List[str],
    background_tasks: BackgroundTasks,
    category: str = "Metal",
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Import multiple materials from Materials Project"""
    results = {
        "imported": [],
        "skipped": [],
        "errors": []
    }
    
    for mp_id in mp_ids:
        try:
            # Check if already imported
            existing = db.query(Material).filter(
                Material.mp_id == mp_id
            ).first()
            
            if existing:
                results["skipped"].append({
                    "mp_id": mp_id,
                    "reason": f"Already imported as '{existing.name}'"
                })
                continue
            
            # Import material
            import_result = await import_material_from_mp(
                MPImportRequest(mp_id=mp_id, category=category),
                background_tasks,
                db,
                current_user
            )
            
            results["imported"].append({
                "mp_id": mp_id,
                "material_id": import_result["material_id"],
                "material_name": import_result["material_name"]
            })
            
        except Exception as e:
            results["errors"].append({
                "mp_id": mp_id,
                "error": str(e)
            })
    
    return {
        "status": "completed",
        "summary": {
            "imported": len(results["imported"]),
            "skipped": len(results["skipped"]),
            "errors": len(results["errors"])
        },
        "details": results
    }


@router.get("/standards/{alloy_code}")
async def get_alloy_standard(
    alloy_code: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get standard data for a specific alloy"""
    standard_data = standards_service.get_alloy_standard(alloy_code)
    
    if not standard_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No standard data found for alloy: {alloy_code}"
        )
    
    return standard_data


@router.get("/standards/search/property")
async def search_by_property(
    property_path: str = Query(..., description="Property path like mechanical.yield_strength"),
    min_value: float = Query(..., description="Minimum value"),
    max_value: float = Query(..., description="Maximum value"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Search alloys by property value range"""
    results = standards_service.search_by_property_range(property_path, min_value, max_value)
    return results


@router.get("/standards/casting-alloys")
async def get_casting_alloys(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get all alloys suitable for casting/melting"""
    return standards_service.get_casting_alloys()


@router.get("/thermal-properties-summary")
async def get_thermal_properties_summary(
    category: Optional[str] = Query(None, description="Filter by material category"),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Get summary of all materials with thermal properties"""
    all_materials = []
    
    # Get materials from standards database
    for cat, alloys in standards_service.standards_data.items():
        # Apply category filter if specified
        if category and category.lower() not in cat.lower():
            continue
            
        for alloy_code, alloy_data in alloys.items():
            if alloy_data.get("thermal"):
                thermal = alloy_data["thermal"]
                all_materials.append({
                    "alloy_code": alloy_code,
                    "common_name": alloy_data.get("common_name", alloy_code),
                    "category": cat,
                    "melting_point": thermal.get("melting_point"),
                    "thermal_conductivity": thermal.get("thermal_conductivity"),
                    "specific_heat": thermal.get("specific_heat"),
                    "solidus": thermal.get("solidus"),
                    "liquidus": thermal.get("liquidus"),
                    "density": alloy_data.get("mechanical", {}).get("density"),
                    "applications": alloy_data.get("applications", [])
                })
    
    # Sort by category and then by name
    all_materials.sort(key=lambda x: (x["category"], x["common_name"]))
    
    summary = {
        "total_materials": len(all_materials),
        "categories": list(set(m["category"] for m in all_materials)),
        "materials": all_materials
    }
    
    return summary


@router.post("/cross-correlate")
async def cross_correlate_material(
    mp_id: str,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    """Cross-correlate Materials Project data with standards"""
    try:
        # Get material details from Materials Project
        mp_details = mp_service.get_material_details(mp_id)
        
        if not mp_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Material {mp_id} not found in Materials Project"
            )
        
        # If it has standard data, compare them
        if mp_details.get("has_standard") and mp_details.get("standard_data"):
            comparison = standards_service.compare_with_mp_data(mp_details, mp_details["standard_data"])
            return {
                "material": mp_details,
                "comparison": comparison
            }
        else:
            return {
                "material": mp_details,
                "comparison": {
                    "message": "No matching standard found for cross-correlation"
                }
            }
            
    except Exception as e:
        logger.error(f"Error cross-correlating material: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error cross-correlating material: {str(e)}"
        )