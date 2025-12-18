/**
 * Unit System Types - Dimensional Analysis
 *
 * Units are defined by 7 SI base dimensions:
 * - Length (L) - meter
 * - Mass (M) - kilogram
 * - Time (T) - second
 * - Electric current (I) - ampere
 * - Temperature (Θ) - kelvin
 * - Amount of substance (N) - mole
 * - Luminous intensity (J) - candela
 */

export interface Unit {
  id: number;
  symbol: string;
  name: string;
  quantity_type?: string;
  length_dim: number;
  mass_dim: number;
  time_dim: number;
  current_dim: number;
  temperature_dim: number;
  amount_dim: number;
  luminosity_dim: number;
  is_base_unit: boolean;
  display_order: number;
}

export interface UnitCreate {
  symbol: string;
  name: string;
  quantity_type?: string;
  length_dim?: number;
  mass_dim?: number;
  time_dim?: number;
  current_dim?: number;
  temperature_dim?: number;
  amount_dim?: number;
  luminosity_dim?: number;
  is_base_unit?: boolean;
}

export interface UnitConversion {
  id: number;
  from_unit_id: number;
  to_unit_id: number;
  multiplier: number;
  offset: number;
  from_unit: Unit;
  to_unit: Unit;
}

export interface UnitConversionCreate {
  from_unit_id: number;
  to_unit_id: number;
  multiplier: number;
  offset: number;
}

export interface ConvertRequest {
  value: number;
  from_symbol: string;
  to_symbol: string;
}

export interface ConvertResponse {
  original_value: number;
  converted_value: number;
  from_unit: string;
  to_unit: string;
  success: boolean;
  error?: string;
}

export interface Dimensions {
  length_dim: number;
  mass_dim: number;
  time_dim: number;
  current_dim: number;
  temperature_dim: number;
  amount_dim: number;
  luminosity_dim: number;
  display: string;
}

export interface CompatibilityResponse {
  compatible: boolean;
  unit1: string;
  unit2: string;
  unit1_dimensions: string;
  unit2_dimensions: string;
}

export interface SeedResponse {
  success: boolean;
  units_created: number;
  conversions_created: number;
  aliases_created: number;
  message: string;
}

// Common quantity types for filtering
export type QuantityType =
  | 'length'
  | 'area'
  | 'volume'
  | 'mass'
  | 'time'
  | 'frequency'
  | 'velocity'
  | 'acceleration'
  | 'force'
  | 'pressure'
  | 'energy'
  | 'power'
  | 'temperature'
  | 'thermal_conductivity'
  | 'specific_heat'
  | 'heat_transfer_coeff'
  | 'density'
  | 'dynamic_viscosity'
  | 'kinematic_viscosity'
  | 'voltage'
  | 'resistance'
  | 'electric_current'
  | 'electric_charge'
  | 'capacitance'
  | 'inductance'
  | 'sound_level'
  | 'angle'
  | 'ratio'
  | 'torque'
  | 'mass_flow'
  | 'volume_flow';

// Helper type for dimension exponents
export interface DimensionExponents {
  L: number;  // Length
  M: number;  // Mass
  T: number;  // Time
  I: number;  // Current
  Θ: number;  // Temperature
  N: number;  // Amount
  J: number;  // Luminosity
}

// Convert Unit to DimensionExponents for easier math
export function unitToDimensions(unit: Unit): DimensionExponents {
  return {
    L: unit.length_dim,
    M: unit.mass_dim,
    T: unit.time_dim,
    I: unit.current_dim,
    Θ: unit.temperature_dim,
    N: unit.amount_dim,
    J: unit.luminosity_dim,
  };
}

// Check if two units have the same dimensions
export function areDimensionsEqual(d1: DimensionExponents, d2: DimensionExponents): boolean {
  return (
    d1.L === d2.L &&
    d1.M === d2.M &&
    d1.T === d2.T &&
    d1.I === d2.I &&
    d1.Θ === d2.Θ &&
    d1.N === d2.N &&
    d1.J === d2.J
  );
}

// Multiply dimensions (for unit * unit)
export function multiplyDimensions(d1: DimensionExponents, d2: DimensionExponents): DimensionExponents {
  return {
    L: d1.L + d2.L,
    M: d1.M + d2.M,
    T: d1.T + d2.T,
    I: d1.I + d2.I,
    Θ: d1.Θ + d2.Θ,
    N: d1.N + d2.N,
    J: d1.J + d2.J,
  };
}

// Divide dimensions (for unit / unit)
export function divideDimensions(d1: DimensionExponents, d2: DimensionExponents): DimensionExponents {
  return {
    L: d1.L - d2.L,
    M: d1.M - d2.M,
    T: d1.T - d2.T,
    I: d1.I - d2.I,
    Θ: d1.Θ - d2.Θ,
    N: d1.N - d2.N,
    J: d1.J - d2.J,
  };
}

// Check if dimensions are all zero (dimensionless)
export function isDimensionless(d: DimensionExponents): boolean {
  return d.L === 0 && d.M === 0 && d.T === 0 && d.I === 0 && d.Θ === 0 && d.N === 0 && d.J === 0;
}

// Format dimensions as a string (e.g., "L·M·T⁻²")
export function formatDimensions(d: DimensionExponents): string {
  const superscript: Record<string, string> = {
    '-': '⁻', '0': '⁰', '1': '¹', '2': '²', '3': '³',
    '4': '⁴', '5': '⁵', '6': '⁶', '7': '⁷', '8': '⁸', '9': '⁹',
  };

  const formatExp = (exp: number): string => {
    return String(exp).split('').map(c => superscript[c] || c).join('');
  };

  const parts: string[] = [];
  const symbols: [keyof DimensionExponents, string][] = [
    ['L', 'L'], ['M', 'M'], ['T', 'T'], ['I', 'I'], ['Θ', 'Θ'], ['N', 'N'], ['J', 'J'],
  ];

  for (const [key, symbol] of symbols) {
    const exp = d[key];
    if (exp === 0) continue;
    if (exp === 1) {
      parts.push(symbol);
    } else {
      parts.push(`${symbol}${formatExp(exp)}`);
    }
  }

  return parts.length > 0 ? parts.join('·') : 'dimensionless';
}
