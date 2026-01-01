import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ModelBuilderData, stepOneSchema, MODEL_CATEGORIES } from './types';

interface StepDefineModelProps {
  data: ModelBuilderData;
  onChange: (data: Partial<ModelBuilderData>) => void;
  onValidChange: (isValid: boolean) => void;
}

type StepOneFormData = z.infer<typeof stepOneSchema>;

const StepDefineModel: React.FC<StepDefineModelProps> = ({ data, onChange, onValidChange }) => {
  // Track if we've synced with parent data (for edit mode)
  const [isSynced, setIsSynced] = React.useState(false);
  const prevDataRef = React.useRef({ name: '', description: '', category: '' });

  const {
    register,
    formState: { errors, isValid },
    watch,
    reset,
  } = useForm<StepOneFormData>({
    resolver: zodResolver(stepOneSchema),
    defaultValues: {
      name: data.name,
      description: data.description,
      category: data.category,
    },
    mode: 'onChange',
  });

  // Sync form when data prop changes (for edit mode)
  React.useEffect(() => {
    // Check if data has meaningful values that differ from what we have
    const hasNewData = data.name || data.description || data.category;
    const isDifferent =
      data.name !== prevDataRef.current.name ||
      data.description !== prevDataRef.current.description ||
      data.category !== prevDataRef.current.category;

    if (hasNewData && isDifferent) {
      reset({
        name: data.name,
        description: data.description,
        category: data.category,
      });
      prevDataRef.current = { name: data.name, description: data.description, category: data.category };
      setIsSynced(true);
    } else if (!hasNewData && !isSynced) {
      // Initial mount with empty data - mark as synced so we can propagate changes
      setIsSynced(true);
    }
  }, [data.name, data.description, data.category, reset, isSynced]);

  // Watch all fields and update parent - but only after initial sync
  const watchedFields = watch();

  React.useEffect(() => {
    // Don't propagate changes until we've synced with any incoming data
    if (!isSynced) return;

    // Only update if values actually changed (prevents loops)
    if (
      watchedFields.name !== prevDataRef.current.name ||
      watchedFields.description !== prevDataRef.current.description ||
      watchedFields.category !== prevDataRef.current.category
    ) {
      prevDataRef.current = {
        name: watchedFields.name,
        description: watchedFields.description || '',
        category: watchedFields.category,
      };
      onChange({
        name: watchedFields.name,
        description: watchedFields.description || '',
        category: watchedFields.category,
      });
    }
  }, [watchedFields.name, watchedFields.description, watchedFields.category, onChange, isSynced]);

  React.useEffect(() => {
    onValidChange(isValid);
  }, [isValid, onValidChange]);

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-medium text-gray-900">Define Your Model</h2>
        <p className="mt-1 text-sm text-gray-500">
          Start by giving your physics model a name and description.
        </p>
      </div>

      <div className="space-y-4">
        {/* Model Name */}
        <div>
          <label htmlFor="name" className="block text-sm font-medium text-gray-700">
            Model Name *
          </label>
          <input
            type="text"
            id="name"
            {...register('name')}
            placeholder="e.g., Crucible Thermal Expansion"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>

        {/* Category */}
        <div>
          <label htmlFor="category" className="block text-sm font-medium text-gray-700">
            Category *
          </label>
          <select
            id="category"
            {...register('category')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          >
            <option value="">Select a category...</option>
            {MODEL_CATEGORIES.map((cat) => (
              <option key={cat.value} value={cat.value}>
                {cat.label}
              </option>
            ))}
          </select>
          {errors.category && (
            <p className="mt-1 text-sm text-red-600">{errors.category.message}</p>
          )}
        </div>

        {/* Description */}
        <div>
          <label htmlFor="description" className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <textarea
            id="description"
            rows={4}
            {...register('description')}
            placeholder="Describe what this model calculates and when to use it..."
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
          />
          <p className="mt-1 text-sm text-gray-500">
            Optional but recommended. Help your team understand when to use this model.
          </p>
        </div>
      </div>
    </div>
  );
};

export default StepDefineModel;
