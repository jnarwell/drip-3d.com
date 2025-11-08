from dataclasses import dataclass
from typing import Optional, Dict
import numpy as np

@dataclass
class DRIPValidation:
    """DRIP number calculation and scaling validation"""
    
    frequency: float  # Hz
    droplet_diameter: float  # meters
    material_density: float  # kg/m³
    acoustic_pressure: float  # Pa
    temperature: float  # Celsius
    material_type: str = "aluminum"  # aluminum, steel, titanium, etc.
    
    def calculate_drip_number(self) -> float:
        """
        Calculate dimensionless DRIP number for scaling validation
        DRIP = (ρ * f² * d³) / (P * η)
        
        Where:
        ρ = material density (kg/m³)
        f = frequency (Hz)
        d = droplet diameter (m)
        P = acoustic pressure (Pa)
        η = dynamic viscosity (Pa·s)
        """
        viscosity = self._get_viscosity(self.temperature, self.material_type)
        
        drip = (
            self.material_density * 
            (self.frequency ** 2) * 
            (self.droplet_diameter ** 3)
        ) / (self.acoustic_pressure * viscosity)
        
        return drip
    
    def _get_viscosity(self, temp: float, material: str) -> float:
        """
        Get material-specific viscosity based on temperature
        Uses empirical models for common DRIP materials
        """
        viscosity_models = {
            "aluminum": lambda T: 0.85e-3 * np.exp(3000 / (T + 273.15)),
            "steel": lambda T: 1.9e-3 * np.exp(4200 / (T + 273.15)),
            "titanium": lambda T: 2.3e-3 * np.exp(4500 / (T + 273.15)),
            "copper": lambda T: 1.2e-3 * np.exp(3500 / (T + 273.15)),
        }
        
        if material.lower() in viscosity_models:
            return viscosity_models[material.lower()](temp)
        else:
            # Default to aluminum model for unknown materials
            return viscosity_models["aluminum"](temp)
    
    def validate_scaling(self, target_drip: float, tolerance: float = 0.1) -> bool:
        """Check if DRIP number is within acceptable range for scaling"""
        actual = self.calculate_drip_number()
        relative_error = abs(actual - target_drip) / target_drip
        return relative_error <= tolerance
    
    def get_scaling_parameters(self, target_drip: float) -> Dict[str, float]:
        """
        Calculate what parameters would need to change to achieve target DRIP number
        """
        current_drip = self.calculate_drip_number()
        ratio = target_drip / current_drip
        
        # Different ways to achieve the target DRIP number
        return {
            "frequency_multiplier": ratio ** 0.5,  # Change frequency
            "diameter_multiplier": ratio ** (1/3),  # Change droplet size
            "pressure_multiplier": 1 / ratio,  # Change acoustic pressure
            "current_drip": current_drip,
            "target_drip": target_drip,
            "ratio": ratio
        }

class ThermalValidation:
    """Thermal system validation calculations"""
    
    @staticmethod
    def calculate_heat_flux(power: float, area: float) -> float:
        """Calculate heat flux in W/m²"""
        return power / area
    
    @staticmethod
    def calculate_thermal_resistance(temp_diff: float, power: float) -> float:
        """Calculate thermal resistance in K/W"""
        return temp_diff / power
    
    @staticmethod
    def validate_temperature_limit(
        measured_temp: float,
        max_allowed: float,
        safety_margin: float = 0.9
    ) -> bool:
        """Check if temperature is within safe operating limits"""
        return measured_temp <= (max_allowed * safety_margin)

class AcousticValidation:
    """Acoustic system validation calculations"""
    
    @staticmethod
    def calculate_steering_efficiency(
        steering_force: float,  # μN
        acoustic_power: float,  # W
        droplet_volume: float  # m³
    ) -> float:
        """Calculate acoustic steering efficiency"""
        # Convert force to N
        force_n = steering_force * 1e-6
        
        # Calculate efficiency metric
        efficiency = (force_n * droplet_volume) / acoustic_power
        return efficiency
    
    @staticmethod
    def validate_steering_force(
        measured_force: float,  # μN
        min_required: float = 40.0,  # μN
        target: float = 96.0  # μN
    ) -> Dict[str, bool]:
        """Validate steering force meets requirements"""
        return {
            "meets_minimum": measured_force >= min_required,
            "meets_target": measured_force >= target,
            "force_ratio": measured_force / target
        }