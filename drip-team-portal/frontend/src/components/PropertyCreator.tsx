import React, { useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { PropertyType, ValueType } from '../types';

interface PropertyCreatorProps {
  propertyType: PropertyType;
  componentId: string;
  onSuccess: () => void;
  onCancel: () => void;
}

const PropertyCreator: React.FC<PropertyCreatorProps> = ({ 
  propertyType, 
  componentId, 
  onSuccess, 
  onCancel 
}) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  
  const [formData, setFormData] = useState({
    name: '',
    unit: '',
    description: '',
    value_type: ValueType.SINGLE,
  });

  const createProperty = useMutation({
    mutationFn: async () => {
      // First create the property definition
      const defResponse = await api.post('/api/v1/property-definitions', {
        ...formData,
        property_type: propertyType,
        is_custom: true,
      });
      
      // Then add it to the component
      await api.post(`/api/v1/components/${componentId}/properties`, {
        property_definition_id: defResponse.data.id,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['property-definitions'] });
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      onSuccess();
    },
  });

  const commonUnits = {
    [PropertyType.THERMAL]: ['°C', 'K', '°F', 'W/m·K', 'J/kg·K', '1/K', 'text'],
    [PropertyType.ELECTRICAL]: ['V', 'A', 'W', 'Ω', 'Hz', 'F', 'H', 'text'],
    [PropertyType.MECHANICAL]: ['N', 'Pa', 'MPa', 'GPa', 'm/s', 'kg', 'kg/m³', 'text'],
    [PropertyType.ACOUSTIC]: ['Hz', 'kHz', 'dB', 'W', 'Pa', 'µm', 'µm/W', 'text'],
    [PropertyType.MATERIAL]: ['', 'mol/L', 'g/cm³', '%', 'text'],
    [PropertyType.DIMENSIONAL]: ['mm', 'cm', 'm', 'in', 'ft', 'kg', 'g', 'text'],
    [PropertyType.OPTICAL]: ['nm', 'µm', 'cd', 'lm', '°', 'n', 'text'],
    [PropertyType.OTHER]: ['', 'units', 'text'],
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (formData.name && formData.unit) {
      createProperty.mutate();
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
          placeholder="e.g., Specific Heat Capacity"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Unit
        </label>
        <div className="space-y-2">
          <input
            type="text"
            value={formData.unit}
            onChange={(e) => setFormData({ ...formData, unit: e.target.value })}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., J/kg·K"
            required
          />
          <div className="flex flex-wrap gap-1">
            {commonUnits[propertyType]?.map((unit) => (
              <button
                key={unit}
                type="button"
                onClick={() => {
                  // Auto-switch to TEXT value type when "text" unit is selected
                  if (unit === 'text') {
                    setFormData({ ...formData, unit, value_type: ValueType.TEXT });
                  } else {
                    setFormData({ ...formData, unit });
                  }
                }}
                className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded transition-colors"
              >
                {unit || 'dimensionless'}
              </button>
            ))}
          </div>
        </div>
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
          placeholder="Brief description of the property"
        />
      </div>

      <div className="flex gap-2 pt-2">
        <button
          type="submit"
          disabled={createProperty.isPending}
          className="flex-1 px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:bg-gray-400"
        >
          {createProperty.isPending ? 'Creating...' : 'Create Property'}
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

export default PropertyCreator;