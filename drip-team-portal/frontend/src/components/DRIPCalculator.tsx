import React, { useState, useEffect } from 'react';

interface DRIPCalculatorProps {
  onCalculate: (dripNumber: number) => void;
}

const DRIPCalculator: React.FC<DRIPCalculatorProps> = ({ onCalculate }) => {
  const [params, setParams] = useState({
    frequency: 40000, // Hz
    droplet_diameter: 0.001, // meters
    material_density: 2700, // kg/m³ (aluminum default)
    acoustic_pressure: 1000, // Pa
    temperature: 700, // Celsius
    material_type: 'aluminum',
  });

  const [dripNumber, setDripNumber] = useState<number | null>(null);

  const materials = {
    aluminum: { density: 2700, label: 'Aluminum' },
    steel: { density: 7850, label: 'Steel' },
    titanium: { density: 4500, label: 'Titanium' },
    copper: { density: 8960, label: 'Copper' },
  };

  useEffect(() => {
    // Update density when material changes
    if (params.material_type in materials) {
      setParams(prev => ({
        ...prev,
        material_density: materials[params.material_type as keyof typeof materials].density,
      }));
    }
  }, [params.material_type]);

  const calculateDRIP = () => {
    // This calculation would normally be done server-side
    // Simplified calculation for demonstration
    const viscosity = getViscosity(params.temperature, params.material_type);
    const drip = (params.material_density * Math.pow(params.frequency, 2) * Math.pow(params.droplet_diameter, 3)) / 
                 (params.acoustic_pressure * viscosity);
    
    setDripNumber(drip);
    onCalculate(drip);
  };

  const getViscosity = (temp: number, material: string): number => {
    // Simplified viscosity model
    const viscosityModels: { [key: string]: (t: number) => number } = {
      aluminum: (t) => 0.85e-3 * Math.exp(3000 / (t + 273.15)),
      steel: (t) => 1.9e-3 * Math.exp(4200 / (t + 273.15)),
      titanium: (t) => 2.3e-3 * Math.exp(4500 / (t + 273.15)),
      copper: (t) => 1.2e-3 * Math.exp(3500 / (t + 273.15)),
    };
    
    return viscosityModels[material]?.(temp) || viscosityModels.aluminum(temp);
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-gray-900">DRIP Number Calculator</h3>
      
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs text-gray-600">Material</label>
          <select
            value={params.material_type}
            onChange={(e) => setParams({ ...params, material_type: e.target.value })}
            className="mt-1 block w-full rounded-md border-gray-300 text-sm"
          >
            {Object.entries(materials).map(([key, value]) => (
              <option key={key} value={key}>{value.label}</option>
            ))}
          </select>
        </div>
        
        <div>
          <label className="block text-xs text-gray-600">Frequency (Hz)</label>
          <input
            type="number"
            value={params.frequency}
            onChange={(e) => setParams({ ...params, frequency: Number(e.target.value) })}
            className="mt-1 block w-full rounded-md border-gray-300 text-sm"
          />
        </div>
        
        <div>
          <label className="block text-xs text-gray-600">Droplet Diameter (m)</label>
          <input
            type="number"
            step="0.0001"
            value={params.droplet_diameter}
            onChange={(e) => setParams({ ...params, droplet_diameter: Number(e.target.value) })}
            className="mt-1 block w-full rounded-md border-gray-300 text-sm"
          />
        </div>
        
        <div>
          <label className="block text-xs text-gray-600">Acoustic Pressure (Pa)</label>
          <input
            type="number"
            value={params.acoustic_pressure}
            onChange={(e) => setParams({ ...params, acoustic_pressure: Number(e.target.value) })}
            className="mt-1 block w-full rounded-md border-gray-300 text-sm"
          />
        </div>
        
        <div>
          <label className="block text-xs text-gray-600">Temperature (°C)</label>
          <input
            type="number"
            value={params.temperature}
            onChange={(e) => setParams({ ...params, temperature: Number(e.target.value) })}
            className="mt-1 block w-full rounded-md border-gray-300 text-sm"
          />
        </div>
        
        <div>
          <label className="block text-xs text-gray-600">Density (kg/m³)</label>
          <input
            type="number"
            value={params.material_density}
            disabled
            className="mt-1 block w-full rounded-md border-gray-300 bg-gray-100 text-sm"
          />
        </div>
      </div>
      
      <button
        type="button"
        onClick={calculateDRIP}
        className="w-full px-3 py-1 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700"
      >
        Calculate DRIP Number
      </button>
      
      {dripNumber !== null && (
        <div className="p-3 bg-indigo-50 border border-indigo-200 rounded">
          <p className="text-sm font-medium text-indigo-900">
            DRIP Number: {dripNumber.toExponential(3)}
          </p>
          <p className="text-xs text-indigo-700 mt-1">
            This dimensionless number characterizes the acoustic droplet formation regime
          </p>
        </div>
      )}
    </div>
  );
};

export default DRIPCalculator;