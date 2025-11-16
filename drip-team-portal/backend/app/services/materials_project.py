from typing import List, Dict, Any, Optional, Tuple
import logging
import json
from datetime import datetime
import os
import httpx
from httpx import AsyncClient
from app.services.alloy_standards import AlloyStandardsService

logger = logging.getLogger(__name__)

class MaterialsProjectService:
    """Service for interacting with Materials Project REST API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("MATERIALS_PROJECT_API_KEY", "x62KSbRt3GD3mX9zYJYurJs0MjLdc4qx")
        # Use the new Materials Project API endpoint
        self.base_url = "https://api.materialsproject.org"
        self.headers = {
            "X-API-KEY": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json"
        }
        
        # Initialize alloy standards service
        self.standards_service = AlloyStandardsService()
        
        # Common material name mappings (expanded for engineering alloys)
        self.material_mappings = {
            # Stainless steels (300 series - Austenitic)
            "stainless steel 304": "Fe-Cr-Ni",
            "ss304": "Fe-Cr-Ni",
            "304": "Fe-Cr-Ni",
            "304l": "Fe-Cr-Ni",
            "stainless steel 316": "Fe-Cr-Ni-Mo",
            "ss316": "Fe-Cr-Ni-Mo", 
            "316": "Fe-Cr-Ni-Mo",
            "316l": "Fe-Cr-Ni-Mo",
            "321": "Fe-Cr-Ni-Ti",
            "347": "Fe-Cr-Ni-Nb",
            
            # Stainless steels (400 series - Ferritic/Martensitic)
            "410": "Fe-Cr",
            "416": "Fe-Cr-S",
            "420": "Fe-Cr-C",
            "430": "Fe-Cr",
            "440c": "Fe-Cr-C",
            
            # Tool steels
            "d2": "Fe-Cr-Mo-V-C",
            "a2": "Fe-Cr-Mo-C",
            "o1": "Fe-Mn-Cr-W-C",
            "h13": "Fe-Cr-Mo-Si-V",
            
            # Aluminum alloys (Wrought)
            "aluminum 1100": "Al",
            "1100": "Al",
            "aluminum 2024": "Al-Cu-Mg",
            "2024": "Al-Cu-Mg",
            "aluminum 3003": "Al-Mn",
            "3003": "Al-Mn",
            "aluminum 5052": "Al-Mg",
            "5052": "Al-Mg",
            "aluminum 6061": "Al-Mg-Si",
            "6061": "Al-Mg-Si",
            "6061-t6": "Al-Mg-Si",
            "aluminum 6063": "Al-Mg-Si",
            "6063": "Al-Mg-Si",
            "aluminum 7075": "Al-Zn-Mg-Cu",
            "7075": "Al-Zn-Mg-Cu",
            "7075-t6": "Al-Zn-Mg-Cu",
            "7071": "Al-Zn-Mg-Cu",  # Common typo/variation for 7075
            
            # Aluminum casting alloys
            "a356": "Al-Si-Mg",
            "356": "Al-Si-Mg",
            "a380": "Al-Si-Cu",
            "380": "Al-Si-Cu",
            "413": "Al-Si",
            "319": "Al-Si-Cu",
            
            # Titanium alloys
            "titanium grade 1": "Ti",
            "titanium grade 2": "Ti",
            "cp titanium": "Ti",
            "titanium grade 5": "Ti-Al-V",
            "ti6al4v": "Ti-Al-V",
            "ti-6al-4v": "Ti-Al-V",
            "ti-6-4": "Ti-Al-V",
            "ti6242": "Ti-Al-Sn-Zr-Mo",
            "ti-6-2-4-2": "Ti-Al-Sn-Zr-Mo",
            
            # Nickel alloys
            "inconel 625": "Ni-Cr-Mo-Nb",
            "625": "Ni-Cr-Mo-Nb",
            "inconel 718": "Ni-Cr-Fe-Nb-Mo",
            "718": "Ni-Cr-Fe-Nb-Mo",
            "hastelloy c276": "Ni-Mo-Cr-W",
            "c276": "Ni-Mo-Cr-W",
            "monel 400": "Ni-Cu",
            "monel": "Ni-Cu",
            
            # Copper alloys
            "brass": "Cu-Zn",
            "260 brass": "Cu-Zn",
            "360 brass": "Cu-Zn-Pb",
            "bronze": "Cu-Sn",
            "phosphor bronze": "Cu-Sn-P",
            "aluminum bronze": "Cu-Al",
            "beryllium copper": "Cu-Be",
            "c17200": "Cu-Be",
            
            # Magnesium alloys
            "az31b": "Mg-Al-Zn",
            "az91d": "Mg-Al-Zn",
            "am60b": "Mg-Al-Mn",
            
            # Common/generic
            "steel": "Fe-C",
            "carbon steel": "Fe-C",
            "mild steel": "Fe-C",
            "cast iron": "Fe-C-Si",
            "copper": "Cu",
            "aluminum": "Al",
            "titanium": "Ti",
            "nickel": "Ni",
            "zinc": "Zn",
            "magnesium": "Mg",
            
            # Additional aluminum alloys with tempers
            "1100-o": "Al",
            "1100-h14": "Al",
            "2024-t3": "Al-Cu-Mg",
            "2024-t4": "Al-Cu-Mg",
            "3003-h14": "Al-Mn",
            "5052-h32": "Al-Mg",
            "5083-h116": "Al-Mg-Mn",
            "5086-h32": "Al-Mg-Mn",
            "6061-o": "Al-Mg-Si",
            "6061-t4": "Al-Mg-Si",
            "6061-t651": "Al-Mg-Si",
            "6063-t5": "Al-Mg-Si",
            "6063-t6": "Al-Mg-Si",
            "7075-o": "Al-Zn-Mg-Cu",
            "7075-t651": "Al-Zn-Mg-Cu",
            "7178-t6": "Al-Zn-Mg-Cu",
            "2219-t87": "Al-Cu",
            "a357-t6": "Al-Si-Mg",
            
            # Additional stainless steels
            "304l": "Fe-Cr-Ni",
            "316nb": "Fe-Cr-Ni-Mo-Nb",
            "17-4ph": "Fe-Cr-Ni-Cu",
            "17-4": "Fe-Cr-Ni-Cu",
            "15-5ph": "Fe-Cr-Ni-Cu",
            "15-5": "Fe-Cr-Ni-Cu",
            "2205": "Fe-Cr-Ni-Mo-N",
            "2507": "Fe-Cr-Ni-Mo-N",
            "904l": "Fe-Ni-Cr-Mo-Cu",
            
            # Additional titanium alloys
            "ti-6al-4v-eli": "Ti-Al-V",
            "grade 23": "Ti-Al-V",
            "grade 1": "Ti",
            "grade 3": "Ti",
            "grade 4": "Ti",
            "ti-6-2-4-2": "Ti-Al-Sn-Zr-Mo",
            "ti-6-2-4-6": "Ti-Al-Sn-Zr-Mo",
            "ti-15-3-3-3": "Ti-V-Cr-Al-Sn",
            "ti-10-2-3": "Ti-V-Fe-Al",
            "ti-5553": "Ti-Al-Mo-V-Cr",
            
            # Nickel alloys
            "inconel 600": "Ni-Cr-Fe",
            "inconel 625": "Ni-Cr-Mo-Nb",
            "inconel 718": "Ni-Cr-Fe-Nb-Mo",
            "inconel x-750": "Ni-Cr-Fe-Ti-Al",
            "x750": "Ni-Cr-Fe-Ti-Al",
            "hastelloy c-276": "Ni-Mo-Cr-W",
            "hastelloy x": "Ni-Cr-Fe-Mo-W",
            "monel 400": "Ni-Cu",
            "monel k-500": "Ni-Cu-Al-Ti",
            "k500": "Ni-Cu-Al-Ti",
            "incoloy 800": "Ni-Fe-Cr",
            "incoloy 825": "Ni-Fe-Cr-Mo-Cu",
            "waspaloy": "Ni-Cr-Co-Mo",
            "rene 41": "Ni-Cr-Co-Mo-Ti-Al",
            
            # Carbon and alloy steels  
            "1018": "Fe-C-Mn",
            "1020": "Fe-C-Mn",
            "1045": "Fe-C-Mn",
            "4130": "Fe-C-Cr-Mo",
            "4140": "Fe-C-Cr-Mo",
            "4340": "Fe-C-Ni-Cr-Mo",
            "8620": "Fe-C-Ni-Cr-Mo",
            "9310": "Fe-C-Ni-Cr-Mo",
            
            # Tool steels
            "a2": "Fe-C-Cr-Mo",
            "d2": "Fe-C-Cr-Mo-V",
            "m2": "Fe-C-W-Mo-V-Cr",
            "o1": "Fe-C-Mn-Cr-W",
            "h13": "Fe-C-Cr-Mo-V-Si",
            "s7": "Fe-C-Cr-Mo",
            "m4": "Fe-C-W-Mo-V-Cr",
            "p20": "Fe-C-Cr-Mo",
            
            # Copper alloys
            "c11000": "Cu",
            "c10200": "Cu",
            "c26000": "Cu-Zn",
            "cartridge brass": "Cu-Zn",
            "70/30 brass": "Cu-Zn",
            "c27000": "Cu-Zn",
            "65/35 brass": "Cu-Zn",
            "naval brass": "Cu-Zn-Sn",
            "c46400": "Cu-Zn-Sn",
            "phosphor bronze": "Cu-Sn-P",
            "c51000": "Cu-Sn-P",
            "c52100": "Cu-Sn-P",
            "aluminum bronze": "Cu-Al",
            "c61400": "Cu-Al-Fe",
            "c63000": "Cu-Al-Fe-Ni",
            "beryllium copper": "Cu-Be",
            "bercu": "Cu-Be",
            "c17200": "Cu-Be",
            "c17500": "Cu-Be-Co",
            "90/10 copper-nickel": "Cu-Ni",
            "c70600": "Cu-Ni",
            "70/30 copper-nickel": "Cu-Ni",
            "c71500": "Cu-Ni",
            "sae 660": "Cu-Sn-Pb-Zn",
            "c93200": "Cu-Sn-Pb-Zn",
            "c95400": "Cu-Al-Fe",
            
            # Refractory metals
            "tungsten": "W",
            "w": "W",
            "molybdenum": "Mo",
            "mo": "Mo",
            "tantalum": "Ta",
            "ta": "Ta",
            "niobium": "Nb",
            "nb": "Nb",
            "rhenium": "Re",
            "re": "Re"
        }
        
    def search_materials_summary(self, 
                               elements: List[str] = None,
                               formula: str = None,
                               material_ids: List[str] = None,
                               exclude_elements: List[str] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Search materials using the new Materials Project API"""
        try:
            # Build query parameters
            params = {}
            if formula:
                params["formula"] = formula
            elif elements:
                # Format: Al-Si or Al,Si
                logger.info(f"Searching with elements: {elements}")
                params["elements"] = ",".join(elements)
            if material_ids:
                params["material_ids"] = ",".join(material_ids)
            if exclude_elements:
                params["exclude_elements"] = ",".join(exclude_elements)
                
            # The new API requires fields in a different format
            # We need to request the full documents, not specific fields
            params["_limit"] = limit  # New API uses _limit instead of limit
            # Include all available fields to check for thermal properties
            params["_fields"] = "material_id,formula_pretty,density,formation_energy_per_atom,energy_above_hull,band_gap,is_stable,is_metal,volume,nsites,nelements,elements,chemsys,symmetry,thermal_expansion,debye,cp,specific_heat,melting_point,thermal_conductivity,bulk_modulus,shear_modulus,poisson_ratio,elastic_moduli,k_voigt,k_reuss,k_vrh,g_voigt,g_reuss,g_vrh"
            
            # Make request to summary endpoint
            response = httpx.get(
                f"{self.base_url}/materials/summary/",
                params=params,
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            data = response.json()
            
            # The new API returns data in 'data' field
            return data.get('data', [])
            
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error searching Materials Project: {e}")
            logger.error(f"Response: {e.response.text[:500]}")
            return []
        except Exception as e:
            logger.error(f"Error searching Materials Project: {e}")
            return []
    
    def get_material_elasticity(self, material_id: str) -> Optional[Dict[str, Any]]:
        """Get elastic properties for a material"""
        try:
            response = httpx.get(
                f"{self.base_url}/materials/elasticity/",
                params={"material_ids": material_id, "_fields": "material_id,bulk_modulus,shear_modulus,universal_anisotropy"},
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
            response.raise_for_status()
            data = response.json()
            results = data.get('data', [])
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error getting elasticity data: {e}")
            return None
        
    def parse_material_search(self, search_term: str) -> Tuple[str, List[str]]:
        """Parse search term to identify if it's a common material name or formula"""
        search_lower = search_term.lower().strip()
        
        # Check if it's a known material name
        if search_lower in self.material_mappings:
            alloy_system = self.material_mappings[search_lower]
            return "alloy", alloy_system.split("-")
        
        # Check partial matches (e.g., "stainless 304" -> "stainless steel 304")
        for material_name, alloy in self.material_mappings.items():
            if search_lower in material_name or material_name in search_lower:
                return "alloy", alloy.split("-")
        
        # If not found, treat as formula/element search
        # Check if it looks like an alloy system (contains hyphen)
        if "-" in search_term:
            return "alloy", [e.strip() for e in search_term.split("-")]
        
        # Single element or formula
        return "element", [search_term]
    
    def identify_common_alloy(self, formula: str, elements: List[str]) -> str:
        """Try to identify common alloy names from composition"""
        formula_lower = formula.lower()
        
        # Stainless steels
        if all(e in elements for e in ["Fe", "Cr"]):
            if "Ni" in elements:
                # 300 series austenitic stainless
                if "Mo" in elements:
                    if "Nb" in elements:
                        return "316Nb Stainless Steel"
                    return "316 Stainless Steel"
                elif "Ti" in elements:
                    return "321 Stainless Steel"
                elif "Nb" in elements:
                    return "347 Stainless Steel"
                else:
                    return "304 Stainless Steel"
            else:
                # 400 series ferritic/martensitic
                if "C" in elements:
                    return "440C Stainless Steel"
                return "430 Stainless Steel"
                
        # Aluminum alloys - check casting alloys first (higher Si content)
        if "Al" in elements:
            # Casting alloys (high Si)
            if "Si" in elements and any(substr in formula for substr in ["Si7", "Si8", "Si9", "Si10", "Si11", "Si12"]):
                if all(e in elements for e in ["Al", "Si", "Mg"]):
                    return "A356 Cast Aluminum"
                elif all(e in elements for e in ["Al", "Si", "Cu"]):
                    return "A380 Cast Aluminum"
                else:
                    return "4xx Cast Aluminum"
            # Wrought alloys
            elif "Cu" in elements and "Mg" in elements:
                return "2024 Aluminum"
            elif "Mg" in elements and "Si" in elements:
                return "6061 Aluminum"
            elif all(e in elements for e in ["Al", "Zn", "Mg", "Cu"]):
                return "7075 Aluminum"
            elif "Mg" in elements:
                return "5xxx Aluminum"
            elif "Mn" in elements:
                return "3003 Aluminum"
            elif len(elements) == 1:
                return "1100 Aluminum"
                
        # Titanium alloys
        if "Ti" in elements:
            if all(e in elements for e in ["Ti", "Al", "V"]):
                return "Ti-6Al-4V"
            elif all(e in elements for e in ["Ti", "Al", "Sn", "Zr", "Mo"]):
                return "Ti-6242"
            elif len(elements) == 1:
                return "CP Titanium"
            else:
                return "Titanium Alloy"
                
        # Nickel superalloys
        if "Ni" in elements:
            if all(e in elements for e in ["Ni", "Cr", "Fe", "Nb", "Mo"]):
                return "Inconel 718"
            elif all(e in elements for e in ["Ni", "Cr", "Mo", "Nb"]):
                return "Inconel 625"
            elif all(e in elements for e in ["Ni", "Mo", "Cr", "W"]):
                return "Hastelloy C-276"
            elif "Cu" in elements:
                return "Monel 400"
                
        # Copper alloys
        if "Cu" in elements:
            if "Zn" in elements:
                if "Pb" in elements:
                    return "360 Brass"
                return "260 Brass"
            elif "Sn" in elements:
                if "P" in elements:
                    return "Phosphor Bronze"
                return "Bronze"
            elif "Al" in elements:
                return "Aluminum Bronze"
            elif "Be" in elements:
                return "Beryllium Copper"
            elif "Ni" in elements:
                return "Cupronickel"
                
        # Tool steels
        if "Fe" in elements and all(e in elements for e in ["Cr", "Mo", "V", "C"]):
            return "D2 Tool Steel"
            
        # Cast iron
        if "Fe" in elements and "C" in elements and "Si" in elements:
            return "Cast Iron"
            
        # Plain carbon steel
        if "Fe" in elements and "C" in elements:
            return "Carbon Steel"
            
        # Magnesium alloys
        if "Mg" in elements:
            if all(e in elements for e in ["Mg", "Al", "Zn"]):
                return "AZ91 Magnesium"
            elif all(e in elements for e in ["Mg", "Al", "Mn"]):
                return "AM60 Magnesium"
                
        return None
    
    def _search_by_category(self, search_term: str) -> List[Dict[str, Any]]:
        """Search for materials by category (e.g., 'stainless steel', 'titanium', 'ceramic')"""
        logger.info(f"_search_by_category called with: '{search_term}'")
        
        # Define category mappings to material types
        category_mappings = {
            # Stainless steels
            "stainless": ["304", "316", "316L", "321", "347", "410", "420", "430", "440C", "17-4PH", "15-5PH", "2205", "904L"],
            "stainless steel": ["304", "316", "316L", "321", "347", "410", "420", "430", "440C", "17-4PH", "15-5PH", "2205", "904L"],
            "ss": ["304", "316", "316L", "321", "347", "410", "420", "430"],
            
            # Aluminum
            "aluminum": ["1100", "2024", "3003", "5052", "5083", "6061", "6063", "7075", "A356", "A380"],
            "aluminium": ["1100", "2024", "3003", "5052", "5083", "6061", "6063", "7075", "A356", "A380"],
            "al": ["1100", "2024", "3003", "5052", "6061", "7075"],
            
            # Titanium
            "titanium": ["grade 1", "grade 2", "grade 5", "ti-6al-4v", "ti-6-4", "cp titanium", "ti6242"],
            "ti": ["grade 2", "grade 5", "ti-6al-4v"],
            
            # Nickel alloys
            "nickel": ["inconel-625", "inconel-718", "inconel-600", "hastelloy-c-276", "monel-400", "monel-k-500"],
            "superalloy": ["inconel-625", "inconel-718", "hastelloy-c-276", "waspaloy", "rene-41"],
            "inconel": ["inconel-625", "inconel-718", "inconel-600", "x-750"],
            
            # Copper alloys
            "copper": ["c11000", "c26000", "c36000", "c51000", "c17200", "c70600", "c93200"],
            "brass": ["260 brass", "360 brass", "c26000", "c36000", "cartridge brass", "naval brass"],
            "bronze": ["phosphor bronze", "aluminum bronze", "c51000", "c52100", "c61400", "c95400"],
            
            # Steels
            "steel": ["1018", "1045", "4130", "4140", "4340", "a36", "d2", "o1", "h13"],
            "carbon steel": ["1018", "1045", "1020", "a36"],
            "alloy steel": ["4130", "4140", "4340", "8620", "9310"],
            "tool steel": ["d2", "a2", "o1", "m2", "h13", "s7"],
            
            # Cast iron
            "cast iron": ["gray iron", "ductile iron", "white iron"],
            "iron": ["gray iron", "ductile iron", "cast iron"],
            
            # Refractory materials
            "refractory": ["w", "mo", "ta", "tungsten", "molybdenum", "tantalum", "rhenium", "hafnium carbide", "tantalum carbide", "zirconia", "alumina"],
            
            # Composites (common)
            "composite": ["carbon fiber", "fiberglass", "kevlar", "cfrp", "gfrp", "carbon-carbon", "sic/sic"],
            
            # Semiconductors
            "semiconductor": ["silicon", "germanium", "gaas", "inp", "gan", "sic", "si", "ge"],
            
            # Biomaterials
            "biomaterial": ["titanium", "ti-6al-4v", "316l", "cobalt-chrome", "peek", "uhmwpe", "hydroxyapatite"],
            "biocompatible": ["titanium", "ti-6al-4v", "316l", "cobalt-chrome"],
            
            # Nanomaterials - will search MP for nano structures
            "nanomaterial": [],
            "nano": [],
            
            # Glass/Ceramic - return empty for now, will search MP
            "glass": [],
            "ceramic": [],
            "polymer": [],
            "plastic": []
        }
        
        # Check if search term matches any category
        matching_materials = []
        
        # First try exact match
        if search_term in category_mappings:
            matching_materials = category_mappings[search_term]
            logger.info(f"Exact match for category '{search_term}', found {len(matching_materials)} materials")
        else:
            # Then try substring match, but skip short abbreviations for non-exact matches
            for category, materials in category_mappings.items():
                # Skip short abbreviations unless exact match
                if len(category) <= 2:
                    continue
                if category in search_term or search_term in category:
                    matching_materials.extend(materials)
                    logger.info(f"Category '{category}' matched search term '{search_term}', found {len(materials)} materials: {materials[:3]}...")
                    break
        
        # Get standards data for matching materials
        results = []
        seen_alloys = set()
        
        if matching_materials:
            logger.info(f"Processing {len(matching_materials)} materials from category")
            for material in matching_materials[:10]:  # Limit to top 10
                if material in seen_alloys:
                    continue
                seen_alloys.add(material)
                
                logger.info(f"Looking up material: '{material}'")
                standard = self.standards_service.get_alloy_standard(material)
                if standard:
                    logger.info(f"Found standard for '{material}': {standard.get('common_name')}")
                    std_result = {
                        "mp_id": f"std-{material}",
                        "formula": standard.get("composition_formula", ""),
                        "common_name": standard.get("common_name", material),
                        "density": standard.get("mechanical", {}).get("density"),
                        "formation_energy": None,
                        "stability": True,
                        "band_gap": None,
                        "crystal_system": None,
                        "space_group": None,
                        "has_standard": True,
                        "data_source": "Engineering Standards",
                        "mechanical_properties": {
                            "yield_strength": standard.get("mechanical", {}).get("yield_strength"),
                            "ultimate_tensile_strength": standard.get("mechanical", {}).get("ultimate_tensile_strength"),
                            "elongation": standard.get("mechanical", {}).get("elongation"),
                            "brinell_hardness": standard.get("mechanical", {}).get("brinell_hardness"),
                            "youngs_modulus": standard.get("mechanical", {}).get("youngs_modulus"),
                            "shear_modulus": standard.get("mechanical", {}).get("shear_modulus"),
                            "poisson_ratio": standard.get("mechanical", {}).get("poisson_ratio")
                        },
                        "thermal_properties": standard.get("thermal", {}),
                        "acoustic_properties": standard.get("acoustic", {}),
                        "applications": standard.get("applications", []),
                        "standards": standard.get("standards", [])
                    }
                
                    # Calculate elastic/acoustic if needed
                    if standard.get("mechanical", {}).get("youngs_modulus") and not std_result.get("elastic_moduli"):
                        E = standard["mechanical"]["youngs_modulus"]
                        G = standard["mechanical"].get("shear_modulus")
                        v = standard["mechanical"].get("poisson_ratio", 0.33)
                        
                        if G:
                            K = E / (3 * (1 - 2 * v))
                            std_result["elastic_moduli"] = {
                                "bulk_modulus": K,
                                "shear_modulus": G,
                                "youngs_modulus": E,
                                "poisson_ratio": v
                            }
                            
                            if std_result["density"] and not std_result.get("acoustic_properties"):
                                acoustic = self._calculate_acoustic_properties(
                                    std_result["density"], K, G
                                )
                                if acoustic:
                                    std_result["acoustic_properties"] = acoustic
                        
                    results.append(std_result)
        
        # For categories without specific standards, search Materials Project
        mp_search_categories = ["glass", "ceramic", "polymer", "plastic", "semiconductor", "nanomaterial", "nano", "composite", "refractory", "biomaterial"]
        
        if search_term in mp_search_categories:
            # Map to element systems
            element_search = {
                "glass": ["Si", "O"],  # Silica-based
                "ceramic": ["Al", "O"],  # Alumina-based  
                "polymer": ["C", "H"],  # Carbon-based
                "plastic": ["C", "H"],
                "semiconductor": ["Si"],  # Silicon-based
                "nanomaterial": ["C"],  # Carbon nanostructures
                "nano": ["C"],
                "composite": ["C", "Si"],  # Carbon/Silicon composites
                "refractory": ["W"],  # Tungsten-based
                "biomaterial": ["Ca", "P"]  # Calcium phosphate
            }
            
            if search_term in element_search:
                mp_results = self.search_materials_summary(
                    elements=element_search[search_term], 
                    limit=10
                )
                
                for doc in mp_results:
                    material_data = {
                        "mp_id": doc.get("material_id", ""),
                        "formula": doc.get("formula_pretty", ""),
                        "common_name": self.identify_common_alloy(
                            doc.get("formula_pretty", ""), 
                            doc.get("elements", [])
                        ),
                        "density": doc.get("density"),
                        "formation_energy": doc.get("formation_energy_per_atom"),
                        "stability": doc.get("is_stable", False),
                        "band_gap": doc.get("band_gap"),
                        "crystal_system": doc.get("symmetry", {}).get("crystal_system") if isinstance(doc.get("symmetry"), dict) else None,
                        "space_group": doc.get("symmetry", {}).get("symbol") if isinstance(doc.get("symmetry"), dict) else None,
                        "data_source": "Materials Project"
                    }
                    results.append(material_data)
        
        logger.info(f"_search_by_category returning {len(results)} results")
        if results:
            logger.info(f"First result: {results[0].get('common_name')} from {results[0].get('data_source', 'unknown')}")
        return results
    
    def _check_summary_thermal_fields(self) -> List[str]:
        """Check what thermal fields are available in the summary endpoint"""
        try:
            # Get schema or test with a known material
            response = httpx.get(
                f"{self.base_url}/materials/summary/",
                params={
                    "elements": "Si",
                    "_limit": 1
                },
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    # Get all keys from first result
                    first_result = data['data'][0]
                    thermal_fields = [key for key in first_result.keys() 
                                    if any(kw in key.lower() for kw in 
                                         ['thermal', 'heat', 'debye', 'melting', 'temperature'])]
                    return thermal_fields
            return []
        except Exception as e:
            logger.error(f"Error checking summary fields: {e}")
            return []
    
    def get_available_thermal_properties(self, material_id: str = "mp-1234") -> Dict[str, Any]:
        """Get thermal properties for a material from MP and standards database"""
        # First check if it's a standard material
        if material_id.startswith("std-"):
            mp_id_part = material_id.replace("std-", "")
            
            # Handle specific category-code format (e.g., "stainless_steel-304")
            if "-" in mp_id_part and not mp_id_part.replace("-", "").isdigit():
                category, alloy_code = mp_id_part.split("-", 1)
                # Get the specific variant from the category
                if category in self.standards_service.standards_data:
                    if alloy_code in self.standards_service.standards_data[category]:
                        standard_data = self.standards_service.standards_data[category][alloy_code]
                    else:
                        standard_data = None
                else:
                    standard_data = None
            else:
                # Fallback to general lookup for simple codes
                alloy_code = mp_id_part
                standard_data = self.standards_service.get_alloy_standard(alloy_code)
            if standard_data and standard_data.get('thermal'):
                return {
                    "material_id": material_id,
                    "source": "alloy_standards",
                    "thermal_properties": standard_data['thermal'],
                    "has_thermal_data": True
                }
            else:
                return {
                    "material_id": material_id,
                    "source": "alloy_standards", 
                    "thermal_properties": {},
                    "has_thermal_data": False
                }
        
        # For Materials Project materials, check available fields
        try:
            summary_fields = self._check_summary_thermal_fields()
            
            # Try to get specific material with all fields
            response = httpx.get(
                f"{self.base_url}/materials/summary/",
                params={
                    "material_ids": material_id,
                    "_limit": 1,
                    "_fields": "material_id,formula_pretty,thermal_properties,debye,melting_point,specific_heat,thermal_conductivity,thermal_expansion,heat_capacity,gruneisen_parameter,seebeck_coefficient,last_updated"
                },
                headers=self.headers,
                timeout=30.0,
                follow_redirects=True
            )
            
            if response.status_code == 200:
                data = response.json()
                materials = data.get('data', [])
                
                if materials:
                    material = materials[0]
                    # Extract any thermal fields that exist
                    thermal_data = {}
                    thermal_keywords = [
                        'thermal', 'heat', 'debye', 'melting', 'cp', 'cv', 
                        'specific_heat', 'conductivity', 'expansion', 'temperature',
                        'phonon', 'gruneisen', 'seebeck', 'enthalpy', 'entropy'
                    ]
                    
                    for key, value in material.items():
                        if any(kw in key.lower() for kw in thermal_keywords) and value is not None:
                            thermal_data[key] = value
                    
                    # Try to enhance with standards data
                    enhanced_thermal = {}
                    if material.get('formula_pretty'):
                        # Try to find matching standard by composition
                        for category, alloys in self.standards_service.standards_data.items():
                            for alloy_code, alloy_data in alloys.items():
                                # Check if formula matches or is similar
                                if (material['formula_pretty'].lower() == alloy_code.lower() or 
                                    material['formula_pretty'].replace("-", "") == alloy_code.replace("-", "")):
                                    if alloy_data.get('thermal'):
                                        enhanced_thermal = alloy_data['thermal']
                                        break
                            if enhanced_thermal:
                                break
                    
                    return {
                        "material_id": material_id,
                        "formula": material.get('formula_pretty', ''),
                        "source": "materials_project",
                        "mp_thermal_fields": summary_fields,
                        "mp_thermal_data": thermal_data,
                        "standards_thermal_data": enhanced_thermal,
                        "has_thermal_data": bool(thermal_data or enhanced_thermal)
                    }
                else:
                    return {
                        "material_id": material_id,
                        "source": "materials_project",
                        "mp_thermal_fields": summary_fields,
                        "mp_thermal_data": {},
                        "standards_thermal_data": {},
                        "has_thermal_data": False
                    }
            else:
                return {"error": f"Failed to get material {material_id}: {response.status_code}"}
        except Exception as e:
            logger.error(f"Error checking thermal properties: {e}")
            return {"error": str(e)}
    
    def search_with_standards_fallback(self, search_term: str) -> List[Dict[str, Any]]:
        """Search with local standards database fallback for known alloys"""
        search_lower = search_term.lower().strip()
        
        # Check if it's a category search
        category_results = self._search_by_category(search_lower)
        if category_results:
            return category_results
        
        # Handle single element searches (Cu, Fe, Al, etc.)
        element_symbols = ["cu", "fe", "al", "ti", "ni", "cr", "si", "mg", "zn", "sn", "pb", 
                          "mo", "w", "v", "nb", "ta", "co", "mn", "be", "ag", "au", "pt", "pd"]
        if search_lower in element_symbols:
            # First get standard alloys for this element
            standards_results = []
            element_upper = search_lower.capitalize()
            
            # Search through all categories for alloys containing this element
            for category, alloys in self.standards_service.standards_data.items():
                for alloy_code, alloy_data in alloys.items():
                    # Check if element is a primary component
                    composition = alloy_data.get("composition", {})
                    
                    # Special handling for categories
                    is_relevant = False
                    if element_upper == "Cu" and category == "copper_alloys":
                        is_relevant = True
                    elif element_upper == "Fe" and category in ["stainless_steel", "tool_steels", "carbon_steels"]:
                        is_relevant = True  
                    elif element_upper == "Ti" and category == "titanium":
                        is_relevant = True
                    elif element_upper == "Ni" and category == "nickel_alloys":
                        is_relevant = True
                    elif element_upper == "Al" and category == "aluminum":
                        is_relevant = True
                    elif element_upper in ["W", "Mo", "Ta"] and category == "refractory_metals":
                        is_relevant = True
                    elif element_upper in composition:
                        # Check if it's a major component (>10% or "balance")
                        comp_value = str(composition.get(element_upper, ""))
                        if "balance" in comp_value.lower() or element_upper == alloy_data.get("composition_formula", "").split("-")[0]:
                            is_relevant = True
                        else:
                            try:
                                # Parse percentage ranges
                                if "-" in comp_value:
                                    low, high = comp_value.split("-")
                                    avg = (float(low) + float(high)) / 2
                                    if avg > 10.0:  # Major component threshold
                                        is_relevant = True
                                elif float(comp_value.replace(" max", "").replace(" min", "")) > 10.0:
                                    is_relevant = True
                            except:
                                pass
                    
                    if is_relevant:
                        # Convert to our format
                        std_result = {
                            "mp_id": f"std-{category}-{alloy_code}",
                            "formula": alloy_data.get("composition_formula", ""),
                            "common_name": alloy_data.get("common_name", alloy_code),
                            "density": alloy_data.get("mechanical", {}).get("density"),
                            "formation_energy": None,
                            "stability": True,
                            "band_gap": None,
                            "crystal_system": None,
                            "space_group": None,
                            "has_standard": True,
                            "data_source": "Local Standards Database",
                            "mechanical_properties": alloy_data.get("mechanical", {}),
                            "thermal_properties": alloy_data.get("thermal", {}),
                            "acoustic_properties": alloy_data.get("acoustic", {}),
                            "applications": alloy_data.get("applications", []),
                            "standards": alloy_data.get("standards", []),
                            "elements": list(composition.keys())
                        }
                        
                        # Calculate elastic moduli if needed
                        if alloy_data.get("mechanical", {}).get("youngs_modulus"):
                            E = alloy_data["mechanical"]["youngs_modulus"]
                            G = alloy_data["mechanical"].get("shear_modulus")
                            v = alloy_data["mechanical"].get("poisson_ratio", 0.33)
                            
                            if G and v < 0.5:
                                K = E / (3 * (1 - 2 * v))
                                std_result["elastic_moduli"] = {
                                    "bulk_modulus": K,
                                    "shear_modulus": G,
                                    "youngs_modulus": E,
                                    "poisson_ratio": v
                                }
                                
                                # Calculate acoustic if density available
                                if std_result["density"]:
                                    acoustic = self._calculate_acoustic_properties(
                                        std_result["density"], K, G
                                    )
                                    if acoustic:
                                        std_result["acoustic_properties"] = acoustic
                        
                        standards_results.append(std_result)
            
            # Then get Materials Project results with diversification
            mp_results = self.search_by_properties(
                elements_include=[element_upper]
            )
            
            # Combine results with standards first
            return standards_results + mp_results
        
        # First check if we have this in our standards database
        standards_results = []
        
        # Check if it's a known material mapping
        if search_lower in self.material_mappings:
            # Try to find the standard - but also check for close matches
            standard = self.standards_service.get_alloy_standard_with_category(search_term)
            
            # If not found directly, try common variations (e.g., 7071 -> 7075)
            if not standard and search_term in ["7071"]:
                standard = self.standards_service.get_alloy_standard("7075")
                if standard:
                    standard = standard.copy()
                    standard["common_name"] = f"{search_term} (Similar to 7075)"
                    
            if standard:
                # Convert to our format
                category = standard.get("_category", "unknown")
                alloy_code = standard.get("_alloy_code", search_term)
                std_result = {
                    "mp_id": f"std-{category}-{alloy_code}",
                    "formula": standard.get("composition_formula", ""),
                    "common_name": standard.get("common_name", search_term),
                    "density": standard.get("mechanical", {}).get("density"),
                    "formation_energy": None,
                    "stability": True,
                    "band_gap": None,
                    "crystal_system": None,
                    "space_group": None,
                    "has_standard": True,
                    "data_source": "Local Standards Database",
                    "mechanical_properties": {
                        "yield_strength": standard.get("mechanical", {}).get("yield_strength"),
                        "ultimate_tensile_strength": standard.get("mechanical", {}).get("ultimate_tensile_strength"),
                        "elongation": standard.get("mechanical", {}).get("elongation"),
                        "brinell_hardness": standard.get("mechanical", {}).get("brinell_hardness"),
                        "youngs_modulus": standard.get("mechanical", {}).get("youngs_modulus"),
                        "shear_modulus": standard.get("mechanical", {}).get("shear_modulus"),
                        "poisson_ratio": standard.get("mechanical", {}).get("poisson_ratio")
                    },
                    "thermal_properties": standard.get("thermal", {}),
                    "acoustic_properties": standard.get("acoustic", {}),
                    "applications": standard.get("applications", []),
                    "standards": standard.get("standards", [])
                }
                
                # Calculate elastic/acoustic if missing
                if standard.get("mechanical", {}).get("youngs_modulus") and not std_result.get("elastic_moduli"):
                    E = standard["mechanical"]["youngs_modulus"]
                    G = standard["mechanical"].get("shear_modulus")
                    v = standard["mechanical"].get("poisson_ratio", 0.33)
                    
                    if G:
                        K = E / (3 * (1 - 2 * v))
                        std_result["elastic_moduli"] = {
                            "bulk_modulus": K,
                            "shear_modulus": G,
                            "youngs_modulus": E,
                            "poisson_ratio": v
                        }
                        
                        # Calculate acoustic if density available
                        if std_result["density"] and not std_result.get("acoustic_properties"):
                            acoustic = self._calculate_acoustic_properties(
                                std_result["density"], K, G
                            )
                            if acoustic:
                                std_result["acoustic_properties"] = acoustic
                
                standards_results.append(std_result)
        
        # Then search Materials Project
        search_type, elements = self.parse_material_search(search_term)
        if search_type == "alloy" and len(elements) > 1:
            mp_results = self.search_aluminum_alloys("-".join(elements))
        else:
            mp_results = self.search_aluminum_alloys(search_term)
        
        # Combine results, standards first
        return standards_results + mp_results
    
    def search_aluminum_alloys(self, alloy_system: str = None) -> List[Dict[str, Any]]:
        """Search for aluminum alloys in Materials Project"""
        # Search for materials
        if alloy_system:
            # For alloy systems like "Al-Si"
            elements = alloy_system.split("-")
            results = self.search_materials_summary(elements=elements, limit=20)
            
            # If no results for complex alloys, try simpler searches
            if not results and len(elements) > 2:
                logger.info(f"No results for {alloy_system}, trying simpler searches")
                # Try binary combinations with Al
                if "Al" in elements:
                    for element in elements:
                        if element != "Al":
                            binary_results = self.search_materials_summary(
                                elements=["Al", element], limit=10
                            )
                            results.extend(binary_results)
                else:
                    # Try the first two elements
                    binary_results = self.search_materials_summary(
                        elements=elements[:2], limit=10
                    )
                    results.extend(binary_results)
                    
                # Remove duplicates
                seen_ids = set()
                unique_results = []
                for result in results:
                    if result.get("material_id") not in seen_ids:
                        seen_ids.add(result.get("material_id"))
                        unique_results.append(result)
                results = unique_results[:20]  # Limit to 20 results
        else:
            # Search for aluminum-containing materials
            results = self.search_materials_summary(elements=["Al"], limit=20)
        
        # Transform results to our format
        materials = []
        for doc in results:
            # Get elements list
            elements = doc.get("elements", [])
            formula = doc.get("formula_pretty", "")
            
            # Try to identify common name
            common_name = self.identify_common_alloy(formula, elements)
            
            material_data = {
                "mp_id": doc.get("material_id", ""),
                "formula": doc.get("formula_pretty", ""),
                "common_name": common_name,
                "density": doc.get("density"),
                "formation_energy": doc.get("formation_energy_per_atom"),
                "stability": doc.get("is_stable", False),
                "band_gap": doc.get("band_gap"),
                "crystal_system": doc.get("symmetry", {}).get("crystal_system") if isinstance(doc.get("symmetry"), dict) else None,
                "space_group": doc.get("symmetry", {}).get("symbol") if isinstance(doc.get("symmetry"), dict) else None,
                "elements": elements  # Include for sorting
            }
            
            # Cross-correlate with standards database
            if common_name:
                material_data = self.standards_service.enhance_material_with_standards(material_data)
            
            # Try to get elastic properties
            if doc.get("material_id"):
                elasticity = self.get_material_elasticity(doc["material_id"])
                if elasticity:
                    # Calculate Young's modulus and Poisson's ratio from bulk and shear moduli
                    K = elasticity.get("bulk_modulus", {}).get("vrh") if isinstance(elasticity.get("bulk_modulus"), dict) else None
                    G = elasticity.get("shear_modulus", {}).get("vrh") if isinstance(elasticity.get("shear_modulus"), dict) else None
                    
                    if K and G:
                        # Calculate Young's modulus: E = 9KG/(3K+G)
                        E = (9 * K * G) / (3 * K + G)
                        # Calculate Poisson's ratio: v = (3K-2G)/(6K+2G)
                        v = (3 * K - 2 * G) / (6 * K + 2 * G)
                        
                        material_data["elastic_moduli"] = {
                            "bulk_modulus": K,
                            "shear_modulus": G,
                            "youngs_modulus": E,
                            "poisson_ratio": v
                        }
                        
                        # Calculate acoustic properties
                        if doc.get("density"):
                            acoustic = self._calculate_acoustic_properties(
                                doc["density"], K, G
                            )
                            if acoustic:
                                material_data["acoustic_properties"] = acoustic
            
            materials.append(material_data)
        
        # Sort materials to prioritize base alloys and those with most properties
        materials = self._sort_by_relevance(materials)
        
        return materials
    
    def get_material_details(self, mp_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific material"""
        try:
            # Handle standard materials from our database
            if mp_id.startswith("std-"):
                mp_id_part = mp_id.replace("std-", "")
                
                # Handle specific category-code format (e.g., "stainless_steel-304")
                if "-" in mp_id_part and not mp_id_part.replace("-", "").isdigit():
                    category, alloy_code = mp_id_part.split("-", 1)
                    # Get the specific variant from the category
                    if category in self.standards_service.standards_data:
                        if alloy_code in self.standards_service.standards_data[category]:
                            standard_data = self.standards_service.standards_data[category][alloy_code]
                        else:
                            standard_data = None
                    else:
                        standard_data = None
                else:
                    # Fallback to general lookup for simple codes
                    alloy_code = mp_id_part
                    standard_data = self.standards_service.get_alloy_standard(alloy_code)
                
                if standard_data:
                    # Convert standard format to match MP format
                    details = {
                        "mp_id": mp_id,
                        "formula": standard_data.get("composition_formula", ""),
                        "common_name": standard_data.get("common_name"),
                        "density": standard_data.get("mechanical", {}).get("density"),
                        "formation_energy": None,
                        "stability": True,
                        "band_gap": None,
                        "crystal_system": None,
                        "space_group": None,
                        "elastic_moduli": None,  # Will be calculated below if data available
                        "acoustic_properties": standard_data.get("acoustic"),
                        "lattice": None,
                        "mechanical_properties": standard_data.get("mechanical"),
                        "thermal_properties": standard_data.get("thermal"),
                        "applications": standard_data.get("applications", []),
                        "standards": standard_data.get("standards", []),
                        "has_standard": True,
                        "data_source": "Local Standards Database",
                        "composition": standard_data.get("composition")
                    }
                    
                    # Calculate elastic moduli if data available
                    if standard_data.get("mechanical", {}).get("youngs_modulus"):
                        E = standard_data["mechanical"]["youngs_modulus"]
                        G = standard_data["mechanical"].get("shear_modulus")
                        v = standard_data["mechanical"].get("poisson_ratio", 0.33)
                        
                        if G and v is not None:
                            # Calculate bulk modulus: K = E / (3 * (1 - 2v))
                            K = E / (3 * (1 - 2 * v)) if v < 0.5 else None
                            
                            if K:
                                details["elastic_moduli"] = {
                                    "bulk_modulus": K,
                                    "shear_modulus": G,
                                    "youngs_modulus": E,
                                    "poisson_ratio": v
                                }
                            
                            # Calculate acoustic if density available
                            if details["density"] and not details.get("acoustic_properties"):
                                acoustic = self._calculate_acoustic_properties(
                                    details["density"], K, G
                                )
                                if acoustic:
                                    details["acoustic_properties"] = acoustic
                    
                    return details
                else:
                    return None
            
            # Get basic info from Materials Project
            results = self.search_materials_summary(material_ids=[mp_id], limit=1)
            if not results:
                return None
                
            doc = results[0]
            
            # Get elements and identify common name
            elements = doc.get("elements", [])
            formula = doc.get("formula_pretty", "")
            common_name = self.identify_common_alloy(formula, elements)
            
            # Extract comprehensive properties
            details = {
                "mp_id": doc.get("material_id", ""),
                "formula": doc.get("formula_pretty", ""),
                "common_name": common_name,
                "density": doc.get("density"),
                "formation_energy": doc.get("formation_energy_per_atom"),
                "energy_above_hull": doc.get("energy_above_hull"),
                "stability": doc.get("is_stable", False),
                "band_gap": doc.get("band_gap"),
                "is_metal": doc.get("is_metal"),
                "crystal_system": doc.get("symmetry", {}).get("crystal_system") if isinstance(doc.get("symmetry"), dict) else None,
                "space_group": doc.get("symmetry", {}).get("symbol") if isinstance(doc.get("symmetry"), dict) else None,
            }
            
            # Cross-correlate with standards database
            if common_name:
                details = self.standards_service.enhance_material_with_standards(details)
            
            # Get elastic properties
            elasticity = self.get_material_elasticity(mp_id)
            if elasticity:
                K = elasticity.get("bulk_modulus", {}).get("vrh") if isinstance(elasticity.get("bulk_modulus"), dict) else None
                G = elasticity.get("shear_modulus", {}).get("vrh") if isinstance(elasticity.get("shear_modulus"), dict) else None
                
                if K and G:
                    E = (9 * K * G) / (3 * K + G)
                    v = (3 * K - 2 * G) / (6 * K + 2 * G)
                    
                    details["elastic_moduli"] = {
                        "bulk_modulus": K,
                        "shear_modulus": G,
                        "youngs_modulus": E,
                        "poisson_ratio": v
                    }
                    
                    # Calculate acoustic properties
                    if doc.get("density"):
                        acoustic_props = self._calculate_acoustic_properties(
                            doc["density"], K, G
                        )
                        if acoustic_props:
                            details["acoustic_properties"] = acoustic_props
            
            return details
            
        except Exception as e:
            logger.error(f"Error getting material details for {mp_id}: {e}")
            return None
    
    def search_by_properties(self, 
                           min_density: float = None,
                           max_density: float = None,
                           min_melting_point: float = None,
                           elements_include: List[str] = None,
                           elements_exclude: List[str] = None) -> List[Dict[str, Any]]:
        """Search materials by specific property ranges"""
        # Increase limit to get more results for diversification
        search_limit = 200 if elements_include and len(elements_include) == 1 else 50
        
        # Use the summary endpoint with element filters
        results = self.search_materials_summary(
            elements=elements_include,
            exclude_elements=elements_exclude,
            limit=search_limit
        )
        
        # Transform to full material format with all available data
        materials = []
        for doc in results:
            density = doc.get("density")
            
            # Apply density filters if specified
            if density:
                if min_density and density < min_density:
                    continue
                if max_density and density > max_density:
                    continue
            
            # Get elements and identify common name
            elements = doc.get("elements", [])
            formula = doc.get("formula_pretty", "")
            common_name = self.identify_common_alloy(formula, elements)
            
            material_data = {
                "mp_id": doc.get("material_id", ""),
                "formula": formula,
                "common_name": common_name,
                "density": density,
                "formation_energy": doc.get("formation_energy_per_atom"),
                "stability": doc.get("is_stable", False),
                "band_gap": doc.get("band_gap"),
                "crystal_system": doc.get("symmetry", {}).get("crystal_system") if isinstance(doc.get("symmetry"), dict) else None,
                "space_group": doc.get("symmetry", {}).get("symbol") if isinstance(doc.get("symmetry"), dict) else None,
                "elements": elements
            }
            
            # Cross-correlate with standards database
            if common_name:
                material_data = self.standards_service.enhance_material_with_standards(material_data)
            
            materials.append(material_data)
        
        # If searching for a single element, diversify results
        if elements_include and len(elements_include) == 1:
            materials = self._diversify_results(materials, target_element=elements_include[0])
        else:
            # Otherwise just sort by relevance
            materials = self._sort_by_relevance(materials)
        
        return materials[:50]  # Return top 50 after diversification
    
    def analyze_oxide_formation(self, base_element: str = "Al") -> List[Dict[str, Any]]:
        """Analyze oxide formation for a base element"""
        # Search for oxides of the base element
        results = self.search_materials_summary(elements=[base_element, "O"], limit=20)
        
        oxides = []
        for doc in results:
            # Filter to only binary oxides
            formula = doc.get("formula_pretty", "")
            if formula.count('-') == 0:  # Simple formula, not complex
                oxide_data = {
                    "mp_id": doc.get("material_id", ""),
                    "formula": formula,
                    "formation_energy": doc.get("formation_energy_per_atom"),
                    "stability": doc.get("is_stable", False),
                    "band_gap": doc.get("band_gap"),
                    "density": doc.get("density")
                }
                
                # Try to get elastic properties
                if doc.get("material_id"):
                    elasticity = self.get_material_elasticity(doc["material_id"])
                    if elasticity:
                        K = elasticity.get("bulk_modulus", {}).get("vrh") if isinstance(elasticity.get("bulk_modulus"), dict) else None
                        G = elasticity.get("shear_modulus", {}).get("vrh") if isinstance(elasticity.get("shear_modulus"), dict) else None
                        
                        if K and G:
                            E = (9 * K * G) / (3 * K + G)
                            oxide_data["elastic_moduli"] = {
                                "bulk_modulus": K,
                                "shear_modulus": G,
                                "youngs_modulus": E
                            }
                
                oxides.append(oxide_data)
        
        # Sort by stability (formation energy)
        oxides.sort(key=lambda x: x.get("formation_energy", 0))
        
        return oxides
    
    def _calculate_acoustic_properties(self, density: float, K: float, G: float) -> Dict[str, float]:
        """Calculate acoustic properties from elastic constants"""
        # Check if values are physical (positive moduli required)
        if K <= 0 or G <= 0 or density <= 0:
            return None
            
        # density in g/cm³, K and G in GPa
        # Convert to SI units
        rho = density * 1000  # kg/m³
        K_si = K * 1e9  # Pa
        G_si = G * 1e9  # Pa
        
        # Check if the wave velocity calculation would be valid
        longitudinal_term = (K_si + 4*G_si/3) / rho
        if longitudinal_term <= 0:
            return None
            
        # Longitudinal wave velocity
        v_l = longitudinal_term ** 0.5  # m/s
        
        # Shear wave velocity
        v_s = (G_si / rho) ** 0.5  # m/s
        
        # Acoustic impedance
        Z_l = rho * v_l  # kg/(m²·s) or Rayl
        Z_s = rho * v_s
        
        return {
            "longitudinal_velocity": round(v_l, 2),
            "shear_velocity": round(v_s, 2),
            "longitudinal_impedance": round(Z_l, 2),
            "shear_impedance": round(Z_s, 2),
            "impedance_contrast_with_air": round(Z_l / 413, 2)  # Air impedance ~413 Rayl
        }
    
    def compare_alloys(self, alloy_formulas: List[str]) -> List[Dict[str, Any]]:
        """Compare multiple alloys for DRIP printing suitability"""
        comparison_data = []
        
        for formula in alloy_formulas:
            # Search for formula
            results = self.search_materials_summary(formula=formula, limit=1)
            
            if results:
                doc = results[0]
                
                data = {
                    "formula": doc.get("formula_pretty", ""),
                    "mp_id": doc.get("material_id", ""),
                    "density": doc.get("density"),
                    "formation_energy": doc.get("formation_energy_per_atom"),
                    "printability_score": self._calculate_printability_score(doc)
                }
                
                # Get elastic data if available
                if doc.get("material_id"):
                    elasticity = self.get_material_elasticity(doc["material_id"])
                    if elasticity and doc.get("density"):
                        K = elasticity.get("bulk_modulus", {}).get("vrh") if isinstance(elasticity.get("bulk_modulus"), dict) else None
                        G = elasticity.get("shear_modulus", {}).get("vrh") if isinstance(elasticity.get("shear_modulus"), dict) else None
                        
                        if K and G:
                            acoustic = self._calculate_acoustic_properties(
                                doc["density"], K, G
                            )
                            if acoustic:
                                data["acoustic_impedance"] = acoustic["longitudinal_impedance"]
                                data["impedance_contrast"] = acoustic["impedance_contrast_with_air"]
                
                comparison_data.append(data)
        
        # Sort by printability score
        comparison_data.sort(key=lambda x: x.get("printability_score", 0), reverse=True)
        
        return comparison_data
    
    def _calculate_printability_score(self, material_doc) -> float:
        """Calculate a printability score for DRIP system"""
        score = 100.0
        
        # Density factor (prefer lighter alloys for better acoustic manipulation)
        density = material_doc.get("density", 0)
        if density and density < 2.5:
            score += 10
        elif density and density > 3.5:
            score -= 20
        
        # Stability factor
        if material_doc.get("is_stable"):
            score += 20
        else:
            score -= 30
        
        # Formation energy bonus
        formation_energy = material_doc.get("formation_energy_per_atom", 0)
        if formation_energy < -1.0:
            score += 10  # Very stable compound
        
        return max(0, min(100, score))  # Clamp to 0-100
    
    def export_to_drip_format(self, materials: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Export Materials Project data to DRIP portal format"""
        drip_materials = []
        
        for mat in materials:
            drip_material = {
                "name": f"{mat['formula']} (MP: {mat['mp_id']})",
                "category": "Metal" if any(m in mat['formula'] for m in ["Al", "Fe", "Ti", "Cu"]) else "Ceramic",
                "subcategory": "From Materials Project",
                "data_source": "Materials Project",
                "source_url": f"https://materialsproject.org/materials/{mat['mp_id']}",
                "properties": []
            }
            
            # Add density
            if mat.get('density'):
                drip_material['properties'].append({
                    "name": "Density",
                    "value": mat['density'],
                    "unit": "g/cm³"
                })
            
            # Add formation energy
            if mat.get('formation_energy'):
                drip_material['properties'].append({
                    "name": "Formation Energy",
                    "value": mat['formation_energy'],
                    "unit": "eV/atom"
                })
            
            # Add elastic properties
            if mat.get('elastic_moduli'):
                for prop, value in mat['elastic_moduli'].items():
                    if value is not None:
                        drip_material['properties'].append({
                            "name": prop.replace('_', ' ').title(),
                            "value": value,
                            "unit": "GPa" if prop != "poisson_ratio" else ""
                        })
            
            # Add acoustic properties
            if mat.get('acoustic_properties'):
                for prop, value in mat['acoustic_properties'].items():
                    unit = "m/s" if "velocity" in prop else "Rayl"
                    if "contrast" in prop:
                        unit = ""  # Dimensionless
                    drip_material['properties'].append({
                        "name": prop.replace('_', ' ').title(),
                        "value": value,
                        "unit": unit
                    })
            
            drip_materials.append(drip_material)
        
        return {
            "materials": drip_materials,
            "metadata": {
                "source": "Materials Project",
                "timestamp": datetime.utcnow().isoformat(),
                "total_materials": len(drip_materials)
            }
        }
    
    def _sort_by_relevance(self, materials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort materials by relevance - prioritizing base alloys and comprehensive property data"""
        
        def score_material(material: Dict[str, Any]) -> float:
            score = 0
            
            # 1. Prioritize materials with common names (identified alloys)
            if material.get("common_name"):
                score += 100
            
            # 2. Prioritize base alloys over complex compositions
            formula = material.get("formula", "")
            elements = material.get("elements", [])
            
            # Simple formulas get higher scores
            if len(elements) <= 3:
                score += 50
            elif len(elements) <= 4:
                score += 30
            
            # Base alloy systems get bonus
            if material.get("common_name"):
                name = material["common_name"].lower()
                # Pure metals or simple alloys
                if any(pure in name for pure in ["1100", "cp titanium", "commercially pure"]):
                    score += 80
                # Base alloy compositions (no temper designation)
                elif not any(temper in name for temper in ["-t", "-h", "-o"]):
                    score += 60
            
            # 3. Prioritize materials with more property data
            property_count = 0
            
            # Count elastic properties
            if material.get("elastic_moduli"):
                elastic = material["elastic_moduli"]
                property_count += sum(1 for v in elastic.values() if v is not None)
                score += property_count * 10
            
            # Count acoustic properties
            if material.get("acoustic_properties"):
                acoustic = material["acoustic_properties"]
                property_count += sum(1 for v in acoustic.values() if v is not None)
                score += property_count * 5
            
            # Standards data is valuable
            if material.get("has_standard"):
                score += 70
                # Mechanical properties from standards
                if material.get("mechanical_properties"):
                    mech = material["mechanical_properties"]
                    property_count += sum(1 for v in mech.values() if v is not None)
                    score += property_count * 15
            
            # Basic properties
            if material.get("density"):
                score += 20
            
            # 4. Stable phases preferred
            if material.get("stability"):
                score += 30
            
            # 5. Lower formation energy (more stable)
            if material.get("formation_energy"):
                # More negative = more stable
                score -= material["formation_energy"] * 10
            
            # 6. Penalize oxides and complex compounds when searching for alloys
            if "O" in elements and len(elements) > 2:
                score -= 50
            
            # Special boost for very common engineering alloys
            if material.get("common_name"):
                common_alloys = {
                    "6061": 200,
                    "7075": 180, 
                    "2024": 170,
                    "5052": 160,
                    "304 stainless": 190,
                    "316 stainless": 185,
                    "ti-6al-4v": 175,
                    "a356": 165,
                    "4140": 155,
                }
                name_lower = material["common_name"].lower()
                for alloy, boost in common_alloys.items():
                    if alloy in name_lower:
                        score += boost
                        break
            
            return score
        
        # Sort by score (descending)
        return sorted(materials, key=score_material, reverse=True)
    
    def _diversify_results(self, materials: List[Dict[str, Any]], target_element: str = None, max_per_group: int = 3) -> List[Dict[str, Any]]:
        """Diversify search results to show varied compositions instead of duplicates"""
        # Group materials by their base composition pattern
        composition_groups = {}
        pure_element = None
        
        for material in materials:
            formula = material.get('formula', '')
            elements = material.get('elements', [])
            
            # Check if it's pure element
            if len(elements) == 1 and elements[0] == target_element:
                if not pure_element or material.get('stability', False):
                    pure_element = material
                continue
            
            # Create a composition signature
            if target_element and target_element in elements:
                # For element-specific searches, group by non-target elements
                other_elements = sorted([e for e in elements if e != target_element])
                if not other_elements:  # Pure element
                    signature = f"{target_element}-pure"
                else:
                    signature = f"{target_element}-{'-'.join(other_elements[:2])}"  # First 2 other elements
            else:
                # For general searches, use first 2-3 elements
                signature = '-'.join(sorted(elements)[:3])
            
            # Group materials by composition type
            if signature not in composition_groups:
                composition_groups[signature] = []
            composition_groups[signature].append(material)
        
        # Build diverse results
        diverse_results = []
        
        # Add pure element first if available
        if pure_element:
            diverse_results.append(pure_element)
        
        # Sort groups by relevance of their best material
        def group_score(materials_in_group):
            if not materials_in_group:
                return 0
            # Score based on: has common name, number of properties, stability
            best = materials_in_group[0]
            score = 0
            if best.get('common_name'):
                score += 1000
            if best.get('mechanical_properties'):
                score += 100
            if best.get('thermal_properties'):
                score += 100
            if best.get('stability'):
                score += 50
            if best.get('elastic_moduli'):
                score += 50
            return score
        
        # Sort each group internally by relevance
        for signature in composition_groups:
            composition_groups[signature] = self._sort_by_relevance(composition_groups[signature])
        
        # Sort groups by their best material's score
        sorted_groups = sorted(composition_groups.items(), 
                             key=lambda x: group_score(x[1]), 
                             reverse=True)
        
        # Add materials from each group (max_per_group from each)
        for signature, group_materials in sorted_groups:
            # Take up to max_per_group materials from each composition group
            for material in group_materials[:max_per_group]:
                diverse_results.append(material)
                if len(diverse_results) >= 50:  # Reasonable limit
                    break
            if len(diverse_results) >= 50:
                break
        
        return diverse_results
    
    def get_thermal_properties(self, mp_id: str) -> Dict[str, Any]:
        """Extract thermal properties for a material (limited in new API)"""
        return {
            "mp_id": mp_id,
            "thermal_data_available": False,
            "note": "Thermal properties not available in current API version"
        }