import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty, ValueType } from '../types';
import { useUnits } from '../contexts/UnitContext';
import { parseValueWithUnit, convertUnit, formatValueWithUnit, formatRangeWithUnit, BASE_UNITS } from '../utils/unitConversion';
import ExpressionInput from './ExpressionInput';

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

  // Check if property has an expression
  const hasExpression = property.value_node?.node_type === 'expression';

  // Get dimension from property unit
  const dimension = getDimensionFromUnit(property.property_definition.unit);
  const userUnit = dimension ? getUserUnit(dimension) : property.property_definition.unit;

  // Initialize input value when entering edit mode
  useEffect(() => {
    if (isEditing) {
      setInputValueFromProperty();
    }
  }, [isEditing]);

  const setInputValueFromProperty = () => {
    const def = property.property_definition;

    // If it has an expression, show the expression
    if (hasExpression && property.value_node?.expression_string) {
      setInputValue(property.value_node.expression_string);
      return;
    }

    // Otherwise show the literal value
    // NOTE: Values are stored in SI units (meters, kg, etc.), not in def.unit
    // So we need to convert FROM the SI unit, not from def.unit
    const siUnit = dimension ? BASE_UNITS[dimension] : def.unit;
    let initialValue = '';
    switch (def.value_type) {
      case ValueType.SINGLE:
        if (property.single_value !== null && property.single_value !== undefined) {
          if (dimension) {
            const convertedValue = convertToUserUnit(property.single_value, siUnit, dimension);
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
            const convertedMin = convertToUserUnit(property.min_value, siUnit, dimension);
            const convertedMax = convertToUserUnit(property.max_value, siUnit, dimension);
            initialValue = `${convertedMin} - ${convertedMax} ${userUnit}`;
          } else {
            initialValue = `${property.min_value} - ${property.max_value} ${def.unit}`;
          }
        }
        break;
      case ValueType.AVERAGE:
        if (property.average_value !== null && property.average_value !== undefined) {
          if (dimension) {
            const convertedAvg = convertToUserUnit(property.average_value, siUnit, dimension);
            const convertedTol = property.tolerance ? convertToUserUnit(property.tolerance, siUnit, dimension) : 0;
            initialValue = convertedTol ? `${convertedAvg} +/- ${convertedTol} ${userUnit}` : `${convertedAvg} ${userUnit}`;
          } else {
            const tol = property.tolerance || 0;
            initialValue = tol ? `${property.average_value} +/- ${tol} ${def.unit}` : `${property.average_value} ${def.unit}`;
          }
        }
        break;
      case ValueType.TEXT:
        if (property.text_value) {
          initialValue = property.text_value;
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
      // Invalidate ALL component-properties queries to refresh dependent values in other components
      // When a value changes, expressions in other components that reference it are recalculated
      queryClient.invalidateQueries({ queryKey: ['component-properties'] });
      setIsEditing(false);
    },
  });

  const handleSave = async () => {
    const values: any = {};
    const trimmed = inputValue.trim();

    // Handle TEXT value type - just save as text_value
    if (property.property_definition.value_type === ValueType.TEXT) {
      values.text_value = trimmed;
      updateProperty.mutate(values);
      return;
    }

    // Check if it's an expression:
    // - Contains # reference (e.g., #component.property)
    // - Contains math operators with values (e.g., 1m + 0.3mm, (1/8)*3mm)
    // We detect expressions by looking for: operators between values, parentheses, or references
    const hasReference = trimmed.includes('#');
    const hasMathExpression = /[\+\-\*\/\(\)]/.test(trimmed) &&
      // Make sure it's not just a negative number or a range like "1 - 2"
      // Look for patterns like "1m + 2mm" or "(1/8)*3" etc.
      (/\d+\.?\d*\s*[a-zA-Z°μ]*\s*[\+\*\/]\s*\d/.test(trimmed) ||
       /\d+\.?\d*\s*[a-zA-Z°μ]*\s*\-\s*\d+\.?\d*\s*[a-zA-Z°μ]+\s*[\+\*\/]/.test(trimmed) ||
       /\(.*\)/.test(trimmed));

    if (hasReference || hasMathExpression) {
      values.expression = trimmed;
    } else {
      // Parse as literal value
      // NOTE: Always convert to SI unit for storage consistency with expressions
      // The backend stores all values in SI (meters, kg, etc.)
      const siUnit = dimension ? BASE_UNITS[dimension] : property.property_definition.unit;
      const parsed = parseValueWithUnit(trimmed, userUnit);

      if (parsed.isRange && parsed.min !== undefined && parsed.max !== undefined) {
        let minBase = parsed.min;
        let maxBase = parsed.max;

        if (dimension) {
          minBase = convertUnit(parsed.min, parsed.unit, siUnit);
          maxBase = convertUnit(parsed.max, parsed.unit, siUnit);
        }

        if (property.property_definition.value_type === ValueType.AVERAGE) {
          values.average_value = (minBase + maxBase) / 2;
          values.tolerance = (maxBase - minBase) / 2;
        } else {
          values.min_value = minBase;
          values.max_value = maxBase;
        }
      } else if (!parsed.isRange && parsed.value !== undefined) {
        let valueBase = parsed.value;

        if (dimension) {
          valueBase = convertUnit(parsed.value, parsed.unit, siUnit);
        }

        if (property.property_definition.value_type === ValueType.SINGLE) {
          values.single_value = valueBase;
        } else if (property.property_definition.value_type === ValueType.AVERAGE) {
          values.average_value = valueBase;
          values.tolerance = 0;
        } else if (property.property_definition.value_type === ValueType.RANGE) {
          values.min_value = valueBase;
          values.max_value = valueBase;
        }
      }
    }

    updateProperty.mutate(values);
  };

  const renderValue = () => {
    const def = property.property_definition;

    if (isEditing) {
      return (
        <div className="flex-1">
          <ExpressionInput
            value={inputValue}
            onChange={setInputValue}
            onSubmit={handleSave}
            onCancel={() => {
              setIsEditing(false);
              setInputValue('');
            }}
            placeholder={`e.g., "10 ${userUnit}" or "#CODE.property"`}
            autoFocus
          />
        </div>
      );
    }

    // Display mode - check for expression first
    if (hasExpression && property.value_node) {
      const computed = property.value_node.computed_value;
      const status = property.value_node.computation_status;
      const expr = property.value_node.expression_string;
      const computedUnit = property.value_node.computed_unit_symbol || def.unit;

      // Get dimension from computed unit and convert to user's preferred unit
      const computedDimension = getDimensionFromUnit(computedUnit);
      let displayValue = '';
      if (status === 'valid' && computed !== null && computed !== undefined) {
        if (computedDimension) {
          const convertedValue = convertToUserUnit(computed, computedUnit, computedDimension);
          displayValue = formatWithUserUnit(convertedValue, computedDimension);
        } else {
          displayValue = formatValueWithUnit(computed, computedUnit);
        }
      }

      return (
        <div className="flex items-center gap-2">
          <span className={status === 'error' ? 'text-red-600' : 'text-gray-900'}>
            {status === 'valid' && computed !== null && computed !== undefined
              ? displayValue
              : status === 'error'
              ? 'Error'
              : 'Calculating...'}
          </span>
          <span className="text-xs text-gray-400 font-mono truncate max-w-32" title={expr || ''}>
            = {expr}
          </span>
          {status === 'stale' && (
            <span className="text-xs px-1 py-0.5 bg-yellow-100 text-yellow-700 rounded">stale</span>
          )}
        </div>
      );
    }

    // Display literal values in user's preferred units
    // NOTE: Values are stored in SI units (meters, kg, etc.), not in def.unit
    // So we need to convert FROM the SI unit, not from def.unit
    const siUnit = dimension ? BASE_UNITS[dimension] : def.unit;

    switch (def.value_type) {
      case ValueType.SINGLE:
        if (property.single_value !== null && property.single_value !== undefined) {
          if (dimension) {
            const convertedValue = convertToUserUnit(property.single_value, siUnit, dimension);
            return <span className="text-gray-900">{formatWithUserUnit(convertedValue, dimension)}</span>;
          } else {
            return <span className="text-gray-900">{formatValueWithUnit(property.single_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;

      case ValueType.RANGE:
        if (property.min_value !== null && property.min_value !== undefined &&
            property.max_value !== null && property.max_value !== undefined) {
          if (dimension) {
            const convertedMin = convertToUserUnit(property.min_value, siUnit, dimension);
            const convertedMax = convertToUserUnit(property.max_value, siUnit, dimension);
            return <span className="text-gray-900">{formatRangeWithUserUnit(convertedMin, convertedMax, dimension)}</span>;
          } else {
            return <span className="text-gray-900">{formatRangeWithUnit(property.min_value, property.max_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;

      case ValueType.AVERAGE:
        if (property.average_value !== null && property.average_value !== undefined) {
          if (dimension) {
            const convertedAvg = convertToUserUnit(property.average_value, siUnit, dimension);
            if (property.tolerance && property.tolerance !== null && property.tolerance !== undefined) {
              const convertedTol = convertToUserUnit(property.tolerance, siUnit, dimension);
              return (
                <span className="text-gray-900">
                  {formatWithUserUnit(convertedAvg, dimension)} +/- {formatWithUserUnit(convertedTol, dimension)}
                </span>
              );
            }
            return <span className="text-gray-900">{formatWithUserUnit(convertedAvg, dimension)}</span>;
          } else {
            if (property.tolerance && property.tolerance !== null && property.tolerance !== undefined) {
              return (
                <span className="text-gray-900">
                  {formatValueWithUnit(property.average_value, '')} +/- {formatValueWithUnit(property.tolerance, def.unit)}
                </span>
              );
            }
            return <span className="text-gray-900">{formatValueWithUnit(property.average_value, def.unit)}</span>;
          }
        }
        return <span className="text-gray-400 italic">Not set</span>;

      case ValueType.TEXT:
        if (property.text_value) {
          return <span className="text-gray-900 font-mono text-sm">{property.text_value}</span>;
        }
        return <span className="text-gray-400 italic">Not set</span>;

      default:
        return <span className="text-gray-400 italic">Not set</span>;
    }
  };

  return (
    <div className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:shadow-sm transition-shadow">
      <div className="flex-1">
        <div className="flex items-center gap-3 w-full">
          <span className="text-sm font-medium text-gray-700 shrink-0">
            {property.property_definition.name}
          </span>
          <div
            className="flex-1 flex items-center gap-2 cursor-pointer min-w-0"
            onClick={() => !isEditing && setIsEditing(true)}
          >
            {renderValue()}
          </div>
          {/* Expression indicator */}
          {hasExpression && !isEditing && (
            <span className="text-xs px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded">
              expr
            </span>
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

      <div className="flex items-center gap-1 ml-4">
        {isEditing ? (
          <>
            <button
              onClick={handleSave}
              disabled={updateProperty.isPending}
              className="p-1.5 text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-50"
              aria-label="Save"
              title="Save"
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
              className="p-1.5 text-gray-500 hover:bg-gray-100 rounded transition-colors"
              aria-label="Cancel"
              title="Cancel"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </>
        ) : (
          <>
            <button
              onClick={() => setIsEditing(true)}
              className="p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded transition-colors"
              aria-label="Edit property"
              title="Edit"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z" />
              </svg>
            </button>
            <button
              onClick={onDelete}
              className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
              aria-label="Delete property"
              title="Delete"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </>
        )}
      </div>
    </div>
  );
};

export default PropertyValue;
