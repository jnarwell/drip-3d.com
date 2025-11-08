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
    },
  });

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

  const getPropertyTypeLabel = (type: PropertyType) => {
    return type.charAt(0).toUpperCase() + type.slice(1) + ' Properties';
  };

  const getPropertyTypeIcon = (type: PropertyType) => {
    const icons: Record<PropertyType, string> = {
      [PropertyType.THERMAL]: '🌡️',
      [PropertyType.ELECTRICAL]: '⚡',
      [PropertyType.MECHANICAL]: '⚙️',
      [PropertyType.ACOUSTIC]: '🔊',
      [PropertyType.MATERIAL]: '🧱',
      [PropertyType.DIMENSIONAL]: '📐',
      [PropertyType.OPTICAL]: '🔍',
      [PropertyType.OTHER]: '📋',
    };
    return icons[type] || '📋';
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
        {Object.entries(groupedProperties).map(([type, props]) => (
          <div key={type} className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center gap-2">
              <span>{getPropertyTypeIcon(type as PropertyType)}</span>
              {getPropertyTypeLabel(type as PropertyType)}
            </h4>
            <div className="space-y-2">
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
        ))}
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