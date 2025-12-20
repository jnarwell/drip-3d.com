import React, { useState, useEffect } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { ComponentProperty, ValueType } from '../types';
import { useUnits } from '../contexts/UnitContext';
import { parseValueWithUnit, convertUnit, formatValueWithUnit, formatRangeWithUnit } from '../utils/unitConversion';
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
            initialValue = convertedTol ? `${convertedAvg} +/- ${convertedTol} ${userUnit}` : `${convertedAvg} ${userUnit}`;
          } else {
            const tol = property.tolerance || 0;
            initialValue = tol ? `${property.average_value} +/- ${tol} ${def.unit}` : `${property.average_value} ${def.unit}`;
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
    const values: any = {};
    const trimmed = inputValue.trim();

    // Check if it's an expression (contains # reference)
    if (trimmed.includes('#')) {
      values.expression = trimmed;
    } else {
      // Parse as literal value
      const baseUnit = property.property_definition.unit;
      const parsed = parseValueWithUnit(trimmed, userUnit);

      if (parsed.isRange && parsed.min !== undefined && parsed.max !== undefined) {
        let minBase = parsed.min;
        let maxBase = parsed.max;

        if (dimension) {
          minBase = convertUnit(parsed.min, parsed.unit, baseUnit);
          maxBase = convertUnit(parsed.max, parsed.unit, baseUnit);
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
          valueBase = convertUnit(parsed.value, parsed.unit, baseUnit);
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
        <div className="w-80">
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
    switch (def.value_type) {
      case ValueType.SINGLE:
        if (property.single_value !== null && property.single_value !== undefined) {
          if (dimension) {
            const convertedValue = convertToUserUnit(property.single_value, def.unit, dimension);
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
            const convertedMin = convertToUserUnit(property.min_value, def.unit, dimension);
            const convertedMax = convertToUserUnit(property.max_value, def.unit, dimension);
            return <span className="text-gray-900">{formatRangeWithUserUnit(convertedMin, convertedMax, dimension)}</span>;
          } else {
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

      <div className="flex items-center gap-2 ml-4">
        {isEditing ? (
          <>
            <button
              onClick={handleSave}
              disabled={updateProperty.isPending}
              className="p-1 text-green-600 hover:bg-green-50 rounded transition-colors disabled:opacity-50"
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
