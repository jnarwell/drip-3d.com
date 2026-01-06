import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { createPortal } from 'react-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import { PropertySourceSummary, PropertyViewData, PropertyViewHeader } from '../../types/resources';
import { useUnits } from '../../contexts/UnitContext';
import { convertUnit } from '../../utils/unitConversion';

// Category display names
const CATEGORY_INFO: Record<string, { name: string }> = {
  electrical: { name: 'Electrical' },
  finishes: { name: 'Surface Finishes' },
  tolerances: { name: 'Tolerances' },
  fasteners: { name: 'Fasteners' },
  process: { name: 'Process/Fluids' },
  structural: { name: 'Structural' },
  material: { name: 'Materials' },
  mechanical: { name: 'Mechanical' },
};

// Type badge colors
const TYPE_COLORS: Record<string, string> = {
  table: 'bg-blue-100 text-blue-800',
  equation: 'bg-purple-100 text-purple-800',
  library: 'bg-green-100 text-green-800',
};

// Format snake_case strings to Title Case (e.g., "flame_cutting" → "Flame Cutting")
const formatSnakeCase = (value: string): string => {
  if (/^[a-z][a-z0-9_]*$/.test(value)) {
    return value
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  }
  return value;
};

const PropertyTables: React.FC = () => {
  const api = useAuthenticatedApi();
  const { getDimensionFromUnit, getUserUnit, unitSettings } = useUnits();
  const [selectedSource, setSelectedSource] = useState<string | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Handle escape key to close fullscreen
  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape' && isFullscreen) {
      setIsFullscreen(false);
    }
  }, [isFullscreen]);

  useEffect(() => {
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [handleEscape]);

  // Fetch all property sources
  const { data: sources, isLoading, error } = useQuery<PropertySourceSummary[]>({
    queryKey: ['eng-property-sources'],
    queryFn: async () => {
      const response = await api.get('/api/v1/eng-properties/sources');
      return response.data;
    }
  });

  // Fetch view data when a source is selected
  const { data: viewData, isLoading: viewLoading } = useQuery<PropertyViewData>({
    queryKey: ['eng-property-view', selectedSource],
    queryFn: async () => {
      const response = await api.get(`/api/v1/eng-properties/sources/${selectedSource}/views/default`);
      return response.data;
    },
    enabled: !!selectedSource,
  });

  // Group sources by category
  const groupedSources = React.useMemo(() => {
    if (!sources) return {};
    const grouped: Record<string, PropertySourceSummary[]> = {};
    for (const source of sources) {
      if (!grouped[source.category]) {
        grouped[source.category] = [];
      }
      grouped[source.category].push(source);
    }
    return grouped;
  }, [sources]);

  // Get unique categories
  const categories = Object.keys(groupedSources);

  // Filter sources by selected category
  const filteredSources = selectedCategory
    ? sources?.filter(s => s.category === selectedCategory)
    : sources;

  // Get selected source details for LOOKUP template
  const selectedSourceData = sources?.find(s => s.id === selectedSource);
  const lookupTemplate = React.useMemo(() => {
    if (!selectedSourceData) return '';

    // Use lookup_source_id if specified, otherwise use the source's own id
    const lookupId = selectedSourceData.lookup_source_id || selectedSourceData.id;

    const requiredInputs = selectedSourceData.inputs.filter(i => !i.optional);
    const optionalInputs = selectedSourceData.inputs.filter(i => i.optional);

    let inputParams: string;
    if (requiredInputs.length > 0) {
      // Show required inputs with =, then optional in brackets
      const required = requiredInputs.map(i => `${i.name}=`).join(', ');
      const optional = optionalInputs.length > 0
        ? `, [${optionalInputs.map(i => `${i.name}=`).join(', ')}]`
        : '';
      inputParams = required + optional;
    } else if (optionalInputs.length > 0) {
      // All optional (like steam) - show all with =
      inputParams = optionalInputs.map(i => `${i.name}=`).join(', ');
    } else {
      inputParams = '';
    }
    return `LOOKUP("${lookupId}", "<output>", ${inputParams})`;
  }, [selectedSourceData]);

  // Get display unit for a header (user preference or fallback to YAML display unit)
  const getDisplayUnit = useCallback((header: PropertyViewHeader): string => {
    // Try to get dimension from SI unit first, then from display unit
    const unitToCheck = header.si_unit || header.unit;
    if (unitToCheck) {
      const dimension = getDimensionFromUnit(unitToCheck);
      if (dimension) {
        // Use user's preferred unit for this dimension
        return getUserUnit(dimension);
      }
    }

    // Fallback to YAML display unit
    return header.unit || header.si_unit || '';
  }, [getDimensionFromUnit, getUserUnit]);

  // Format a value with unit conversion and precision
  const formatValue = useCallback((
    value: unknown,
    header: PropertyViewHeader
  ): string => {
    if (value === null || value === undefined) return '—';

    // String values (snake_case formatting)
    if (typeof value === 'string') {
      return formatSnakeCase(value);
    }

    // Non-numeric values
    if (typeof value !== 'number') {
      return String(value);
    }

    // Numeric value - convert and format
    let displayValue = value;
    // Use si_unit if available, otherwise fall back to header.unit for source unit
    const sourceUnit = header.si_unit || header.unit;
    const displayUnit = getDisplayUnit(header);

    // Convert from source to user's display unit if needed
    if (sourceUnit && displayUnit && sourceUnit !== displayUnit) {
      try {
        displayValue = convertUnit(value, sourceUnit, displayUnit);
      } catch {
        // If conversion fails, use original value
        displayValue = value;
      }
    }

    // Get precision from user settings based on dimension
    const dimension = sourceUnit ? getDimensionFromUnit(sourceUnit) : null;
    const setting = dimension ? unitSettings[dimension] : null;
    const precision = setting?.precision || 0.01;

    // Calculate decimal places from precision
    const decimalPlaces = Math.max(0, -Math.floor(Math.log10(precision)));

    // Format based on magnitude
    const absValue = Math.abs(displayValue);
    if (absValue === 0) {
      return '0';
    } else if (absValue >= 1e6 || absValue < 1e-3) {
      // Scientific notation for very large/small values
      return displayValue.toExponential(decimalPlaces);
    } else if (absValue >= 1000) {
      // Large values - fewer decimal places
      return displayValue.toFixed(Math.max(0, decimalPlaces - 2));
    } else {
      return displayValue.toFixed(decimalPlaces);
    }
  }, [getDisplayUnit, getDimensionFromUnit, unitSettings]);

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="sm:flex sm:items-center sm:justify-between mb-4">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">Engineering Reference Tables</h2>
            <p className="mt-1 text-sm text-gray-600">
              Standard reference data for engineering calculations. Use{' '}
              <code className="bg-gray-100 px-1 rounded">LOOKUP("source_id", "output", input=value)</code> in expressions.
            </p>
          </div>
        </div>

        {/* Category filter tabs */}
        {categories.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-4">
            <button
              onClick={() => setSelectedCategory(null)}
              className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                selectedCategory === null
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All ({sources?.length || 0})
            </button>
            {categories.map(cat => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                className={`px-3 py-1.5 text-sm font-medium rounded-full transition-colors ${
                  selectedCategory === cat
                    ? 'bg-indigo-600 text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {CATEGORY_INFO[cat]?.name || cat} ({groupedSources[cat]?.length || 0})
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Content */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Source List */}
        <div className="lg:col-span-1 bg-white shadow rounded-lg overflow-hidden">
          <div className="px-4 py-3 bg-gray-50 border-b">
            <h3 className="text-sm font-medium text-gray-700">Available Tables</h3>
          </div>

          {isLoading ? (
            <div className="p-4">
              <div className="animate-pulse space-y-3">
                {[1, 2, 3].map(i => (
                  <div key={i} className="h-16 bg-gray-100 rounded"></div>
                ))}
              </div>
            </div>
          ) : error ? (
            <div className="p-4 text-red-600">Failed to load tables</div>
          ) : (
            <div className="divide-y divide-gray-100 max-h-[600px] overflow-y-auto">
              {filteredSources?.map(source => (
                <button
                  key={source.id}
                  onClick={() => setSelectedSource(source.id)}
                  className={`w-full text-left px-4 py-3 hover:bg-gray-50 transition-colors ${
                    selectedSource === source.id ? 'bg-indigo-50 border-l-4 border-indigo-600' : ''
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {source.name}
                      </p>
                      <p className="text-xs text-gray-500 truncate mt-0.5">
                        {source.description}
                      </p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${TYPE_COLORS[source.type]}`}>
                          {source.type}
                        </span>
                        <span className="text-xs text-gray-400">
                          {source.column_count || source.outputs.length} columns
                        </span>
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Table View */}
        <div className="lg:col-span-2 bg-white shadow rounded-lg overflow-hidden">
          {selectedSource && viewData ? (
            <>
              <div className="px-4 py-3 bg-gray-50 border-b">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-sm font-medium text-gray-900">{viewData.metadata.view_name}</h3>
                    <p className="text-xs text-gray-500 mt-0.5">
                      Source: {viewData.metadata.source_name}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 max-w-md truncate" title={lookupTemplate}>
                      {lookupTemplate}
                    </code>
                    <button
                      onClick={() => setIsFullscreen(true)}
                      className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
                      title="Expand table"
                    >
                      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
                      </svg>
                    </button>
                  </div>
                </div>
              </div>

              <div className="overflow-x-auto max-h-[500px] overflow-y-auto">
                {viewLoading ? (
                  <div className="p-4 animate-pulse">
                    <div className="h-64 bg-gray-100 rounded"></div>
                  </div>
                ) : (
                  <table className="min-w-full divide-y divide-gray-200 table-auto">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        {viewData.headers.map((header, idx) => {
                          const displayUnit = getDisplayUnit(header);
                          return (
                            <th
                              key={idx}
                              className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                            >
                              <div>{header.label}</div>
                              {displayUnit && (
                                <div className="text-gray-400 font-normal normal-case whitespace-nowrap">
                                  ({displayUnit})
                                </div>
                              )}
                            </th>
                          );
                        })}
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {viewData.rows.map((row, rowIdx) => (
                        <tr key={rowIdx} className="hover:bg-gray-50">
                          {viewData.headers.map((header, colIdx) => {
                            const value = row.values[header.key];
                            const isInput = header.is_input;

                            return (
                              <td
                                key={colIdx}
                                className={`px-3 py-1.5 text-sm whitespace-nowrap ${
                                  isInput
                                    ? 'font-medium text-gray-900'
                                    : 'text-gray-600 font-mono'
                                }`}
                              >
                                {formatValue(value, header)}
                              </td>
                            );
                          })}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            </>
          ) : (
            <div className="flex items-center justify-center h-64 text-gray-500">
              <div className="text-center">
                <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <p className="mt-2 text-sm">Select a table to view its data</p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Fullscreen Modal - rendered via portal to ensure proper z-index stacking */}
      {isFullscreen && viewData && createPortal(
        <div className="fixed inset-0 z-[100] bg-black bg-opacity-50 flex items-center justify-center p-2">
          <div className="bg-gray-50 rounded-lg shadow-2xl w-full max-w-7xl max-h-[95vh] flex flex-col overflow-hidden">
            {/* Modal Header */}
            <div className="px-4 py-3 bg-gray-50 border-b flex-shrink-0">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="text-sm font-medium text-gray-900">{viewData.metadata.view_name}</h3>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Source: {viewData.metadata.source_name}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <code className="text-xs bg-gray-100 px-2 py-1 rounded text-gray-600 max-w-lg truncate" title={lookupTemplate}>
                    {lookupTemplate}
                  </code>
                  <button
                    onClick={() => setIsFullscreen(false)}
                    className="p-1.5 text-gray-400 hover:text-gray-600 hover:bg-gray-200 rounded transition-colors"
                    title="Close (Esc)"
                  >
                    <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>
            </div>

            {/* Modal Table Content */}
            <div className="overflow-auto flex-1">
              <table className="min-w-full divide-y divide-gray-200 table-auto">
                <thead className="bg-gray-50 sticky top-0">
                  <tr>
                    {viewData.headers.map((header, idx) => {
                      const displayUnit = getDisplayUnit(header);
                      return (
                        <th
                          key={idx}
                          className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider whitespace-nowrap"
                        >
                          <div>{header.label}</div>
                          {displayUnit && (
                            <div className="text-gray-400 font-normal normal-case whitespace-nowrap">
                              ({displayUnit})
                            </div>
                          )}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {viewData.rows.map((row, rowIdx) => (
                    <tr key={rowIdx} className="hover:bg-gray-50">
                      {viewData.headers.map((header, colIdx) => {
                        const value = row.values[header.key];
                        const isInput = header.is_input;

                        return (
                          <td
                            key={colIdx}
                            className={`px-3 py-1.5 text-sm whitespace-nowrap ${
                              isInput
                                ? 'font-medium text-gray-900'
                                : 'text-gray-600 font-mono'
                            }`}
                          >
                            {formatValue(value, header)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
};

export default PropertyTables;
