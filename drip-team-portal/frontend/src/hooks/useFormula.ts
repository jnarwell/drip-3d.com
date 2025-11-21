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
      expression,
      propertyDefinitionId 
    }: { 
      propertyId: number;
      componentId: string; 
      expression: string;
      propertyDefinitionId: number;
    }) => {
      // Extract variables from expression
      const variablePattern = /#([a-zA-Z0-9_\-\.]+)/g;
      const variables = [];
      let match;
      
      while ((match = variablePattern.exec(expression)) !== null) {
        variables.push(match[1]);
      }

      // Create references for each variable
      const references = variables.map(varId => {
        const parts = varId.split('.');
        if (varId.startsWith('comp_')) {
          // Extract component ID from comp_CMP-001 format
          const compIdMatch = parts[0].match(/comp_CMP-(\d+)/);
          const compId = compIdMatch ? parseInt(compIdMatch[1]) : null;
          
          return {
            variable_name: varId.replace('#', ''),
            reference_type: 'component_property',
            target_component_id: compId,
            target_property_definition_id: null, // Would need to resolve this from property name
            description: `Reference to ${varId}`
          };
        } else if (varId.startsWith('const_')) {
          return {
            variable_name: varId.replace('#', ''),
            reference_type: 'system_constant',
            target_constant_symbol: parts[0].split('_')[1],
            description: `Reference to constant ${varId}`
          };
        }
        return null;
      }).filter(Boolean);

      // Create the formula
      const formula = await api.post('/api/v1/formulas/', {
        name: `Formula for property ${propertyId}`,
        description: `Auto-generated formula: ${expression}`,
        property_definition_id: propertyDefinitionId,
        component_id: componentId ? parseInt(componentId.split('-')[1]) : null,
        formula_expression: expression, // Keep the original expression with # symbols
        references
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