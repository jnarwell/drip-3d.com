"""Service for managing alloy standards and cross-referencing with Materials Project data"""

import json
import os
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from .nist_webbook import nist_service

logger = logging.getLogger(__name__)

class AlloyStandardsService:
    """Manages alloy standards data and cross-references with Materials Project"""
    
    def __init__(self):
        # Load standards database
        self.standards_data = self._load_standards_database()
        self.alloy_index = self._build_alloy_index()
        
    def _load_standards_database(self) -> Dict[str, Any]:
        """Load the unified alloy standards JSON database"""
        try:
            # Load main alloy standards database
            main_path = Path(__file__).parent.parent / "data" / "alloy_standards.json"
            
            if main_path.exists():
                with open(main_path, 'r') as f:
                    data = json.load(f)
                    
                # Check if this is the unified format by looking for _metadata
                if "_metadata" in data and data["_metadata"].get("unified"):
                    # Extract alloy data (exclude metadata)
                    alloy_data = {k: v for k, v in data.items() if not k.startswith("_")}
                
                    # Convert new structure to backward-compatible format
                    converted_data = self._convert_unified_format(alloy_data)
                    
                    total_alloys = sum(len(alloys) for alloys in converted_data.values())
                    logger.info(f"Loaded unified alloy standards for {len(converted_data)} material categories with {total_alloys} alloys")
                    return converted_data
                else:
                    # Legacy format, load as before
                    logger.info("Loading legacy alloy standards format")
                    return self._load_legacy_format(data)
                
            # Fallback to legacy databases if main file doesn't exist
            else:
                logger.warning("Main alloy standards file not found, falling back to legacy databases")
                return self._load_legacy_databases()
                
        except Exception as e:
            logger.error(f"Error loading unified alloy standards database: {e}")
            return self._load_legacy_databases()
    
    def _build_alloy_index(self) -> Dict[str, Dict[str, Any]]:
        """Build a searchable index of all alloys"""
        index = {}
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                # Add main alloy code
                index[alloy_code.lower()] = {
                    "category": category,
                    "code": alloy_code,
                    "data": alloy_data
                }
                
                # Add common name variations
                common_name = alloy_data.get("common_name", "")
                if common_name:
                    # Index by simplified common name
                    simplified = common_name.lower().replace(" ", "").replace("-", "")
                    index[simplified] = {
                        "category": category,
                        "code": alloy_code,
                        "data": alloy_data
                    }
                    
                # Add UNS number if available
                uns = alloy_data.get("uns", "")
                if uns:
                    index[uns.lower()] = {
                        "category": category,
                        "code": alloy_code,
                        "data": alloy_data
                    }
        
        logger.info(f"Built alloy index with {len(index)} entries")
        return index
    
    def get_alloy_standard(self, alloy_name: str) -> Optional[Dict[str, Any]]:
        """Get standard data for an alloy by name/code"""
        # Try exact match first
        search_key = alloy_name.lower().strip()
        result = None
        
        if search_key in self.alloy_index:
            result = self.alloy_index[search_key]["data"].copy()
            
        # Try without spaces/hyphens
        elif search_key.replace(" ", "").replace("-", "") in self.alloy_index:
            simplified = search_key.replace(" ", "").replace("-", "")
            result = self.alloy_index[simplified]["data"].copy()
            
        # Try partial matches (e.g., "6061" might match "6061-T6")
        # But avoid single letter matches unless exact
        else:
            for key, value in self.alloy_index.items():
                # Skip single letter partial matches
                if len(search_key) == 1:
                    continue
                if search_key in key or key in search_key:
                    result = value["data"].copy()
                    break
        
        # Add composition formula if we found a result
        if result and "composition" in result:
            result["composition_formula"] = self._generate_composition_formula(result["composition"])
                    
        return result
    
    def get_alloy_standard_with_category(self, alloy_name: str) -> Optional[Dict[str, Any]]:
        """Get standard data for an alloy by name/code, including category information"""
        search_key = alloy_name.lower().strip()
        
        # Try exact match first
        if search_key in self.alloy_index:
            entry = self.alloy_index[search_key]
            result = entry["data"].copy()
            result["_category"] = entry["category"]
            result["_alloy_code"] = entry["code"]
            
        # Try without spaces/hyphens
        elif search_key.replace(" ", "").replace("-", "") in self.alloy_index:
            simplified = search_key.replace(" ", "").replace("-", "")
            entry = self.alloy_index[simplified]
            result = entry["data"].copy()
            result["_category"] = entry["category"]
            result["_alloy_code"] = entry["code"]
            
        # Try partial matches
        else:
            result = None
            for key, value in self.alloy_index.items():
                if len(search_key) == 1:
                    continue
                if search_key in key or key in search_key:
                    result = value["data"].copy()
                    result["_category"] = value["category"]
                    result["_alloy_code"] = value["code"]
                    break
        
        # Add composition formula if we found a result
        if result and "composition" in result:
            result["composition_formula"] = self._generate_composition_formula(result["composition"])
                    
        return result
    
    def _generate_composition_formula(self, composition: Dict[str, str]) -> str:
        """Generate a formula-like string from composition data"""
        # Get main elements (> 1%)
        main_elements = []
        for element, percentage in composition.items():
            if element == "balance" or element in ["Fe", "Al", "Cu", "Ti", "Ni", "Mg"]:
                # Parse percentage ranges
                if "-" in str(percentage):
                    try:
                        low, high = percentage.split("-")
                        avg = (float(low) + float(high)) / 2
                        if avg > 1.0 or element == percentage:  # Major element
                            main_elements.append(element)
                    except:
                        if element != "balance":
                            main_elements.append(element)
                elif percentage == "balance":
                    main_elements.insert(0, element)  # Put balance element first
                else:
                    try:
                        if float(percentage.replace(" max", "").replace(" min", "")) > 1.0:
                            main_elements.append(element)
                    except:
                        pass
        
        # Create formula (like Al-Mg-Si for 6061)
        return "-".join(main_elements) if main_elements else ""
    
    def enhance_material_with_standards(self, material: Dict[str, Any], include_nist_data: bool = True) -> Dict[str, Any]:
        """Enhance Materials Project material data with standards information and NIST data"""
        enhanced = material.copy()
        
        # Try to find matching standard data
        common_name = material.get("common_name", "")
        if common_name:
            # Extract alloy code from common name (e.g., "316 Stainless Steel" -> "316")
            parts = common_name.split()
            for part in parts:
                standard_data = self.get_alloy_standard(part)
                if standard_data:
                    enhanced["standard_data"] = standard_data
                    enhanced["has_standard"] = True
                    
                    # Add mechanical properties not in Materials Project
                    if "mechanical" in standard_data:
                        enhanced["mechanical_properties"] = standard_data["mechanical"]
                        
                    # Add thermal properties
                    if "thermal" in standard_data:
                        enhanced["thermal_properties"] = standard_data["thermal"]
                        
                    # Add applications
                    if "applications" in standard_data:
                        enhanced["applications"] = standard_data["applications"]
                        
                    # Add standards references
                    if "standards" in standard_data:
                        enhanced["standards"] = standard_data["standards"]
                    
                    # Enhance with NIST temperature-dependent data (TEMPORARILY DISABLED)
                    if include_nist_data:
                        try:
                            # DISABLED: NIST API calls causing timeouts in search
                            # enhanced_with_nist = nist_service.enhance_alloy_with_nist_data(standard_data)
                            # if enhanced_with_nist.get('nist_enhanced'):
                            #     enhanced["temperature_dependent_properties"] = enhanced_with_nist["temperature_dependent_properties"]
                            #     enhanced["nist_enhanced"] = True
                            #     logger.info(f"✅ Enhanced {common_name} with NIST temperature-dependent data")
                            pass  # Skip NIST enhancement for now
                        except Exception as e:
                            logger.warning(f"Could not enhance {common_name} with NIST data: {e}")
                        
                    break
        
        return enhanced
    
    def compare_with_mp_data(self, mp_material: Dict[str, Any], standard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare Materials Project data with standard values"""
        comparison = {
            "material_id": mp_material.get("mp_id"),
            "common_name": mp_material.get("common_name"),
            "matches": [],
            "discrepancies": [],
            "additional_from_standards": []
        }
        
        # Compare density
        if mp_material.get("density") and standard_data.get("mechanical", {}).get("density"):
            mp_density = mp_material["density"]
            std_density = standard_data["mechanical"]["density"]
            diff_percent = abs((mp_density - std_density) / std_density * 100)
            
            if diff_percent < 2:  # Within 2% tolerance
                comparison["matches"].append({
                    "property": "density",
                    "mp_value": mp_density,
                    "standard_value": std_density,
                    "unit": "g/cm³",
                    "difference": f"{diff_percent:.1f}%"
                })
            else:
                comparison["discrepancies"].append({
                    "property": "density",
                    "mp_value": mp_density,
                    "standard_value": std_density,
                    "unit": "g/cm³",
                    "difference": f"{diff_percent:.1f}%"
                })
        
        # Compare elastic moduli if available
        if mp_material.get("elastic_moduli") and standard_data.get("mechanical"):
            mp_elastic = mp_material["elastic_moduli"]
            std_mech = standard_data["mechanical"]
            
            # Young's modulus
            if mp_elastic.get("youngs_modulus") and std_mech.get("youngs_modulus"):
                mp_E = mp_elastic["youngs_modulus"]
                std_E = std_mech["youngs_modulus"]
                diff_percent = abs((mp_E - std_E) / std_E * 100)
                
                if diff_percent < 10:  # Within 10% tolerance for elastic properties
                    comparison["matches"].append({
                        "property": "youngs_modulus",
                        "mp_value": mp_E,
                        "standard_value": std_E,
                        "unit": "GPa",
                        "difference": f"{diff_percent:.1f}%"
                    })
                else:
                    comparison["discrepancies"].append({
                        "property": "youngs_modulus",
                        "mp_value": mp_E,
                        "standard_value": std_E,
                        "unit": "GPa",
                        "difference": f"{diff_percent:.1f}%"
                    })
            
            # Poisson's ratio
            if mp_elastic.get("poisson_ratio") and std_mech.get("poisson_ratio"):
                mp_nu = mp_elastic["poisson_ratio"]
                std_nu = std_mech["poisson_ratio"]
                diff = abs(mp_nu - std_nu)
                
                if diff < 0.02:  # Within 0.02 absolute tolerance
                    comparison["matches"].append({
                        "property": "poisson_ratio",
                        "mp_value": mp_nu,
                        "standard_value": std_nu,
                        "unit": "",
                        "difference": f"{diff:.3f}"
                    })
                else:
                    comparison["discrepancies"].append({
                        "property": "poisson_ratio",
                        "mp_value": mp_nu,
                        "standard_value": std_nu,
                        "unit": "",
                        "difference": f"{diff:.3f}"
                    })
        
        # Add properties only in standards (not in Materials Project)
        if standard_data.get("mechanical"):
            std_mech = standard_data["mechanical"]
            
            # Yield strength
            if std_mech.get("yield_strength"):
                comparison["additional_from_standards"].append({
                    "property": "yield_strength",
                    "value": std_mech["yield_strength"],
                    "unit": "MPa",
                    "source": "Industry Standard"
                })
            
            # UTS
            if std_mech.get("ultimate_tensile_strength"):
                comparison["additional_from_standards"].append({
                    "property": "ultimate_tensile_strength",
                    "value": std_mech["ultimate_tensile_strength"],
                    "unit": "MPa",
                    "source": "Industry Standard"
                })
            
            # Hardness
            if std_mech.get("brinell_hardness"):
                comparison["additional_from_standards"].append({
                    "property": "brinell_hardness",
                    "value": std_mech["brinell_hardness"],
                    "unit": "HB",
                    "source": "Industry Standard"
                })
        
        # Add thermal properties if available
        if standard_data.get("thermal"):
            std_thermal = standard_data["thermal"]
            
            if std_thermal.get("melting_point"):
                comparison["additional_from_standards"].append({
                    "property": "melting_point",
                    "value": std_thermal["melting_point"],
                    "unit": "°C",
                    "source": "Industry Standard"
                })
            
            if std_thermal.get("thermal_conductivity"):
                comparison["additional_from_standards"].append({
                    "property": "thermal_conductivity",
                    "value": std_thermal["thermal_conductivity"],
                    "unit": "W/m·K",
                    "source": "Industry Standard"
                })
        
        return comparison
    
    def search_by_standard(self, standard: str) -> List[Dict[str, Any]]:
        """Search for alloys by standard specification (e.g., ASTM B209)"""
        results = []
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                standards = alloy_data.get("standards", [])
                if any(standard.upper() in std.upper() for std in standards):
                    results.append({
                        "category": category,
                        "alloy_code": alloy_code,
                        "common_name": alloy_data.get("common_name"),
                        "standards": standards,
                        "data": alloy_data
                    })
        
        return results
    
    def search_by_property_range(self, property_path: str, min_val: float, max_val: float) -> List[Dict[str, Any]]:
        """Search for alloys within a property range"""
        results = []
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                # Navigate property path (e.g., "mechanical.yield_strength")
                parts = property_path.split(".")
                value = alloy_data
                
                try:
                    for part in parts:
                        value = value.get(part)
                        if value is None:
                            break
                    
                    if value is not None and min_val <= value <= max_val:
                        results.append({
                            "category": category,
                            "alloy_code": alloy_code,
                            "common_name": alloy_data.get("common_name"),
                            "property_value": value,
                            "data": alloy_data
                        })
                except:
                    continue
        
        return sorted(results, key=lambda x: x["property_value"])
    
    def _convert_unified_format(self, unified_data: Dict[str, Any]) -> Dict[str, Any]:
        """Convert unified format to backward-compatible format"""
        converted = {}
        
        for category, alloys in unified_data.items():
            converted[category] = {}
            
            for alloy_code, alloy_data in alloys.items():
                # Convert unified structure back to old format for compatibility
                old_format = {
                    "common_name": alloy_data.get("common_name"),
                    "uns": alloy_data.get("uns"),
                    "composition": alloy_data.get("composition", {}),
                    "applications": alloy_data.get("applications", []),
                    "standards": alloy_data.get("standards", []),
                    "source": alloy_data.get("source", "Unknown")
                }
                
                # Convert properties structure
                properties = alloy_data.get("properties", {})
                
                # Extract mechanical properties
                if "mechanical" in properties:
                    old_format["mechanical"] = {}
                    for prop_name, prop_data in properties["mechanical"].items():
                        if isinstance(prop_data, dict) and "value" in prop_data:
                            old_format["mechanical"][prop_name] = prop_data["value"]
                        else:
                            old_format["mechanical"][prop_name] = prop_data
                            
                # Extract thermal properties
                if "thermal" in properties:
                    old_format["thermal"] = {}
                    for prop_name, prop_data in properties["thermal"].items():
                        if isinstance(prop_data, dict) and "value" in prop_data:
                            old_format["thermal"][prop_name] = prop_data["value"]
                        else:
                            old_format["thermal"][prop_name] = prop_data
                            
                # Extract acoustic properties if available
                if "acoustic" in properties:
                    old_format["acoustic"] = {}
                    for prop_name, prop_data in properties["acoustic"].items():
                        if isinstance(prop_data, dict) and "value" in prop_data:
                            old_format["acoustic"][prop_name] = prop_data["value"]
                        else:
                            old_format["acoustic"][prop_name] = prop_data
                            
                # Add source tracking metadata
                old_format["_property_sources"] = self._extract_property_sources(properties)
                old_format["_temperature_dependent"] = self._extract_temperature_flags(properties)
                
                # Generate composition formula if missing
                if "composition" in old_format and "composition_formula" not in old_format:
                    old_format["composition_formula"] = self._generate_composition_formula(old_format["composition"])
                    
                converted[category][alloy_code] = old_format
                
        return converted
    
    def _extract_property_sources(self, properties: Dict[str, Any]) -> Dict[str, str]:
        """Extract source information for each property"""
        sources = {}
        for category, props in properties.items():
            for prop_name, prop_data in props.items():
                if isinstance(prop_data, dict) and "source" in prop_data:
                    sources[f"{category}.{prop_name}"] = prop_data["source"]
        return sources
    
    def _extract_temperature_flags(self, properties: Dict[str, Any]) -> Dict[str, bool]:
        """Extract temperature dependency flags for each property"""
        temp_flags = {}
        for category, props in properties.items():
            for prop_name, prop_data in props.items():
                if isinstance(prop_data, dict) and "temperature_dependent" in prop_data:
                    temp_flags[f"{category}.{prop_name}"] = prop_data["temperature_dependent"]
        return temp_flags
    
    def _load_legacy_databases(self) -> Dict[str, Any]:
        """Load legacy databases as fallback"""
        try:
            data = {}
            
            # Load databases in order of priority
            database_files = [
                "alloy_standards.json",
                "alloy_standards_basic.json", 
                "alloy_standards_extended.json"
            ]
            
            for db_file in database_files:
                data_path = Path(__file__).parent.parent / "data" / db_file
                
                if data_path.exists():
                    with open(data_path, 'r') as f:
                        db_data = json.load(f)
                        # Merge categories
                        for category, alloys in db_data.items():
                            if category not in data:
                                data[category] = {}
                            # Merge alloys within category
                            for alloy_code, alloy_data in alloys.items():
                                # Extended database takes priority over basic
                                if alloy_code not in data[category] or db_file == "alloy_standards_extended.json":
                                    # Generate composition formula if missing
                                    if "composition" in alloy_data and "composition_formula" not in alloy_data:
                                        alloy_data["composition_formula"] = self._generate_composition_formula(alloy_data["composition"])
                                    alloy_data["_source_database"] = db_file
                                    data[category][alloy_code] = alloy_data
                                    
            total_alloys = sum(len(alloys) for alloys in data.values())
            logger.info(f"Loaded legacy alloy standards for {len(data)} material categories with {total_alloys} alloys")
            return data
        except Exception as e:
            logger.error(f"Error loading legacy alloy standards database: {e}")
            return {}
    
    def _load_legacy_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Load data that's already in legacy format"""
        for category, alloys in data.items():
            for alloy_code, alloy_data in alloys.items():
                # Generate composition formula if missing
                if "composition" in alloy_data and "composition_formula" not in alloy_data:
                    alloy_data["composition_formula"] = self._generate_composition_formula(alloy_data["composition"])
                alloy_data["_source_database"] = "alloy_standards.json"
                
        total_alloys = sum(len(alloys) for alloys in data.values())
        logger.info(f"Loaded legacy alloy standards for {len(data)} material categories with {total_alloys} alloys")
        return data
    
    def get_alloys_by_application(self, application_keyword: str) -> List[Dict[str, Any]]:
        """Find alloys used for specific applications"""
        results = []
        keyword_lower = application_keyword.lower()
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                applications = alloy_data.get("applications", [])
                if any(keyword_lower in app.lower() for app in applications):
                    results.append({
                        "category": category,
                        "alloy_code": alloy_code,
                        "common_name": alloy_data.get("common_name"),
                        "applications": applications,
                        "data": alloy_data
                    })
        
        return results
    
    def get_casting_alloys(self) -> List[Dict[str, Any]]:
        """Get all alloys suitable for casting"""
        results = []
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                # Check if marked as casting alloy
                if alloy_data.get("casting", False):
                    results.append({
                        "category": category,
                        "alloy_code": alloy_code,
                        "common_name": alloy_data.get("common_name"),
                        "solidus": alloy_data.get("thermal", {}).get("solidus"),
                        "liquidus": alloy_data.get("thermal", {}).get("liquidus"),
                        "data": alloy_data
                    })
                # Also check if it's an aluminum casting alloy (A356, etc.)
                elif category == "aluminum" and ("cast" in alloy_data.get("common_name", "").lower() or 
                                                 alloy_code.lower().startswith("a")):
                    results.append({
                        "category": category,
                        "alloy_code": alloy_code,
                        "common_name": alloy_data.get("common_name"),
                        "solidus": alloy_data.get("thermal", {}).get("solidus"),
                        "liquidus": alloy_data.get("thermal", {}).get("liquidus"),
                        "data": alloy_data
                    })
        
        return results
    
    def get_enhanced_alloy_data(self, alloy_name: str, include_nist_data: bool = True) -> Optional[Dict[str, Any]]:
        """Get alloy data enhanced with NIST temperature-dependent properties"""
        standard_data = self.get_alloy_standard(alloy_name)
        if not standard_data:
            return None
            
        enhanced = standard_data.copy()
        
        # Enhance with NIST data if requested (TEMPORARILY DISABLED)
        if include_nist_data:
            try:
                # DISABLED: NIST API calls causing timeouts
                # enhanced_with_nist = nist_service.enhance_alloy_with_nist_data(standard_data)
                # if enhanced_with_nist.get('nist_enhanced'):
                #     enhanced.update(enhanced_with_nist)
                #     logger.info(f"✅ Enhanced {alloy_name} with NIST data")
                pass  # Skip NIST enhancement
            except Exception as e:
                logger.warning(f"Could not enhance {alloy_name} with NIST data: {e}")
        
        return enhanced
    
    def get_property_at_temperature(self, alloy_name: str, property_name: str, temperature: float) -> Optional[float]:
        """Get a specific property value at a given temperature for an alloy"""
        enhanced_data = self.get_enhanced_alloy_data(alloy_name, include_nist_data=True)
        if not enhanced_data:
            return None
            
        # Check if we have temperature-dependent data
        temp_props = enhanced_data.get('temperature_dependent_properties', {})
        if property_name in temp_props:
            prop_data = temp_props[property_name]
            values = prop_data.get('values', [])
            
            if not values:
                return None
            
            # Linear interpolation between data points
            values.sort(key=lambda x: x[0])  # Sort by temperature
            
            # Check bounds
            if temperature < values[0][0] or temperature > values[-1][0]:
                logger.warning(f"Temperature {temperature} outside valid range for {property_name}")
                return None
            
            # Find interpolation points
            for i in range(len(values) - 1):
                t1, v1 = values[i]
                t2, v2 = values[i + 1]
                
                if t1 <= temperature <= t2:
                    # Linear interpolation
                    if t1 == t2:
                        return v1
                    return v1 + (v2 - v1) * (temperature - t1) / (t2 - t1)
            
        # Fallback to static property if available
        static_props = enhanced_data.get('thermal', {}) if 'thermal' in property_name else enhanced_data.get('mechanical', {})
        if static_props and property_name.replace('_', ' ') in static_props:
            return static_props[property_name.replace('_', ' ')]
            
        return None
    
    def generate_temperature_curve(self, alloy_name: str, property_name: str, 
                                 temp_min: float = 273, temp_max: float = 1273, 
                                 num_points: int = 50) -> Optional[List[Tuple[float, float]]]:
        """Generate temperature curve for a property across a temperature range"""
        enhanced_data = self.get_enhanced_alloy_data(alloy_name, include_nist_data=True)
        if not enhanced_data:
            return None
            
        temp_props = enhanced_data.get('temperature_dependent_properties', {})
        if property_name not in temp_props:
            logger.info(f"No temperature-dependent data for {property_name} in {alloy_name}")
            return None
            
        # Generate points across the temperature range
        temp_step = (temp_max - temp_min) / (num_points - 1)
        curve_points = []
        
        for i in range(num_points):
            temp = temp_min + i * temp_step
            value = self.get_property_at_temperature(alloy_name, property_name, temp)
            if value is not None:
                curve_points.append((temp, value))
        
        return curve_points if curve_points else None
    
    def bulk_enhance_alloys_with_nist(self, material_categories: Optional[List[str]] = None) -> Dict[str, Any]:
        """Bulk enhance multiple alloys with NIST data"""
        logger.info("🚀 Starting bulk enhancement of alloys with NIST data")
        
        results = {
            'enhanced': [],
            'failed': [],
            'skipped': [],
            'total_processed': 0
        }
        
        categories_to_process = material_categories or list(self.standards_data.keys())
        
        for category in categories_to_process:
            if category not in self.standards_data:
                continue
                
            logger.info(f"📂 Processing category: {category}")
            
            for alloy_code, alloy_data in self.standards_data[category].items():
                results['total_processed'] += 1
                
                try:
                    # DISABLED: NIST API calls causing timeouts
                    # enhanced = nist_service.enhance_alloy_with_nist_data(alloy_data)
                    # if enhanced.get('nist_enhanced'):
                    #     results['enhanced'].append({
                    #         'category': category,
                    #         'alloy_code': alloy_code,
                    #         'common_name': alloy_data.get('common_name'),
                    #         'properties_added': list(enhanced.get('temperature_dependent_properties', {}).keys())
                    #     })
                    #     logger.info(f"✅ Enhanced {alloy_code}")
                    # else:
                    results['skipped'].append({
                        'category': category,
                        'alloy_code': alloy_code,
                        'reason': 'NIST enhancement temporarily disabled'
                    })
                        
                except Exception as e:
                    results['failed'].append({
                        'category': category,
                        'alloy_code': alloy_code,
                        'error': str(e)
                    })
                    logger.error(f"❌ Failed to enhance {alloy_code}: {e}")
        
        logger.info(f"🎉 Bulk enhancement complete: {len(results['enhanced'])} enhanced, "
                   f"{len(results['failed'])} failed, {len(results['skipped'])} skipped")
        
        return results
    
    def get_property_source_info(self, alloy_name: str) -> Optional[Dict[str, Any]]:
        """Get source and temperature dependency information for an alloy's properties"""
        alloy_data = self.get_alloy_standard(alloy_name)
        if not alloy_data:
            return None
            
        return {
            "alloy_name": alloy_name,
            "database_source": alloy_data.get("source", alloy_data.get("_source_database", "Unknown")),
            "property_sources": alloy_data.get("_property_sources", {}),
            "temperature_dependent_properties": alloy_data.get("_temperature_dependent", {}),
            "available_properties": {
                "mechanical": list(alloy_data.get("mechanical", {}).keys()),
                "thermal": list(alloy_data.get("thermal", {}).keys()),
                "acoustic": list(alloy_data.get("acoustic", {}).keys())
            }
        }
    
    def get_all_sources_summary(self) -> Dict[str, Any]:
        """Get summary of all data sources used in the database"""
        sources = set()
        property_sources = set()
        temp_dependent_count = 0
        total_properties = 0
        
        for category, alloys in self.standards_data.items():
            for alloy_code, alloy_data in alloys.items():
                # Database sources
                if "source" in alloy_data:
                    sources.add(alloy_data["source"])
                if "_source_database" in alloy_data:
                    sources.add(alloy_data["_source_database"])
                    
                # Property sources
                prop_sources = alloy_data.get("_property_sources", {})
                property_sources.update(prop_sources.values())
                
                # Temperature dependency
                temp_flags = alloy_data.get("_temperature_dependent", {})
                temp_dependent_count += sum(temp_flags.values())
                total_properties += len(temp_flags)
                
        return {
            "database_sources": list(sources),
            "property_sources": list(property_sources), 
            "total_alloys": sum(len(alloys) for alloys in self.standards_data.values()),
            "total_properties": total_properties,
            "temperature_dependent_properties": temp_dependent_count,
            "categories": list(self.standards_data.keys())
        }