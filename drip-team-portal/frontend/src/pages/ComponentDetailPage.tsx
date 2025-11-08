import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { Component } from '../types';
import PropertyList from '../components/PropertyList';

const ComponentDetailPage: React.FC = () => {
  const { componentId } = useParams<{ componentId: string }>();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();

  const { data: component, isLoading, error } = useQuery<Component>({
    queryKey: ['component', componentId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/components/${componentId}`);
      return response.data;
    },
    enabled: !!componentId,
  });

  const handleReturnToComponents = () => {
    navigate('/components');
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !component) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error loading component</p>
        <button
          onClick={handleReturnToComponents}
          className="text-indigo-600 hover:text-indigo-800"
        >
          Return to Components
        </button>
      </div>
    );
  }

  return (
    <div className="h-full">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-4 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{component.name}</h1>
            <p className="text-sm text-gray-600 mt-1">{component.part_number}</p>
          </div>
          <button
            onClick={handleReturnToComponents}
            className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
            Return to Components
          </button>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6">
        <PropertyList componentId={component.component_id} />
        
        {/* Additional sections can be added here */}
        <div className="mt-8 bg-gray-50 rounded-lg p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Additional Information</h3>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span className="text-gray-600">Component ID:</span>
              <span className="font-mono">{component.component_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Category:</span>
              <span>{component.category}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-600">Status:</span>
              <span>{component.status}</span>
            </div>
            {component.supplier && (
              <div className="flex justify-between">
                <span className="text-gray-600">Supplier:</span>
                <span>{component.supplier}</span>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComponentDetailPage;