"""Service for integrating with NIST Chemistry WebBook to get temperature-dependent properties"""

import asyncio
import aiohttp
import requests
import json
import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from urllib.parse import urlencode, quote
import time

logger = logging.getLogger(__name__)

@dataclass
class TemperatureProperty:
    """Temperature-dependent property data"""
    property_name: str
    values: List[Tuple[float, float]]  # (temperature, value) pairs
    unit: str
    temperature_unit: str = "K"
    function_type: str = "tabular"  # "tabular", "polynomial", "linear"
    coefficients: Optional[List[float]] = None
    valid_temp_min: Optional[float] = None
    valid_temp_max: Optional[float] = None
    source: str = "NIST WebBook"

class NistWebBookService:
    """Service for extracting temperature-dependent properties from NIST Chemistry WebBook"""
    
    def __init__(self):
        self.base_url = "https://webbook.nist.gov"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (DRIP Materials Database) NIST WebBook Integration'
        })
        
        # Cache to avoid repeated requests
        self.cache = {}
        self.rate_limit_delay = 1.0  # seconds between requests
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Enforce rate limiting to be respectful to NIST servers"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.rate_limit_delay:
            time.sleep(self.rate_limit_delay - time_since_last)
        self.last_request_time = time.time()
        
    def search_compound(self, compound_name: str, cas_number: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Search for a compound in NIST WebBook and return basic info"""
        cache_key = f"search_{compound_name}_{cas_number}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        logger.info(f"🔍 Searching NIST WebBook for: {compound_name}")
        self._rate_limit()
        
        try:
            # Build search URL
            params = {
                'Name': compound_name,
                'Units': 'SI'
            }
            if cas_number:
                params['ID'] = cas_number
                
            search_url = f"{self.base_url}/cgi/cbook.cgi"
            response = self.session.get(search_url, params=params)
            
            if response.status_code == 200:
                # Parse response to extract compound ID and available data
                result = self._parse_search_results(response.text, compound_name)
                self.cache[cache_key] = result
                return result
            else:
                logger.warning(f"NIST search failed for {compound_name}: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching NIST for {compound_name}: {e}")
            return None
    
    def _parse_search_results(self, html_content: str, compound_name: str) -> Optional[Dict[str, Any]]:
        """Parse NIST search results to extract compound information"""
        try:
            # Look for compound ID in the HTML
            id_pattern = r'ID=([A-Z0-9]+)'
            id_matches = re.findall(id_pattern, html_content)
            
            if not id_matches:
                logger.info(f"No compound ID found for {compound_name}")
                return None
                
            compound_id = id_matches[0]
            
            # Check what data is available
            available_data = {
                'thermochemistry': 'thermo-const' in html_content,
                'phase_change': 'phase' in html_content,
                'thermophysical': 'thermo-fld' in html_content,
                'gas_phase': 'gas' in html_content
            }
            
            logger.info(f"✅ Found NIST compound {compound_id} for {compound_name}, available: {available_data}")
            
            return {
                'compound_id': compound_id,
                'name': compound_name,
                'available_data': available_data
            }
            
        except Exception as e:
            logger.error(f"Error parsing NIST search results: {e}")
            return None
    
    def get_thermal_conductivity_curve(self, compound_info: Dict[str, Any]) -> Optional[TemperatureProperty]:
        """Get temperature-dependent thermal conductivity data"""
        compound_id = compound_info.get('compound_id')
        if not compound_id:
            return None
            
        logger.info(f"🌡️ Getting thermal conductivity for compound {compound_id}")
        self._rate_limit()
        
        try:
            # Request thermophysical data
            params = {
                'ID': compound_id,
                'Mask': '20',  # Thermal conductivity
                'Type': 'JANAFL',
                'Table': 'on'
            }
            
            url = f"{self.base_url}/cgi/fluid.cgi"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return self._parse_thermal_conductivity(response.text)
            else:
                logger.warning(f"Failed to get thermal conductivity for {compound_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting thermal conductivity: {e}")
            return None
    
    def _parse_thermal_conductivity(self, html_content: str) -> Optional[TemperatureProperty]:
        """Parse thermal conductivity data from NIST response"""
        try:
            # Look for data tables in the HTML
            # NIST typically presents data in tables with Temperature and Property columns
            table_pattern = r'<table[^>]*>.*?</table>'
            tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for table in tables:
                # Look for temperature and thermal conductivity columns
                if 'conductivity' in table.lower() or 'k' in table.lower():
                    data_points = self._extract_table_data(table)
                    if data_points:
                        return TemperatureProperty(
                            property_name="thermal_conductivity",
                            values=data_points,
                            unit="W/m·K",
                            temperature_unit="K"
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing thermal conductivity data: {e}")
            return None
    
    def get_density_curve(self, compound_info: Dict[str, Any]) -> Optional[TemperatureProperty]:
        """Get temperature-dependent density data"""
        compound_id = compound_info.get('compound_id')
        if not compound_id:
            return None
            
        logger.info(f"⚖️ Getting density for compound {compound_id}")
        self._rate_limit()
        
        try:
            params = {
                'ID': compound_id,
                'Mask': '1',  # Density
                'Type': 'JANAFL',
                'Table': 'on'
            }
            
            url = f"{self.base_url}/cgi/fluid.cgi"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return self._parse_density(response.text)
            else:
                logger.warning(f"Failed to get density for {compound_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting density: {e}")
            return None
    
    def _parse_density(self, html_content: str) -> Optional[TemperatureProperty]:
        """Parse density data from NIST response"""
        try:
            table_pattern = r'<table[^>]*>.*?</table>'
            tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for table in tables:
                if 'density' in table.lower() or 'ρ' in table.lower():
                    data_points = self._extract_table_data(table)
                    if data_points:
                        return TemperatureProperty(
                            property_name="density",
                            values=data_points,
                            unit="kg/m³",
                            temperature_unit="K"
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing density data: {e}")
            return None
    
    def get_viscosity_curve(self, compound_info: Dict[str, Any]) -> Optional[TemperatureProperty]:
        """Get temperature-dependent viscosity data"""
        compound_id = compound_info.get('compound_id')
        if not compound_id:
            return None
            
        logger.info(f"🌊 Getting viscosity for compound {compound_id}")
        self._rate_limit()
        
        try:
            params = {
                'ID': compound_id,
                'Mask': '10',  # Viscosity
                'Type': 'JANAFL',
                'Table': 'on'
            }
            
            url = f"{self.base_url}/cgi/fluid.cgi"
            response = self.session.get(url, params=params)
            
            if response.status_code == 200:
                return self._parse_viscosity(response.text)
            else:
                logger.warning(f"Failed to get viscosity for {compound_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting viscosity: {e}")
            return None
    
    def _parse_viscosity(self, html_content: str) -> Optional[TemperatureProperty]:
        """Parse viscosity data from NIST response"""
        try:
            table_pattern = r'<table[^>]*>.*?</table>'
            tables = re.findall(table_pattern, html_content, re.DOTALL | re.IGNORECASE)
            
            for table in tables:
                if 'viscosity' in table.lower() or 'μ' in table.lower():
                    data_points = self._extract_table_data(table)
                    if data_points:
                        return TemperatureProperty(
                            property_name="dynamic_viscosity",
                            values=data_points,
                            unit="Pa·s",
                            temperature_unit="K"
                        )
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing viscosity data: {e}")
            return None
    
    def _extract_table_data(self, table_html: str) -> List[Tuple[float, float]]:
        """Extract temperature-property data points from HTML table"""
        try:
            # Remove HTML tags and extract numerical data
            text = re.sub(r'<[^>]+>', ' ', table_html)
            
            # Look for patterns like "temperature property" in rows
            lines = text.split('\n')
            data_points = []
            
            for line in lines:
                # Match lines with two numbers (temperature and property value)
                numbers = re.findall(r'-?\d+\.?\d*(?:[eE][+-]?\d+)?', line)
                if len(numbers) >= 2:
                    try:
                        temp = float(numbers[0])
                        value = float(numbers[1])
                        # Basic sanity checks
                        if 0 < temp < 5000 and value > 0:  # Reasonable temperature and positive property
                            data_points.append((temp, value))
                    except ValueError:
                        continue
            
            return data_points[:50] if data_points else []  # Limit to 50 points max
            
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return []
    
    def get_comprehensive_properties(self, compound_name: str, cas_number: Optional[str] = None) -> Dict[str, TemperatureProperty]:
        """Get all available temperature-dependent properties for a compound"""
        logger.info(f"📊 Getting comprehensive properties for {compound_name}")
        
        # First search for the compound
        compound_info = self.search_compound(compound_name, cas_number)
        if not compound_info:
            logger.warning(f"Could not find {compound_name} in NIST WebBook")
            return {}
        
        properties = {}
        
        # Get thermal conductivity if available
        thermal_cond = self.get_thermal_conductivity_curve(compound_info)
        if thermal_cond:
            properties['thermal_conductivity'] = thermal_cond
            
        # Get density if available
        density = self.get_density_curve(compound_info)
        if density:
            properties['density'] = density
            
        # Get viscosity if available
        viscosity = self.get_viscosity_curve(compound_info)
        if viscosity:
            properties['dynamic_viscosity'] = viscosity
        
        logger.info(f"✅ Retrieved {len(properties)} temperature-dependent properties for {compound_name}")
        return properties
    
    def enhance_alloy_with_nist_data(self, alloy_data: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance alloy data with NIST temperature-dependent properties"""
        enhanced = alloy_data.copy()
        
        # Try to find NIST data using common name
        common_name = alloy_data.get('common_name', '')
        if not common_name:
            return enhanced
            
        # Extract the main element from the alloy name
        main_elements = ['aluminum', 'copper', 'titanium', 'iron', 'nickel', 'magnesium']
        target_element = None
        
        for element in main_elements:
            if element.lower() in common_name.lower():
                target_element = element
                break
        
        if target_element:
            logger.info(f"🔬 Enhancing {common_name} with NIST data for {target_element}")
            nist_properties = self.get_comprehensive_properties(target_element)
            
            if nist_properties:
                enhanced['temperature_dependent_properties'] = {}
                
                for prop_name, temp_prop in nist_properties.items():
                    enhanced['temperature_dependent_properties'][prop_name] = {
                        'values': temp_prop.values,
                        'unit': temp_prop.unit,
                        'temperature_unit': temp_prop.temperature_unit,
                        'function_type': temp_prop.function_type,
                        'source': 'NIST WebBook'
                    }
                    
                enhanced['nist_enhanced'] = True
                logger.info(f"✅ Enhanced {common_name} with {len(nist_properties)} temperature curves")
        
        return enhanced

# Global instance
nist_service = NistWebBookService()