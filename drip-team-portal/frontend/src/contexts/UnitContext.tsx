import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { convertUnit, formatValueWithUnit, formatRangeWithUnit } from '../utils/unitConversion';

interface UnitSetting {
  system: 'metric' | 'imperial';
  scale: string;
  precision?: number; // Decimal precision (default 0.01 means 2 decimal places)
}

interface UnitSettings {
  [dimension: string]: UnitSetting;
}

interface UnitContextValue {
  unitSettings: UnitSettings;
  updateUnitSetting: (dimension: string, setting: UnitSetting) => void;
  convertToUserUnit: (value: number, fromUnit: string, dimension: string) => number;
  formatWithUserUnit: (value: number | null | undefined, dimension: string, precision?: number) => string;
  formatRangeWithUserUnit: (min: number | null | undefined, max: number | null | undefined, dimension: string, precision?: number) => string;
  getUserUnit: (dimension: string) => string;
  getDimensionFromUnit: (unit: string) => string | null;
  isLoading: boolean;
  saveAllPreferences: (settings?: UnitSettings) => Promise<void>;
}

const UnitContext = createContext<UnitContextValue | null>(null);

// Map units to their dimensions
const UNIT_TO_DIMENSION: Record<string, string> = {
  // Length units
  'nm': 'length', 'μm': 'length', 'mm': 'length', 'cm': 'length', 'm': 'length', 'km': 'length',
  'in': 'length', 'ft': 'length', 'yd': 'length', 'mi': 'length', 'mil': 'length', 'thou': 'length',

  // Area units
  'mm²': 'area', 'cm²': 'area', 'm²': 'area', 'km²': 'area', 'ha': 'area',
  'in²': 'area', 'ft²': 'area', 'yd²': 'area', 'mi²': 'area', 'acre': 'area',

  // Volume units
  'mm³': 'volume', 'cm³': 'volume', 'mL': 'volume', 'L': 'volume', 'm³': 'volume', 'km³': 'volume',
  'in³': 'volume', 'ft³': 'volume', 'fl oz': 'volume', 'gal': 'volume', 'bbl': 'volume',

  // Mass units
  'μg': 'mass', 'mg': 'mass', 'g': 'mass', 'kg': 'mass', 't': 'mass', 'Mt': 'mass',
  'oz': 'mass', 'lb': 'mass', 'ton': 'mass', 'grain': 'mass',

  // Force units
  'μN': 'force', 'mN': 'force', 'N': 'force', 'kN': 'force', 'MN': 'force',
  'lbf': 'force', 'ozf': 'force', 'kip': 'force', 'pdl': 'force',

  // Pressure/Stress units
  'Pa': 'pressure', 'kPa': 'pressure', 'MPa': 'pressure', 'GPa': 'pressure', 'bar': 'pressure', 'mbar': 'pressure',
  'psi': 'pressure', 'psf': 'pressure', 'inHg': 'pressure', 'inH₂O': 'pressure', 'ksi': 'pressure',

  // Temperature units
  'K': 'temperature', '°C': 'temperature', '°F': 'temperature', '°R': 'temperature',

  // Time units
  'ps': 'time', 'ns': 'time', 'μs': 'time', 'ms': 'time', 's': 'time', 'min': 'time',
  'h': 'time', 'd': 'time', 'wk': 'time', 'mo': 'time', 'yr': 'time',

  // Frequency units
  'Hz': 'frequency', 'kHz': 'frequency', 'MHz': 'frequency', 'GHz': 'frequency', 'THz': 'frequency',
  'mHz': 'frequency', 'rpm': 'angularVelocity', 'rps': 'angularVelocity',

  // Energy units
  'J': 'energy', 'kJ': 'energy', 'MJ': 'energy', 'GJ': 'energy', 'Wh': 'energy', 'kWh': 'energy',
  'cal': 'energy', 'eV': 'energy', 'BTU': 'energy', 'ft·lbf': 'energy', 'hp·h': 'energy',

  // Power units
  'W': 'power', 'mW': 'power', 'kW': 'power', 'MW': 'power', 'GW': 'power',
  'hp': 'power', 'BTU/h': 'power', 'ft·lbf/s': 'power',

  // Torque units
  'N·m': 'torque', 'kN·m': 'torque', 'N·mm': 'torque', 'mN·m': 'torque',
  'lbf·ft': 'torque', 'lbf·in': 'torque', 'ozf·in': 'torque',

  // Density units
  'kg/m³': 'density', 'g/cm³': 'density', 'kg/L': 'density', 'g/mL': 'density',
  'lb/ft³': 'density', 'lb/in³': 'density', 'lb/gal': 'density', 'oz/in³': 'density',

  // Strain units (dimensionless)
  '1': 'strain', 'μɛ': 'strain', '%': 'strain', '‰': 'strain',

  // Angular units
  'rad': 'angle', 'mrad': 'angle', 'μrad': 'angle',
  'deg': 'angle', 'arcmin': 'angle', 'arcsec': 'angle', 'rev': 'angle',
  '°': 'angle',

  // Angular velocity
  'rad/s': 'angularVelocity', 'rad/min': 'angularVelocity', 'deg/s': 'angularVelocity',

  // Velocity
  'mm/s': 'velocity', 'cm/s': 'velocity', 'm/s': 'velocity', 'km/h': 'velocity', 'm/min': 'velocity',
  'ft/s': 'velocity', 'ft/min': 'velocity', 'mph': 'velocity', 'in/s': 'velocity', 'kn': 'velocity',

  // Acceleration
  'm/s²': 'acceleration', 'cm/s²': 'acceleration',
  'ft/s²': 'acceleration', 'in/s²': 'acceleration',

  // Flow rate
  'm³/s': 'flowRate', 'L/s': 'flowRate', 'L/min': 'flowRate', 'm³/h': 'flowRate', 'mL/min': 'flowRate',
  'ft³/s': 'flowRate', 'ft³/min': 'flowRate', 'gal/min': 'flowRate', 'gal/h': 'flowRate',

  // Viscosity
  'Pa·s': 'viscosity', 'mPa·s': 'viscosity', 'cP': 'viscosity', 'P': 'viscosity',
  'lbf·s/ft²': 'viscosity', 'lbf·s/in²': 'viscosity',

  // Kinematic viscosity
  'm²/s': 'kinematicViscosity', 'mm²/s': 'kinematicViscosity', 'cSt': 'kinematicViscosity', 'St': 'kinematicViscosity',
  'ft²/s': 'kinematicViscosity', 'in²/s': 'kinematicViscosity',

  // Thermal properties
  'W/(m·K)': 'thermalConductivity', 'mW/(m·K)': 'thermalConductivity',
  'BTU/(h·ft·°F)': 'thermalConductivity', 'BTU·in/(h·ft²·°F)': 'thermalConductivity',

  'J/(kg·K)': 'specificHeat', 'kJ/(kg·K)': 'specificHeat', 'cal/(g·°C)': 'specificHeat',
  'BTU/(lb·°F)': 'specificHeat',

  '1/K': 'thermalExpansion', '1/°C': 'thermalExpansion', 'ppm/K': 'thermalExpansion', 'ppm/°C': 'thermalExpansion',
  '1/°F': 'thermalExpansion', '1/°R': 'thermalExpansion', 'ppm/°F': 'thermalExpansion',

  // Electrical units
  'A': 'electricCurrent', 'mA': 'electricCurrent', 'μA': 'electricCurrent', 'nA': 'electricCurrent', 'kA': 'electricCurrent',
  'V': 'voltage', 'mV': 'voltage', 'μV': 'voltage', 'nV': 'voltage', 'kV': 'voltage', 'MV': 'voltage',
  'Ω': 'resistance', 'mΩ': 'resistance', 'kΩ': 'resistance', 'MΩ': 'resistance', 'GΩ': 'resistance',
  'F': 'capacitance', 'mF': 'capacitance', 'μF': 'capacitance', 'nF': 'capacitance', 'pF': 'capacitance',
  'H': 'inductance', 'mH': 'inductance', 'μH': 'inductance', 'nH': 'inductance',
  'C': 'electricCharge', 'mC': 'electricCharge', 'μC': 'electricCharge', 'nC': 'electricCharge', 'pC': 'electricCharge',
  'A·h': 'electricCharge', 'mA·h': 'electricCharge',

  // Magnetic units
  'T': 'magneticField', 'mT': 'magneticField', 'μT': 'magneticField', 'nT': 'magneticField', 'G': 'magneticField', 'kG': 'magneticField',
  'Wb': 'magneticFlux', 'mWb': 'magneticFlux', 'μWb': 'magneticFlux', 'Mx': 'magneticFlux',

  // Light
  'cd': 'luminousIntensity', 'mcd': 'luminousIntensity', 'kcd': 'luminousIntensity',
  'cp': 'luminousIntensity', // candlepower

  // Chemical
  'mol': 'amountOfSubstance', 'mmol': 'amountOfSubstance', 'μmol': 'amountOfSubstance', 'nmol': 'amountOfSubstance', 'kmol': 'amountOfSubstance',
  'lbmol': 'amountOfSubstance',

  'mol/m³': 'concentration', 'mol/L': 'concentration', 'mmol/L': 'concentration', 'μmol/L': 'concentration',
  'M': 'concentration', 'mM': 'concentration', 'mol/ft³': 'concentration', 'mol/gal': 'concentration',
};

// Determine if a unit is imperial or metric
const IMPERIAL_UNITS = new Set([
  'in', 'ft', 'yd', 'mi', 'mil', 'thou',
  'in²', 'ft²', 'yd²', 'mi²', 'acre',
  'in³', 'ft³', 'fl oz', 'gal', 'bbl',
  'oz', 'lb', 'ton', 'grain',
  'lbf', 'ozf', 'kip', 'pdl',
  'psi', 'psf', 'inHg', 'inH₂O', 'ksi',
  '°F', '°R',
  'BTU', 'ft·lbf', 'hp·h',
  'hp', 'BTU/h', 'ft·lbf/s',
  'lbf·ft', 'lbf·in', 'ozf·in',
  'lb/ft³', 'lb/in³', 'lb/gal', 'oz/in³',
  'ft/s', 'ft/min', 'mph', 'in/s', 'kn',
  'ft/s²', 'in/s²',
  'ft³/s', 'ft³/min', 'gal/min', 'gal/h',
  'lbf·s/ft²', 'lbf·s/in²',
  'ft²/s', 'in²/s',
  'BTU/(h·ft·°F)', 'BTU·in/(h·ft²·°F)',
  'BTU/(lb·°F)',
  '1/°F', '1/°R', 'ppm/°F',
]);

const DEFAULT_UNIT_SETTINGS: UnitSettings = {
  length: { system: 'metric', scale: 'm', precision: 0.01 },
  area: { system: 'metric', scale: 'm²', precision: 0.01 },
  volume: { system: 'metric', scale: 'm³', precision: 0.01 },
  angle: { system: 'metric', scale: 'rad', precision: 0.01 },
  mass: { system: 'metric', scale: 'kg', precision: 0.01 },
  force: { system: 'metric', scale: 'N', precision: 0.01 },
  pressure: { system: 'metric', scale: 'Pa', precision: 0.01 },
  stress: { system: 'metric', scale: 'Pa', precision: 0.01 },
  strain: { system: 'metric', scale: '1', precision: 0.0001 },
  density: { system: 'metric', scale: 'kg/m³', precision: 0.01 },
  torque: { system: 'metric', scale: 'N·m', precision: 0.01 },
  energy: { system: 'metric', scale: 'J', precision: 0.01 },
  power: { system: 'metric', scale: 'W', precision: 0.01 },
  temperature: { system: 'metric', scale: 'K', precision: 0.01 },
  thermalConductivity: { system: 'metric', scale: 'W/(m·K)', precision: 0.01 },
  specificHeat: { system: 'metric', scale: 'J/(kg·K)', precision: 0.01 },
  thermalExpansion: { system: 'metric', scale: '1/K', precision: 0.000001 },
  electricCurrent: { system: 'metric', scale: 'A', precision: 0.01 },
  voltage: { system: 'metric', scale: 'V', precision: 0.01 },
  resistance: { system: 'metric', scale: 'Ω', precision: 0.01 },
  capacitance: { system: 'metric', scale: 'F', precision: 0.01 },
  inductance: { system: 'metric', scale: 'H', precision: 0.01 },
  electricCharge: { system: 'metric', scale: 'C', precision: 0.01 },
  magneticField: { system: 'metric', scale: 'T', precision: 0.01 },
  magneticFlux: { system: 'metric', scale: 'Wb', precision: 0.01 },
  time: { system: 'metric', scale: 's', precision: 0.01 },
  frequency: { system: 'metric', scale: 'Hz', precision: 0.01 },
  angularVelocity: { system: 'metric', scale: 'rad/s', precision: 0.01 },
  velocity: { system: 'metric', scale: 'm/s', precision: 0.01 },
  acceleration: { system: 'metric', scale: 'm/s²', precision: 0.01 },
  flowRate: { system: 'metric', scale: 'm³/s', precision: 0.01 },
  viscosity: { system: 'metric', scale: 'Pa·s', precision: 0.01 },
  kinematicViscosity: { system: 'metric', scale: 'm²/s', precision: 0.01 },
  luminousIntensity: { system: 'metric', scale: 'cd', precision: 0.01 },
  amountOfSubstance: { system: 'metric', scale: 'mol', precision: 0.01 },
  concentration: { system: 'metric', scale: 'mol/m³', precision: 0.01 },
};

interface BackendPreference {
  id: number;
  quantity_type: string;
  unit_symbol: string;
  unit_name: string;
  unit_id: number;
  precision: number;
}

export const UnitProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  // Local state for unit settings - starts with defaults, merges with API data
  const [unitSettings, setUnitSettings] = useState<UnitSettings>(() => {
    // Load from localStorage as initial fallback
    const saved = localStorage.getItem('unitSettings');
    return saved ? JSON.parse(saved) : DEFAULT_UNIT_SETTINGS;
  });

  // Fetch preferences from backend
  const { data: backendPreferences, isLoading } = useQuery<BackendPreference[]>({
    queryKey: ['unit-preferences'],
    queryFn: async () => {
      const response = await api.get('/api/v1/me/unit-preferences');
      return response.data;
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Merge backend preferences with defaults when they arrive
  useEffect(() => {
    if (backendPreferences && backendPreferences.length > 0) {
      setUnitSettings(prev => {
        const merged = { ...prev };
        for (const pref of backendPreferences) {
          const system = IMPERIAL_UNITS.has(pref.unit_symbol) ? 'imperial' : 'metric';
          merged[pref.quantity_type] = {
            system,
            scale: pref.unit_symbol,
            precision: pref.precision,
          };
        }
        return merged;
      });
    }
  }, [backendPreferences]);

  // Save to localStorage as backup whenever settings change
  useEffect(() => {
    localStorage.setItem('unitSettings', JSON.stringify(unitSettings));
  }, [unitSettings]);

  // Mutation to update a single preference
  const updatePreferenceMutation = useMutation({
    mutationFn: async (data: { quantity_type: string; unit_symbol: string; precision: number }) => {
      const response = await api.put(`/api/v1/me/unit-preferences/${data.quantity_type}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-preferences'] });
    },
  });

  // Mutation to bulk update all preferences
  const bulkUpdateMutation = useMutation({
    mutationFn: async (preferences: { quantity_type: string; unit_symbol: string; precision: number }[]) => {
      const response = await api.put('/api/v1/me/unit-preferences', { preferences });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['unit-preferences'] });
    },
  });

  // Update a single unit setting (local only - use saveAllPreferences to persist)
  const updateUnitSetting = useCallback((dimension: string, setting: UnitSetting) => {
    setUnitSettings(prev => ({
      ...prev,
      [dimension]: setting
    }));
  }, []);

  // Save all current settings to the backend
  // Accepts optional settings parameter to avoid race condition with state updates
  const saveAllPreferences = useCallback(async (settingsToSave?: UnitSettings) => {
    const settingsSource = settingsToSave || unitSettings;
    const preferences = Object.entries(settingsSource).map(([dimension, setting]) => ({
      quantity_type: dimension,
      unit_symbol: setting.scale,
      precision: setting.precision ?? 0.01,
    }));
    await bulkUpdateMutation.mutateAsync(preferences);
  }, [unitSettings, bulkUpdateMutation]);

  const getDimensionFromUnit = useCallback((unit: string): string | null => {
    return UNIT_TO_DIMENSION[unit] || null;
  }, []);

  const getUserUnit = useCallback((dimension: string): string => {
    return unitSettings[dimension]?.scale || DEFAULT_UNIT_SETTINGS[dimension]?.scale || '';
  }, [unitSettings]);

  const convertToUserUnit = useCallback((value: number, fromUnit: string, dimension: string): number => {
    const userUnit = getUserUnit(dimension);
    if (!userUnit || userUnit === fromUnit) return value;

    return convertUnit(value, fromUnit, userUnit);
  }, [getUserUnit]);

  const formatWithUserUnit = useCallback((
    value: number | null | undefined,
    dimension: string,
    overridePrecision?: number
  ): string => {
    if (value === null || value === undefined) return '';
    const userUnit = getUserUnit(dimension);
    const setting = unitSettings[dimension] || DEFAULT_UNIT_SETTINGS[dimension];
    const precision = overridePrecision !== undefined ? overridePrecision : setting?.precision || 0.01;

    // Round value to precision
    const rounded = Math.round(value / precision) * precision;

    // Calculate decimal places from precision
    const decimalPlaces = Math.max(0, -Math.floor(Math.log10(precision)));

    return formatValueWithUnit(rounded, userUnit, decimalPlaces);
  }, [getUserUnit, unitSettings]);

  const formatRangeWithUserUnit = useCallback((
    min: number | null | undefined,
    max: number | null | undefined,
    dimension: string,
    overridePrecision?: number
  ): string => {
    if (min === null || min === undefined || max === null || max === undefined) return '';
    const userUnit = getUserUnit(dimension);
    const setting = unitSettings[dimension] || DEFAULT_UNIT_SETTINGS[dimension];
    const precision = overridePrecision !== undefined ? overridePrecision : setting?.precision || 0.01;

    // Round values to precision
    const roundedMin = Math.round(min / precision) * precision;
    const roundedMax = Math.round(max / precision) * precision;

    // Calculate decimal places from precision
    const decimalPlaces = Math.max(0, -Math.floor(Math.log10(precision)));

    return formatRangeWithUnit(roundedMin, roundedMax, userUnit, decimalPlaces);
  }, [getUserUnit, unitSettings]);

  return (
    <UnitContext.Provider value={{
      unitSettings,
      updateUnitSetting,
      convertToUserUnit,
      formatWithUserUnit,
      formatRangeWithUserUnit,
      getUserUnit,
      getDimensionFromUnit,
      isLoading,
      saveAllPreferences,
    }}>
      {children}
    </UnitContext.Provider>
  );
};

export const useUnits = () => {
  const context = useContext(UnitContext);
  if (!context) {
    throw new Error('useUnits must be used within a UnitProvider');
  }
  return context;
};
