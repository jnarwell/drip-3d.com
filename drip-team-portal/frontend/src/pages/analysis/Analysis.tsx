import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import { useAnalysisWebSocket } from '../../hooks/useAnalysisWebSocket';
import ExpressionInput from '../../components/ExpressionInput';
interface AnalysisOutput {
  name: string;
  computed_value: number | null;
  computed_unit: string;
  computation_status: 'pending' | 'valid' | 'stale' | 'error';
}

interface AnalysisInput {
  input_name: string;
  unit?: string;
  literal_value: number | string | null;
  literal_unit_id?: number | null;
  source_value_node_id?: number | null;
  source_lookup?: { expression?: string } | null;
}

interface Analysis {
  id: number;
  name: string;
  description?: string;
  model_name: string;
  model_category: string;
  model_version_id: number;
  computation_status: 'valid' | 'stale' | 'error' | 'pending';
  created_at: string;
  updated_at?: string;
  output_value_nodes: AnalysisOutput[];
  inputs: AnalysisInput[];
}

const STATUS_COLORS: Record<string, string> = {
  valid: 'bg-green-100 text-green-800',
  stale: 'bg-yellow-100 text-yellow-800',
  error: 'bg-red-100 text-red-800',
  pending: 'bg-blue-100 text-blue-800',
};

const STATUS_LABELS: Record<string, string> = {
  valid: 'VALID',
  stale: 'STALE',
  error: 'ERROR',
  pending: 'PENDING',
};

const CATEGORY_COLORS: Record<string, string> = {
  thermal: 'bg-red-100 text-red-800',
  mechanical: 'bg-blue-100 text-blue-800',
  electrical: 'bg-yellow-100 text-yellow-800',
  acoustic: 'bg-green-100 text-green-800',
  fluid: 'bg-cyan-100 text-cyan-800',
  material: 'bg-purple-100 text-purple-800',
};

export default function Analysis() {
  const navigate = useNavigate();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [deleteModalId, setDeleteModalId] = useState<number | null>(null);

  // Inline editing state
  const [editingInput, setEditingInput] = useState<{
    analysisId: number;
    inputName: string;
  } | null>(null);
  const [editValue, setEditValue] = useState('');

  // Connect to WebSocket for real-time updates
  const { isConnected } = useAnalysisWebSocket();

  // Fetch analyses
  const { data: analyses, isLoading, error } = useQuery<Analysis[]>({
    queryKey: ['analyses'],
    queryFn: async () => {
      const response = await api.get('/api/v1/analyses');
      return response.data;
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.delete(`/api/v1/analyses/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      setDeleteModalId(null);
    },
  });

  // Re-evaluate mutation
  const evaluateMutation = useMutation({
    mutationFn: async (id: number) => {
      const response = await api.post(`/api/v1/analyses/${id}/evaluate`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
    },
  });

  // Update binding mutation for inline editing
  const updateBindingMutation = useMutation({
    mutationFn: async ({
      analysisId,
      inputName,
      newValue,
    }: {
      analysisId: number;
      inputName: string;
      newValue: string;
    }) => {
      // Get current analysis to preserve other bindings
      const currentAnalysis = analyses?.find((a) => a.id === analysisId);
      if (!currentAnalysis) throw new Error('Analysis not found');

      // Build current bindings object
      const currentBindings: Record<string, string | number> = {};
      currentAnalysis.inputs.forEach((input) => {
        if (input.literal_value !== null && input.literal_value !== undefined) {
          currentBindings[input.input_name] = input.literal_value;
        } else if (input.source_lookup?.expression) {
          currentBindings[input.input_name] = input.source_lookup.expression;
        } else if (input.source_value_node_id) {
          currentBindings[input.input_name] = `#REF:${input.source_value_node_id}`;
        }
      });

      // Parse and update the specific input
      let parsedValue: string | number = newValue;
      if (!newValue.startsWith('#')) {
        const num = parseFloat(newValue);
        if (!isNaN(num)) {
          parsedValue = num;
        }
      }
      currentBindings[inputName] = parsedValue;

      // Send PATCH request
      const response = await api.patch(`/api/v1/analyses/${analysisId}`, {
        bindings: currentBindings,
      });
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
      setEditingInput(null);
      setEditValue('');
      // Auto-evaluate after saving the binding
      evaluateMutation.mutate(variables.analysisId);
    },
    onError: (error: Error) => {
      alert(`Failed to update: ${error.message}`);
    },
  });

  // Start editing an input
  const startEditing = (analysisId: number, input: AnalysisInput) => {
    let currentValue = '';
    if (input.literal_value !== null && input.literal_value !== undefined) {
      currentValue = String(input.literal_value);
    } else if (input.source_lookup?.expression) {
      currentValue = input.source_lookup.expression;
    } else if (input.source_value_node_id) {
      currentValue = `#REF:${input.source_value_node_id}`;
    }
    setEditingInput({ analysisId, inputName: input.input_name });
    setEditValue(currentValue);
  };

  // Save the edited value
  const saveEdit = () => {
    if (!editingInput || !editValue.trim()) return;
    updateBindingMutation.mutate({
      analysisId: editingInput.analysisId,
      inputName: editingInput.inputName,
      newValue: editValue.trim(),
    });
  };

  // Cancel editing
  const cancelEdit = () => {
    setEditingInput(null);
    setEditValue('');
  };

  const handleDelete = (id: number) => {
    deleteMutation.mutate(id);
  };

  const formatOutput = (output: AnalysisOutput) => {
    if (output.computed_value === null) {
      return <span className="text-gray-400">—</span>;
    }

    // Format the value with appropriate precision
    const value = output.computed_value;
    let displayValue: string;

    if (Math.abs(value) >= 1000 || (Math.abs(value) < 0.01 && value !== 0)) {
      displayValue = value.toExponential(3);
    } else {
      displayValue = value.toPrecision(4);
    }

    return (
      <span className="font-mono">
        <span className="font-medium text-gray-900">{displayValue}</span>
        <span className="ml-1 text-gray-500">{output.computed_unit}</span>
      </span>
    );
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return `${diffDays}d ago`;
  };

  // Sort analyses alphabetically by name
  const sortedAnalyses = analyses?.slice().sort((a, b) => a.name.localeCompare(b.name));
  const analysisToDelete = analyses?.find(a => a.id === deleteModalId);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
            <p className="mt-1 text-sm text-gray-500">Loading...</p>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-sm text-gray-500">Loading analyses...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
          </div>
        </div>
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-700">Failed to load analyses: {(error as Error).message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <div className="flex items-center gap-3">
            <h1 className="text-2xl font-bold text-gray-900">Analysis</h1>
            {isConnected && (
              <span className="inline-flex items-center px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">
                <span className="w-1.5 h-1.5 bg-green-500 rounded-full mr-1.5 animate-pulse"></span>
                Live
              </span>
            )}
          </div>
          <p className="mt-1 text-sm text-gray-500">
            Named model instances with real-time updates
          </p>
        </div>
        <Link
          to="/analysis/new"
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 transition-colors"
        >
          <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          New Analysis
        </Link>
      </div>

      {/* Empty state */}
      {!sortedAnalyses || sortedAnalyses.length === 0 ? (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200">
          <div className="p-12 text-center">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
            </svg>
            <h3 className="mt-4 text-lg font-medium text-gray-900">No analyses yet</h3>
            <p className="mt-2 text-sm text-gray-500">
              Create your first analysis to track system-level calculations continuously.
            </p>
            <Link
              to="/analysis/new"
              className="mt-6 inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700"
            >
              <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Analysis
            </Link>
          </div>
        </div>
      ) : (
        /* Table */
        <div className="bg-white shadow-sm rounded-lg overflow-hidden border border-gray-200">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Name
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Model
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Output
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Last Updated
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedAnalyses.map((analysis) => (
                <React.Fragment key={analysis.id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-6 py-4">
                      <div>
                        <button
                          onClick={() => setExpandedId(expandedId === analysis.id ? null : analysis.id)}
                          className="text-left group"
                        >
                          <div className="flex items-center gap-2">
                            <svg
                              className={`w-4 h-4 text-gray-400 transition-transform ${expandedId === analysis.id ? 'rotate-90' : ''}`}
                              fill="none"
                              stroke="currentColor"
                              viewBox="0 0 24 24"
                            >
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                            </svg>
                            <span className="text-sm font-medium text-gray-900 group-hover:text-indigo-600">
                              {analysis.name}
                            </span>
                          </div>
                        </button>
                        {analysis.description && (
                          <div className="mt-1 text-sm text-gray-500 pl-6">{analysis.description}</div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-900">{analysis.model_name}</span>
                        {analysis.model_category && (
                          <span className={`text-xs px-2 py-0.5 rounded-full ${CATEGORY_COLORS[analysis.model_category] || 'bg-gray-100 text-gray-800'}`}>
                            {analysis.model_category}
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 text-sm">
                      {analysis.output_value_nodes && analysis.output_value_nodes.length > 0 ? (
                        <div>
                          <div className="text-xs text-gray-500 mb-0.5">{analysis.output_value_nodes[0].name}</div>
                          {formatOutput(analysis.output_value_nodes[0])}
                        </div>
                      ) : (
                        <span className="text-gray-400">No outputs</span>
                      )}
                    </td>
                    <td className="px-6 py-4">
                      <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${STATUS_COLORS[analysis.computation_status] || STATUS_COLORS.pending}`}>
                        {STATUS_LABELS[analysis.computation_status] || 'PENDING'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-sm text-gray-500">
                      {analysis.updated_at ? formatTimeAgo(analysis.updated_at) : formatTimeAgo(analysis.created_at)}
                    </td>
                    <td className="px-6 py-4 text-right text-sm font-medium">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          onClick={() => evaluateMutation.mutate(analysis.id)}
                          disabled={evaluateMutation.isPending}
                          className="text-indigo-600 hover:text-indigo-900 disabled:opacity-50 disabled:cursor-not-allowed"
                          title="Refresh"
                        >
                          <svg
                            className={`w-4 h-4 ${evaluateMutation.isPending ? 'animate-spin' : ''}`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                        <button
                          onClick={() => navigate(`/analysis/${analysis.id}/edit`)}
                          className="text-indigo-600 hover:text-indigo-900"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => setDeleteModalId(analysis.id)}
                          disabled={deleteMutation.isPending}
                          className="text-red-600 hover:text-red-900 disabled:opacity-50"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                  {/* Expanded row showing bindings */}
                  {expandedId === analysis.id && (
                    <tr className="bg-gray-50">
                      <td colSpan={6} className="px-6 py-4">
                        <div className="ml-6">
                          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">Input Bindings</h4>
                          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
                            {analysis.inputs && analysis.inputs.length > 0 ? (
                              analysis.inputs.map((input, idx) => {
                                const isEditing =
                                  editingInput?.analysisId === analysis.id &&
                                  editingInput?.inputName === input.input_name;

                                return (
                                  <div key={idx} className="bg-white rounded border border-gray-200 p-2">
                                    <div className="text-xs text-gray-500">
                                      {input.input_name}
                                      {input.unit && <span className="ml-1 text-gray-400">({input.unit})</span>}
                                    </div>

                                    {isEditing ? (
                                      // EDIT MODE
                                      <div className="mt-1">
                                        <ExpressionInput
                                          value={editValue}
                                          onChange={setEditValue}
                                          onSubmit={saveEdit}
                                          onCancel={cancelEdit}
                                          placeholder="Value or #CODE.property"
                                          autoFocus
                                        />
                                        {updateBindingMutation.isPending && (
                                          <div className="mt-1 text-xs text-gray-400">Saving...</div>
                                        )}
                                      </div>
                                    ) : (
                                      // READ MODE - double-click to edit
                                      <div
                                        className="text-sm font-mono truncate cursor-pointer hover:bg-gray-100 rounded px-1 -mx-1 py-0.5 transition-colors"
                                        onDoubleClick={() => startEditing(analysis.id, input)}
                                        title="Double-click to edit"
                                      >
                                        {/* Show literal value */}
                                        {input.literal_value !== null && input.literal_value !== undefined && (
                                          <span className="text-gray-900">{input.literal_value}</span>
                                        )}
                                        {/* Show #REF binding */}
                                        {input.source_value_node_id && (
                                          <span className="text-indigo-600">#REF:{input.source_value_node_id}</span>
                                        )}
                                        {/* Show expression/lookup */}
                                        {input.source_lookup?.expression && (
                                          <span className="text-purple-600" title={input.source_lookup.expression}>
                                            {input.source_lookup.expression}
                                          </span>
                                        )}
                                        {/* Fallback if nothing */}
                                        {input.literal_value === null &&
                                         !input.source_value_node_id &&
                                         !input.source_lookup?.expression && (
                                          <span className="text-gray-400">—</span>
                                        )}
                                      </div>
                                    )}
                                  </div>
                                );
                              })
                            ) : (
                              <div className="text-sm text-gray-400">No bindings</div>
                            )}
                          </div>
                          {analysis.output_value_nodes && analysis.output_value_nodes.length > 1 && (
                            <div className="mt-4">
                              <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">All Outputs</h4>
                              <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                                {analysis.output_value_nodes.map((output, idx) => (
                                  <div key={idx} className="bg-white rounded border border-gray-200 p-2">
                                    <div className="text-xs text-gray-500">{output.name}</div>
                                    <div className="text-sm">{formatOutput(output)}</div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      {deleteModalId && analysisToDelete && (
        <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-xl">
            <h3 className="text-lg font-medium text-gray-900 mb-4">Delete Analysis</h3>
            <p className="text-sm text-gray-500 mb-6">
              Are you sure you want to delete <strong>{analysisToDelete.name}</strong>? This action cannot be undone.
            </p>
            <div className="flex justify-end space-x-3">
              <button
                onClick={() => setDeleteModalId(null)}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50"
                disabled={deleteMutation.isPending}
              >
                Cancel
              </button>
              <button
                onClick={() => handleDelete(deleteModalId)}
                disabled={deleteMutation.isPending}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 disabled:opacity-50"
              >
                {deleteMutation.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
