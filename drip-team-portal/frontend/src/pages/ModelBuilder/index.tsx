import React, { useState, useCallback, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import { ModelBuilderData, CreateModelRequest, CreateModelResponse, ModelVariable, initialModelData } from './types';
import ProgressStepper from './components/ProgressStepper';
import NavigationButtons from './components/NavigationButtons';
import StepDefineModel from './StepDefineModel';
import StepInputsOutputs from './StepInputsOutputs';
import StepEquations from './StepEquations';
import StepValidate from './StepValidate';

const STEPS = [
  { number: 1, title: 'Define Model' },
  { number: 2, title: 'Inputs & Outputs' },
  { number: 3, title: 'Equations' },
  { number: 4, title: 'Validate & Create' },
];

const ModelBuilder: React.FC = () => {
  const navigate = useNavigate();
  const { modelId } = useParams<{ modelId?: string }>();
  const api = useAuthenticatedApi();

  const isEditMode = Boolean(modelId);

  const [step, setStep] = useState(1);
  const [modelData, setModelData] = useState<ModelBuilderData>(initialModelData);
  const [stepValid, setStepValid] = useState<Record<number, boolean>>({
    1: false,
    2: false,
    3: false,
    4: true, // Default to true, will be updated by validation
  });
  const [initialized, setInitialized] = useState(!isEditMode); // Skip init if creating new

  // Fetch existing model if editing
  const { data: existingModel, isLoading: loadingModel } = useQuery({
    queryKey: ['physics-model', modelId],
    queryFn: async () => {
      if (!modelId) return null;
      const response = await api.get(`/api/v1/physics-models/${modelId}`);
      return response.data;
    },
    enabled: isEditMode,
  });

  // Pre-populate form when existing model loads
  useEffect(() => {
    if (existingModel && !initialized) {
      const currentVersion = existingModel.current_version;

      // Convert inputs to ModelVariable format with IDs
      const inputs: ModelVariable[] = (currentVersion?.inputs || existingModel.inputs || []).map(
        (inp: { name: string; unit: string; description?: string }, idx: number) => ({
          id: `input-${idx}-${Date.now()}`,
          name: inp.name,
          unit: inp.unit || '',
          description: inp.description || '',
        })
      );

      // Convert outputs to ModelVariable format with IDs
      const outputs: ModelVariable[] = (currentVersion?.outputs || existingModel.outputs || []).map(
        (out: { name: string; unit: string; description?: string }, idx: number) => ({
          id: `output-${idx}-${Date.now()}`,
          name: out.name,
          unit: out.unit || '',
          description: out.description || '',
        })
      );

      setModelData({
        name: existingModel.name || '',
        description: existingModel.description || '',
        category: existingModel.category || '',
        inputs,
        outputs,
        equations: currentVersion?.equations || {},
      });

      // Mark step 1 as valid since we have data
      setStepValid((prev) => ({ ...prev, 1: true }));
      setInitialized(true);
    }
  }, [existingModel, initialized]);

  // Update model data from steps
  const handleDataChange = useCallback((updates: Partial<ModelBuilderData>) => {
    setModelData((prev) => ({ ...prev, ...updates }));
  }, []);

  // Stable callbacks for each step's validity - avoids infinite loops
  const handleStep1Valid = useCallback((isValid: boolean) => {
    setStepValid((prev) => ({ ...prev, 1: isValid }));
  }, []);
  const handleStep2Valid = useCallback((isValid: boolean) => {
    setStepValid((prev) => ({ ...prev, 2: isValid }));
  }, []);
  const handleStep3Valid = useCallback((isValid: boolean) => {
    setStepValid((prev) => ({ ...prev, 3: isValid }));
  }, []);
  const handleStep4Valid = useCallback((isValid: boolean) => {
    setStepValid((prev) => ({ ...prev, 4: isValid }));
  }, []);

  // Create model mutation
  const createModel = useMutation<CreateModelResponse, Error, CreateModelRequest>({
    mutationFn: async (request) => {
      const response = await api.post('/api/v1/physics-models', request);
      return response.data;
    },
    onSuccess: (data) => {
      navigate('/models', { state: { created: data.name } });
    },
  });

  // Update model mutation
  const updateModel = useMutation<CreateModelResponse, Error, CreateModelRequest>({
    mutationFn: async (request) => {
      const response = await api.patch(`/api/v1/physics-models/${modelId}`, request);
      return response.data;
    },
    onSuccess: (data) => {
      navigate('/models', { state: { updated: data.name } });
    },
  });

  // Handle save (create or update)
  const handleSave = () => {
    const request: CreateModelRequest = {
      name: modelData.name,
      description: modelData.description || undefined,
      category: modelData.category,
      inputs: modelData.inputs.map((v) => ({
        name: v.name,
        unit: v.unit,
        description: v.description || undefined,
      })),
      outputs: modelData.outputs.map((v) => ({
        name: v.name,
        unit: v.unit,
        description: v.description || undefined,
      })),
      equations: modelData.equations,
    };

    if (isEditMode) {
      updateModel.mutate(request);
    } else {
      createModel.mutate(request);
    }
  };

  const saveError = isEditMode ? updateModel.error : createModel.error;
  const isSaving = isEditMode ? updateModel.isPending : createModel.isPending;

  const canProceed = stepValid[step];

  // Show loading state while fetching model for edit
  if (isEditMode && loadingModel) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading model...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">
          {isEditMode ? 'Edit Physics Model' : 'Create Physics Model'}
        </h1>
        <p className="mt-1 text-sm text-gray-500">
          {isEditMode
            ? `Update "${existingModel?.name || 'model'}" configuration and equations.`
            : 'Build a reusable physics model template for your engineering calculations.'}
        </p>
      </div>

      {/* Progress Stepper */}
      <ProgressStepper currentStep={step} steps={STEPS} />

      {/* Step Content */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        {step === 1 && (
          <StepDefineModel
            data={modelData}
            onChange={handleDataChange}
            onValidChange={handleStep1Valid}
          />
        )}

        {step === 2 && (
          <StepInputsOutputs
            data={modelData}
            onChange={handleDataChange}
            onValidChange={handleStep2Valid}
          />
        )}

        {step === 3 && (
          <StepEquations
            data={modelData}
            onChange={handleDataChange}
            onValidChange={handleStep3Valid}
          />
        )}

        {step === 4 && (
          <StepValidate
            data={modelData}
            onValidChange={handleStep4Valid}
          />
        )}

        {/* Error display */}
        {saveError && (
          <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex">
              <svg
                className="h-5 w-5 text-red-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-red-800">
                  Error {isEditMode ? 'updating' : 'creating'} model
                </h3>
                <p className="mt-1 text-sm text-red-700">
                  {saveError.message || 'An unexpected error occurred'}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Navigation */}
        <NavigationButtons
          step={step}
          totalSteps={STEPS.length}
          onNext={() => setStep((s) => Math.min(s + 1, STEPS.length))}
          onBack={() => setStep((s) => Math.max(s - 1, 1))}
          onSave={handleSave}
          canProceed={canProceed}
          isSaving={isSaving}
          isEditMode={isEditMode}
        />
      </div>

      {/* Cancel link */}
      <div className="mt-4 text-center">
        <button
          type="button"
          onClick={() => navigate('/models')}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Cancel and return to models
        </button>
      </div>
    </div>
  );
};

export default ModelBuilder;
