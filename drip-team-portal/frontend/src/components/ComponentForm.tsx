import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ComponentCategory, ComponentStatus, RDPhase } from '../types';

const componentSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  category: z.nativeEnum(ComponentCategory),
  phase: z.nativeEnum(RDPhase),
  part_number: z.string().optional(),
  supplier: z.string().optional(),
  unit_cost: z.union([z.number().positive(), z.literal('')]).optional(),
  quantity: z.union([z.number().int().positive(), z.literal('')]).optional(),
  notes: z.string().optional(),
  tech_specs: z.record(z.string(), z.any()).optional(),
});

type ComponentFormData = z.infer<typeof componentSchema>;

interface ComponentFormProps {
  initialData?: Partial<ComponentFormData>;
  onSubmit: (data: ComponentFormData) => void;
  onCancel: () => void;
  isEdit?: boolean;
}

const ComponentForm: React.FC<ComponentFormProps> = ({ 
  initialData, 
  onSubmit, 
  onCancel,
  isEdit = false 
}) => {
  const { register, handleSubmit, formState: { errors } } = useForm<ComponentFormData>({
    resolver: zodResolver(componentSchema),
    defaultValues: initialData || {
      category: ComponentCategory.MECHANICAL,
      phase: RDPhase.PHASE_1,
      quantity: 1,
    },
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      <div>
        <label htmlFor="name" className="block text-sm font-medium text-gray-700">
          Component Name *
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
          {Object.values(ComponentCategory).map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
      </div>

      <div>
        <label htmlFor="phase" className="block text-sm font-medium text-gray-700">
          R&D Phase *
        </label>
        <select
          id="phase"
          {...register('phase')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value={RDPhase.PHASE_1}>
            Phase 1 - Basic Acoustic (Styrofoam + Gallium Indium)
          </option>
          <option value={RDPhase.PHASE_2}>
            Phase 2 - Aluminum Testing & Production Research
          </option>
          <option value={RDPhase.PHASE_3}>
            Phase 3 - L1 PROTOTYPE
          </option>
        </select>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="part_number" className="block text-sm font-medium text-gray-700">
            Part Number
          </label>
          <input
            type="text"
            id="part_number"
            {...register('part_number')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label htmlFor="supplier" className="block text-sm font-medium text-gray-700">
            Supplier
          </label>
          <input
            type="text"
            id="supplier"
            {...register('supplier')}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="unit_cost" className="block text-sm font-medium text-gray-700">
            Unit Cost ($)
          </label>
          <input
            type="number"
            id="unit_cost"
            step="0.01"
            {...register('unit_cost', { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>

        <div>
          <label htmlFor="quantity" className="block text-sm font-medium text-gray-700">
            Quantity
          </label>
          <input
            type="number"
            id="quantity"
            {...register('quantity', { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
        </div>
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
          {isEdit ? 'Update Component' : 'Create Component'}
        </button>
      </div>
    </form>
  );
};

export default ComponentForm;