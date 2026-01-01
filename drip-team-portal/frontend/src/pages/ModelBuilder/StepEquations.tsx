import React from 'react';
import { ModelBuilderData } from './types';

interface StepEquationsProps {
  data: ModelBuilderData;
  onChange: (data: Partial<ModelBuilderData>) => void;
  onValidChange: (isValid: boolean) => void;
}

const StepEquations: React.FC<StepEquationsProps> = ({ data, onChange, onValidChange }) => {
  const updateEquation = (outputName: string, equation: string) => {
    onChange({
      equations: {
        ...data.equations,
        [outputName]: equation,
      },
    });
  };

  const insertVariable = (outputName: string, varName: string) => {
    const currentEquation = data.equations[outputName] || '';
    updateEquation(outputName, currentEquation + varName);
  };

  // Validate: all outputs have equations
  React.useEffect(() => {
    const allOutputsHaveEquations = data.outputs.every(
      (output) => (data.equations[output.name] || '').trim().length > 0
    );
    onValidChange(allOutputsHaveEquations);
  }, [data.equations, data.outputs, onValidChange]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Define Equations</h2>
        <p className="mt-1 text-sm text-gray-500">
          Write the equation for each output using your input variables.
          Use standard math operators: + - * / ^ ( )
        </p>
      </div>

      {/* Available inputs reference */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">Available Input Variables</h3>
        <div className="flex flex-wrap gap-2">
          {data.inputs.map((input) => (
            <span
              key={input.id}
              className="inline-flex items-center px-2.5 py-1 rounded-md text-sm bg-blue-100 text-blue-800"
            >
              <code className="font-mono">{input.name}</code>
              <span className="ml-1 text-blue-600 text-xs">({input.unit})</span>
            </span>
          ))}
        </div>
      </div>

      {/* Equation editors for each output */}
      <div className="space-y-4">
        {data.outputs.map((output) => (
          <div key={output.id} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="block text-sm font-medium text-gray-900">
                  <code className="font-mono text-indigo-600">{output.name}</code>
                  <span className="ml-2 text-gray-500 font-normal">({output.unit})</span>
                </label>
                {output.description && (
                  <p className="text-xs text-gray-500 mt-0.5">{output.description}</p>
                )}
              </div>
            </div>

            {/* Equation input */}
            <div className="relative">
              <div className="absolute left-3 top-2.5 text-gray-400 font-mono text-sm">
                {output.name} =
              </div>
              <textarea
                value={data.equations[output.name] || ''}
                onChange={(e) => updateEquation(output.name, e.target.value)}
                placeholder="Enter equation using input variables..."
                rows={2}
                className="block w-full pl-24 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 font-mono text-sm"
              />
            </div>

            {/* Quick insert buttons */}
            <div className="mt-2 flex flex-wrap gap-1">
              <span className="text-xs text-gray-500 mr-2">Insert:</span>
              {data.inputs.map((input) => (
                <button
                  key={input.id}
                  type="button"
                  onClick={() => insertVariable(output.name, input.name)}
                  className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700 font-mono"
                >
                  {input.name}
                </button>
              ))}
              <span className="text-gray-300 mx-1">|</span>
              {['+', '-', '*', '/', '^', '(', ')', ' '].map((op) => (
                <button
                  key={op}
                  type="button"
                  onClick={() => insertVariable(output.name, op === ' ' ? ' ' : ` ${op} `)}
                  className="px-2 py-0.5 text-xs bg-gray-100 hover:bg-gray-200 rounded text-gray-700 font-mono"
                >
                  {op === ' ' ? 'space' : op}
                </button>
              ))}
            </div>

            {/* Missing equation warning */}
            {!(data.equations[output.name] || '').trim() && (
              <p className="mt-2 text-sm text-amber-600">
                Equation required for this output.
              </p>
            )}
          </div>
        ))}
      </div>

      {/* Example */}
      <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Example Equations</h3>
        <div className="space-y-1 text-sm text-gray-600 font-mono">
          <p>thermal_growth = alpha * diameter * delta_T</p>
          <p>min_pitch = crucible_od + 2 * thermal_growth</p>
          <p>stress = force / area</p>
        </div>
      </div>
    </div>
  );
};

export default StepEquations;
