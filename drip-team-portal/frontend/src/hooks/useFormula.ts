import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty } from '../types';

export function useFormula() {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const createFormula = useMutation({
    mutationFn: async ({ 
      propertyId, 
      componentId,
      componentDbId,
      expression,
      propertyDefinitionId 
    }: { 
      propertyId: number;
      componentId: string;
      componentDbId: number;
      expression: string;
      propertyDefinitionId: number;
    }) => {
      console.log('Creating formula with:', {
        propertyId,
        componentId,
        componentDbId,
        expression,
        propertyDefinitionId
      });

      // Create the formula without references for now to debug
      const formula = await api.post('/api/v1/formulas/', {
        name: `Formula for property ${propertyId}`,
        description: `Auto-generated formula: ${expression}`,
        property_definition_id: propertyDefinitionId,
        component_id: componentDbId, // Use the actual database ID
        formula_expression: expression,
        references: [] // Empty references for now
      });

      // Update the property to use this formula
      await api.patch(`/api/v1/components/${componentId}/properties/${propertyId}`, {
        is_calculated: true,
        formula_id: formula.data.id
      });

      // Calculate the formula value
      const result = await api.post(`/api/v1/components/${componentId}/properties/${propertyId}/calculate`);
      
      return result.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: ['component-properties', variables.componentId] 
      });
    },
  });

  const calculateProperty = useMutation({
    mutationFn: async ({ 
      componentId, 
      propertyId 
    }: { 
      componentId: string; 
      propertyId: number; 
    }) => {
      const response = await api.post(
        `/api/v1/components/${componentId}/properties/${propertyId}/calculate`
      );
      return response.data;
    },
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({ 
        queryKey: ['component-properties', variables.componentId] 
      });
    },
  });

  return {
    createFormula,
    calculateProperty
  };
}