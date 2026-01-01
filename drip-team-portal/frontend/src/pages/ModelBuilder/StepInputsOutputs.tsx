import React, { useState, useCallback } from 'react';
import { ModelBuilderData, ModelVariable } from './types';

interface StepInputsOutputsProps {
  data: ModelBuilderData;
  onChange: (data: Partial<ModelBuilderData>) => void;
  onValidChange: (isValid: boolean) => void;
}

// Common engineering units grouped by dimension (use Unicode superscripts to match backend)
const UNIT_SUGGESTIONS: Record<string, string[]> = {
  Length: ['m', 'mm', 'cm', 'km', 'in', 'ft'],
  Area: ['m²', 'cm²', 'mm²', 'in²', 'ft²'],
  Volume: ['m³', 'cm³', 'mm³', 'L', 'mL', 'in³', 'ft³'],
  Mass: ['kg', 'g', 'mg', 'lb', 'oz'],
  Time: ['s', 'ms', 'min', 'h'],
  Temperature: ['K', '°C', '°F'],
  Force: ['N', 'kN', 'lbf'],
  Pressure: ['Pa', 'kPa', 'MPa', 'bar', 'psi'],
  Energy: ['J', 'kJ', 'MJ', 'Wh', 'kWh', 'BTU'],
  Power: ['W', 'kW', 'MW', 'hp'],
  Velocity: ['m/s', 'km/h', 'mm/s', 'ft/s', 'mph'],
  Acceleration: ['m/s²', 'ft/s²', 'g'],
  Density: ['kg/m³', 'g/cm³', 'lb/ft³', 'lb/in³'],
  'Thermal Expansion': ['1/K', '1/°C', 'ppm/K'],
  'Heat Capacity': ['J/K', 'kJ/K', 'J/°C', 'BTU/°F'],
  'Specific Heat': ['J/(kg·K)', 'kJ/(kg·K)', 'BTU/(lb·°F)'],
  'Thermal Conductivity': ['W/(m·K)', 'BTU/(h·ft·°F)'],
  Dimensionless: ['1', '%', 'ratio'],
};

const ALL_UNITS = Object.values(UNIT_SUGGESTIONS).flat();

interface VariableEditorProps {
  variable: ModelVariable;
  onUpdate: (updated: ModelVariable) => void;
  onDelete: () => void;
  type: 'input' | 'output';
}

const VariableEditor: React.FC<VariableEditorProps> = ({ variable, onUpdate, onDelete, type }) => {
  const [showUnitSuggestions, setShowUnitSuggestions] = useState(false);
  const [unitFilter, setUnitFilter] = useState(variable.unit);

  // Sync local state when prop changes (for edit mode)
  React.useEffect(() => {
    setUnitFilter(variable.unit);
  }, [variable.unit]);

  const filteredUnits = unitFilter
    ? ALL_UNITS.filter((u) => u.toLowerCase().includes(unitFilter.toLowerCase()))
    : ALL_UNITS;

  return (
    <div className="flex items-start gap-3 p-3 bg-gray-50 rounded-lg">
      {/* Variable Name */}
      <div className="flex-1">
        <label className="block text-xs font-medium text-gray-500 mb-1">Name</label>
        <input
          type="text"
          value={variable.name}
          onChange={(e) => onUpdate({ ...variable, name: e.target.value })}
          placeholder={type === 'input' ? 'e.g., crucible_od' : 'e.g., min_pitch'}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
        />
      </div>

      {/* Unit with autocomplete */}
      <div className="w-32 relative">
        <label className="block text-xs font-medium text-gray-500 mb-1">Unit</label>
        <input
          type="text"
          value={unitFilter}
          onChange={(e) => {
            setUnitFilter(e.target.value);
            onUpdate({ ...variable, unit: e.target.value });
          }}
          onFocus={() => setShowUnitSuggestions(true)}
          onBlur={() => setTimeout(() => setShowUnitSuggestions(false), 200)}
          placeholder="e.g., mm"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
        />
        {showUnitSuggestions && filteredUnits.length > 0 && (
          <div className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md border border-gray-200 max-h-40 overflow-auto">
            {filteredUnits.slice(0, 10).map((unit) => (
              <button
                key={unit}
                type="button"
                onClick={() => {
                  setUnitFilter(unit);
                  onUpdate({ ...variable, unit });
                  setShowUnitSuggestions(false);
                }}
                className="block w-full text-left px-3 py-1.5 text-sm hover:bg-gray-100"
              >
                {unit}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Description */}
      <div className="flex-1">
        <label className="block text-xs font-medium text-gray-500 mb-1">Description</label>
        <input
          type="text"
          value={variable.description || ''}
          onChange={(e) => onUpdate({ ...variable, description: e.target.value })}
          placeholder="Optional description"
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 text-sm"
        />
      </div>

      {/* Delete button */}
      <button
        type="button"
        onClick={onDelete}
        className="mt-5 p-1.5 text-gray-400 hover:text-red-500"
        title="Remove variable"
      >
        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
  );
};

const StepInputsOutputs: React.FC<StepInputsOutputsProps> = ({ data, onChange, onValidChange }) => {
  const generateId = () => `var_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  const addInput = useCallback(() => {
    const newInput: ModelVariable = { id: generateId(), name: '', unit: '', description: '' };
    onChange({ inputs: [...data.inputs, newInput] });
  }, [data.inputs, onChange]);

  const addOutput = useCallback(() => {
    const newOutput: ModelVariable = { id: generateId(), name: '', unit: '', description: '' };
    onChange({ outputs: [...data.outputs, newOutput] });
  }, [data.outputs, onChange]);

  const updateInput = useCallback((index: number, updated: ModelVariable) => {
    const newInputs = [...data.inputs];
    newInputs[index] = updated;
    onChange({ inputs: newInputs });
  }, [data.inputs, onChange]);

  const updateOutput = useCallback((index: number, updated: ModelVariable) => {
    const newOutputs = [...data.outputs];
    newOutputs[index] = updated;
    onChange({ outputs: newOutputs });
  }, [data.outputs, onChange]);

  const deleteInput = useCallback((index: number) => {
    onChange({ inputs: data.inputs.filter((_, i) => i !== index) });
  }, [data.inputs, onChange]);

  const deleteOutput = useCallback((index: number) => {
    onChange({ outputs: data.outputs.filter((_, i) => i !== index) });
  }, [data.outputs, onChange]);

  // Validate: at least 1 input and 1 output with name and unit
  React.useEffect(() => {
    const hasValidInputs = data.inputs.length > 0 &&
      data.inputs.every((v) => v.name.trim() && v.unit.trim());
    const hasValidOutputs = data.outputs.length > 0 &&
      data.outputs.every((v) => v.name.trim() && v.unit.trim());
    onValidChange(hasValidInputs && hasValidOutputs);
  }, [data.inputs, data.outputs, onValidChange]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Define Inputs & Outputs</h2>
        <p className="mt-1 text-sm text-gray-500">
          Specify the variables your model uses. Inputs are values you provide; outputs are calculated results.
        </p>
      </div>

      {/* Inputs Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-900">
            Inputs
            <span className="ml-2 text-gray-400 font-normal">
              ({data.inputs.length} defined)
            </span>
          </h3>
          <button
            type="button"
            onClick={addInput}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Input
          </button>
        </div>

        <div className="space-y-2">
          {data.inputs.length === 0 ? (
            <div className="text-center py-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
              <p className="text-sm text-gray-500">No inputs defined yet.</p>
              <button
                type="button"
                onClick={addInput}
                className="mt-2 text-sm text-indigo-600 hover:text-indigo-700"
              >
                Add your first input
              </button>
            </div>
          ) : (
            data.inputs.map((input, index) => (
              <VariableEditor
                key={input.id}
                variable={input}
                onUpdate={(updated) => updateInput(index, updated)}
                onDelete={() => deleteInput(index)}
                type="input"
              />
            ))
          )}
        </div>
      </div>

      {/* Outputs Section */}
      <div>
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-medium text-gray-900">
            Outputs
            <span className="ml-2 text-gray-400 font-normal">
              ({data.outputs.length} defined)
            </span>
          </h3>
          <button
            type="button"
            onClick={addOutput}
            className="inline-flex items-center px-3 py-1.5 text-sm font-medium text-indigo-600 hover:text-indigo-700"
          >
            <svg className="h-4 w-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            Add Output
          </button>
        </div>

        <div className="space-y-2">
          {data.outputs.length === 0 ? (
            <div className="text-center py-6 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
              <p className="text-sm text-gray-500">No outputs defined yet.</p>
              <button
                type="button"
                onClick={addOutput}
                className="mt-2 text-sm text-indigo-600 hover:text-indigo-700"
              >
                Add your first output
              </button>
            </div>
          ) : (
            data.outputs.map((output, index) => (
              <VariableEditor
                key={output.id}
                variable={output}
                onUpdate={(updated) => updateOutput(index, updated)}
                onDelete={() => deleteOutput(index)}
                type="output"
              />
            ))
          )}
        </div>
      </div>

      {/* Validation hint */}
      {(data.inputs.length === 0 || data.outputs.length === 0) && (
        <p className="text-sm text-amber-600 bg-amber-50 p-3 rounded-md">
          You need at least one input and one output to proceed.
        </p>
      )}
    </div>
  );
};

export default StepInputsOutputs;
