import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { Component, ComponentStatus, ComponentCategory, RDPhase } from '../types';
import ComponentForm from '../components/ComponentForm';
import ComponentDetailModal from '../components/ComponentDetailModal';

const ComponentRegistry: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [filters, setFilters] = useState({
    category: '',
    status: '',
    search: '',
  });
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingComponent, setEditingComponent] = useState<Component | null>(null);
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const { data: components, isLoading } = useQuery<Component[]>({
    queryKey: ['components', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters.category) params.append('category', filters.category);
      if (filters.status) params.append('status', filters.status);
      if (filters.search) params.append('search', filters.search);
      
      const response = await api.get(`/api/v1/components?${params}`);
      return response.data;
    },
  });

  const createComponent = useMutation({
    mutationFn: async (data: any) => {
      return await api.post('/api/v1/components', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
      setShowCreateForm(false);
    },
  });

  const updateComponent = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      return await api.patch(`/api/v1/components/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
      setEditingComponent(null);
    },
  });

  const deleteComponent = useMutation({
    mutationFn: async (componentId: string) => {
      return await api.delete(`/api/v1/components/${componentId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
    },
  });

  const updateStatus = useMutation({
    mutationFn: async ({ componentId, status }: { componentId: string; status: ComponentStatus }) => {
      return await api.patch(`/api/v1/components/${componentId}/status`, { status });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['components'] });
    },
  });

  const exportComponents = () => {
    const csv = [
      ['Component ID', 'Name', 'Category', 'Status', 'Part Number', 'Supplier', 'Unit Cost'],
      ...(components || []).map(c => [
        c.component_id,
        c.name,
        c.category,
        c.status,
        c.part_number || '',
        c.supplier || '',
        c.unit_cost?.toString() || '',
      ]),
    ].map(row => row.join(',')).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `components_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const statusColors: { [key: string]: string } = {
    NOT_TESTED: 'bg-gray-100 text-gray-800',
    IN_TESTING: 'bg-blue-100 text-blue-800',
    VERIFIED: 'bg-green-100 text-green-800',
    FAILED: 'bg-red-100 text-red-800',
  };

  const formatStatus = (status: string) => status.replace('_', ' ');

  const formatPhase = (phase: RDPhase) => {
    switch (phase) {
      case RDPhase.PHASE_1:
        return 'Phase 1';
      case RDPhase.PHASE_2:
        return 'Phase 2';
      case RDPhase.PHASE_3:
        return 'Phase 3';
      default:
        return phase;
    }
  };

  const getPhaseColor = (phase: RDPhase) => {
    switch (phase) {
      case RDPhase.PHASE_1:
        return 'bg-purple-100 text-purple-800';
      case RDPhase.PHASE_2:
        return 'bg-orange-100 text-orange-800';
      case RDPhase.PHASE_3:
        return 'bg-indigo-100 text-indigo-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Component Registry</h1>
        <div className="flex space-x-3">
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
          >
            Add Component
          </button>
          <button
            onClick={exportComponents}
            className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Export to CSV
          </button>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-4">
        <select
          value={filters.category}
          onChange={(e) => setFilters({ ...filters, category: e.target.value })}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">All Categories</option>
          {Object.values(ComponentCategory).map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>

        <select
          value={filters.status}
          onChange={(e) => setFilters({ ...filters, status: e.target.value })}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        >
          <option value="">All Statuses</option>
          {Object.values(ComponentStatus).map(status => (
            <option key={status} value={status}>{formatStatus(status)}</option>
          ))}
        </select>

        <input
          type="text"
          placeholder="Search components..."
          value={filters.search}
          onChange={(e) => setFilters({ ...filters, search: e.target.value })}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500"
        />
      </div>

      {/* Component Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {components?.map(component => (
            <div 
              key={component.id} 
              className="bg-white rounded-lg shadow p-4 cursor-pointer hover:shadow-lg transition-shadow select-none"
              onClick={(e) => {
                // Prevent opening modal when clicking on buttons
                if ((e.target as HTMLElement).closest('button')) {
                  return;
                }
                console.log('Component clicked:', component.name);
                setSelectedComponent(component);
                setShowDetailModal(true);
              }}
            >
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-lg font-medium text-gray-900">{component.name}</h3>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const newStatus = component.status === ComponentStatus.VERIFIED 
                      ? ComponentStatus.NOT_TESTED 
                      : ComponentStatus.VERIFIED;
                    updateStatus.mutate({
                      componentId: component.component_id,
                      status: newStatus
                    });
                  }}
                  className={`px-2 py-1 text-xs font-medium rounded cursor-pointer hover:opacity-80 ${statusColors[component.status]}`}
                  title="Click to toggle status"
                >
                  {formatStatus(component.status)}
                </button>
              </div>
              
              <div className="mb-3">
                <span className={`inline-block px-3 py-1 text-sm font-medium rounded-full ${getPhaseColor(component.phase)}`}>
                  {formatPhase(component.phase)}
                </span>
              </div>
              
              <dl className="space-y-1 text-sm text-gray-600">
                <div className="flex justify-between">
                  <dt>ID:</dt>
                  <dd className="font-mono">{component.component_id}</dd>
                </div>
                <div className="flex justify-between">
                  <dt>Category:</dt>
                  <dd>{component.category}</dd>
                </div>
                {component.part_number && (
                  <div className="flex justify-between">
                    <dt>Part #:</dt>
                    <dd>{component.part_number}</dd>
                  </div>
                )}
                {component.supplier && (
                  <div className="flex justify-between">
                    <dt>Supplier:</dt>
                    <dd>{component.supplier}</dd>
                  </div>
                )}
                {component.unit_cost && (
                  <div className="flex justify-between">
                    <dt>Cost:</dt>
                    <dd>${component.unit_cost.toFixed(2)}</dd>
                  </div>
                )}
              </dl>

              {/* Action Buttons */}
              <div className="mt-4 flex gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setEditingComponent(component);
                  }}
                  className="px-3 py-1 text-xs font-medium text-indigo-600 border border-indigo-600 rounded hover:bg-indigo-50"
                >
                  Edit
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm('Are you sure you want to delete this component?')) {
                      deleteComponent.mutate(component.component_id);
                    }
                  }}
                  className="px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create Component Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Add New Component
              </h2>
              <ComponentForm
                onSubmit={(data) => {
                  createComponent.mutate({
                    ...data,
                    status: ComponentStatus.NOT_TESTED,
                  });
                }}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Edit Component Modal */}
      {editingComponent && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Edit Component
              </h2>
              <ComponentForm
                initialData={editingComponent}
                onSubmit={(data) => {
                  updateComponent.mutate({
                    id: editingComponent.component_id,
                    data,
                  });
                }}
                onCancel={() => setEditingComponent(null)}
                isEdit
              />
            </div>
          </div>
        </div>
      )}

      {/* Component Detail Modal */}
      {selectedComponent && (
        <ComponentDetailModal
          component={selectedComponent}
          isOpen={showDetailModal}
          onClose={() => {
            setShowDetailModal(false);
            setSelectedComponent(null);
          }}
        />
      )}
    </div>
  );
};

export default ComponentRegistry;