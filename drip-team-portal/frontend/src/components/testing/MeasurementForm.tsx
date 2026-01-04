import React, { useState, useEffect } from 'react';

interface ParameterSchema {
  name: string;
  unit_id?: number;
  unit_symbol?: string;  // Denormalized unit symbol
  type?: 'number' | 'string' | 'boolean';
  required?: boolean;
  target?: number;        // Backend uses 'target' not 'target_value'
  tolerance_pct?: number; // Backend uses 'tolerance_pct' not 'tolerance_percent'
  min_value?: number;
  max_value?: number;
  description?: string;
}

interface MeasurementFormProps {
  outputSchema: ParameterSchema[];
  recordedParameters: Set<string>;
  onSubmit: (data: { parameter_name: string; measured_value: number; notes?: string }) => void;
  isSubmitting?: boolean;
}

const MeasurementForm: React.FC<MeasurementFormProps> = ({
  outputSchema,
  recordedParameters,
  onSubmit,
  isSubmitting = false,
}) => {
  const [selectedParameter, setSelectedParameter] = useState<string>('');
  const [value, setValue] = useState<string>('');
  const [notes, setNotes] = useState<string>('');

  // Find the current parameter definition
  const currentParam = outputSchema.find(p => p.name === selectedParameter);

  // Auto-select first unrecorded parameter
  useEffect(() => {
    if (!selectedParameter) {
      const firstUnrecorded = outputSchema.find(p => !recordedParameters.has(p.name));
      if (firstUnrecorded) {
        setSelectedParameter(firstUnrecorded.name);
      }
    }
  }, [outputSchema, recordedParameters, selectedParameter]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedParameter || !value) return;

    onSubmit({
      parameter_name: selectedParameter,
      measured_value: parseFloat(value),
      notes: notes || undefined,
    });

    // Reset form
    setValue('');
    setNotes('');

    // Auto-select next unrecorded parameter
    const nextUnrecorded = outputSchema.find(
      p => p.name !== selectedParameter && !recordedParameters.has(p.name)
    );
    if (nextUnrecorded) {
      setSelectedParameter(nextUnrecorded.name);
    }
  };

  // Calculate if current value is within tolerance
  const getValueStatus = (): { status: 'ok' | 'warning' | 'error'; message: string } | null => {
    if (!currentParam || !value) return null;

    const numValue = parseFloat(value);
    if (isNaN(numValue)) return null;

    if (currentParam.target !== undefined) {
      const target = currentParam.target;
      let toleranceAbs = 0;

      if (currentParam.tolerance_pct !== undefined) {
        toleranceAbs = Math.abs(target * currentParam.tolerance_pct / 100);
      }

      const error = Math.abs(numValue - target);
      const errorPercent = target !== 0 ? (error / Math.abs(target)) * 100 : 0;

      if (toleranceAbs > 0) {
        if (error <= toleranceAbs) {
          return {
            status: 'ok',
            message: `Within tolerance (${errorPercent.toFixed(1)}% error)`,
          };
        } else if (error <= toleranceAbs * 1.5) {
          return {
            status: 'warning',
            message: `Close to tolerance (${errorPercent.toFixed(1)}% error)`,
          };
        } else {
          return {
            status: 'error',
            message: `Outside tolerance (${errorPercent.toFixed(1)}% error)`,
          };
        }
      }
    }

    // Check min/max bounds
    if (currentParam.min_value !== undefined && parseFloat(value) < currentParam.min_value) {
      return { status: 'error', message: `Below minimum (${currentParam.min_value})` };
    }
    if (currentParam.max_value !== undefined && parseFloat(value) > currentParam.max_value) {
      return { status: 'error', message: `Above maximum (${currentParam.max_value})` };
    }

    return null;
  };

  const valueStatus = getValueStatus();

  const getStatusColors = (status: 'ok' | 'warning' | 'error') => {
    switch (status) {
      case 'ok':
        return 'bg-green-50 border-green-300 text-green-700';
      case 'warning':
        return 'bg-yellow-50 border-yellow-300 text-yellow-700';
      case 'error':
        return 'bg-red-50 border-red-300 text-red-700';
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Parameter Selector */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Parameter
        </label>
        <select
          value={selectedParameter}
          onChange={(e) => setSelectedParameter(e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
        >
          <option value="">Select parameter...</option>
          {outputSchema.map(param => {
            const isRecorded = recordedParameters.has(param.name);
            return (
              <option key={param.name} value={param.name}>
                {param.name}{param.unit_symbol ? ` (${param.unit_symbol})` : ''}
                {isRecorded ? ' ✓' : ''}
              </option>
            );
          })}
        </select>
      </div>

      {/* Target/Tolerance Info */}
      {currentParam && (
        <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm font-medium text-blue-900">{currentParam.name}</p>
              {currentParam.description && (
                <p className="text-xs text-blue-700 mt-0.5">{currentParam.description}</p>
              )}
            </div>
            {currentParam.unit_symbol && (
              <span className="text-xs font-mono text-blue-600">{currentParam.unit_symbol}</span>
            )}
          </div>
          <div className="mt-2 flex flex-wrap gap-3 text-xs">
            {currentParam.target !== undefined && (
              <span className="px-2 py-1 bg-blue-100 rounded">
                Target: {currentParam.target} {currentParam.unit_symbol || ''}
              </span>
            )}
            {currentParam.tolerance_pct !== undefined && (
              <span className="px-2 py-1 bg-blue-100 rounded">
                ±{currentParam.tolerance_pct}%
              </span>
            )}
            {currentParam.min_value !== undefined && (
              <span className="px-2 py-1 bg-gray-100 rounded">
                Min: {currentParam.min_value}
              </span>
            )}
            {currentParam.max_value !== undefined && (
              <span className="px-2 py-1 bg-gray-100 rounded">
                Max: {currentParam.max_value}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Value Input */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Measured Value
          {currentParam?.unit_symbol && <span className="text-gray-500 ml-1">({currentParam.unit_symbol})</span>}
        </label>
        <div className="relative">
          <input
            type="number"
            step="any"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent ${
              valueStatus
                ? getStatusColors(valueStatus.status)
                : 'border-gray-300'
            }`}
            placeholder="Enter measured value..."
            required
          />
          {currentParam?.unit_symbol && (
            <span className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 text-sm">
              {currentParam.unit_symbol}
            </span>
          )}
        </div>
        {valueStatus && (
          <p className={`mt-1 text-xs ${
            valueStatus.status === 'ok'
              ? 'text-green-600'
              : valueStatus.status === 'warning'
              ? 'text-yellow-600'
              : 'text-red-600'
          }`}>
            {valueStatus.message}
          </p>
        )}
      </div>

      {/* Notes */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Notes (optional)
        </label>
        <textarea
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          rows={2}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
          placeholder="Any observations or notes..."
        />
      </div>

      {/* Submit Button */}
      <button
        type="submit"
        disabled={!selectedParameter || !value || isSubmitting}
        className={`w-full py-2 rounded-lg font-medium transition-colors ${
          selectedParameter && value && !isSubmitting
            ? 'bg-indigo-600 text-white hover:bg-indigo-700'
            : 'bg-gray-300 text-gray-500 cursor-not-allowed'
        }`}
      >
        {isSubmitting ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            Recording...
          </span>
        ) : (
          'Record Measurement'
        )}
      </button>

      {/* Quick record indicator */}
      {recordedParameters.size > 0 && (
        <p className="text-xs text-gray-500 text-center">
          {recordedParameters.size} of {outputSchema.length} parameters recorded
        </p>
      )}
    </form>
  );
};

export default MeasurementForm;
