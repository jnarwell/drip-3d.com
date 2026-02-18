import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import StepSelectModel from '../InstanceCreator/StepSelectModel';
import StepBindInputs from '../InstanceCreator/StepBindInputs';
import { PhysicsModel, CreateInstanceRequest, ModelInstance } from '../InstanceCreator/types';

const STEPS = [
  { id: 1, name: 'Name', description: 'Give your analysis a name' },
  { id: 2, name: 'Select Model', description: 'Choose a physics model template' },
  { id: 3, name: 'Bind Inputs', description: 'Connect inputs to data sources' },
  { id: 4, name: 'Review', description: 'Review and create' },
];

export default function AnalysisCreator() {
  const navigate = useNavigate();
  const { analysisId } = useParams<{ analysisId?: string }>();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const isEditMode = Boolean(analysisId);

  // Wizard state
  const [currentStep, setCurrentStep] = useState(1);
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedModel, setSelectedModel] = useState<PhysicsModel | null>(null);
  const [bindings, setBindings] = useState<Record<string, string>>({});
  const [bindingsValid, setBindingsValid] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [initialized, setInitialized] = useState(!isEditMode);

  // Fetch existing analysis if editing
  const { data: existingAnalysis, isLoading: loadingAnalysis } = useQuery({
    queryKey: ['analysis', analysisId],
    queryFn: async () => {
      if (!analysisId) return null;
      const response = await api.get(`/api/v1/analyses/${analysisId}`);
      return response.data;
    },
    enabled: isEditMode,
  });

  // Fetch models list to find the model by version_id
  const { data: models } = useQuery({
    queryKey: ['physics-models'],
    queryFn: async () => {
      const response = await api.get('/api/v1/physics-models');
      return response.data;
    },
    enabled: isEditMode,
  });

  // Pre-populate form when existing analysis loads
  useEffect(() => {
    if (existingAnalysis && !initialized) {
      setName(existingAnalysis.name || '');
      setDescription(existingAnalysis.description || '');

      // Convert inputs array to bindings object
      const inputBindings: Record<string, string> = {};
      if (existingAnalysis.inputs) {
        existingAnalysis.inputs.forEach((input: any) => {
          if (input.literal_value !== null && input.literal_value !== undefined) {
            inputBindings[input.input_name] = String(input.literal_value);
          } else if (input.source_lookup?.expression) {
            inputBindings[input.input_name] = input.source_lookup.expression;
          } else if (input.source_value_node_id) {
            inputBindings[input.input_name] = `#REF:${input.source_value_node_id}`;
          }
        });
      }
      setBindings(inputBindings);
      // Existing bindings were previously accepted; treat as valid initially
      // StepBindInputs will re-validate when the user reaches step 3
      setBindingsValid(true);
      setInitialized(true);
    }
  }, [existingAnalysis, initialized]);

  // Find and set the model once models are loaded
  useEffect(() => {
    if (existingAnalysis?.model_version_id && models && !selectedModel) {
      // Find model that has this version
      const model = models.find((m: any) =>
        m.version_id === existingAnalysis.model_version_id ||
        m.current_version?.id === existingAnalysis.model_version_id
      );
      if (model) {
        setSelectedModel(model);
      }
    }
  }, [existingAnalysis, models, selectedModel]);

  // Create analysis mutation
  const createInstance = useMutation<ModelInstance, Error, CreateInstanceRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/api/v1/analyses', request);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      navigate('/analysis');
    },
    onError: (err) => {
      setError(err.message || 'Failed to create analysis');
    },
  });

  // Update analysis mutation
  const updateInstance = useMutation({
    mutationFn: async (request: { name: string; description?: string; bindings: Record<string, string> }) => {
      const response = await api.patch(`/api/v1/analyses/${analysisId}`, request);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      queryClient.invalidateQueries({ queryKey: ['analysis', analysisId] });
      navigate('/analysis');
    },
    onError: (err: any) => {
      setError(err.message || 'Failed to update analysis');
    },
  });

  const handleModelSelect = (model: PhysicsModel) => {
    const isSameModelInEditMode = isEditMode && selectedModel && (
      selectedModel.id === model.id || selectedModel.version_id === model.version_id
    );
    setSelectedModel(model);
    if (!isSameModelInEditMode) {
      setBindings({});
      setBindingsValid(false);
    }
  };

  const handleCreate = () => {
    if (!selectedModel) return;

    setError(null);

    if (isEditMode) {
      updateInstance.mutate({
        name,
        description: description || undefined,
        bindings,
      });
    } else {
      createInstance.mutate({
        name,
        model_version_id: selectedModel.version_id,
        // No target_component_id for named analyses
        bindings,
      });
    }
  };

  const isSaving = isEditMode ? updateInstance.isPending : createInstance.isPending;

  // Show loading state while fetching analysis for edit
  if (isEditMode && loadingAnalysis) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading analysis...</p>
        </div>
      </div>
    );
  }

  const canProceed = () => {
    switch (currentStep) {
      case 1:
        return name.trim().length > 0;
      case 2:
        return !!selectedModel;
      case 3:
        if (!selectedModel) return false;
        const requiredInputs = (selectedModel.inputs || []).filter(i => !i.optional);
        const allFilled = requiredInputs.every(i => bindings[i.name]);
        return allFilled && bindingsValid;
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

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {isEditMode ? 'Edit Analysis' : 'New Analysis'}
              </h1>
              <p className="text-sm text-gray-600">
                {isEditMode
                  ? `Update "${existingAnalysis?.name || 'analysis'}" configuration`
                  : 'Create a named model instance that updates continuously'}
              </p>
            </div>
            <button
              onClick={() => navigate('/analysis')}
              className="text-gray-500 hover:text-gray-700 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Progress stepper */}
      <div className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <nav aria-label="Progress">
            <ol className="flex items-center">
              {STEPS.map((step, stepIdx) => (
                <li key={step.id} className={`relative ${stepIdx !== STEPS.length - 1 ? 'flex-1' : ''}`}>
                  <div className="flex items-center">
                    {/* Circle */}
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

                    {/* Step title */}
                    <span
                      className={`ml-3 text-sm font-medium ${
                        step.id < currentStep || step.id === currentStep ? 'text-indigo-600' : 'text-gray-500'
                      }`}
                    >
                      {step.name}
                    </span>

                    {/* Connector line - flex item, not absolute */}
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

      {/* Main content */}
      <div className="max-w-4xl mx-auto px-6 py-8">
        <div className="bg-white rounded-lg shadow-sm border p-6">
          {/* Step 1: Name and Description */}
          {currentStep === 1 && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">Name Your Analysis</h2>
                <p className="text-sm text-gray-600">
                  Give your analysis a descriptive name so you can easily identify it later.
                </p>
              </div>

              <div className="space-y-4">
                <div>
                  <label htmlFor="name" className="block text-sm font-medium text-gray-700 mb-2">
                    Analysis Name <span className="text-red-500">*</span>
                  </label>
                  <input
                    type="text"
                    id="name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                    placeholder="e.g., Achievable Distance"
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                    autoFocus
                  />
                  <p className="mt-1 text-xs text-gray-500">
                    Use a descriptive name that explains what this analysis tracks.
                  </p>
                </div>

                <div>
                  <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                    Description (optional)
                  </label>
                  <textarea
                    id="description"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Brief description of what this analysis calculates..."
                    rows={3}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
                  />
                </div>
              </div>

              {/* Examples */}
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h3 className="text-sm font-medium text-gray-700 mb-2">Example Names</h3>
                <div className="grid grid-cols-2 gap-2 text-sm text-gray-600">
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                    Achievable Distance
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                    Thermal Stability
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                    Droplet Trajectory
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                    Power Consumption
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Select Model */}
          {currentStep === 2 && (
            isEditMode && selectedModel ? (
              <div className="space-y-6">
                <div>
                  <h2 className="text-lg font-semibold text-gray-900">Model Selection</h2>
                  <p className="text-sm text-gray-600">
                    The model cannot be changed when editing. Create a new analysis to use a different model.
                  </p>
                </div>
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-indigo-100 rounded-lg flex items-center justify-center">
                      <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{selectedModel.name}</p>
                      <p className="text-sm text-gray-500">{selectedModel.category}</p>
                    </div>
                    <span className="ml-auto px-2 py-1 text-xs font-medium text-gray-500 bg-gray-200 rounded">
                      Locked
                    </span>
                  </div>
                </div>
              </div>
            ) : (
              <StepSelectModel
                selectedModel={selectedModel}
                onSelect={handleModelSelect}
              />
            )
          )}

          {/* Step 3: Bind Inputs */}
          {currentStep === 3 && selectedModel && (
            <StepBindInputs
              model={selectedModel}
              bindings={bindings}
              onChange={setBindings}
              onValidationChange={setBindingsValid}
            />
          )}

          {/* Step 4: Review */}
          {currentStep === 4 && selectedModel && (
            <div className="space-y-6">
              <div>
                <h2 className="text-lg font-semibold text-gray-900">
                  {isEditMode ? 'Review & Update' : 'Review & Create'}
                </h2>
                <p className="text-sm text-gray-600">
                  {isEditMode
                    ? 'Review your changes before updating.'
                    : 'Review your analysis configuration before creating.'}
                </p>
              </div>

              {/* Error message */}
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

              {/* Summary cards */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                    </svg>
                    Analysis Name
                  </h3>
                  <p className="text-gray-900 font-medium">{name}</p>
                  {description && <p className="text-sm text-gray-500 mt-1">{description}</p>}
                </div>

                <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                    </svg>
                    Model
                  </h3>
                  <p className="text-gray-900 font-medium">{selectedModel.name}</p>
                  <p className="text-sm text-gray-500 mt-1">{selectedModel.category}</p>
                </div>
              </div>

              {/* Input bindings */}
              <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                <h3 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                  </svg>
                  Input Bindings
                </h3>
                <div className="space-y-2">
                  {(selectedModel.inputs || []).map(input => {
                    const value = bindings[input.name];
                    const isBound = !!value;
                    const isRequired = !input.optional;

                    return (
                      <div
                        key={input.name}
                        className={`flex items-center justify-between p-2 rounded ${
                          isBound
                            ? 'bg-green-50 border border-green-200'
                            : isRequired
                            ? 'bg-red-50 border border-red-200'
                            : 'bg-gray-100 border border-gray-200'
                        }`}
                      >
                        <div>
                          <span className="text-sm font-medium text-gray-900">{input.name}</span>
                          <span className="text-xs text-gray-500 ml-2">({input.unit})</span>
                          {isRequired && !isBound && (
                            <span className="text-xs text-red-500 ml-2">Required</span>
                          )}
                        </div>
                        <div className="text-sm font-mono text-indigo-600 max-w-xs truncate">
                          {value || <span className="text-gray-400">Not bound</span>}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Outputs */}
              <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                <h3 className="text-sm font-medium text-indigo-700 mb-3 flex items-center gap-2">
                  <svg className="w-4 h-4 text-indigo-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Outputs (will be computed)
                </h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                  {(selectedModel.outputs || []).map(output => (
                    <div key={output.name} className="flex items-center gap-2 text-sm">
                      <span className="w-2 h-2 bg-indigo-400 rounded-full"></span>
                      <span className="text-indigo-900">{output.name}</span>
                      <span className="text-indigo-500">({output.unit})</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Navigation buttons */}
        <div className="mt-6 flex justify-between">
          <button
            onClick={currentStep === 1 ? () => navigate('/analysis') : handleBack}
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
              disabled={!canProceed() || isSaving}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                canProceed() && !isSaving
                  ? 'bg-indigo-600 text-white hover:bg-indigo-700'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              {isSaving ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {isEditMode ? 'Updating...' : 'Creating...'}
                </span>
              ) : (
                isEditMode ? 'Update Analysis' : 'Create Analysis'
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
