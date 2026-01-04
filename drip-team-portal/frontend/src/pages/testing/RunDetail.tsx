import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import ValidationDisplay from '../../components/testing/ValidationDisplay';

type RunStatus = 'SETUP' | 'IN_PROGRESS' | 'COMPLETED' | 'ABORTED';
type CompletionResult = 'PASS' | 'PARTIAL' | 'FAIL';

interface ParameterSchema {
  name: string;
  unit_id?: number;
  unit_symbol?: string;
  type?: 'number' | 'string' | 'boolean';
  target?: number;
  tolerance_pct?: number;
}

interface TestProtocol {
  id: string;
  name: string;
  category: string;
  description?: string;
  procedure?: string;
  input_schema: ParameterSchema[];
  output_schema: ParameterSchema[];
}

interface Measurement {
  id: number;
  run_id: number;
  parameter_name: string;
  measured_value: number;
  unit_id?: number;
  unit_symbol?: string;
  notes?: string;
  timestamp: string;
}

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
}

interface Component {
  component_id: string;
  name: string;
  part_number: string;
  category: string;
}

interface TestRun {
  id: string;
  protocol_id: string;
  protocol?: TestProtocol;
  component_id?: string;
  component?: Component;
  status: RunStatus;
  result?: CompletionResult;
  configuration: Record<string, number | string | boolean>;
  measurements: Measurement[];
  validation_results?: ValidationResult[];
  notes?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  created_by?: string;
}

const STATUS_STYLES: Record<RunStatus, { bg: string; text: string; label: string }> = {
  SETUP: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Setup' },
  IN_PROGRESS: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'In Progress' },
  COMPLETED: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
  ABORTED: { bg: 'bg-red-100', text: 'text-red-800', label: 'Aborted' },
};

const RESULT_STYLES: Record<CompletionResult, { bg: string; text: string; border: string }> = {
  PASS: { bg: 'bg-green-100', text: 'text-green-800', border: 'border-green-200' },
  PARTIAL: { bg: 'bg-yellow-100', text: 'text-yellow-800', border: 'border-yellow-200' },
  FAIL: { bg: 'bg-red-100', text: 'text-red-800', border: 'border-red-200' },
};

export default function RunDetail() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();

  const { data: run, isLoading, error } = useQuery<TestRun>({
    queryKey: ['test-run', runId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/runs/${runId}`);
      return response.data;
    },
    enabled: !!runId,
  });

  // Fetch protocol details separately if not included in run response
  const { data: protocol } = useQuery<TestProtocol>({
    queryKey: ['test-protocol', run?.protocol_id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/${run!.protocol_id}`);
      return response.data;
    },
    enabled: !!run?.protocol_id && !run?.protocol,
  });

  // Use fetched protocol if run.protocol is not populated
  const effectiveProtocol = run?.protocol || protocol;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="text-center py-12">
        <p className="text-red-600 mb-4">Error loading test run</p>
        <button
          onClick={() => navigate('/testing')}
          className="text-indigo-600 hover:text-indigo-800"
        >
          Return to Testing
        </button>
      </div>
    );
  }

  const statusStyle = STATUS_STYLES[run.status];
  const resultStyle = run.result ? RESULT_STYLES[run.result] : null;

  // Calculate duration if we have both timestamps
  const duration = run.started_at && run.completed_at
    ? Math.round((new Date(run.completed_at).getTime() - new Date(run.started_at).getTime()) / 1000)
    : null;

  const formatDuration = (seconds: number) => {
    if (seconds < 60) return `${seconds}s`;
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="h-full">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/testing')}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {effectiveProtocol?.name || 'Test Run Details'}
                </h1>
                <p className="text-sm text-gray-600 mt-1">
                  Run ID: <span className="font-mono">{run.id}</span>
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusStyle.bg} ${statusStyle.text}`}>
                {statusStyle.label}
              </span>
              {resultStyle && (
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${resultStyle.bg} ${resultStyle.text}`}>
                  {run.result}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="p-6 max-w-6xl mx-auto">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          {/* Protocol Info */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Protocol</h3>
            <p className="font-medium text-gray-900 text-lg">{effectiveProtocol?.name || 'Loading...'}</p>
            <p className="text-sm text-gray-500 mt-1">{effectiveProtocol?.category}</p>
            {effectiveProtocol?.description && (
              <p className="text-sm text-gray-600 mt-2">{effectiveProtocol.description}</p>
            )}
          </div>

          {/* Component Info */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Component</h3>
            {run.component ? (
              <>
                <p className="font-medium text-gray-900 text-lg">{run.component.name}</p>
                <p className="text-sm text-gray-500 mt-1">{run.component.part_number}</p>
                <p className="text-sm text-gray-500">{run.component.category}</p>
              </>
            ) : (
              <p className="text-gray-500 italic">Standalone test (no component)</p>
            )}
          </div>

          {/* Timing Info */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h3 className="text-sm font-semibold text-gray-500 uppercase mb-3">Timing</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="text-gray-900">{new Date(run.created_at).toLocaleString()}</span>
              </div>
              {run.started_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Started</span>
                  <span className="text-gray-900">{new Date(run.started_at).toLocaleString()}</span>
                </div>
              )}
              {run.completed_at && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Completed</span>
                  <span className="text-gray-900">{new Date(run.completed_at).toLocaleString()}</span>
                </div>
              )}
              {duration !== null && (
                <div className="flex justify-between pt-2 border-t">
                  <span className="text-gray-500">Duration</span>
                  <span className="font-medium text-gray-900">{formatDuration(duration)}</span>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Configuration */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Configuration</h2>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {effectiveProtocol?.input_schema?.map(input => {
              const value = run.configuration?.[input.name];
              return (
                <div key={input.name} className="p-3 bg-gray-50 rounded-lg">
                  <p className="text-xs text-gray-500 uppercase">{input.name}</p>
                  <p className="font-mono text-gray-900 mt-1">
                    {value !== undefined ? String(value) : '-'} {input.unit_symbol || ''}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* Measurements */}
        {run.measurements && run.measurements.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              Measurements ({run.measurements.length})
            </h2>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parameter</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Target</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recorded At</th>
                    <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200">
                  {run.measurements.map((measurement, idx) => {
                    const outputDef = effectiveProtocol?.output_schema?.find(o => o.name === measurement.parameter_name);
                    const unitDisplay = measurement.unit_symbol || outputDef?.unit_symbol || '';
                    return (
                      <tr key={measurement.id || idx}>
                        <td className="px-4 py-3 text-sm font-medium text-gray-900">
                          {measurement.parameter_name}
                        </td>
                        <td className="px-4 py-3 text-sm font-mono text-gray-900">
                          {measurement.measured_value} {unitDisplay}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {outputDef?.target !== undefined ? (
                            <>
                              {outputDef.target} {unitDisplay}
                              {outputDef.tolerance_pct && ` ±${outputDef.tolerance_pct}%`}
                            </>
                          ) : (
                            '-'
                          )}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {new Date(measurement.timestamp).toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500 max-w-xs truncate">
                          {measurement.notes || '-'}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Validation Results */}
        {run.validation_results && run.validation_results.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Validation Results</h2>
            <ValidationDisplay results={run.validation_results} showDetails />
          </div>
        )}

        {/* Notes */}
        {run.notes && (
          <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-6 mb-6">
            <h2 className="text-lg font-semibold text-yellow-800 mb-2">Notes</h2>
            <p className="text-yellow-700 whitespace-pre-wrap">{run.notes}</p>
          </div>
        )}

        {/* Procedure Reference */}
        {effectiveProtocol?.procedure && (
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">Procedure Reference</h2>
            <div className="bg-gray-50 rounded-lg p-4 text-sm text-gray-700 whitespace-pre-wrap max-h-64 overflow-y-auto">
              {effectiveProtocol.procedure}
            </div>
          </div>
        )}

        {/* Action buttons */}
        <div className="mt-8 flex gap-4">
          <button
            onClick={() => navigate('/testing')}
            className="px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition-colors"
          >
            Back to Testing
          </button>
          {run.status === 'IN_PROGRESS' && (
            <button
              onClick={() => navigate(`/testing/runs/${runId}/execute`)}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors"
            >
              Continue Execution
            </button>
          )}
          {run.protocol_id && (
            <button
              onClick={() => navigate(`/testing/protocols/${run.protocol_id}/run`)}
              className="px-4 py-2 border border-indigo-600 text-indigo-600 rounded-lg hover:bg-indigo-50 transition-colors"
            >
              Run Again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
