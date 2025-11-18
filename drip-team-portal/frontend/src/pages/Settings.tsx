import React, { useState } from 'react';
import { useAuth0 } from '@auth0/auth0-react';
import { useUnits } from '../contexts/UnitContext';

interface UnitSetting {
  system: 'metric' | 'imperial';
  scale: string;
  precision?: number;
}

interface UnitSettings {
  [dimension: string]: UnitSetting;
}

const Settings: React.FC = () => {
  const { user } = useAuth0();
  const { unitSettings: currentUnitSettings, updateUnitSetting } = useUnits();
  const [theme, setTheme] = useState<'light' | 'dark' | 'system'>('system');
  const [expandedSections, setExpandedSections] = useState<{ [key: string]: boolean }>({
    'general': true,
    'units': true
  });
  const [unitSettings, setUnitSettings] = useState<UnitSettings>(currentUnitSettings || {
    // Geometric dimensions
    length: { system: 'metric', scale: 'm' },
    area: { system: 'metric', scale: 'm²' },
    volume: { system: 'metric', scale: 'm³' },
    angle: { system: 'metric', scale: 'rad' },
    
    // Mechanical dimensions
    mass: { system: 'metric', scale: 'kg' },
    force: { system: 'metric', scale: 'N' },
    pressure: { system: 'metric', scale: 'Pa' },
    stress: { system: 'metric', scale: 'Pa' },
    strain: { system: 'metric', scale: '1' },
    density: { system: 'metric', scale: 'kg/m³' },
    torque: { system: 'metric', scale: 'N·m' },
    energy: { system: 'metric', scale: 'J' },
    power: { system: 'metric', scale: 'W' },
    
    // Thermal dimensions
    temperature: { system: 'metric', scale: 'K' },
    thermalConductivity: { system: 'metric', scale: 'W/(m·K)' },
    specificHeat: { system: 'metric', scale: 'J/(kg·K)' },
    thermalExpansion: { system: 'metric', scale: '1/K' },
    
    // Electrical dimensions
    electricCurrent: { system: 'metric', scale: 'A' },
    voltage: { system: 'metric', scale: 'V' },
    resistance: { system: 'metric', scale: 'Ω' },
    capacitance: { system: 'metric', scale: 'F' },
    inductance: { system: 'metric', scale: 'H' },
    electricCharge: { system: 'metric', scale: 'C' },
    
    // Magnetic dimensions
    magneticField: { system: 'metric', scale: 'T' },
    magneticFlux: { system: 'metric', scale: 'Wb' },
    
    // Time and frequency
    time: { system: 'metric', scale: 's' },
    frequency: { system: 'metric', scale: 'Hz' },
    angularVelocity: { system: 'metric', scale: 'rad/s' },
    
    // Flow and transport
    velocity: { system: 'metric', scale: 'm/s' },
    acceleration: { system: 'metric', scale: 'm/s²' },
    flowRate: { system: 'metric', scale: 'm³/s' },
    viscosity: { system: 'metric', scale: 'Pa·s' },
    kinematicViscosity: { system: 'metric', scale: 'm²/s' },
    
    // Other physical properties
    luminousIntensity: { system: 'metric', scale: 'cd' },
    amountOfSubstance: { system: 'metric', scale: 'mol' },
    concentration: { system: 'metric', scale: 'mol/m³' },
  });

  const unitOptions = {
    // Length units
    length: {
      metric: ['nm', 'μm', 'mm', 'cm', 'm', 'km'],
      imperial: ['in', 'ft', 'yd', 'mi', 'mil', 'thou']
    },
    // Area units
    area: {
      metric: ['mm²', 'cm²', 'm²', 'km²', 'ha'],
      imperial: ['in²', 'ft²', 'yd²', 'mi²', 'acre']
    },
    // Volume units
    volume: {
      metric: ['mm³', 'cm³', 'mL', 'L', 'm³', 'km³'],
      imperial: ['in³', 'ft³', 'fl oz', 'gal', 'bbl']
    },
    // Angle units
    angle: {
      metric: ['rad', 'mrad', 'μrad'],
      imperial: ['deg', 'arcmin', 'arcsec', 'rev']
    },
    // Mass units
    mass: {
      metric: ['μg', 'mg', 'g', 'kg', 't', 'Mt'],
      imperial: ['oz', 'lb', 'ton', 'grain']
    },
    // Force units
    force: {
      metric: ['μN', 'mN', 'N', 'kN', 'MN'],
      imperial: ['lbf', 'ozf', 'kip', 'pdl']
    },
    // Pressure units
    pressure: {
      metric: ['Pa', 'kPa', 'MPa', 'GPa', 'bar', 'mbar'],
      imperial: ['psi', 'psf', 'inHg', 'inH₂O']
    },
    // Stress units (same as pressure)
    stress: {
      metric: ['Pa', 'kPa', 'MPa', 'GPa'],
      imperial: ['psi', 'ksi', 'psf']
    },
    // Strain units (dimensionless)
    strain: {
      metric: ['1', 'μɛ', '%', '‰'],
      imperial: ['1', 'μɛ', '%', '‰']
    },
    // Density units
    density: {
      metric: ['kg/m³', 'g/cm³', 'kg/L', 'g/mL'],
      imperial: ['lb/ft³', 'lb/in³', 'lb/gal', 'oz/in³']
    },
    // Torque units
    torque: {
      metric: ['N·m', 'kN·m', 'N·mm', 'mN·m'],
      imperial: ['lbf·ft', 'lbf·in', 'ozf·in']
    },
    // Energy units
    energy: {
      metric: ['J', 'kJ', 'MJ', 'GJ', 'Wh', 'kWh', 'cal', 'eV'],
      imperial: ['BTU', 'ft·lbf', 'hp·h']
    },
    // Power units
    power: {
      metric: ['W', 'mW', 'kW', 'MW', 'GW'],
      imperial: ['hp', 'BTU/h', 'ft·lbf/s']
    },
    // Temperature units
    temperature: {
      metric: ['K', '°C'],
      imperial: ['°F', '°R']
    },
    // Thermal conductivity
    thermalConductivity: {
      metric: ['W/(m·K)', 'mW/(m·K)'],
      imperial: ['BTU/(h·ft·°F)', 'BTU·in/(h·ft²·°F)']
    },
    // Specific heat
    specificHeat: {
      metric: ['J/(kg·K)', 'kJ/(kg·K)', 'cal/(g·°C)'],
      imperial: ['BTU/(lb·°F)']
    },
    // Thermal expansion
    thermalExpansion: {
      metric: ['1/K', '1/°C', 'ppm/K', 'ppm/°C'],
      imperial: ['1/°F', '1/°R', 'ppm/°F']
    },
    // Electric current
    electricCurrent: {
      metric: ['nA', 'μA', 'mA', 'A', 'kA'],
      imperial: ['A', 'mA', 'μA'] // Same as metric
    },
    // Voltage
    voltage: {
      metric: ['nV', 'μV', 'mV', 'V', 'kV', 'MV'],
      imperial: ['V', 'mV', 'kV'] // Same as metric
    },
    // Resistance
    resistance: {
      metric: ['mΩ', 'Ω', 'kΩ', 'MΩ', 'GΩ'],
      imperial: ['Ω', 'kΩ', 'MΩ'] // Same as metric
    },
    // Capacitance
    capacitance: {
      metric: ['pF', 'nF', 'μF', 'mF', 'F'],
      imperial: ['pF', 'nF', 'μF', 'mF', 'F'] // Same as metric
    },
    // Inductance
    inductance: {
      metric: ['nH', 'μH', 'mH', 'H'],
      imperial: ['H', 'mH', 'μH'] // Same as metric
    },
    // Electric charge
    electricCharge: {
      metric: ['C', 'mC', 'μC', 'nC', 'pC', 'A·h', 'mA·h'],
      imperial: ['C', 'A·h'] // Same as metric
    },
    // Magnetic field
    magneticField: {
      metric: ['T', 'mT', 'μT', 'nT', 'G', 'kG'],
      imperial: ['T', 'G'] // Same as metric
    },
    // Magnetic flux
    magneticFlux: {
      metric: ['Wb', 'mWb', 'μWb', 'Mx'],
      imperial: ['Wb', 'Mx'] // Same as metric
    },
    // Time
    time: {
      metric: ['ps', 'ns', 'μs', 'ms', 's', 'min', 'h', 'd', 'yr'],
      imperial: ['s', 'min', 'h', 'd', 'wk', 'mo', 'yr'] // Mostly same
    },
    // Frequency
    frequency: {
      metric: ['mHz', 'Hz', 'kHz', 'MHz', 'GHz', 'THz'],
      imperial: ['Hz', 'kHz', 'MHz', 'GHz'] // Same as metric
    },
    // Angular velocity
    angularVelocity: {
      metric: ['rad/s', 'rad/min', 'deg/s'],
      imperial: ['rpm', 'rps', 'deg/s']
    },
    // Velocity
    velocity: {
      metric: ['mm/s', 'cm/s', 'm/s', 'km/h', 'm/min'],
      imperial: ['ft/s', 'ft/min', 'mph', 'in/s', 'kn']
    },
    // Acceleration
    acceleration: {
      metric: ['m/s²', 'cm/s²', 'g'],
      imperial: ['ft/s²', 'in/s²', 'g']
    },
    // Flow rate
    flowRate: {
      metric: ['m³/s', 'L/s', 'L/min', 'm³/h', 'mL/min'],
      imperial: ['ft³/s', 'ft³/min', 'gal/min', 'gal/h']
    },
    // Viscosity (dynamic)
    viscosity: {
      metric: ['Pa·s', 'mPa·s', 'cP', 'P'],
      imperial: ['lbf·s/ft²', 'lbf·s/in²']
    },
    // Kinematic viscosity
    kinematicViscosity: {
      metric: ['m²/s', 'mm²/s', 'cSt', 'St'],
      imperial: ['ft²/s', 'in²/s']
    },
    // Luminous intensity
    luminousIntensity: {
      metric: ['cd', 'mcd', 'kcd'],
      imperial: ['cd', 'cp'] // candlepower
    },
    // Amount of substance
    amountOfSubstance: {
      metric: ['mol', 'mmol', 'μmol', 'nmol', 'kmol'],
      imperial: ['mol', 'lbmol'] // pound-mole
    },
    // Concentration
    concentration: {
      metric: ['mol/m³', 'mol/L', 'mmol/L', 'μmol/L', 'M', 'mM'],
      imperial: ['mol/ft³', 'mol/gal']
    }
  };

  const unitCategories = {
    'Geometric': ['length', 'area', 'volume', 'angle'],
    'Mechanical': ['mass', 'force', 'pressure', 'stress', 'strain', 'density', 'torque', 'energy', 'power'],
    'Thermal': ['temperature', 'thermalConductivity', 'specificHeat', 'thermalExpansion'],
    'Electrical': ['electricCurrent', 'voltage', 'resistance', 'capacitance', 'inductance', 'electricCharge'],
    'Magnetic': ['magneticField', 'magneticFlux'],
    'Time & Motion': ['time', 'frequency', 'angularVelocity', 'velocity', 'acceleration'],
    'Flow & Transport': ['flowRate', 'viscosity', 'kinematicViscosity'],
    'Other': ['luminousIntensity', 'amountOfSubstance', 'concentration']
  };

  const dimensionDisplayNames: { [key: string]: string } = {
    length: 'Length',
    area: 'Area',
    volume: 'Volume',
    angle: 'Angle',
    mass: 'Mass',
    force: 'Force',
    pressure: 'Pressure',
    stress: 'Stress',
    strain: 'Strain',
    density: 'Density',
    torque: 'Torque',
    energy: 'Energy',
    power: 'Power',
    temperature: 'Temperature',
    thermalConductivity: 'Thermal Conductivity',
    specificHeat: 'Specific Heat',
    thermalExpansion: 'Thermal Expansion',
    electricCurrent: 'Electric Current',
    voltage: 'Voltage',
    resistance: 'Resistance',
    capacitance: 'Capacitance',
    inductance: 'Inductance',
    electricCharge: 'Electric Charge',
    magneticField: 'Magnetic Field',
    magneticFlux: 'Magnetic Flux',
    time: 'Time',
    frequency: 'Frequency',
    angularVelocity: 'Angular Velocity',
    velocity: 'Velocity',
    acceleration: 'Acceleration',
    flowRate: 'Flow Rate',
    viscosity: 'Dynamic Viscosity',
    kinematicViscosity: 'Kinematic Viscosity',
    luminousIntensity: 'Luminous Intensity',
    amountOfSubstance: 'Amount of Substance',
    concentration: 'Concentration'
  };

  const handleSystemChange = (dimension: string, system: 'metric' | 'imperial') => {
    const options = unitOptions[dimension as keyof typeof unitOptions];
    const defaultScale = options[system][0];
    
    setUnitSettings(prev => ({
      ...prev,
      [dimension]: { system, scale: defaultScale }
    }));
  };

  const handleScaleChange = (dimension: string, scale: string) => {
    setUnitSettings(prev => ({
      ...prev,
      [dimension]: { ...prev[dimension], scale }
    }));
  };

  const handlePrecisionChange = (dimension: string, precision: number) => {
    setUnitSettings(prev => ({
      ...prev,
      [dimension]: { ...prev[dimension], precision }
    }));
  };

  const toggleSection = (section: string) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
        <p className="mt-1 text-sm text-gray-600">
          Manage your account settings and preferences
        </p>
      </div>

      {/* General Settings */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('general')}
          className="w-full px-6 py-4 bg-white hover:bg-gray-50 flex items-center justify-between text-left transition-colors"
        >
          <h2 className="text-lg font-medium text-gray-900">General Settings</h2>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              expandedSections['general'] ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {expandedSections['general'] && (
        <div className="px-6 pb-6 pt-2 border-t">
        <div className="space-y-4">
          {/* Account Information */}
          <div>
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
              type="email"
              value={user?.email || 'user@drip-3d.com'}
              disabled
              className="mt-1 block w-full rounded-md border-gray-300 bg-gray-50 shadow-sm sm:text-sm"
            />
          </div>

          {/* Theme Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
            <div className="flex space-x-4">
              {(['light', 'dark', 'system'] as const).map((option) => (
                <label key={option} className="flex items-center">
                  <input
                    type="radio"
                    name="theme"
                    value={option}
                    checked={theme === option}
                    onChange={(e) => setTheme(e.target.value as typeof theme)}
                    className="h-4 w-4 border-gray-300 text-indigo-600 focus:ring-indigo-500"
                  />
                  <span className="ml-2 text-sm text-gray-700 capitalize">{option}</span>
                </label>
              ))}
            </div>
          </div>

          {/* Password Change */}
          <div>
            <button className="text-sm text-indigo-600 hover:text-indigo-500">
              Change Password
            </button>
          </div>
        </div>
        </div>
        )}
      </div>

      {/* Unit Settings */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <button
          onClick={() => toggleSection('units')}
          className="w-full px-6 py-4 bg-white hover:bg-gray-50 flex items-center justify-between text-left transition-colors"
        >
          <h2 className="text-lg font-medium text-gray-900">Unit Settings</h2>
          <svg
            className={`w-5 h-5 text-gray-500 transition-transform ${
              expandedSections['units'] ? 'rotate-180' : ''
            }`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
        
        {expandedSections['units'] && (
        <div className="px-6 pb-6 pt-2 border-t">
        <p className="text-sm text-gray-600 mb-6">
          Set your preferred measurement units for different physical quantities
        </p>

        <div className="space-y-8">
          {Object.entries(unitCategories).map(([category, dimensions]) => (
            <div key={category}>
              <h3 className="text-md font-medium text-gray-800 mb-3">{category}</h3>
              <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {dimensions.map((dimension) => {
                      const setting = unitSettings[dimension];
                      const options = unitOptions[dimension as keyof typeof unitOptions];
                      
                      return (
                        <div key={dimension} className="border rounded-lg p-4">
                          <label className="block text-sm font-medium text-gray-700 mb-2">
                            {dimensionDisplayNames[dimension]}
                          </label>
                          
                          {/* System Selection */}
                          <div className="flex space-x-2 mb-2">
                            <button
                              onClick={() => handleSystemChange(dimension, 'metric')}
                              className={`flex-1 px-3 py-1 text-xs rounded ${
                                setting.system === 'metric'
                                  ? 'bg-indigo-600 text-white'
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                              }`}
                            >
                              Metric
                            </button>
                            <button
                              onClick={() => handleSystemChange(dimension, 'imperial')}
                              className={`flex-1 px-3 py-1 text-xs rounded ${
                                setting.system === 'imperial'
                                  ? 'bg-indigo-600 text-white'
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                              }`}
                            >
                              Imperial
                            </button>
                          </div>
                          
                          {/* Scale Selection */}
                          <select
                            value={setting.scale}
                            onChange={(e) => handleScaleChange(dimension, e.target.value)}
                            className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500 mb-2"
                          >
                            {options[setting.system].map((unit) => (
                              <option key={unit} value={unit}>
                                {unit}
                              </option>
                            ))}
                          </select>
                          
                          {/* Precision Selection */}
                          <div className="mt-2">
                            <label className="block text-xs text-gray-600 mb-1">Decimal Precision</label>
                            <select
                              value={setting.precision || 0.01}
                              onChange={(e) => handlePrecisionChange(dimension, parseFloat(e.target.value))}
                              className="block w-full rounded-md border-gray-300 shadow-sm text-sm focus:border-indigo-500 focus:ring-indigo-500"
                            >
                              <option value="1">0 decimals (1)</option>
                              <option value="0.1">1 decimal (0.1)</option>
                              <option value="0.01">2 decimals (0.01)</option>
                              <option value="0.001">3 decimals (0.001)</option>
                              <option value="0.0001">4 decimals (0.0001)</option>
                              <option value="0.00001">5 decimals (0.00001)</option>
                              <option value="0.000001">6 decimals (0.000001)</option>
                            </select>
                          </div>
                        </div>
                      );
                    })}
              </div>
            </div>
          ))}
        </div>
        </div>
        )}
      </div>

      {/* Save Button */}
      <div className="flex justify-end">
        <button
          type="button"
          onClick={() => {
            // Save each unit setting to the context
            Object.entries(unitSettings).forEach(([dimension, setting]) => {
              updateUnitSetting(dimension, setting);
            });
            // You could add a toast notification here
            alert('Settings saved successfully!');
          }}
          className="inline-flex justify-center rounded-md border border-transparent bg-indigo-600 py-2 px-4 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
};

export default Settings;