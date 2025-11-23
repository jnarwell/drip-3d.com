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

      // Use the new create-from-expression endpoint
      const response = await api.post('/api/v1/formulas/create-from-expression', {
        propertyId,
        componentId,
        componentDbId,
        expression,
        propertyDefinitionId
      });

      return response.data;
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

  const recalculateProperty = useMutation({
    mutationFn: async ({ 
      propertyId 
    }: { 
      propertyId: number; 
    }) => {
      const response = await api.post(
        `/api/v1/formulas/recalculate-property/${propertyId}`
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ 
        queryKey: ['component-properties'] 
      });
    },
  });

  return {
    createFormula,
    calculateProperty,
    recalculateProperty
  };
}