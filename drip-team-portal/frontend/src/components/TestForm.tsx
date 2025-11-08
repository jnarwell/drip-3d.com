import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TestStatus } from '../types';

const testSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  category: z.string().min(1, 'Category is required'),
  purpose: z.string().optional(),
  duration_hours: z.union([z.number().positive(), z.literal('')]).optional(),
  prerequisites: z.array(z.string()).optional(),
  engineer: z.string().optional(),
  notes: z.string().optional(),
});

type TestFormData = z.infer<typeof testSchema>;

interface TestFormProps {
  initialData?: Partial<TestFormData>;
  onSubmit: (data: TestFormData) => void;
  onCancel: () => void;
  isEdit?: boolean;
}

const TestForm: React.FC<TestFormProps> = ({ 
  initialData, 
  onSubmit, 
  onCancel,
  isEdit = false 
}) => {
  const { register, handleSubmit, formState: { errors }, watch, setValue } = useForm<TestFormData>({
    resolver: zodResolver(testSchema),
    defaultValues: initialData || {
      category: 'Acoustic',
      prerequisites: [],
    },
  });

  const categories = ['Acoustic', 'Thermal', 'Mechanical', 'Electrical', 'Integration', 'System', 'Physics Validation'];

  const handlePrerequisitesChange = (value: string) => {
    const prereqs = value.split(',').map(s => s.trim()).filter(s => s);
    setValue('prerequisites', prereqs);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Test Name *
        </label>
        <input
          type="text"
          id="name"
          {...register('name')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
        {errors.name && (
          <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
        )}
      </div>

      <div>
        <label htmlFor="category" className="block text-sm font-medium text-gray-700">
          Category *
        </label>
        <select
          id="category"
          {...register('category')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="purpose" className="block text-sm font-medium text-gray-700">
          Purpose
        </label>
        <textarea
          id="purpose"
          rows={2}
          {...register('purpose')}
          placeholder="What is this test validating?"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="duration_hours" className="block text-sm font-medium text-gray-700">
            Duration (hours)
          </label>
          <input
            type="number"
            id="duration_hours"
            step="0.5"
            {...register('duration_hours', { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label htmlFor="engineer" className="block text-sm font-medium text-gray-700">
            Assigned Engineer
          </label>
          <input
            type="email"
            id="engineer"
            {...register('engineer')}
            placeholder="engineer@drip-3d.com"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div>
        <label htmlFor="prerequisites" className="block text-sm font-medium text-gray-700">
          Prerequisites
        </label>
        <input
          type="text"
          id="prerequisites"
          defaultValue={initialData?.prerequisites?.join(', ')}
          onChange={(e) => handlePrerequisitesChange(e.target.value)}
          placeholder="Comma-separated test IDs (e.g., TST-001, TST-002)"
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
        <p className="mt-1 text-sm text-gray-500">Enter test IDs that must be completed before this test</p>
      </div>

      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
          Notes
        </label>
        <textarea
          id="notes"
          rows={3}
          {...register('notes')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      <div className="flex justify-end space-x-3 pt-4">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
        >
          {isEdit ? 'Update Test' : 'Create Test'}
        </button>
      </div>
    </form>
  );
};

export default TestForm;