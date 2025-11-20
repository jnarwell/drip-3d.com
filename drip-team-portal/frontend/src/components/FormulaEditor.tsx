import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';

interface PropertyReference {
  id?: number;
  variable_name: string;
  reference_type: 'component_property' | 'system_constant' | 'literal_value' | 'function_call';
  target_component_id?: number;
  target_property_definition_id?: number;
  target_constant_symbol?: string;
  literal_value?: number;
  function_name?: string;
  function_args?: number[];
  description?: string;
  units_expected?: string;
  default_value?: number;
}

interface PropertyFormula {
  id?: number;
  name: string;
  description?: string;
  property_definition_id: number;
  component_id?: number;
  formula_expression: string;
  references: PropertyReference[];
  is_active?: boolean;
  validation_status?: string;
  validation_message?: string;
}

interface FormulaEditorProps {
  propertyDefinitionId: number;
  componentId?: number;
  existingFormula?: PropertyFormula;
  onSave: (formula: PropertyFormula) => void;
  onCancel: () => void;
}

const FormulaEditor: React.FC<FormulaEditorProps> = ({
  propertyDefinitionId,
  componentId,
  existingFormula,
  onSave,
  onCancel
}) => {
  const queryClient = useQueryClient();
  
  const [formula, setFormula] = useState<PropertyFormula>({
    name: existingFormula?.name || '',
    description: existingFormula?.description || '',
    property_definition_id: propertyDefinitionId,
    component_id: componentId,
    formula_expression: existingFormula?.formula_expression || '',
    references: existingFormula?.references || [],
    is_active: existingFormula?.is_active ?? true
  });
  
  const [activeReferenceIndex, setActiveReferenceIndex] = useState<number | null>(null);
  const [validationResult, setValidationResult] = useState<any>(null);

  // Fetch available references (properties, constants, components)
  const { data: availableRefs } = useQuery({
    queryKey: ['formula-references'],
    queryFn: async () => {
      const response = await api.get('/api/v1/formulas/references/available');
      return response.data;
    }
  });

  // Create formula mutation
  const createFormula = useMutation({
    mutationFn: async (formulaData: PropertyFormula) => {
      const response = await api.post('/api/v1/formulas/', formulaData);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['formulas'] });
      onSave(data);
    }
  });

  // Update formula mutation  
  const updateFormula = useMutation({
    mutationFn: async (formulaData: PropertyFormula) => {
      const response = await api.put(`/api/v1/formulas/${existingFormula?.id}`, {
        name: formulaData.name,
        description: formulaData.description,
        formula_expression: formulaData.formula_expression,
        is_active: formulaData.is_active
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['formulas'] });
      onSave(data);
    }
  });

  // Validate formula mutation
  const validateFormula = useMutation({
    mutationFn: async () => {
      if (!existingFormula?.id) return null;
      const response = await api.post(`/api/v1/formulas/${existingFormula.id}/validate`);
      return response.data;
    },
    onSuccess: (data) => {
      setValidationResult(data);
    }
  });

  const addReference = () => {
    setFormula(prev => ({
      ...prev,
      references: [
        ...prev.references,
        {
          variable_name: '',
          reference_type: 'literal_value',
          literal_value: 0
        }
      ]
    }));
    setActiveReferenceIndex(formula.references.length);
  };

  const updateReference = (index: number, updates: Partial<PropertyReference>) => {
    setFormula(prev => ({
      ...prev,
      references: prev.references.map((ref, i) => 
        i === index ? { ...ref, ...updates } : ref
      )
    }));
  };

  const removeReference = (index: number) => {
    setFormula(prev => ({
      ...prev,
      references: prev.references.filter((_, i) => i !== index)
    }));
    setActiveReferenceIndex(null);
  };

  const insertVariableIntoExpression = (variableName: string) => {
    setFormula(prev => ({
      ...prev,
      formula_expression: prev.formula_expression + variableName
    }));
  };

  const handleSave = () => {
    if (existingFormula?.id) {
      updateFormula.mutate(formula);
    } else {
      createFormula.mutate(formula);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h3 className="text-lg font-medium text-gray-900">
          {existingFormula ? 'Edit Formula' : 'Create Formula'}
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          Define a mathematical formula for calculating this property
        </p>
      </div>

      {/* Basic Info */}
      <div className="grid grid-cols-1 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">
            Formula Name
          </label>
          <input
            type="text"
            value={formula.name}
            onChange={(e) => setFormula({...formula, name: e.target.value})}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="e.g., Thermal Resistance Calculation"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">
            Description
          </label>
          <textarea
            value={formula.description || ''}
            onChange={(e) => setFormula({...formula, description: e.target.value})}
            rows={2}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
            placeholder="Describe what this formula calculates..."
          />
        </div>
      </div>

      {/* Formula Expression */}
      <div>
        <label className="block text-sm font-medium text-gray-700">
          Mathematical Expression
        </label>
        <textarea
          value={formula.formula_expression}
          onChange={(e) => setFormula({...formula, formula_expression: e.target.value})}
          rows={3}
          className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 font-mono"
          placeholder="e.g., thickness / (k * area)"
        />
        <p className="mt-1 text-xs text-gray-500">
          Use variable names that you'll define below. Supported functions: sqrt, log, sin, cos, tan, exp, abs, min, max
        </p>
      </div>

      {/* Variable References */}
      <div>
        <div className="flex justify-between items-center">
          <h4 className="text-sm font-medium text-gray-900">Variable References</h4>
          <button
            type="button"
            onClick={addReference}
            className="px-3 py-1 text-sm bg-indigo-600 text-white rounded-md hover:bg-indigo-700"
          >
            Add Variable
          </button>
        </div>

        <div className="mt-3 space-y-3">
          {formula.references.map((ref, index) => (
            <div
              key={index}
              className={`border rounded-lg p-4 ${
                activeReferenceIndex === index ? 'border-indigo-300 bg-indigo-50' : 'border-gray-200'
              }`}
            >
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-medium text-gray-700">
                    Variable Name
                  </label>
                  <div className="flex">
                    <input
                      type="text"
                      value={ref.variable_name}
                      onChange={(e) => updateReference(index, {variable_name: e.target.value})}
                      className="flex-1 mt-1 px-2 py-1 text-sm border border-gray-300 rounded-l-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="e.g., k, thickness"
                    />
                    <button
                      type="button"
                      onClick={() => insertVariableIntoExpression(ref.variable_name)}
                      className="mt-1 px-2 py-1 text-xs bg-gray-100 border border-l-0 border-gray-300 rounded-r-md hover:bg-gray-200"
                      title="Insert into formula"
                    >
                      →
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-medium text-gray-700">
                    Reference Type
                  </label>
                  <select
                    value={ref.reference_type}
                    onChange={(e) => updateReference(index, {
                      reference_type: e.target.value as PropertyReference['reference_type'],
                      // Clear other fields when type changes
                      target_component_id: undefined,
                      target_property_definition_id: undefined,
                      target_constant_symbol: undefined,
                      literal_value: e.target.value === 'literal_value' ? 0 : undefined
                    })}
                    className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                  >
                    <option value="literal_value">Literal Value</option>
                    <option value="system_constant">System Constant</option>
                    <option value="component_property">Component Property</option>
                    <option value="function_call">Function Call</option>
                  </select>
                </div>

                {/* Reference-specific fields */}
                {ref.reference_type === 'literal_value' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700">
                      Value
                    </label>
                    <input
                      type="number"
                      step="any"
                      value={ref.literal_value || 0}
                      onChange={(e) => updateReference(index, {literal_value: parseFloat(e.target.value)})}
                      className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    />
                  </div>
                )}

                {ref.reference_type === 'system_constant' && (
                  <div>
                    <label className="block text-xs font-medium text-gray-700">
                      Constant
                    </label>
                    <select
                      value={ref.target_constant_symbol || ''}
                      onChange={(e) => updateReference(index, {target_constant_symbol: e.target.value})}
                      className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    >
                      <option value="">Select constant...</option>
                      {availableRefs?.constants.map((constant: any) => (
                        <option key={constant.symbol} value={constant.symbol}>
                          {constant.symbol} - {constant.name} ({constant.value} {constant.unit})
                        </option>
                      ))}
                    </select>
                  </div>
                )}

                {ref.reference_type === 'component_property' && (
                  <>
                    <div>
                      <label className="block text-xs font-medium text-gray-700">
                        Component
                      </label>
                      <select
                        value={ref.target_component_id || ''}
                        onChange={(e) => updateReference(index, {
                          target_component_id: e.target.value ? parseInt(e.target.value) : undefined
                        })}
                        className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="">This component</option>
                        {availableRefs?.components.map((component: any) => (
                          <option key={component.id} value={component.id}>
                            {component.component_id} - {component.name}
                          </option>
                        ))}
                      </select>
                    </div>

                    <div>
                      <label className="block text-xs font-medium text-gray-700">
                        Property
                      </label>
                      <select
                        value={ref.target_property_definition_id || ''}
                        onChange={(e) => updateReference(index, {
                          target_property_definition_id: parseInt(e.target.value)
                        })}
                        className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                      >
                        <option value="">Select property...</option>
                        {availableRefs?.properties.map((property: any) => (
                          <option key={property.id} value={property.id}>
                            {property.name} ({property.unit})
                          </option>
                        ))}
                      </select>
                    </div>
                  </>
                )}

                <div className="col-span-2">
                  <label className="block text-xs font-medium text-gray-700">
                    Description (optional)
                  </label>
                  <input
                    type="text"
                    value={ref.description || ''}
                    onChange={(e) => updateReference(index, {description: e.target.value})}
                    className="mt-1 block w-full px-2 py-1 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500"
                    placeholder="Describe this variable..."
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={() => removeReference(index)}
                className="mt-2 text-xs text-red-600 hover:text-red-800"
              >
                Remove Variable
              </button>
            </div>
          ))}

          {formula.references.length === 0 && (
            <div className="text-center py-8 text-gray-500 border border-dashed border-gray-300 rounded-lg">
              <p className="text-sm">No variables defined</p>
              <p className="text-xs">Add variables that your formula uses</p>
            </div>
          )}
        </div>
      </div>

      {/* Validation Result */}
      {validationResult && (
        <div className={`rounded-lg p-4 ${
          validationResult.is_valid 
            ? 'bg-green-50 border border-green-200' 
            : 'bg-red-50 border border-red-200'
        }`}>
          <div className="flex">
            <div className="flex-shrink-0">
              {validationResult.is_valid ? (
                <svg className="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
              ) : (
                <svg className="h-5 w-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              )}
            </div>
            <div className="ml-3">
              <h4 className={`text-sm font-medium ${
                validationResult.is_valid ? 'text-green-800' : 'text-red-800'
              }`}>
                {validationResult.is_valid ? 'Formula Valid' : 'Formula Invalid'}
              </h4>
              {validationResult.error_message && (
                <p className={`text-sm ${validationResult.is_valid ? 'text-green-700' : 'text-red-700'}`}>
                  {validationResult.error_message}
                </p>
              )}
              {validationResult.variables_found && (
                <p className="text-xs text-gray-600 mt-1">
                  Variables found: {validationResult.variables_found.join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex justify-between">
        <div>
          {existingFormula?.id && (
            <button
              type="button"
              onClick={() => validateFormula.mutate()}
              disabled={validateFormula.isPending}
              className="px-4 py-2 text-sm font-medium text-indigo-600 bg-white border border-indigo-600 rounded-md hover:bg-indigo-50 disabled:opacity-50"
            >
              {validateFormula.isPending ? 'Validating...' : 'Validate Formula'}
            </button>
          )}
        </div>

        <div className="flex space-x-3">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={createFormula.isPending || updateFormula.isPending || !formula.name || !formula.formula_expression}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {createFormula.isPending || updateFormula.isPending 
              ? 'Saving...' 
              : existingFormula ? 'Update Formula' : 'Create Formula'
            }
          </button>
        </div>
      </div>
    </div>
  );
};

export default FormulaEditor;