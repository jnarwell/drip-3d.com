import React, { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import { ModelBuilderData, ValidateModelResponse, MODEL_CATEGORIES } from './types';

interface StepValidateProps {
  data: ModelBuilderData;
  onValidChange: (isValid: boolean) => void;
}

const StepValidate: React.FC<StepValidateProps> = ({ data, onValidChange }) => {
  const api = useAuthenticatedApi();

  // Prepare request payload
  const validatePayload = {
    inputs: data.inputs.map((v) => ({
      name: v.name,
      unit: v.unit,
      description: v.description,
    })),
    outputs: data.outputs.map((v) => ({
      name: v.name,
      unit: v.unit,
      description: v.description,
    })),
    equations: data.equations,
  };

  // Call validation API
  const {
    data: validation,
    isLoading,
    error,
  } = useQuery<ValidateModelResponse>({
    queryKey: ['validate-model', validatePayload],
    queryFn: async () => {
      const response = await api.post('/api/v1/physics-models/validate', validatePayload);
      return response.data;
    },
    // Refetch when entering this step
    staleTime: 0,
    retry: false,
  });

  // Update valid state based on validation result
  useEffect(() => {
    if (validation) {
      onValidChange(validation.valid);
    } else if (error) {
      // If API doesn't exist yet, allow proceeding (MVP)
      onValidChange(true);
    }
  }, [validation, error, onValidChange]);

  const categoryLabel = MODEL_CATEGORIES.find((c) => c.value === data.category)?.label || data.category;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Review & Create</h2>
        <p className="mt-1 text-sm text-gray-500">
          Review your model configuration before creating it.
        </p>
      </div>

      {/* Model Summary */}
      <div className="bg-white border border-gray-200 rounded-lg divide-y divide-gray-200">
        {/* Basic Info */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Model Information
          </h3>
          <dl className="grid grid-cols-2 gap-4">
            <div>
              <dt className="text-sm text-gray-500">Name</dt>
              <dd className="text-sm font-medium text-gray-900">{data.name}</dd>
            </div>
            <div>
              <dt className="text-sm text-gray-500">Category</dt>
              <dd className="text-sm font-medium text-gray-900">{categoryLabel}</dd>
            </div>
            {data.description && (
              <div className="col-span-2">
                <dt className="text-sm text-gray-500">Description</dt>
                <dd className="text-sm text-gray-900">{data.description}</dd>
              </div>
            )}
          </dl>
        </div>

        {/* Inputs */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Inputs ({data.inputs.length})
          </h3>
          <div className="space-y-2">
            {data.inputs.map((input) => (
              <div
                key={input.id}
                className="flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-2"
              >
                <div>
                  <code className="font-mono text-indigo-600">{input.name}</code>
                  {input.description && (
                    <span className="ml-2 text-gray-500">- {input.description}</span>
                  )}
                </div>
                <span className="text-gray-500">{input.unit}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Outputs */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Outputs ({data.outputs.length})
          </h3>
          <div className="space-y-2">
            {data.outputs.map((output) => (
              <div
                key={output.id}
                className="flex items-center justify-between text-sm bg-gray-50 rounded px-3 py-2"
              >
                <div>
                  <code className="font-mono text-indigo-600">{output.name}</code>
                  {output.description && (
                    <span className="ml-2 text-gray-500">- {output.description}</span>
                  )}
                </div>
                <span className="text-gray-500">{output.unit}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Equations */}
        <div className="p-4">
          <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
            Equations
          </h3>
          <div className="space-y-2 font-mono text-sm">
            {data.outputs.map((output) => (
              <div key={output.id} className="bg-gray-50 rounded px-3 py-2">
                <span className="text-indigo-600">{output.name}</span>
                <span className="text-gray-500"> = </span>
                <span className="text-gray-900">{data.equations[output.name]}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Validation Results */}
      <div className="border border-gray-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Validation</h3>

        {isLoading && (
          <div className="flex items-center text-sm text-gray-500">
            <svg
              className="animate-spin h-4 w-4 mr-2 text-indigo-600"
              fill="none"
              viewBox="0 0 24 24"
            >
              <circle
                className="opacity-25"
                cx="12"
                cy="12"
                r="10"
                stroke="currentColor"
                strokeWidth="4"
              />
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              />
            </svg>
            Validating model...
          </div>
        )}

        {error && (
          <div className="text-sm">
            <div className="flex items-center text-amber-600 mb-2">
              <svg className="h-4 w-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                />
              </svg>
              Validation API not available yet
            </div>
            <p className="text-gray-500">
              The dimensional analysis endpoint is not implemented yet.
              You can still create the model.
            </p>
          </div>
        )}

        {validation && (
          <div>
            {validation.valid ? (
              <div className="flex items-center text-green-600">
                <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M5 13l4 4L19 7"
                  />
                </svg>
                All validations passed
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center text-red-600">
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                  Validation errors found
                </div>
                <ul className="list-disc list-inside text-sm text-red-600 space-y-1">
                  {validation.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Dimensional analysis details */}
            {validation.dimensional_analysis && Object.keys(validation.dimensional_analysis).length > 0 && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-700 mb-2">Dimensional Analysis</h4>
                <div className="space-y-2">
                  {Object.entries(validation.dimensional_analysis).map(([output, result]) => {
                    const isWarning = result.valid && result.message &&
                      (result.message.includes('not recognized') || result.message.includes('cannot verify') || result.message.includes('not checked'));
                    return (
                    <div
                      key={output}
                      className={`text-sm p-2 rounded ${
                        !result.valid ? 'bg-red-50' : isWarning ? 'bg-yellow-50' : 'bg-green-50'
                      }`}
                    >
                      <div className="flex items-center">
                        {!result.valid ? (
                          <svg
                            className="h-4 w-4 text-red-500 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M6 18L18 6M6 6l12 12"
                            />
                          </svg>
                        ) : isWarning ? (
                          <svg
                            className="h-4 w-4 text-yellow-500 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z"
                            />
                          </svg>
                        ) : (
                          <svg
                            className="h-4 w-4 text-green-500 mr-2"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M5 13l4 4L19 7"
                            />
                          </svg>
                        )}
                        <code className="font-mono">{output}</code>
                      </div>
                      {((!result.valid) || isWarning) && result.message && (
                        <p className={isWarning ? 'ml-6 text-yellow-700' : 'ml-6 text-red-600'}>{result.message}</p>
                      )}
                    </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default StepValidate;
