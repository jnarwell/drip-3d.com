import React from 'react';
import { PropertyTableTemplate, TableType, InterpolationType } from '../../types/resources';
import { formatDistanceToNow } from 'date-fns';

interface PropertyTableTemplatesListProps {
  templates: PropertyTableTemplate[];
}

const PropertyTableTemplatesList: React.FC<PropertyTableTemplatesListProps> = ({ templates }) => {
  const getTableTypeLabel = (type: TableType) => {
    switch (type) {
      case TableType.SINGLE_VAR_LOOKUP:
        return 'Single Variable';
      case TableType.RANGE_BASED_LOOKUP:
        return 'Range-based';
      case TableType.MULTI_VAR_LOOKUP:
        return 'Multi-variable';
      case TableType.REFERENCE_ONLY:
        return 'Reference Only';
      default:
        return type;
    }
  };

  const getInterpolationLabel = (type: InterpolationType) => {
    switch (type) {
      case InterpolationType.LINEAR:
        return 'Linear';
      case InterpolationType.LOGARITHMIC:
        return 'Logarithmic';
      case InterpolationType.POLYNOMIAL:
        return 'Polynomial';
      case InterpolationType.RANGE_LOOKUP:
        return 'Range Lookup';
      case InterpolationType.NONE:
        return 'None';
      default:
        return type;
    }
  };

  return (
    <div className="bg-white shadow overflow-hidden sm:rounded-lg">
      <div className="grid gap-4 p-4">
        {templates.map((template) => (
          <div 
            key={template.id} 
            className="border border-gray-200 rounded-lg p-4 hover:border-indigo-300 hover:shadow-md transition-all"
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center">
                  <h3 className="text-lg font-medium text-gray-900">{template.name}</h3>
                  {template.is_public && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-green-100 text-green-800">
                      Public
                    </span>
                  )}
                  {template.usage_count > 0 && (
                    <span className="ml-2 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
                      {template.usage_count} uses
                    </span>
                  )}
                </div>
                {template.description && (
                  <p className="mt-1 text-sm text-gray-600">{template.description}</p>
                )}
                
                <div className="mt-2 flex flex-wrap gap-2 text-xs">
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                    Type: {getTableTypeLabel(template.table_type)}
                  </span>
                  <span className="inline-flex items-center px-2 py-0.5 rounded bg-gray-100 text-gray-700">
                    Interpolation: {getInterpolationLabel(template.interpolation_type)}
                  </span>
                  {template.extrapolation_allowed && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-yellow-100 text-yellow-800">
                      Extrapolation allowed
                    </span>
                  )}
                  {template.require_monotonic && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-purple-100 text-purple-800">
                      Monotonic
                    </span>
                  )}
                  {template.created_from_document && (
                    <span className="inline-flex items-center px-2 py-0.5 rounded bg-indigo-100 text-indigo-800">
                      From document
                    </span>
                  )}
                </div>

                <div className="mt-3 grid grid-cols-2 gap-4 text-xs">
                  <div>
                    <p className="font-medium text-gray-700">Independent Variables ({template.independent_vars.length}):</p>
                    <ul className="mt-1 space-y-0.5">
                      {template.independent_vars.map((v, i) => (
                        <li key={i} className="text-gray-600">
                          {v.symbol} - {v.name} {v.unit && `(${v.unit})`}
                        </li>
                      ))}
                    </ul>
                  </div>
                  <div>
                    <p className="font-medium text-gray-700">Dependent Variables ({template.dependent_vars.length}):</p>
                    <ul className="mt-1 space-y-0.5">
                      {template.dependent_vars.slice(0, 3).map((v, i) => (
                        <li key={i} className="text-gray-600">
                          {v.symbol} - {v.name} {v.unit && `(${v.unit})`}
                        </li>
                      ))}
                      {template.dependent_vars.length > 3 && (
                        <li className="text-gray-400">... and {template.dependent_vars.length - 3} more</li>
                      )}
                    </ul>
                  </div>
                </div>

                <div className="mt-3 flex items-center text-xs text-gray-500">
                  <span>Created by {template.created_by}</span>
                  <span className="mx-2">•</span>
                  <span>{formatDistanceToNow(new Date(template.created_at), { addSuffix: true })}</span>
                </div>
              </div>

              <div className="ml-4 flex flex-col space-y-2">
                <button className="text-sm text-indigo-600 hover:text-indigo-900">
                  Use Template
                </button>
                <button className="text-sm text-gray-600 hover:text-gray-900">
                  Edit
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default PropertyTableTemplatesList;