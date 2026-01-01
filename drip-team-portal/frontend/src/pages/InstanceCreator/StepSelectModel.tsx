import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import { PhysicsModel } from './types';

interface StepSelectModelProps {
  selectedModel: PhysicsModel | null;
  onSelect: (model: PhysicsModel) => void;
}

export default function StepSelectModel({ selectedModel, onSelect }: StepSelectModelProps) {
  const api = useAuthenticatedApi();

  const { data: models, isLoading, error } = useQuery({
    queryKey: ['physics-models'],
    queryFn: async () => {
      const response = await api.get('/api/v1/physics-models');
      return response.data as PhysicsModel[];
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
        Failed to load models
      </div>
    );
  }

  const categories = [...new Set(models?.map(m => m.category) || [])];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-gray-900">Select a Physics Model</h2>
        <p className="text-sm text-gray-600">
          Choose a model template to use for your calculation.
        </p>
      </div>

      {categories.map(category => {
        const categoryModels = models?.filter(m => m.category === category) || [];
        if (categoryModels.length === 0) return null;

        return (
          <div key={category}>
            <h3 className="text-sm font-medium text-gray-700 mb-2 capitalize">{category}</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {categoryModels.map(model => {
                const isSelected = selectedModel?.id === model.id;
                const inputs = model.current_version?.inputs || model.inputs || [];
                const outputs = model.current_version?.outputs || model.outputs || [];

                return (
                  <button
                    key={model.id}
                    onClick={() => onSelect({
                      ...model,
                      version_id: model.current_version?.id || model.version_id,
                      inputs,
                      outputs,
                    })}
                    className={`text-left p-4 rounded-lg border-2 transition-all ${
                      isSelected
                        ? 'border-indigo-600 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300 bg-white'
                    }`}
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900">{model.name}</h4>
                        {model.description && (
                          <p className="text-sm text-gray-500 mt-1 line-clamp-2">
                            {model.description}
                          </p>
                        )}
                        <div className="mt-2 flex items-center gap-4 text-xs text-gray-500">
                          <span>{inputs.length} inputs</span>
                          <span>{outputs.length} outputs</span>
                        </div>
                      </div>
                      {isSelected && (
                        <div className="ml-2 flex-shrink-0">
                          <svg className="w-5 h-5 text-indigo-600" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  </button>
                );
              })}
            </div>
          </div>
        );
      })}

      {(!models || models.length === 0) && (
        <div className="text-center py-12 text-gray-500">
          <p>No physics models available.</p>
          <p className="text-sm mt-1">Create a model first using the Model Builder.</p>
        </div>
      )}
    </div>
  );
}
