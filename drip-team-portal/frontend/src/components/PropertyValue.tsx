import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty, ValueType } from '../types';

interface PropertyValueProps {
  property: ComponentProperty;
  componentId: string;
  onDelete: () => void;
}

const PropertyValue: React.FC<PropertyValueProps> = ({ property, componentId, onDelete }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [editValues, setEditValues] = useState({
    single_value: property.single_value || 0,
    min_value: property.min_value || 0,
    max_value: property.max_value || 0,
    average_value: property.average_value || 0,
    tolerance: property.tolerance || 0,
  });

  const updateProperty = useMutation({
    mutationFn: async (values: Partial<typeof editValues>) => {
      await api.patch(`/api/v1/components/${componentId}/properties/${property.id}`, values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      setIsEditing(false);
    },
  });

  const handleSave = () => {
    const values: any = {};
    
    switch (property.property_definition.value_type) {
      case ValueType.SINGLE:
        values.single_value = editValues.single_value;
        break;
      case ValueType.RANGE:
        values.min_value = editValues.min_value;
        values.max_value = editValues.max_value;
        break;
      case ValueType.AVERAGE:
        values.average_value = editValues.average_value;
        values.tolerance = editValues.tolerance;
        break;
    }
    
    updateProperty.mutate(values);
  };

  const renderValue = () => {
    const def = property.property_definition;
    
    if (isEditing) {
      switch (def.value_type) {
        case ValueType.SINGLE:
          return (
            <input
              type="number"
              value={editValues.single_value}
              onChange={(e) => setEditValues({ ...editValues, single_value: parseFloat(e.target.value) })}
              className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
              autoFocus
            />
          );
        case ValueType.RANGE:
          return (
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={editValues.min_value}
                onChange={(e) => setEditValues({ ...editValues, min_value: parseFloat(e.target.value) })}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <span className="text-gray-500">to</span>
              <input
                type="number"
                value={editValues.max_value}
                onChange={(e) => setEditValues({ ...editValues, max_value: parseFloat(e.target.value) })}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          );
        case ValueType.AVERAGE:
          return (
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={editValues.average_value}
                onChange={(e) => setEditValues({ ...editValues, average_value: parseFloat(e.target.value) })}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
              <span className="text-gray-500">±</span>
              <input
                type="number"
                value={editValues.tolerance}
                onChange={(e) => setEditValues({ ...editValues, tolerance: parseFloat(e.target.value) })}
                className="w-20 px-2 py-1 border border-gray-300 rounded text-sm"
              />
            </div>
          );
      }
    }
    
    // Display mode
    switch (def.value_type) {
      case ValueType.SINGLE:
        return property.single_value !== null ? (
          <span className="text-gray-900">{property.single_value}</span>
        ) : (
          <span className="text-gray-400 italic">Not set</span>
        );
      case ValueType.RANGE:
        return property.min_value !== null && property.max_value !== null ? (
          <span className="text-gray-900">{property.min_value} - {property.max_value}</span>
        ) : (
          <span className="text-gray-400 italic">Not set</span>
        );
      case ValueType.AVERAGE:
        return property.average_value !== null ? (
          <span className="text-gray-900">
            {property.average_value} {property.tolerance ? `± ${property.tolerance}` : ''}
          </span>
        ) : (
          <span className="text-gray-400 italic">Not set</span>
        );
    }
  };

  return (
    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
      <div className="flex-1">
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-gray-700">
            {property.property_definition.name}
          </span>
          <div 
            className="flex items-center gap-2 cursor-pointer"
            onClick={() => !isEditing && setIsEditing(true)}
          >
            {renderValue()}
            <span className="text-xs text-gray-500">{property.property_definition.unit}</span>
          </div>
        </div>
        {property.notes && (
          <p className="text-xs text-gray-500 mt-1">
            {property.notes}
            {property.notes.includes('From material:') && (
              <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                Material Property
              </span>
            )}
          </p>
        )}
      </div>
      
      <div className="flex items-center gap-2 ml-4">
        {isEditing ? (
          <>
            <button
              onClick={handleSave}
              className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors"
              aria-label="Save"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </button>
            <button
              onClick={() => setIsEditing(false)}
              className="p-1 text-gray-500 hover:bg-gray-100 rounded transition-colors"
              aria-label="Cancel"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </>
        ) : (
          <button
            onClick={onDelete}
            className="p-1 text-red-500 hover:bg-red-50 rounded transition-colors"
            aria-label="Delete property"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>
    </div>
  );
};

export default PropertyValue;