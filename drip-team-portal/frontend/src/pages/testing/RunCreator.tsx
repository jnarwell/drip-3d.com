import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';

interface TestProtocol {
  id: number | string;
  name: string;
  category: string;
  description?: string;
  procedure_text?: string;
  procedure?: string;
  input_schema: ParameterSchema[];
  output_schema: ParameterSchema[];
  is_active: boolean;
}

interface ParameterSchema {
  name: string;
  unit: string;
  type: 'number' | 'string' | 'boolean';
  required?: boolean;
  default_value?: number | string | boolean;
  min_value?: number;
  max_value?: number;
  description?: string;
}

interface Component {
  component_id: string;
  name: string;
  part_number: string;
  category: string;
}

const STEPS = [
  { id: 1, name: 'Protocol', description: 'Select test protocol' },
  { id: 2, name: 'Component', description: 'Select target component (optional)' },
  { id: 3, name: 'Configure', description: 'Set input parameters' },
  { id: 4, name: 'Review', description: 'Review and start' },
];

export default function RunCreator() {
  const navigate = useNavigate();
  const { protocolId: urlProtocolId } = useParams<{ protocolId: string }>();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  // Get protocol ID from URL path parameter
  const preselectedProtocolId = urlProtocolId;

  // Wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [selectedProtocol, setSelectedProtocol] = useState<TestProtocol | null>(null);
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [configuration, setConfiguration] = useState<Record<string, number | string | boolean>>({});
  const [notes, setNotes] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Fetch protocols
  const { data: protocols, isLoading: loadingProtocols } = useQuery<TestProtocol[]>({
    queryKey: ['test-protocols'],
    queryFn: async () => {
      const response = await api.get('/api/v1/test-protocols');
      return response.data;
    },
  });

  // Fetch components
  const { data: components } = useQuery<Component[]>({
    queryKey: ['components'],
    queryFn: async () => {
      const response = await api.get('/api/v1/components');
      return response.data;
    },
  });

  // Pre-select protocol if provided in URL path
  useEffect(() => {
    if (preselectedProtocolId && protocols && !selectedProtocol) {
      // Compare as strings since URL param is string, protocol.id might be number
      const protocol = protocols.find(p => String(p.id) === preselectedProtocolId);
      if (protocol) {
        setSelectedProtocol(protocol);
        initializeConfiguration(protocol);
        setCurrentStep(2);
      }
    }
  }, [preselectedProtocolId, protocols, selectedProtocol]);

  // Initialize configuration with defaults when protocol changes
  const initializeConfiguration = (protocol: TestProtocol) => {
    const defaults: Record<string, number | string | boolean> = {};
    protocol.input_schema.forEach(param => {
      if (param.default_value !== undefined) {
        defaults[param.name] = param.default_value;
      }
    });
    setConfiguration(defaults);
  };

  // Create run mutation
  const createRun = useMutation({
    mutationFn: async (request: {
      protocol_id: number;
      component_id?: number;
      configuration: Record<string, number | string | boolean>;
      notes?: string;
    }) => {
      const response = await api.post(`/api/v1/test-protocols/${request.protocol_id}/runs`, request);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['test-runs'] });
      navigate(`/testing/runs/${data.id}/execute`);
    },
    onError: (err: any) => {
      const detail = err.response?.data?.detail;
      if (Array.isArray(detail)) {
        // FastAPI 422 errors return an array of validation errors
        setError(detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', '));
      } else if (typeof detail === 'string') {
        setError(detail);
      } else {
        setError(err.message || 'Failed to create test run');
      }
    },
  });

  const handleProtocolSelect = (protocol: TestProtocol) => {
    setSelectedProtocol(protocol);
    initializeConfiguration(protocol);
  };

  const handleConfigChange = (name: string, value: number | string | boolean) => {
    setConfiguration(prev => ({ ...prev, [name]: value }));
  };

  const handleCreate = () => {
    if (!selectedProtocol) return;
    setError(null);

    // Convert IDs to numbers as backend expects int types
    const protocolId = typeof selectedProtocol.id === 'string'
      ? parseInt(selectedProtocol.id, 10)
      : selectedProtocol.id;
    const componentId = selectedComponent?.component_id
      ? parseInt(selectedComponent.component_id, 10)
      : undefined;

    createRun.mutate({
      protocol_id: protocolId,
      component_id: componentId,
      configuration,
      notes: notes || undefined,
    });
  };

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return !!selectedProtocol;
      case 2:
        return true; // Component is optional
      case 3:
        if (!selectedProtocol) return false;
        const requiredInputs = selectedProtocol.input_schema.filter(p => p.required);
        return requiredInputs.every(p => configuration[p.name] !== undefined && configuration[p.name] !== '');
      case 4:
        return true;
      default:
        return false;
    }
  };

  const handleNext = () => {
    if (canProceed() && currentStep < 4) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  if (loadingProtocols) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading protocols...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">New Test Run</h1>
              <p className="text-sm text-gray-600">Create and configure a new test execution</p>
            </div>
            <button
              onClick={() => navigate('/testing')}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Progress Stepper */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {STEPS.map((step, stepIdx) => (
                <li key={step.id} className={`relative ${stepIdx !== STEPS.length - 1 ? 'flex-1' : ''}`}>
                  <div className="flex items-center">
                    <div
                      className={`relative flex h-8 w-8 items-center justify-center rounded-full border-2 ${
                        step.id < currentStep
                          ? 'border-indigo-600 bg-indigo-600'
                          : step.id === currentStep
                          ? 'border-indigo-600 bg-white'
                          : 'border-gray-300 bg-white'
                      }`}
                    >
                      {step.id < currentStep ? (
                        <svg className="h-5 w-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                            clipRule="evenodd"
                          />
                        </svg>
                      ) : (
                        <span
                          className={`text-sm font-medium ${
                            step.id === currentStep ? 'text-indigo-600' : 'text-gray-500'
                          }`}
                        >
                          {step.id}
                        </span>
                      )}
                    </div>
                    <span
                      className={`ml-3 text-sm font-medium ${
                        step.id <= currentStep ? 'text-indigo-600' : 'text-gray-500'
                      }`}
                    >
                      {step.name}
                    </span>
                    {stepIdx !== STEPS.length - 1 && (
                      <div className="ml-4 flex-1 h-0.5 bg-gray-200">
                        <div
                          className={`h-full ${step.id < currentStep ? 'bg-indigo-600' : 'bg-gray-200'}`}
                          style={{ width: step.id < currentStep ? '100%' : '0%' }}
                        />
                      </div>
                    )}
                  </div>
                </li>
              ))}
            </ol>
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {/* Step 1: Select Protocol */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Select Test Protocol</h2>
                <p className="text-sm text-gray-600">Choose the protocol that defines this test</p>
              </div>

              <div className="grid grid-cols-1 gap-3">
                {protocols?.filter(p => p.is_active).map(protocol => (
                  <button
                    key={protocol.id}
                    onClick={() => handleProtocolSelect(protocol)}
                    className={`p-4 rounded-lg border-2 text-left transition-all ${
                      selectedProtocol?.id === protocol.id
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-indigo-300 hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-medium text-gray-900">{protocol.name}</h3>
                        <p className="text-sm text-gray-500 mt-1">{protocol.description}</p>
                        <div className="flex items-center gap-4 mt-2 text-xs text-gray-500">
                          <span className="px-2 py-0.5 bg-gray-100 rounded">{protocol.category}</span>
                          <span>{protocol.input_schema.length} inputs</span>
                          <span>{protocol.output_schema.length} outputs</span>
                        </div>
                      </div>
                      {selectedProtocol?.id === protocol.id && (
                        <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                      )}
                    </div>
                  </button>
                ))}
              </div>

              {protocols?.filter(p => p.is_active).length === 0 && (
                <div className="text-center py-8 text-gray-500">
                  <p>No active protocols available.</p>
                  <button
                    onClick={() => navigate('/testing/protocols/new')}
                    className="mt-2 text-indigo-600 hover:text-indigo-800"
                  >
                    Create a protocol
                  </button>
                </div>
              )}
            </div>
          )}

          {/* Step 2: Select Component (Optional) */}
          {currentStep === 2 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Select Component (Optional)</h2>
                <p className="text-sm text-gray-600">
                  Link this test run to a specific component, or skip to run a standalone test
                </p>
              </div>

              <div className="space-y-3">
                <button
                  onClick={() => setSelectedComponent(null)}
                  className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                    selectedComponent === null
                      ? 'border-indigo-600 bg-indigo-50'
                      : 'border-gray-200 hover:border-indigo-300'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-gray-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">No Component</p>
                      <p className="text-sm text-gray-500">Run as standalone test</p>
                    </div>
                  </div>
                </button>

                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-200" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">or select a component</span>
                  </div>
                </div>

                <div className="max-h-64 overflow-y-auto space-y-2">
                  {components?.map(component => (
                    <button
                      key={component.component_id}
                      onClick={() => setSelectedComponent(component)}
                      className={`w-full p-4 rounded-lg border-2 text-left transition-all ${
                        selectedComponent?.component_id === component.component_id
                          ? 'border-indigo-600 bg-indigo-50'
                          : 'border-gray-200 hover:border-indigo-300'
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium text-gray-900">{component.name}</p>
                          <p className="text-sm text-gray-500">{component.part_number}</p>
                        </div>
                        <span className="text-xs px-2 py-0.5 bg-gray-100 rounded">{component.category}</span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 3: Configure Inputs */}
          {currentStep === 3 && selectedProtocol && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Configure Test Inputs</h2>
                <p className="text-sm text-gray-600">Set the input parameters for this test run</p>
              </div>

              <div className="space-y-4">
                {selectedProtocol.input_schema.map(param => (
                  <div key={param.name} className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <label className="block text-sm font-medium text-gray-900">
                          {param.name}
                          {param.required && <span className="text-red-500 ml-1">*</span>}
                        </label>
                        {param.description && (
                          <p className="text-xs text-gray-500 mt-0.5">{param.description}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 font-mono">{param.unit}</span>
                    </div>

                    {param.type === 'number' ? (
                      <input
                        type="number"
                        value={configuration[param.name] as number || ''}
                        onChange={(e) => handleConfigChange(param.name, parseFloat(e.target.value) || 0)}
                        min={param.min_value}
                        max={param.max_value}
                        step="any"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder={param.default_value !== undefined ? `Default: ${param.default_value}` : ''}
                      />
                    ) : param.type === 'boolean' ? (
                      <div className="flex items-center gap-4">
                        <label className="flex items-center">
                          <input
                            type="radio"
                            checked={configuration[param.name] === true}
                            onChange={() => handleConfigChange(param.name, true)}
                            className="mr-2"
                          />
                          <span className="text-sm">Yes</span>
                        </label>
                        <label className="flex items-center">
                          <input
                            type="radio"
                            checked={configuration[param.name] === false}
                            onChange={() => handleConfigChange(param.name, false)}
                            className="mr-2"
                          />
                          <span className="text-sm">No</span>
                        </label>
                      </div>
                    ) : (
                      <input
                        type="text"
                        value={configuration[param.name] as string || ''}
                        onChange={(e) => handleConfigChange(param.name, e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                        placeholder={param.default_value !== undefined ? `Default: ${param.default_value}` : ''}
                      />
                    )}

                    {(param.min_value !== undefined || param.max_value !== undefined) && (
                      <p className="text-xs text-gray-400 mt-1">
                        Range: {param.min_value ?? '-∞'} to {param.max_value ?? '∞'} {param.unit}
                      </p>
                    )}
                  </div>
                ))}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes (optional)</label>
                <textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  placeholder="Any notes about this test run..."
                />
              </div>

              {/* Procedure Preview */}
              {(selectedProtocol.procedure_text || selectedProtocol.procedure) && (
                <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                  <h3 className="text-sm font-medium text-blue-900 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                    Procedure Preview
                  </h3>
                  <div className="text-sm text-blue-800 whitespace-pre-wrap max-h-48 overflow-y-auto">
                    {selectedProtocol.procedure_text || selectedProtocol.procedure}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && selectedProtocol && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Review & Start</h2>
                <p className="text-sm text-gray-600">Review your test configuration before starting</p>
              </div>

              {error && (
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <div className="flex items-center gap-2 text-red-800">
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                        clipRule="evenodd"
                      />
                    </svg>
                    <span className="text-sm font-medium">{error}</span>
                  </div>
                </div>
              )}

              {/* Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Protocol</h3>
                  <p className="font-medium text-gray-900">{selectedProtocol.name}</p>
                  <p className="text-sm text-gray-500">{selectedProtocol.category}</p>
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Component</h3>
                  {selectedComponent ? (
                    <>
                      <p className="font-medium text-gray-900">{selectedComponent.name}</p>
                      <p className="text-sm text-gray-500">{selectedComponent.part_number}</p>
                    </>
                  ) : (
                    <p className="text-gray-500 italic">No component selected</p>
                  )}
                </div>
              </div>

              {/* Configuration Summary */}
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3">Configuration</h3>
                <div className="grid grid-cols-2 gap-2">
                  {selectedProtocol.input_schema.map(param => (
                    <div key={param.name} className="flex justify-between p-2 bg-white rounded border">
                      <span className="text-sm text-gray-600">{param.name}</span>
                      <span className="text-sm font-mono text-gray-900">
                        {configuration[param.name] !== undefined
                          ? String(configuration[param.name])
                          : <span className="text-gray-400">-</span>
                        } {param.unit}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Expected Outputs */}
              <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                <h3 className="text-sm font-medium text-indigo-700 mb-3">Expected Outputs</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {selectedProtocol.output_schema.map(output => (
                    <div key={output.name} className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                      <span className="text-indigo-900">{output.name}</span>
                      <span className="text-indigo-500">({output.unit})</span>
                    </div>
                  ))}
                </div>
              </div>

              {notes && (
                <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                  <h3 className="text-sm font-medium text-yellow-800 mb-2">Notes</h3>
                  <p className="text-sm text-yellow-700">{notes}</p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Navigation */}
        <div className="mt-6 flex justify-between">
          <button
            onClick={currentStep === 1 ? () => navigate('/testing') : handleBack}
            className="px-4 py-2 rounded-lg font-medium transition-colors bg-gray-200 text-gray-700 hover:bg-gray-300"
          >
            {currentStep === 1 ? 'Cancel' : 'Back'}
          </button>

          {currentStep < 4 ? (
            <button
              onClick={handleNext}
              disabled={!canProceed()}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                canProceed()
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Next
            </button>
          ) : (
            <button
              onClick={handleCreate}
              disabled={createRun.isPending}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                !createRun.isPending
                  ? 'bg-green-600 text-white hover:bg-green-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {createRun.isPending ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Creating...
                </span>
              ) : (
                'Start Test Run'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}