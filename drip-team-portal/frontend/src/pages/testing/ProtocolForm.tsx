import React, { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm, useFieldArray, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthenticatedApi } from '../../services/api';
import type { TestProtocol, InputSchemaItem, OutputSchemaItem } from '../../types';

// Zod schemas
const inputSchemaItemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  unit_id: z.number().optional().nullable(),
  required: z.boolean(),
  description: z.string().optional(),
  default_value: z.number().optional().nullable(),
});

const outputSchemaItemSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  unit_id: z.number().optional().nullable(),
  target: z.number().optional().nullable(),
  tolerance_pct: z.number().min(0).max(100).optional().nullable(),
  min_value: z.number().optional().nullable(),
  max_value: z.number().optional().nullable(),
  description: z.string().optional(),
});

const checklistItemSchema = z.object({
  step: z.string().min(1, 'Step is required'),
});

const protocolFormSchema = z.object({
  name: z.string().min(1, 'Name is required').max(200),
  description: z.string().optional(),
  category: z.string().optional(),
  procedure: z.string().optional(),
  equipment: z.string().optional(), // Will be split into array
  model_id: z.number().optional().nullable(),
  input_schema: z.array(inputSchemaItemSchema).optional(),
  output_schema: z.array(outputSchemaItemSchema).optional(),
  setup_checklist: z.array(checklistItemSchema).optional(),
});

type ProtocolFormData = z.infer<typeof protocolFormSchema>;

interface PhysicsModel {
  id: number;
  name: string;
  category: string;
}

const CATEGORIES = [
  'Acoustic',
  'Thermal',
  'Mechanical',
  'Electrical',
  'Integration',
  'System',
  'Physics Validation',
];

const ProtocolForm: React.FC = () => {
  const { protocolId } = useParams<{ protocolId: string }>();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const isEdit = !!protocolId;

  // Form setup
  const {
    register,
    control,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<ProtocolFormData>({
    resolver: zodResolver(protocolFormSchema),
    defaultValues: {
      name: '',
      description: '',
      category: '',
      procedure: '',
      equipment: '',
      input_schema: [],
      output_schema: [],
      setup_checklist: [],
    },
  });

  // Field arrays for dynamic schema builders
  const {
    fields: inputFields,
    append: appendInput,
    remove: removeInput,
  } = useFieldArray({
    control,
    name: 'input_schema',
  });

  const {
    fields: outputFields,
    append: appendOutput,
    remove: removeOutput,
  } = useFieldArray({
    control,
    name: 'output_schema',
  });

  const {
    fields: checklistFields,
    append: appendChecklist,
    remove: removeChecklist,
  } = useFieldArray({
    control,
    name: 'setup_checklist',
  });

  // Fetch existing protocol for edit
  const { data: protocol } = useQuery<TestProtocol>({
    queryKey: ['test-protocol', protocolId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/${protocolId}`);
      return response.data;
    },
    enabled: isEdit,
  });

  // Fetch physics models for dropdown
  const { data: models } = useQuery<PhysicsModel[]>({
    queryKey: ['physics-models'],
    queryFn: async () => {
      const response = await api.get('/api/v1/physics-models');
      return response.data;
    },
  });

  // Reset form when protocol loads
  useEffect(() => {
    if (protocol) {
      reset({
        name: protocol.name,
        description: protocol.description || '',
        category: protocol.category || '',
        procedure: protocol.procedure || '',
        equipment: protocol.equipment?.join(', ') || '',
        model_id: protocol.model_id || null,
        input_schema: protocol.input_schema || [],
        output_schema: protocol.output_schema || [],
        setup_checklist: protocol.setup_checklist?.map((s: string) => ({ step: s })) || [],
      });
    }
  }, [protocol, reset]);

  // Create mutation
  const createProtocol = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.post('/api/v1/test-protocols', data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['test-protocols'] });
      navigate(`/testing/protocols/${data.id}`);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to create protocol');
    },
  });

  // Update mutation
  const updateProtocol = useMutation({
    mutationFn: async (data: any) => {
      const response = await api.patch(`/api/v1/test-protocols/${protocolId}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-protocols'] });
      queryClient.invalidateQueries({ queryKey: ['test-protocol', protocolId] });
      navigate(`/testing/protocols/${protocolId}`);
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to update protocol');
    },
  });

  const onSubmit = (data: ProtocolFormData) => {
    // Transform equipment string to array and checklist items to string array
    const payload = {
      ...data,
      equipment: data.equipment
        ? data.equipment.split(',').map((s) => s.trim()).filter(Boolean)
        : [],
      model_id: data.model_id || null,
      setup_checklist: data.setup_checklist?.map((item) => item.step).filter(Boolean) || [],
    };

    if (isEdit) {
      updateProtocol.mutate(payload);
    } else {
      createProtocol.mutate(payload);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow-sm border">
        {/* Header */}
        <div className="px-6 py-4 border-b">
          <h1 className="text-xl font-bold text-gray-900">
            {isEdit ? 'Edit Protocol' : 'New Test Protocol'}
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            Define a reusable test template with inputs, outputs, and procedures.
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-6">
          {/* Basic Info */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Name *
              </label>
              <input
                type="text"
                {...register('name')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="e.g., Thermal Cycling Test"
              />
              {errors.name && (
                <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
              )}
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Description
              </label>
              <textarea
                {...register('description')}
                rows={2}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="Brief description of what this test validates"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Category
              </label>
              <select
                {...register('category')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
              >
                <option value="">Select category...</option>
                {CATEGORIES.map((cat) => (
                  <option key={cat} value={cat}>{cat}</option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700">
                Physics Model (optional)
              </label>
              <Controller
                name="model_id"
                control={control}
                render={({ field }) => (
                  <select
                    {...field}
                    value={field.value || ''}
                    onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                    className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                  >
                    <option value="">No model</option>
                    {models?.map((model) => (
                      <option key={model.id} value={model.id}>
                        {model.name} ({model.category})
                      </option>
                    ))}
                  </select>
                )}
              />
            </div>

            <div className="md:col-span-2">
              <label className="block text-sm font-medium text-gray-700">
                Equipment (comma-separated)
              </label>
              <input
                type="text"
                {...register('equipment')}
                className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                placeholder="e.g., Thermal chamber, Data logger, Multimeter"
              />
            </div>
          </div>

          {/* Input Schema Builder */}
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Input Parameters</h3>
              <button
                type="button"
                onClick={() => appendInput({ name: '', required: true, description: '' })}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                + Add Input
              </button>
            </div>
            {inputFields.length === 0 ? (
              <p className="text-sm text-gray-500">No input parameters. Click "Add Input" to define test inputs.</p>
            ) : (
              <div className="space-y-3">
                {inputFields.map((field, index) => (
                  <div key={field.id} className="flex gap-3 items-start bg-gray-50 p-3 rounded">
                    <div className="flex-1 grid grid-cols-2 md:grid-cols-4 gap-3">
                      <div>
                        <input
                          {...register(`input_schema.${index}.name`)}
                          placeholder="Parameter name"
                          className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <input
                          {...register(`input_schema.${index}.description`)}
                          placeholder="Description"
                          className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                        />
                      </div>
                      <div>
                        <Controller
                          name={`input_schema.${index}.default_value`}
                          control={control}
                          render={({ field }) => (
                            <input
                              type="number"
                              step="any"
                              {...field}
                              value={field.value ?? ''}
                              onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                              placeholder="Default"
                              className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                            />
                          )}
                        />
                      </div>
                      <div className="flex items-center gap-2">
                        <label className="flex items-center gap-1 text-sm">
                          <input
                            type="checkbox"
                            {...register(`input_schema.${index}.required`)}
                            className="rounded border-gray-300 text-indigo-600"
                          />
                          Required
                        </label>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={() => removeInput(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Output Schema Builder */}
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium text-gray-900">Output Parameters</h3>
              <button
                type="button"
                onClick={() => appendOutput({ name: '', description: '' })}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                + Add Output
              </button>
            </div>
            {outputFields.length === 0 ? (
              <p className="text-sm text-gray-500">No output parameters. Click "Add Output" to define expected measurements.</p>
            ) : (
              <div className="space-y-3">
                {outputFields.map((field, index) => (
                  <div key={field.id} className="bg-gray-50 p-3 rounded">
                    <div className="flex gap-3 items-start">
                      <div className="flex-1 grid grid-cols-2 md:grid-cols-3 gap-3">
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Name</label>
                          <input
                            {...register(`output_schema.${index}.name`)}
                            placeholder="Parameter name"
                            className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Description</label>
                          <input
                            {...register(`output_schema.${index}.description`)}
                            placeholder="Description"
                            className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Target Value</label>
                          <Controller
                            name={`output_schema.${index}.target`}
                            control={control}
                            render={({ field }) => (
                              <input
                                type="number"
                                step="any"
                                {...field}
                                value={field.value ?? ''}
                                onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                                placeholder="Expected value"
                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                              />
                            )}
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Tolerance %</label>
                          <Controller
                            name={`output_schema.${index}.tolerance_pct`}
                            control={control}
                            render={({ field }) => (
                              <input
                                type="number"
                                step="0.1"
                                min="0"
                                max="100"
                                {...field}
                                value={field.value ?? ''}
                                onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                                placeholder="e.g., 5"
                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                              />
                            )}
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Min Value</label>
                          <Controller
                            name={`output_schema.${index}.min_value`}
                            control={control}
                            render={({ field }) => (
                              <input
                                type="number"
                                step="any"
                                {...field}
                                value={field.value ?? ''}
                                onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                                placeholder="Minimum"
                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                              />
                            )}
                          />
                        </div>
                        <div>
                          <label className="block text-xs text-gray-500 mb-1">Max Value</label>
                          <Controller
                            name={`output_schema.${index}.max_value`}
                            control={control}
                            render={({ field }) => (
                              <input
                                type="number"
                                step="any"
                                {...field}
                                value={field.value ?? ''}
                                onChange={(e) => field.onChange(e.target.value ? Number(e.target.value) : null)}
                                placeholder="Maximum"
                                className="w-full text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                              />
                            )}
                          />
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeOutput(index)}
                        className="text-red-500 hover:text-red-700 p-1 mt-5"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Setup Checklist Builder */}
          <div className="border rounded-lg p-4">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-medium text-gray-900">Setup Checklist</h3>
                <p className="text-sm text-gray-500">Steps to verify before starting the test</p>
              </div>
              <button
                type="button"
                onClick={() => appendChecklist({ step: '' })}
                className="text-sm text-indigo-600 hover:text-indigo-800"
              >
                + Add Step
              </button>
            </div>
            {checklistFields.length === 0 ? (
              <p className="text-sm text-gray-500">No checklist items. Click "Add Step" to define setup verification steps.</p>
            ) : (
              <div className="space-y-2">
                {checklistFields.map((field, index) => (
                  <div key={field.id} className="flex gap-3 items-center bg-gray-50 p-2 rounded">
                    <span className="text-sm text-gray-400 w-6">{index + 1}.</span>
                    <input
                      {...register(`setup_checklist.${index}.step`)}
                      placeholder="e.g., Verify equipment calibration is current"
                      className="flex-1 text-sm rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
                    />
                    <button
                      type="button"
                      onClick={() => removeChecklist(index)}
                      className="text-red-500 hover:text-red-700 p-1"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Procedure */}
          <div>
            <label className="block text-sm font-medium text-gray-700">
              Procedure
            </label>
            <textarea
              {...register('procedure')}
              rows={8}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 font-mono text-sm"
              placeholder={`1. Setup equipment according to specification
2. Configure test parameters
3. Execute test sequence
4. Record measurements
5. Verify results against targets`}
            />
          </div>

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || createProtocol.isPending || updateProtocol.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50"
            >
              {isSubmitting || createProtocol.isPending || updateProtocol.isPending
                ? 'Saving...'
                : isEdit
                ? 'Update Protocol'
                : 'Create Protocol'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ProtocolForm;
