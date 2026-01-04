import React from 'react';

interface ValidationResult {
  parameter_name: string;
  status: 'PASS' | 'WARNING' | 'FAIL';
  measured_value: number;
  predicted_value?: number;
  target_value?: number;
  tolerance?: number;
  tolerance_percent?: number;
  error_value?: number;
  error_percent?: number;
  message?: string;
  unit?: string;
}

interface ValidationDisplayProps {
  results: ValidationResult[];
  showDetails?: boolean;
}

const STATUS_CONFIG = {
  PASS: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-800',
    icon: (
      <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
      </svg>
    ),
    label: 'Pass',
  },
  WARNING: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-800',
    icon: (
      <svg className="w-5 h-5 text-yellow-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
      </svg>
    ),
    label: 'Warning',
  },
  FAIL: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-800',
    icon: (
      <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
      </svg>
    ),
    label: 'Fail',
  },
};

const ValidationDisplay: React.FC<ValidationDisplayProps> = ({ results, showDetails = false }) => {
  // Calculate summary counts
  const summary = results.reduce(
    (acc, result) => {
      acc[result.status]++;
      acc.total++;
      return acc;
    },
    { PASS: 0, WARNING: 0, FAIL: 0, total: 0 }
  );

  const formatValue = (value: number | undefined, unit?: string): string => {
    if (value === undefined) return '-';
    const formatted = Number.isInteger(value) ? value.toString() : value.toFixed(4);
    return unit ? `${formatted} ${unit}` : formatted;
  };

  const formatPercent = (value: number | undefined): string => {
    if (value === undefined) return '-';
    return `${value.toFixed(2)}%`;
  };

  return (
    <div className="space-y-4">
      {/* Results List */}
      <div className="space-y-2">
        {results.map((result, idx) => {
          const config = STATUS_CONFIG[result.status];
          return (
            <div
              key={`${result.parameter_name}-${idx}`}
              className={`p-4 rounded-lg border ${config.bg} ${config.border}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-start gap-3">
                  {config.icon}
                  <div>
                    <p className={`font-medium ${config.text}`}>{result.parameter_name}</p>
                    {result.message && (
                      <p className="text-sm text-gray-600 mt-0.5">{result.message}</p>
                    )}
                  </div>
                </div>
                <span className={`text-xs font-medium px-2 py-1 rounded ${config.bg} ${config.text}`}>
                  {config.label}
                </span>
              </div>

              {/* Detailed view */}
              {showDetails && (
                <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
                  <div>
                    <p className="text-xs text-gray-500 uppercase">Measured</p>
                    <p className="font-mono text-gray-900">
                      {formatValue(result.measured_value, result.unit)}
                    </p>
                  </div>

                  {result.predicted_value !== undefined && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase">Predicted</p>
                      <p className="font-mono text-gray-900">
                        {formatValue(result.predicted_value, result.unit)}
                      </p>
                    </div>
                  )}

                  {result.target_value !== undefined && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase">Target</p>
                      <p className="font-mono text-gray-900">
                        {formatValue(result.target_value, result.unit)}
                        {result.tolerance !== undefined && (
                          <span className="text-gray-500"> ±{result.tolerance}</span>
                        )}
                        {result.tolerance_percent !== undefined && (
                          <span className="text-gray-500"> ±{result.tolerance_percent}%</span>
                        )}
                      </p>
                    </div>
                  )}

                  {(result.error_value !== undefined || result.error_percent !== undefined) && (
                    <div>
                      <p className="text-xs text-gray-500 uppercase">Error</p>
                      <p className={`font-mono ${
                        result.status === 'PASS'
                          ? 'text-green-700'
                          : result.status === 'WARNING'
                          ? 'text-yellow-700'
                          : 'text-red-700'
                      }`}>
                        {result.error_value !== undefined && formatValue(result.error_value, result.unit)}
                        {result.error_percent !== undefined && (
                          <span className="ml-1">({formatPercent(result.error_percent)})</span>
                        )}
                      </p>
                    </div>
                  )}
                </div>
              )}

              {/* Compact view with key metrics */}
              {!showDetails && (
                <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                  <span>
                    Measured: <span className="font-mono">{formatValue(result.measured_value, result.unit)}</span>
                  </span>
                  {result.target_value !== undefined && (
                    <span>
                      Target: <span className="font-mono">{formatValue(result.target_value, result.unit)}</span>
                    </span>
                  )}
                  {result.error_percent !== undefined && (
                    <span className={`font-medium ${
                      result.status === 'PASS'
                        ? 'text-green-600'
                        : result.status === 'WARNING'
                        ? 'text-yellow-600'
                        : 'text-red-600'
                    }`}>
                      {formatPercent(result.error_percent)} error
                    </span>
                  )}
                </div>
              )}
            </div>
          );
        })}
      </div>

      {/* Summary Bar */}
      <div className="flex items-center justify-between p-4 bg-gray-100 rounded-lg">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-700">
              <span className="font-medium">{summary.PASS}</span> Pass
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
            <span className="text-sm text-gray-700">
              <span className="font-medium">{summary.WARNING}</span> Warning
            </span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-sm text-gray-700">
              <span className="font-medium">{summary.FAIL}</span> Fail
            </span>
          </div>
        </div>

        <div className="text-sm text-gray-500">
          {summary.total} validation{summary.total !== 1 ? 's' : ''} total
        </div>
      </div>

      {/* Pass rate indicator */}
      {summary.total > 0 && (
        <div className="relative pt-1">
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-gray-600">Pass Rate</span>
            <span className="text-xs font-medium text-gray-600">
              {((summary.PASS / summary.total) * 100).toFixed(0)}%
            </span>
          </div>
          <div className="flex h-2 rounded-full overflow-hidden bg-gray-200">
            {summary.PASS > 0 && (
              <div
                className="bg-green-500"
                style={{ width: `${(summary.PASS / summary.total) * 100}%` }}
              />
            )}
            {summary.WARNING > 0 && (
              <div
                className="bg-yellow-500"
                style={{ width: `${(summary.WARNING / summary.total) * 100}%` }}
              />
            )}
            {summary.FAIL > 0 && (
              <div
                className="bg-red-500"
                style={{ width: `${(summary.FAIL / summary.total) * 100}%` }}
              />
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default ValidationDisplay;
