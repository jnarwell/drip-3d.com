import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { TestResultStatus } from '../types';
import DRIPCalculator from './DRIPCalculator';

const testResultSchema = z.object({
  result: z.nativeEnum(TestResultStatus),
  component_id: z.string().optional(),
  steering_force: z.number().optional(),
  bonding_strength: z.number().optional(),
  temperature_max: z.number().optional(),
  drip_number: z.number().optional(),
  notes: z.string().optional(),
});

type TestResultFormData = z.infer<typeof testResultSchema>;

interface TestResultFormProps {
  testId: string;
  onSubmit: (data: TestResultFormData) => void;
  onCancel: () => void;
}

const TestResultForm: React.FC<TestResultFormProps> = ({ testId, onSubmit, onCancel }) => {
  const { register, handleSubmit, setValue, watch, formState: { errors } } = useForm<TestResultFormData>({
    resolver: zodResolver(testResultSchema),
  });
  
  const [showDripCalculator, setShowDripCalculator] = useState(false);
  
  const testCategory = getTestCategory(testId);
  const resultValue = watch('result');

  function getTestCategory(id: string): string {
    const prefix = id.split('-')[0];
    const categoryMap: { [key: string]: string } = {
      'AC': 'Acoustic',
      'TH': 'Thermal',
      'ME': 'Mechanical',
      'EL': 'Electrical',
      'MA': 'Material',
    };
    return categoryMap[prefix] || 'General';
  }

  const getTestCriteria = (category: string) => {
    const criteria: { [key: string]: any } = {
      'Acoustic': {
        steering_force: { min: 40, target: 96, unit: 'μN' },
      },
      'Thermal': {
        temperature_max: { max: 1500, warning: 1200, unit: '°C' },
      },
      'Mechanical': {
        bonding_strength: { min: 50, target: 100, unit: 'MPa' },
      },
    };
    return criteria[category] || {};
  };

  const criteria = getTestCriteria(testCategory);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
      {/* Component ID (optional) */}
      <div>
        <label htmlFor="component_id" className="block text-sm font-medium text-gray-700">
          Component ID (optional)
        </label>
        <input
          type="text"
          {...register('component_id')}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          placeholder="e.g., 40KHZ_TRANSDUCERS"
        />
      </div>

      {/* Dynamic fields based on test category */}
      {testCategory === 'Acoustic' && (
        <>
          <div>
            <label htmlFor="steering_force" className="block text-sm font-medium text-gray-700">
              Steering Force (μN)
            </label>
            <input
              type="number"
              step="0.1"
              {...register('steering_force', { valueAsNumber: true })}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
            />
            {errors.steering_force && (
              <p className="mt-1 text-sm text-red-600">{errors.steering_force.message}</p>
            )}
          </div>
          
          <div>
            <button
              type="button"
              onClick={() => setShowDripCalculator(!showDripCalculator)}
              className="text-sm text-indigo-600 hover:text-indigo-500"
            >
              {showDripCalculator ? 'Hide' : 'Show'} DRIP Calculator
            </button>
            {showDripCalculator && (
              <div className="mt-2 p-4 border rounded-lg bg-gray-50">
                <DRIPCalculator
                  onCalculate={(drip) => setValue('drip_number', drip)}
                />
              </div>
            )}
          </div>
        </>
      )}

      {testCategory === 'Thermal' && (
        <div>
          <label htmlFor="temperature_max" className="block text-sm font-medium text-gray-700">
            Maximum Temperature (°C)
          </label>
          <input
            type="number"
            {...register('temperature_max', { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
          {errors.temperature_max && (
            <p className="mt-1 text-sm text-red-600">{errors.temperature_max.message}</p>
          )}
        </div>
      )}

      {testCategory === 'Mechanical' && (
        <div>
          <label htmlFor="bonding_strength" className="block text-sm font-medium text-gray-700">
            Bonding Strength (MPa)
          </label>
          <input
            type="number"
            step="0.1"
            {...register('bonding_strength', { valueAsNumber: true })}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
          />
          {errors.bonding_strength && (
            <p className="mt-1 text-sm text-red-600">{errors.bonding_strength.message}</p>
          )}
        </div>
      )}

      {/* Pass/Fail Result */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Test Result</label>
        <div className="flex gap-4">
          {Object.values(TestResultStatus).map((status) => (
            <label key={status} className="flex items-center">
              <input
                type="radio"
                value={status}
                {...register('result')}
                className="mr-2"
              />
              <span className={`px-3 py-1 rounded text-sm font-medium ${
                status === TestResultStatus.PASS
                  ? 'bg-green-100 text-green-800'
                  : status === TestResultStatus.FAIL
                  ? 'bg-red-100 text-red-800'
                  : 'bg-yellow-100 text-yellow-800'
              }`}>
                {status}
              </span>
            </label>
          ))}
        </div>
        {errors.result && (
          <p className="mt-1 text-sm text-red-600">Please select a result</p>
        )}
      </div>

      {/* Notes */}
      <div>
        <label htmlFor="notes" className="block text-sm font-medium text-gray-700">
          Notes (optional)
        </label>
        <textarea
          {...register('notes')}
          rows={3}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Form Actions */}
      <div className="flex justify-end gap-3 pt-4 border-t">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Submit Test Result
        </button>
      </div>
    </form>
  );
};

export default TestResultForm;