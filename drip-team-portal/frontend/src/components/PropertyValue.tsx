import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty, ValueType } from '../types';
import { useUnits } from '../contexts/UnitContext';
import { parseValueWithUnit, convertUnit, formatValueWithUnit, formatRangeWithUnit } from '../utils/unitConversion';
import { FormulaInput } from './FormulaInput';
import { hasVariableReferences, resolveAllVariables, replaceVariableReferences, isFormula } from '../utils/variableResolver';
import { useFormula } from '../hooks/useFormula';

interface PropertyValueProps {
  property: ComponentProperty;
  componentId: string;
  onDelete: () => void;
}

const PropertyValue: React.FC<PropertyValueProps> = ({ property, componentId, onDelete }) => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [isEditing, setIsEditing] = useState(false);
  const [inputValue, setInputValue] = useState('');
  const { formatWithUserUnit, formatRangeWithUserUnit, getUserUnit, getDimensionFromUnit, convertToUserUnit } = useUnits();
  const { createFormula } = useFormula();

  // Get dimension from property unit
  const dimension = getDimensionFromUnit(property.property_definition.unit);
  const userUnit = dimension ? getUserUnit(dimension) : property.property_definition.unit;

  // Initialize input value when entering edit mode
  useEffect(() => {
    if (isEditing) {
      // Check if property has a formula - fetch the expression from backend
      if (property.is_calculated && property.formula_id) {
        // Add a small delay to ensure backend is ready
        const timer = setTimeout(() => {
          api.get(`/api/v1/formulas/property/${property.id}/formula`)
            .then(response => {
              if (response.data.has_formula && response.data.expression) {
                setInputValue(response.data.expression);
              }
            })
            .catch(error => {
              console.error('Error fetching formula:', error);
              // Fall back to stored formula expression if available
              // First try notes, then try the formula description pattern
              if (property.notes) {
                // Check for the standard formula pattern in notes
                const formulaMatch = property.notes.match(/Formula.*?: (.+?)(?:\s*$|\s*-)/);
                if (formulaMatch) {
                  setInputValue(formulaMatch[1]);
                  return;
                }
                // Also check if the entire note might be a formula
                if (property.notes.includes('.') && (property.notes.includes('cmp') || /[+\-*/()]/.test(property.notes))) {
                  setInputValue(property.notes);
                  return;
                }
              }
              // If all else fails, show the calculated value
              setInputValueFromProperty();
            });
        }, 100);
        
        return () => clearTimeout(timer);
      }
      
      // No formula - show the current value
      setInputValueFromProperty();
    }
  }, [isEditing, property.formula_id, property.is_calculated]);

  const setInputValueFromProperty = () => {
    const def = property.property_definition;
    let initialValue = '';
    
    switch (def.value_type) {
      case ValueType.SINGLE:
        if (property.single_value !== null && property.single_value !== undefined) {
          if (dimension) {
            const convertedValue = convertToUserUnit(property.single_value, def.unit, dimension);
            initialValue = `${convertedValue} ${userUnit}`;
          } else {
            initialValue = `${property.single_value} ${def.unit}`;
          }
        }
        break;
      case ValueType.RANGE:
        if (property.min_value !== null && property.min_value !== undefined && 
            property.max_value !== null && property.max_value !== undefined) {
          if (dimension) {
            const convertedMin = convertToUserUnit(property.min_value, def.unit, dimension);
            const convertedMax = convertToUserUnit(property.max_value, def.unit, dimension);
            initialValue = `${convertedMin} - ${convertedMax} ${userUnit}`;
          } else {
            initialValue = `${property.min_value} - ${property.max_value} ${def.unit}`;
          }
        }
        break;
      case ValueType.AVERAGE:
        if (property.average_value !== null && property.average_value !== undefined) {
          if (dimension) {
            const convertedAvg = convertToUserUnit(property.average_value, def.unit, dimension);
            const convertedTol = property.tolerance ? convertToUserUnit(property.tolerance, def.unit, dimension) : 0;
            initialValue = convertedTol ? `${convertedAvg} ± ${convertedTol} ${userUnit}` : `${convertedAvg} ${userUnit}`;
          } else {
            const tol = property.tolerance || 0;
            initialValue = tol ? `${property.average_value} ± ${tol} ${def.unit}` : `${property.average_value} ${def.unit}`;
          }
        }
        break;
    }
    
    setInputValue(initialValue);
  };

  const updateProperty = useMutation({
    mutationFn: async (values: any) => {
      await api.patch(`/api/v1/components/${componentId}/properties/${property.id}`, values);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['component-properties', componentId] });
      setIsEditing(false);
    },
  });

  const handleSave = async () => {
    let valueToProcess = inputValue;
    const values: any = {};
    const baseUnit = property.property_definition.unit;
    
    // Check if the input contains variable references or formulas
    if (hasVariableReferences(inputValue) || isFormula(inputValue)) {
      try {
        // Create a formula on the backend
        const result = await createFormula.mutateAsync({
          propertyId: property.id,
          componentId: componentId,
          componentDbId: property.component_id, // Use the property's component_id which is the DB ID
          expression: inputValue,
          propertyDefinitionId: property.property_definition.id
        });
        
        console.log('Formula created:', result);
        
        // Check if formula was successfully created and applied
        if (result.validation_status === 'error') {
          console.error('Formula validation failed:', result.validation_message || 'Unknown error');
          console.error('Full formula result:', result);
          // Don't exit - continue to save as manual value
        } else {
          setIsEditing(false);
          return; // Exit early - the formula creation will update the property
        }
        
      } catch (error: any) {
        console.error('Error creating formula:', error);
        console.error('Error response:', error.response?.data);
        // Fall back to storing as notes if formula creation fails
        values.is_calculated = false;
        values.calculation_status = 'manual';
        values.notes = `Formula (failed to create): ${inputValue}`;
        // Log error detail if available
        if (error.response?.data?.detail) {
          console.error('Formula creation failed with detail:', error.response.data.detail);
        }
      }
    } else {
      // Regular value - mark as manual
      values.is_calculated = false;
      values.calculation_status = 'manual';
    }
    
    const parsed = parseValueWithUnit(valueToProcess, userUnit);
    
    // Always try to convert to base unit if we have a known dimension
    // If user didn't specify a unit, parsed.unit will be userUnit (their preference)
    // We need to convert from that to the base unit
    
    if (parsed.isRange && parsed.min !== undefined && parsed.max !== undefined) {
      // Convert from parsed unit (which could be user's unit) to base unit
      let minBase = parsed.min;
      let maxBase = parsed.max;
      
      if (dimension) {
        // We know the dimension, so convert from parsed unit to base unit
        minBase = convertUnit(parsed.min, parsed.unit, baseUnit);
        maxBase = convertUnit(parsed.max, parsed.unit, baseUnit);
      }
      
      if (property.property_definition.value_type === ValueType.AVERAGE) {
        // For average type, calculate average and tolerance
        values.average_value = (minBase + maxBase) / 2;
        values.tolerance = (maxBase - minBase) / 2;
      } else {
        // For range type
        values.min_value = minBase;
        values.max_value = maxBase;
      }
    } else if (!parsed.isRange && parsed.value !== undefined) {
      // Single value - convert to base unit
      let valueBase = parsed.value;
      
      if (dimension) {
        // We know the dimension, so convert from parsed unit to base unit
        valueBase = convertUnit(parsed.value, parsed.unit, baseUnit);
        console.log('Converting value:', parsed.value, parsed.unit, '->', valueBase, baseUnit);
      }
      
      if (property.property_definition.value_type === ValueType.SINGLE) {
        values.single_value = valueBase;
      } else if (property.property_definition.value_type === ValueType.AVERAGE) {
        values.average_value = valueBase;
        values.tolerance = 0;
      } else if (property.property_definition.value_type === ValueType.RANGE) {
        // If they entered a single value for a range property, use it as both min and max
        values.min_value = valueBase;
        values.max_value = valueBase;
      }
    }
    
    updateProperty.mutate(values);
  };

  const renderValue = () => {
    const def = property.property_definition;
    
    if (isEditing) {
      return (
        <FormulaInput
          value={inputValue}
          onChange={setInputValue}
          placeholder={`e.g., "10 ${userUnit}" or "cmp1.width * 2"`}
          componentId={componentId}
          className="w-64"
        />
      );
    }
    
    // Display mode - show values in user's preferred units if conversion available
    switch (def.value_type) {
      case ValueType.SINGLE:
        if (property.single_value !== null && property.single_value !== undefined) {
          if (dimension) {
            const convertedValue = convertToUserUnit(property.single_value, def.unit, dimension);
            return <span className="text-gray-900">{formatWithUserUnit(convertedValue, dimension)}</span>;
          } else {
            // No conversion available, show original value with original unit
            return <span className="text-gray-900">{formatValueWithUnit(property.single_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;
        
      case ValueType.RANGE:
        if (property.min_value !== null && property.min_value !== undefined && 
            property.max_value !== null && property.max_value !== undefined) {
          if (dimension) {
            const convertedMin = convertToUserUnit(property.min_value, def.unit, dimension);
            const convertedMax = convertToUserUnit(property.max_value, def.unit, dimension);
            return <span className="text-gray-900">{formatRangeWithUserUnit(convertedMin, convertedMax, dimension)}</span>;
          } else {
            // No conversion available, show original values with original unit
            return <span className="text-gray-900">{formatRangeWithUnit(property.min_value, property.max_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;
        
      case ValueType.AVERAGE:
        if (property.average_value !== null && property.average_value !== undefined) {
          if (dimension) {
            const convertedAvg = convertToUserUnit(property.average_value, def.unit, dimension);
            if (property.tolerance && property.tolerance !== null && property.tolerance !== undefined) {
              const convertedTol = convertToUserUnit(property.tolerance, def.unit, dimension);
              return (
                <span className="text-gray-900">
                  {formatWithUserUnit(convertedAvg, dimension)} ± {formatWithUserUnit(convertedTol, dimension)}
                </span>
              );
            }
            return <span className="text-gray-900">{formatWithUserUnit(convertedAvg, dimension)}</span>;
          } else {
            // No conversion available, show original values with original unit
            if (property.tolerance && property.tolerance !== null && property.tolerance !== undefined) {
              return (
                <span className="text-gray-900">
                  {formatValueWithUnit(property.average_value, '')} ± {formatValueWithUnit(property.tolerance, def.unit)}
                </span>
              );
            }
            return <span className="text-gray-900">{formatValueWithUnit(property.average_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;
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
          </div>
          
          {/* Formula indicator */}
          {(property.is_calculated || property.formula_id) && (
            <div className="flex items-center gap-1">
              <svg className="w-3 h-3 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z" clipRule="evenodd" />
                <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
              </svg>
              <span className="text-xs text-purple-600 font-medium">
                {property.calculation_status === 'calculated' ? 'Formula' : 
                 property.calculation_status === 'error' ? 'Error' : 
                 property.calculation_status === 'stale' ? 'Stale' : 'Formula'}
              </span>
            </div>
          )}
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
              onClick={() => {
                setIsEditing(false);
                setInputValue('');
              }}
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