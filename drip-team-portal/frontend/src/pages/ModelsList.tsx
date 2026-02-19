import React, { useState, useRef, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';

interface PhysicsModel {
  id: string;
  name: string;
  description?: string;
  category: string;
  created_at: string;
  updated_at: string;
  current_version?: {
    id: string;
    version: number;
    inputs: Array<{ name: string; unit: string; description?: string }>;
    outputs: Array<{ name: string; unit: string; description?: string }>;
  };
}

const CATEGORY_COLORS: Record<string, string> = {
  thermal: 'bg-orange-100 text-orange-800',
  mechanical: 'bg-blue-100 text-blue-800',
  acoustic: 'bg-purple-100 text-purple-800',
  electrical: 'bg-yellow-100 text-yellow-800',
  fluid: 'bg-cyan-100 text-cyan-800',
  structural: 'bg-green-100 text-green-800',
  electromagnetic: 'bg-pink-100 text-pink-800',
  optical: 'bg-indigo-100 text-indigo-800',
  multiphysics: 'bg-gray-100 text-gray-800',
  other: 'bg-gray-100 text-gray-800',
};

const ModelsList: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const createdModelName = location.state?.created;

  // Dropdown state
  const [openDropdownId, setOpenDropdownId] = useState<string | null>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setOpenDropdownId(null);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const { data: models, isLoading, error } = useQuery<PhysicsModel[]>({
    queryKey: ['physics-models'],
    queryFn: async () => {
      const response = await api.get('/api/v1/physics-models');
      return response.data;
    },
  });

  // Delete mutation
  const deleteModel = useMutation({
    mutationFn: async (modelId: string) => {
      try {
        await api.delete(`/api/v1/physics-models/${modelId}`);
      } catch (err: any) {
        // Extract error message from backend response
        const message = err.response?.data?.detail || err.message || 'Failed to delete model';
        throw new Error(message);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['physics-models'] });
      setOpenDropdownId(null);
    },
    onError: (error: Error) => {
      alert(error.message);
    },
  });

  return (
    <div>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Physics Models</h1>
          <p className="mt-1 text-sm text-gray-500">
            Reusable physics model templates for engineering calculations.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/models/new"
            className="inline-flex items-center px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700"
          >
            <svg
              className="h-4 w-4 mr-2"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 4v16m8-8H4"
              />
            </svg>
            New Model
          </Link>
        </div>
      </div>

      {/* Success message */}
      {createdModelName && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-md">
          <div className="flex">
            <svg
              className="h-5 w-5 text-green-400"
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
            <p className="ml-3 text-sm text-green-700">
              Model "{createdModelName}" created successfully!
            </p>
          </div>
        </div>
      )}

      {/* Loading state */}
      {isLoading && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <svg
            className="animate-spin mx-auto h-8 w-8 text-indigo-600"
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
          <p className="mt-4 text-sm text-gray-500">Loading models...</p>
        </div>
      )}

      {/* Error state */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
          <div className="flex">
            <svg className="h-5 w-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="ml-3 text-sm text-red-700">
              Failed to load models: {(error as Error).message}
            </p>
          </div>
        </div>
      )}

      {/* Models list */}
      {!isLoading && !error && models && models.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Category
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Variables
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Version
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {models.map((model) => (
                <tr key={model.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{model.name}</div>
                      {model.description && (
                        <div className="text-sm text-gray-500 truncate max-w-md">
                          {model.description}
                        </div>
                      )}
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${CATEGORY_COLORS[model.category] || CATEGORY_COLORS.other}`}>
                      {model.category}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    {model.current_version ? (
                      <span>
                        {model.current_version.inputs.length} inputs, {model.current_version.outputs.length} outputs
                      </span>
                    ) : (
                      <span className="text-gray-400">-</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-500">
                    v{model.current_version?.version || 1}
                  </td>
                  <td className="px-6 py-4 text-right text-sm font-medium">
                    <div className="relative inline-block" ref={openDropdownId === model.id ? dropdownRef : null}>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setOpenDropdownId(openDropdownId === model.id ? null : model.id);
                        }}
                        aria-label="Model actions"
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z" />
                        </svg>
                      </button>

                      {openDropdownId === model.id && (
                        <div className="absolute right-0 z-50 top-full mt-1 w-48 rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5">
                          <div className="py-1">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                navigate(`/models/${model.id}/edit`);
                                setOpenDropdownId(null);
                              }}
                              className="block w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100"
                            >
                              Edit Model
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                if (confirm(`Delete model "${model.name}"? This cannot be undone.`)) {
                                  deleteModel.mutate(model.id);
                                }
                                setOpenDropdownId(null);
                              }}
                              className="block w-full px-4 py-2 text-left text-sm text-red-600 hover:bg-red-50"
                            >
                              Delete Model
                            </button>
                          </div>
                        </div>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Empty state */}
      {!isLoading && !error && (!models || models.length === 0) && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-12 text-center">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No models yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Get started by creating your first physics model template.
            </p>
            <div className="mt-6">
              <Link
                to="/models/new"
                className="inline-flex items-center px-4 py-2 text-sm font-medium text-indigo-600 bg-indigo-50 rounded-md hover:bg-indigo-100"
              >
                <svg
                  className="h-4 w-4 mr-2"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create Model
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* Info card */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
        <h3 className="text-sm font-medium text-blue-800 mb-2">
          What are Physics Models?
        </h3>
        <p className="text-sm text-blue-700">
          Physics models are reusable calculation templates that define inputs, outputs,
          and the equations that relate them. Once created, you can create instances of
          a model with specific input values to calculate outputs automatically.
        </p>
        <ul className="mt-3 text-sm text-blue-600 list-disc list-inside space-y-1">
          <li>Define input variables with units (e.g., diameter in mm)</li>
          <li>Define output variables with units (e.g., stress in MPa)</li>
          <li>Write equations using standard math notation</li>
          <li>Automatic dimensional analysis validates unit consistency</li>
        </ul>
      </div>
    </div>
  );
};

export default ModelsList;
