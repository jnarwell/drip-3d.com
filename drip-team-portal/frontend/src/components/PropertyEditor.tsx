import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { PropertyDefinition, ValueType } from '../types';

interface PropertyEditorProps {
  propertyDef: PropertyDefinition;
  onSuccess: () => void;
  onCancel: () => void;
}

const PropertyEditor: React.FC<PropertyEditorProps> = ({
  propertyDef,
  onSuccess,
  onCancel
}) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const [formData, setFormData] = useState({
    name: propertyDef.name,
    unit: propertyDef.unit,
    description: propertyDef.description || '',
    value_type: propertyDef.value_type,
  });

  const updateProperty = useMutation({
    mutationFn: async () => {
      await api.patch(`/api/v1/property-definitions/${propertyDef.id}`, formData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property-definitions'] });
      queryClient.invalidateQueries({ queryKey: ['component-properties'] });
      onSuccess();
    },
    onError: (error: any) => {
      alert(error.response?.data?.detail || 'Failed to update property definition');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.unit) {
      updateProperty.mutate();
    }
  };

  return (
    <form onSubmit={handleSubmit} className="p-4 space-y-4">
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Property Name
        </label>
        <input
          type="text"
          value={formData.name}
          onChange={(e) => setFormData({ ...formData, name: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Unit
        </label>
        <input
          type="text"
          value={formData.unit}
          onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          placeholder="e.g., mm, text, °C"
          required
        />
        <p className="text-xs text-gray-500 mt-1">
          Use "text" for textual properties (codes, identifiers, etc.)
        </p>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Value Type
        </label>
        <select
          value={formData.value_type}
          onChange={(e) => setFormData({ ...formData, value_type: e.target.value as ValueType })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value={ValueType.SINGLE}>Single Value</option>
          <option value={ValueType.RANGE}>Range (Min-Max)</option>
          <option value={ValueType.AVERAGE}>Average with Tolerance</option>
          <option value={ValueType.TEXT}>Text (String)</option>
        </select>
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Description (Optional)
        </label>
        <textarea
          value={formData.description}
          onChange={(e) => setFormData({ ...formData, description: e.target.value })}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
          rows={2}
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={updateProperty.isPending}
          className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:bg-gray-400"
        >
          {updateProperty.isPending ? 'Saving...' : 'Save Changes'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 bg-gray-200 text-gray-700 rounded-md hover:bg-gray-300 transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};

export default PropertyEditor;
