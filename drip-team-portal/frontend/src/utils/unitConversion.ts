interface UnitConversion {
  from: string;
  to: string;
  factor: number;
  offset?: number; // For temperature conversions
}

// Base SI units for each dimension
export const BASE_UNITS: Record<string, string> = {
  length: 'm',
  area: 'm²',
  volume: 'm³',
  mass: 'kg',
  force: 'N',
  pressure: 'Pa',
  temperature: 'K',
  time: 's',
  energy: 'J',
  power: 'W',
  // Add more as needed
};

// Conversion factors to base units
export const TO_BASE_CONVERSIONS: Record<string, number> = {
  // Length - to meters
  'nm': 1e-9,
  'μm': 1e-6,
  'mm': 0.001,
  'cm': 0.01,
  'm': 1,
  'km': 1000,
  'in': 0.0254,
  'ft': 0.3048,
  'yd': 0.9144,
  'mi': 1609.344,
  'mil': 0.0000254,
  'thou': 0.0000254,
  
  // Area - to m²
  'mm²': 1e-6,
  'cm²': 1e-4,
  'm²': 1,
  'km²': 1e6,
  'ha': 1e4,
  'in²': 0.00064516,
  'ft²': 0.092903,
  'yd²': 0.836127,
  'mi²': 2.59e6,
  'acre': 4046.86,
  
  // Volume - to m³
  'mm³': 1e-9,
  'cm³': 1e-6,
  'mL': 1e-6,
  'L': 0.001,
  'm³': 1,
  'km³': 1e9,
  'in³': 1.6387e-5,
  'ft³': 0.0283168,
  'fl oz': 2.9574e-5,
  'gal': 0.00378541,
  'bbl': 0.158987,
  
  // Mass - to kg
  'μg': 1e-9,
  'mg': 1e-6,
  'g': 0.001,
  'kg': 1,
  't': 1000,
  'Mt': 1e6,
  'oz': 0.0283495,
  'lb': 0.453592,
  'ton': 907.185,
  'grain': 6.4799e-5,
  
  // Force - to N
  'μN': 1e-6,
  'mN': 1e-3,
  'N': 1,
  'kN': 1000,
  'MN': 1e6,
  'lbf': 4.44822,
  'ozf': 0.278014,
  'kip': 4448.22,
  'pdl': 0.138255,
  
  // Pressure - to Pa
  'Pa': 1,
  'kPa': 1000,
  'MPa': 1e6,
  'GPa': 1e9,
  'bar': 1e5,
  'mbar': 100,
  'psi': 6894.76,
  'psf': 47.8803,
  'inHg': 3386.39,
  'inH₂O': 249.082,
  'ksi': 6.89476e6,
  
  // Time - to seconds
  'ps': 1e-12,
  'ns': 1e-9,
  'μs': 1e-6,
  'ms': 0.001,
  's': 1,
  'min': 60,
  'h': 3600,
  'd': 86400,
  'wk': 604800,
  'mo': 2.628e6,
  'yr': 3.154e7,
  
  // Energy - to J
  'J': 1,
  'kJ': 1000,
  'MJ': 1e6,
  'GJ': 1e9,
  'Wh': 3600,
  'kWh': 3.6e6,
  'cal': 4.184,
  'eV': 1.6022e-19,
  'BTU': 1055.06,
  'ft·lbf': 1.35582,
  'hp·h': 2.685e6,
  
  // Power - to W
  'W': 1,
  'mW': 0.001,
  'kW': 1000,
  'MW': 1e6,
  'GW': 1e9,
  'hp': 745.7,
  'BTU/h': 0.293071,
  'ft·lbf/s': 1.35582,
  
  // Frequency - to Hz
  'Hz': 1,
  'kHz': 1000,
  'MHz': 1e6,
  'GHz': 1e9,
  'THz': 1e12,
  'mHz': 0.001,
  'rpm': 1/60,  // revolutions per minute to Hz
  'rps': 1,     // revolutions per second

  // Density - to kg/m³
  'kg/m³': 1,
  'g/cm³': 1000,
  'kg/L': 1000,
  'g/mL': 1000,
  'lb/ft³': 16.0185,
  'lb/in³': 27679.9,
  'lb/gal': 119.826,
  'oz/in³': 1729.99,

  // Thermal expansion - to 1/K
  '1/K': 1,
  '1/°C': 1,  // Same as 1/K for coefficients
  'ppm/K': 1e-6,
  'ppm/°C': 1e-6,
  'µm/(m·K)': 1e-6,  // Same as ppm/K
  '1/°F': 1.8,  // 1/°F = 1.8 * 1/K
  '1/°R': 1.8,
  'ppm/°F': 1.8e-6,

  // Thermal conductivity - to W/(m·K)
  'W/(m·K)': 1,
  'mW/(m·K)': 0.001,
  'BTU/(h·ft·°F)': 1.731,
  'BTU·in/(h·ft²·°F)': 0.1442,

  // Specific heat - to J/(kg·K)
  'J/(kg·K)': 1,
  'kJ/(kg·K)': 1000,
  'cal/(g·°C)': 4184,
  'BTU/(lb·°F)': 4186.8,
};

// Temperature unit aliases for robust matching
// Note: Avoiding single letters like 'C' (Coulombs), 'F' (Farads), 'R' that conflict with other units
const TEMP_ALIASES: Record<string, string> = {
  'K': 'K',
  'kelvin': 'K',
  '°C': '°C',
  '℃': '°C',
  'degC': '°C',
  'celsius': '°C',
  '°F': '°F',
  '℉': '°F',
  'degF': '°F',
  'fahrenheit': '°F',
  '°R': '°R',
  'rankine': '°R',
};

// Normalize temperature unit to canonical form
function normalizeTemperatureUnit(unit: string): string {
  return TEMP_ALIASES[unit] || unit;
}

// Temperature conversions (special case)
export function convertTemperature(value: number, fromUnit: string, toUnit: string): number {
  // Normalize units to handle variations like 'C' vs '°C'
  const from = normalizeTemperatureUnit(fromUnit);
  const to = normalizeTemperatureUnit(toUnit);

  if (from === to) return value;

  let kelvin = value;

  // Convert to Kelvin first
  switch (from) {
    case 'K':
      kelvin = value;
      break;
    case '°C':
      kelvin = value + 273.15;
      break;
    case '°F':
      kelvin = (value - 32) * 5/9 + 273.15;
      break;
    case '°R':
      kelvin = value * 5/9;
      break;
    default:
      console.warn(`Unknown temperature unit: ${fromUnit}`);
      return value;
  }

  // Convert from Kelvin to target
  switch (to) {
    case 'K':
      return kelvin;
    case '°C':
      return kelvin - 273.15;
    case '°F':
      return (kelvin - 273.15) * 9/5 + 32;
    case '°R':
      return kelvin * 9/5;
    default:
      console.warn(`Unknown temperature unit: ${toUnit}`);
      return value;
  }
}

// Check if a unit is a temperature unit
function isTemperatureUnit(unit: string): boolean {
  return unit in TEMP_ALIASES;
}

export function convertUnit(value: number, fromUnit: string, toUnit: string): number {
  if (fromUnit === toUnit) return value;

  // Handle temperature specially - check both raw and normalized forms
  if (isTemperatureUnit(fromUnit) && isTemperatureUnit(toUnit)) {
    return convertTemperature(value, fromUnit, toUnit);
  }

  // Convert to base unit first
  const toBase = TO_BASE_CONVERSIONS[fromUnit] || 1;
  const fromBase = TO_BASE_CONVERSIONS[toUnit] || 1;

  return value * toBase / fromBase;
}

export function parseValueWithUnit(input: string, defaultUnit: string): {
  value?: number;
  min?: number;
  max?: number;
  unit: string;
  isRange: boolean;
} {
  const trimmed = input.trim();
  if (!trimmed) {
    return { unit: defaultUnit, isRange: false };
  }
  
  // Regular expressions for different formats
  const singleValueRegex = /^(-?\d+\.?\d*)\s*([a-zA-Z°₀₁₂₃⁰¹²³·/%]*)?$/;
  const rangeRegex = /^(-?\d+\.?\d*)\s*(?:to|-|–)\s*(-?\d+\.?\d*)\s*([a-zA-Z°₀₁₂₃⁰¹²³·/%]*)?$/;
  const toleranceRegex = /^(-?\d+\.?\d*)\s*(?:±|\\+\/-)\s*(-?\d+\.?\d*)\s*([a-zA-Z°₀₁₂₃⁰¹²³·/%]*)?$/;
  
  // Check for range format (e.g., "10-20 mm" or "10 to 20 mm")
  const rangeMatch = trimmed.match(rangeRegex);
  if (rangeMatch) {
    const [_, min, max, unit] = rangeMatch;
    return {
      min: parseFloat(min),
      max: parseFloat(max),
      unit: unit || defaultUnit,
      isRange: true
    };
  }
  
  // Check for tolerance format (e.g., "10 ± 2 mm")
  const toleranceMatch = trimmed.match(toleranceRegex);
  if (toleranceMatch) {
    const [_, value, tolerance, unit] = toleranceMatch;
    const val = parseFloat(value);
    const tol = parseFloat(tolerance);
    return {
      min: val - tol,
      max: val + tol,
      unit: unit || defaultUnit,
      isRange: true
    };
  }
  
  // Check for single value (e.g., "10 mm" or "10")
  const singleMatch = trimmed.match(singleValueRegex);
  if (singleMatch) {
    const [_, value, unit] = singleMatch;
    return {
      value: parseFloat(value),
      unit: unit || defaultUnit,
      isRange: false
    };
  }
  
  // If no match, return default
  return { unit: defaultUnit, isRange: false };
}

export function formatValueWithUnit(
  value: number | null | undefined, 
  unit: string, 
  decimalPlaces: number = 2
): string {
  if (value === null || value === undefined) return '';
  
  // Special handling for frequency units to show appropriate scale
  if (unit === 'Hz' && value >= 1000) {
    if (value >= 1e12) {
      return `${(value / 1e12).toFixed(decimalPlaces)} THz`;
    } else if (value >= 1e9) {
      return `${(value / 1e9).toFixed(decimalPlaces)} GHz`;
    } else if (value >= 1e6) {
      return `${(value / 1e6).toFixed(decimalPlaces)} MHz`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(decimalPlaces)} kHz`;
    }
  }
  
  // Check if we should use scientific notation (> 1000 or < 0.001)
  if (Math.abs(value) > 1000 || (Math.abs(value) < 0.001 && value !== 0)) {
    // Use scientific notation with specified decimal places
    return `${value.toExponential(decimalPlaces)} ${unit}`;
  }
  
  // Always show the exact number of decimal places requested
  return `${value.toFixed(decimalPlaces)} ${unit}`;
}

export function formatRangeWithUnit(
  min: number | null | undefined,
  max: number | null | undefined,
  unit: string,
  decimalPlaces: number = 2
): string {
  if (min === null || min === undefined || max === null || max === undefined) return '';
  
  // Special handling for frequency units
  if (unit === 'Hz' && (min >= 1000 || max >= 1000)) {
    let scale = 'Hz';
    let divisor = 1;
    
    // Use the larger value to determine the scale
    const maxVal = Math.max(Math.abs(min), Math.abs(max));
    if (maxVal >= 1e12) {
      scale = 'THz';
      divisor = 1e12;
    } else if (maxVal >= 1e9) {
      scale = 'GHz';
      divisor = 1e9;
    } else if (maxVal >= 1e6) {
      scale = 'MHz';
      divisor = 1e6;
    } else if (maxVal >= 1000) {
      scale = 'kHz';
      divisor = 1000;
    }
    
    return `${(min / divisor).toFixed(decimalPlaces)} - ${(max / divisor).toFixed(decimalPlaces)} ${scale}`;
  }
  
  // Check if both values should use scientific notation
  if ((Math.abs(min) > 1000 || Math.abs(max) > 1000) || 
      ((Math.abs(min) < 0.001 && min !== 0) || (Math.abs(max) < 0.001 && max !== 0))) {
    return `${min.toExponential(decimalPlaces)} - ${max.toExponential(decimalPlaces)} ${unit}`;
  }
  
  // Regular formatting with exact decimal places
  return `${min.toFixed(decimalPlaces)} - ${max.toFixed(decimalPlaces)} ${unit}`;
}

// ============== API Sync (Optional) ==============
// These functions can be used to fetch conversion data from the backend API
// The backend is the single source of truth for unit definitions

interface BulkUnitsResponse {
  conversions: Record<string, { factor: number; offset: number }>;
  aliases: Record<string, string>;
  base_units: Record<string, string>;
  units: Record<string, { name: string; quantity_type: string; is_base_unit: boolean }>;
}

let _apiConversions: BulkUnitsResponse | null = null;

/**
 * Fetch unit conversion data from the backend API.
 * This can be used to sync frontend with backend or for dynamic unit loading.
 */
export async function fetchUnitConversions(): Promise<BulkUnitsResponse | null> {
  try {
    const response = await fetch('/api/v1/units/bulk');
    if (!response.ok) {
      console.warn('Failed to fetch unit conversions from API');
      return null;
    }
    _apiConversions = await response.json();
    return _apiConversions;
  } catch (error) {
    console.warn('Error fetching unit conversions:', error);
    return null;
  }
}

/**
 * Get conversion factor, preferring API data if available.
 * Falls back to hardcoded TO_BASE_CONVERSIONS.
 */
export function getConversionFactor(unit: string): number {
  // Try API data first
  if (_apiConversions?.conversions[unit]) {
    return _apiConversions.conversions[unit].factor;
  }
  // Fall back to hardcoded
  return TO_BASE_CONVERSIONS[unit] ?? 1;
}

/**
 * Check if API conversions have been loaded.
 */
export function hasApiConversions(): boolean {
  return _apiConversions !== null;
}