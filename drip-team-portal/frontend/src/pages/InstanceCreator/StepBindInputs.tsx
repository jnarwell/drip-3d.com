import React from 'react';
import { PhysicsModel } from './types';

interface StepBindInputsProps {
  model: PhysicsModel;
  bindings: Record<string, string>;
  onChange: (bindings: Record<string, string>) => void;
}

export default function StepBindInputs({ model, bindings, onChange }: StepBindInputsProps) {
  const inputs = model.inputs || [];

  const handleInputChange = (name: string, value: string) => {
    onChange({
      ...bindings,
      [name]: value,
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Bind Inputs</h2>
        <p className="text-sm text-gray-600">
          Provide values for each input. You can enter literal values or reference expressions.
        </p>
      </div>

      <div className="space-y-4">
        {inputs.map(input => {
          const value = bindings[input.name] || '';
          const isRequired = input.required !== false && !input.optional;

          return (
            <div key={input.name} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <label className="block text-sm font-medium text-gray-900">
                    {input.name}
                    {isRequired && <span className="text-red-500 ml-1">*</span>}
                  </label>
                  {input.description && (
                    <p className="text-xs text-gray-500 mt-0.5">{input.description}</p>
                  )}
                </div>
                <span className="text-xs text-gray-500 bg-gray-200 px-2 py-0.5 rounded">
                  {input.unit}
                </span>
              </div>

              <input
                type="text"
                value={value}
                onChange={(e) => handleInputChange(input.name, e.target.value)}
                placeholder={`Enter value or expression (e.g., 100, #COMP.prop)`}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm font-mono"
              />

              <div className="mt-2 text-xs text-gray-500">
                Examples: <code className="bg-gray-200 px-1 rounded">25.5</code>,{' '}
                <code className="bg-gray-200 px-1 rounded">#FRAME.height</code>,{' '}
                <code className="bg-gray-200 px-1 rounded">LOOKUP("steam", "h", T=373)</code>
              </div>
            </div>
          );
        })}
      </div>

      {inputs.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          This model has no inputs to bind.
        </div>
      )}
    </div>
  );
}
