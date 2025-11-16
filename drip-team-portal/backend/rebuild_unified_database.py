#!/usr/bin/env python3
"""Rebuild the unified alloy standards database with all data from legacy files"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Set

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_legacy_file(file_path: Path, source_name: str) -> Dict[str, Any]:
    """Load a legacy alloy standards file"""
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        logger.info(f"✅ Loaded {file_path.name}: {sum(len(alloys) for alloys in data.values())} alloys")
        return data, source_name
    except Exception as e:
        logger.error(f"❌ Error loading {file_path}: {e}")
        return {}, source_name

def convert_to_unified_format(category_name: str, alloy_code: str, alloy_data: Dict[str, Any], source: str) -> Dict[str, Any]:
    """Convert legacy alloy data to unified format with source tracking"""
    
    # Extract base alloy and temper if possible
    base_alloy = alloy_code
    temper = None
    
    # Parse temper from common patterns
    if '-' in alloy_code:
        parts = alloy_code.split('-')
        if len(parts) == 2:
            base_alloy = parts[0]
            temper = parts[1]
    
    unified = {
        "common_name": alloy_data.get("common_name", f"{alloy_code} Alloy"),
        "uns": alloy_data.get("uns", ""),
        "base_alloy": base_alloy,
        "composition": alloy_data.get("composition", {}),
        "properties": {},
        "applications": alloy_data.get("applications", []),
        "standards": alloy_data.get("standards", []),
        "source": source
    }
    
    if temper:
        unified["temper"] = temper
    
    # Convert properties with source tracking
    property_categories = ["mechanical", "thermal", "acoustic", "electrical", "optical"]
    
    for prop_category in property_categories:
        if prop_category in alloy_data:
            unified["properties"][prop_category] = {}
            
            for prop_name, prop_value in alloy_data[prop_category].items():
                # Determine if property is temperature dependent
                temp_dependent_props = {
                    "thermal_conductivity": True,
                    "specific_heat": True, 
                    "density": True,
                    "dynamic_viscosity": True,
                    "electrical_resistivity": True,
                    "coefficient_of_thermal_expansion": True
                }
                
                is_temp_dependent = prop_name in temp_dependent_props
                nist_available = prop_name in ["thermal_conductivity", "density", "dynamic_viscosity", "specific_heat"]
                
                prop_entry = {
                    "value": prop_value,
                    "source": source,
                    "temperature_dependent": is_temp_dependent
                }
                
                # Add units based on property name
                units = {
                    "density": "g/cm³",
                    "yield_strength": "MPa", 
                    "ultimate_tensile_strength": "MPa",
                    "elongation": "%",
                    "youngs_modulus": "GPa",
                    "shear_modulus": "GPa",
                    "poisson_ratio": "",
                    "brinell_hardness": "HB",
                    "melting_point": "°C",
                    "thermal_conductivity": "W/m·K",
                    "specific_heat": "J/kg·K",
                    "longitudinal_velocity": "m/s",
                    "shear_velocity": "m/s",
                    "acoustic_impedance": "MRayl",
                    "coefficient_of_thermal_expansion": "μm/m·K",
                    "electrical_resistivity": "μΩ·cm"
                }
                
                prop_entry["unit"] = units.get(prop_name, "")
                
                if nist_available:
                    prop_entry["nist_available"] = True
                    
                unified["properties"][prop_category][prop_name] = prop_entry
    
    return unified

def resolve_conflicts(existing: Dict[str, Any], new: Dict[str, Any], existing_source: str, new_source: str) -> Dict[str, Any]:
    """Resolve conflicts between duplicate alloys from different sources"""
    
    # Priority order: Extended > Basic > Original
    source_priority = {
        "Extended_Database": 3,
        "Basic_Database": 2, 
        "Original_Database": 1
    }
    
    existing_priority = source_priority.get(existing_source, 0)
    new_priority = source_priority.get(new_source, 0)
    
    if new_priority > existing_priority:
        logger.info(f"  🔄 Replacing {existing_source} with {new_source} (higher priority)")
        return new
    elif new_priority == existing_priority:
        # Merge properties, keeping both sources
        logger.info(f"  🔗 Merging properties from {existing_source} and {new_source}")
        merged = existing.copy()
        
        # Merge properties from new source
        for prop_category, props in new.get("properties", {}).items():
            if prop_category not in merged["properties"]:
                merged["properties"][prop_category] = {}
            
            for prop_name, prop_data in props.items():
                if prop_name not in merged["properties"][prop_category]:
                    merged["properties"][prop_category][prop_name] = prop_data
                    
        # Merge other fields
        merged["applications"] = list(set(merged.get("applications", []) + new.get("applications", [])))
        merged["standards"] = list(set(merged.get("standards", []) + new.get("standards", [])))
        
        return merged
    else:
        logger.info(f"  ⚠️ Keeping {existing_source} over {new_source} (higher priority)")
        return existing

def main():
    """Rebuild the unified alloy standards database"""
    logger.info("🚀 Rebuilding unified alloy standards database")
    
    # Define source files and their priorities
    source_files = [
        (Path("app/data/legacy/legacy_alloy_standards.json"), "Original_Database"),
        (Path("app/data/legacy/legacy_alloy_standards_basic.json"), "Basic_Database"),
        (Path("app/data/legacy/legacy_alloy_standards_extended.json"), "Extended_Database")
    ]
    
    unified_data = {}
    all_categories = set()
    total_alloys = 0
    
    # Process each source file
    for file_path, source_name in source_files:
        if not file_path.exists():
            logger.warning(f"⚠️ File not found: {file_path}")
            continue
            
        legacy_data, source = load_legacy_file(file_path, source_name)
        
        for category, alloys in legacy_data.items():
            all_categories.add(category)
            
            # Standardize category names
            standardized_category = category.lower().replace("_", "_")
            
            if standardized_category not in unified_data:
                unified_data[standardized_category] = {}
            
            for alloy_code, alloy_data in alloys.items():
                # Convert to unified format
                unified_alloy = convert_to_unified_format(standardized_category, alloy_code, alloy_data, source)
                
                # Handle duplicates
                if alloy_code in unified_data[standardized_category]:
                    logger.info(f"🔍 Duplicate found: {alloy_code} in {standardized_category}")
                    existing = unified_data[standardized_category][alloy_code]
                    existing_source = existing.get("source", "Unknown")
                    
                    unified_data[standardized_category][alloy_code] = resolve_conflicts(
                        existing, unified_alloy, existing_source, source
                    )
                else:
                    unified_data[standardized_category][alloy_code] = unified_alloy
                    total_alloys += 1
    
    # Add metadata
    metadata = {
        "_metadata": {
            "version": "2.0.0",
            "unified": True,
            "rebuild_date": "2025-11-12",
            "sources": {
                "Original_Database": "legacy_alloy_standards.json (92 alloys, 7 categories)",
                "Basic_Database": "legacy_alloy_standards_basic.json (22 alloys, 9 categories)", 
                "Extended_Database": "legacy_alloy_standards_extended.json (73 alloys, 13 categories)",
                "NIST": "NIST Chemistry WebBook",
                "Materials_Project": "Materials Project Database",
                "MatWeb": "MatWeb Database"
            },
            "property_sources": {
                "Original_Database": "Original alloy standards compilation",
                "Basic_Database": "Basic database compilation",
                "Extended_Database": "Extended database with additional alloys", 
                "ASTM_Standards": "Industry standard values",
                "NIST": "NIST experimental data",
                "Materials_Project": "DFT calculations",
                "MatWeb": "Engineering database"
            },
            "temperature_dependent_flags": {
                "thermal_conductivity": True,
                "specific_heat": True,
                "density": True,
                "dynamic_viscosity": True,
                "electrical_resistivity": True,
                "coefficient_of_thermal_expansion": True
            },
            "total_alloys": total_alloys,
            "total_categories": len(unified_data),
            "categories": list(unified_data.keys()),
            "rebuild_notes": "Comprehensive rebuild from all legacy sources with conflict resolution and source tracking"
        }
    }
    
    # Combine data and metadata
    final_data = {**unified_data, **metadata}
    
    # Write to file
    output_path = Path("app/data/alloy_standards_rebuilt.json")
    with open(output_path, 'w') as f:
        json.dump(final_data, f, indent=2)
    
    logger.info(f"🎉 Rebuilt unified database:")
    logger.info(f"   📊 {len(unified_data)} categories")
    logger.info(f"   🔧 {total_alloys} total alloys")
    logger.info(f"   📁 Categories: {', '.join(unified_data.keys())}")
    logger.info(f"   💾 Saved to: {output_path}")
    
    # Summary by category
    logger.info(f"\n📋 Category breakdown:")
    for category, alloys in unified_data.items():
        logger.info(f"   {category}: {len(alloys)} alloys")

if __name__ == "__main__":
    main()