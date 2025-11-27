import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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

  const { data: properties, isLoading } = useQuery<ComponentProperty[]>({
    queryKey: ['component-properties', componentId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/components/${componentId}/properties`);
      console.log('PropertyList: Fetched properties:', response.data.map((p: any) => ({
        id: p.id,
        name: p.property_definition?.name,
        is_calculated: p.is_calculated,
        formula_id: p.formula_id,
        value: p.single_value || p.average_value,
        calculation_status: p.calculation_status
      })));
      return response.data;
    },
  });

  const deleteProperty = useMutation({
    mutationFn: async (propertyId: number) => {
      await api.delete(`/api/v1/components/${componentId}/properties/${propertyId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
    },
  });

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
                      onDelete={() => deleteProperty.mutate(property.id)}
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
    </div>
  );
};

export default PropertyList;