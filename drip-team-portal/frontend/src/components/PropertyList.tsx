import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { AxiosError } from 'axios';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty, PropertyType, PropertyDefinition } from '../types';
import AddPropertyDropdown from './AddPropertyDropdown';
import PropertyValue from './PropertyValue';
import MaterialSelector from './MaterialSelector';

interface PropertyListProps {
  componentId: string;
}

const PropertyList: React.FC<PropertyListProps> = ({ componentId }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [groupedProperties, setGroupedProperties] = useState<Record<PropertyType, ComponentProperty[]>>({} as Record<PropertyType, ComponentProperty[]>);
  const [collapsedCategories, setCollapsedCategories] = useState<Record<PropertyType, boolean>>({} as Record<PropertyType, boolean>);
  const [pendingDeleteProperty, setPendingDeleteProperty] = useState<ComponentProperty | null>(null);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { data: properties, isLoading } = useQuery<ComponentProperty[]>({
    queryKey: ['component-properties', componentId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/components/${componentId}/properties`);
      return response.data;
    },
  });

  const deleteProperty = useMutation({
    mutationFn: async (propertyId: number) => {
      await api.delete(`/api/v1/components/${componentId}/properties/${propertyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      setPendingDeleteProperty(null);
      setDeleteError(null);
    },
    onError: (error: AxiosError<{ detail: string }>) => {
      const status = error.response?.status;
      const detail = error.response?.data?.detail;
      if (status === 409) {
        setDeleteError(
          detail || 'This property is referenced by other values and cannot be deleted. Remove those references first.'
        );
      } else {
        setDeleteError('Failed to delete property. Please try again.');
      }
    },
  });

  const handleDeleteRequest = (property: ComponentProperty) => {
    setDeleteError(null);
    setPendingDeleteProperty(property);
  };

  const handleDeleteConfirm = () => {
    if (pendingDeleteProperty) {
      deleteProperty.mutate(pendingDeleteProperty.id);
    }
  };

  const handleDeleteCancel = () => {
    setPendingDeleteProperty(null);
    setDeleteError(null);
  };

  // Load collapsed state from localStorage on component mount
  useEffect(() => {
    const savedCollapsedState = localStorage.getItem('property-categories-collapsed');
    if (savedCollapsedState) {
      try {
        setCollapsedCategories(JSON.parse(savedCollapsedState));
      } catch (error) {
        console.error('Failed to parse saved collapsed state:', error);
      }
    }
  }, []);

  useEffect(() => {
    if (properties) {
      const grouped = properties.reduce((acc, prop) => {
        const type = prop.property_definition.property_type;
        if (!acc[type]) {
          acc[type] = [];
        }
        acc[type].push(prop);
        return acc;
      }, {} as Record<PropertyType, ComponentProperty[]>);
      setGroupedProperties(grouped);
    }
  }, [properties]);

  // Toggle collapse state for a category
  const toggleCategoryCollapse = (category: PropertyType) => {
    const newCollapsedState = {
      ...collapsedCategories,
      [category]: !collapsedCategories[category]
    };
    setCollapsedCategories(newCollapsedState);
    
    // Save to localStorage
    localStorage.setItem('property-categories-collapsed', JSON.stringify(newCollapsedState));
  };

  const getPropertyTypeLabel = (type: PropertyType) => {
    return type.charAt(0).toUpperCase() + type.slice(1) + ' Properties';
  };

  const getPropertyTypeIcon = (type: PropertyType) => {
    // Removed emojis for professional appearance
    return '';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Material Selection */}
      <MaterialSelector componentId={componentId} />
      
      {/* Header with Add Property button */}
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-900">Component Properties</h3>
        <AddPropertyDropdown componentId={componentId} />
      </div>

      {/* Properties grouped by type */}
      <div className="space-y-6">
        {Object.entries(groupedProperties).map(([type, props]) => {
          const isCollapsed = collapsedCategories[type as PropertyType];
          return (
            <div key={type} className="bg-gray-50 rounded-lg overflow-hidden">
              {/* Category Header - Clickable */}
              <button
                onClick={() => toggleCategoryCollapse(type as PropertyType)}
                className="w-full px-4 py-3 flex items-center justify-between text-left hover:bg-gray-100 transition-colors duration-150 focus:outline-none focus:bg-gray-100"
              >
                <h4 className="text-sm font-medium text-gray-700">
                  {getPropertyTypeLabel(type as PropertyType)}
                </h4>
                <div className="flex items-center space-x-2">
                  <span className="text-xs text-gray-500 bg-gray-200 px-2 py-1 rounded-full">
                    {props.length}
                  </span>
                  <svg
                    className={`w-5 h-5 text-gray-400 transition-transform duration-200 ${
                      isCollapsed ? 'rotate-0' : 'rotate-90'
                    }`}
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 5l7 7-7 7"
                    />
                  </svg>
                </div>
              </button>
              
              {/* Category Content - Collapsible */}
              <div
                className={`transition-all duration-300 ease-in-out ${
                  isCollapsed ? 'max-h-0' : 'max-h-[1000px]'
                } overflow-hidden`}
              >
                <div className="px-4 pt-2 pb-4 space-y-2">
                  {props.map((property) => (
                    <PropertyValue
                      key={property.id}
                      property={property}
                      componentId={componentId}
                      onDelete={() => handleDeleteRequest(property)}
                    />
                  ))}
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Empty state */}
      {(!properties || properties.length === 0) && (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <p className="text-gray-500 mb-4">No properties defined yet</p>
          <p className="text-sm text-gray-400">Click "Add Property" to get started</p>
        </div>
      )}

      {/* Delete Property Confirmation Dialog */}
      {pendingDeleteProperty && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50 p-4"
          onClick={handleDeleteCancel}
        >
          <div
            className="bg-white rounded-lg shadow-xl w-full max-w-md"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-6 py-4 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Delete Property</h2>
              <p className="text-sm text-gray-500 mt-1">
                {pendingDeleteProperty.property_definition.name}
              </p>
            </div>

            <div className="px-6 py-4 space-y-3">
              <p className="text-sm text-gray-700">
                Are you sure you want to delete{' '}
                <span className="font-medium">{pendingDeleteProperty.property_definition.name}</span>?
                This action cannot be undone.
              </p>

              {deleteError && (
                <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                  <div className="flex items-start gap-2">
                    <svg className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <p className="text-sm text-red-700">{deleteError}</p>
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t flex justify-end gap-3">
              <button
                type="button"
                onClick={handleDeleteCancel}
                disabled={deleteProperty.isPending}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleDeleteConfirm}
                disabled={deleteProperty.isPending || !!deleteError}
                className="px-4 py-2 text-sm font-medium text-white bg-red-600 border border-transparent rounded-md hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {deleteProperty.isPending ? 'Deleting...' : 'Delete'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default PropertyList;