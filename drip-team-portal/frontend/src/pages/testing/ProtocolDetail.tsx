import React from 'react';
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import type { TestProtocolDetail, ProtocolStats, TestRunStatus, TestResultStatus } from '../../types';

const RESULT_COLORS: Record<string, string> = {
  PASS: 'bg-green-100 text-green-800',
  FAIL: 'bg-red-100 text-red-800',
  PARTIAL: 'bg-yellow-100 text-yellow-800',
};

const STATUS_COLORS: Record<string, string> = {
  SETUP: 'bg-gray-100 text-gray-800',
  IN_PROGRESS: 'bg-blue-100 text-blue-800',
  COMPLETED: 'bg-green-100 text-green-800',
  ABORTED: 'bg-red-100 text-red-800',
};

const ProtocolDetail: React.FC = () => {
  const { protocolId } = useParams<{ protocolId: string }>();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();
  // Fetch protocol details
  const { data: protocol, isLoading, error } = useQuery<TestProtocolDetail>({
    queryKey: ['test-protocol', protocolId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/${protocolId}`);
      return response.data;
    },
    enabled: !!protocolId,
  });

  // Fetch protocol stats
  const { data: stats } = useQuery<ProtocolStats>({
    queryKey: ['test-protocol-stats', protocolId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/${protocolId}/stats`);
      return response.data;
    },
    enabled: !!protocolId,
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !protocol) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error loading protocol</p>
        <Link to="/testing" className="text-indigo-600 hover:underline mt-2 inline-block">
          Back to Testing
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <div className="flex items-start justify-between">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <Link
                to="/testing"
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">{protocol.name}</h1>
              {!protocol.is_active && (
                <span className="px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-600 rounded">
                  Inactive
                </span>
              )}
            </div>
            {protocol.description && (
              <p className="text-gray-600 mt-1">{protocol.description}</p>
            )}
            <div className="flex gap-3 mt-3 text-sm text-gray-500">
              {protocol.category && (
                <span className="px-2 py-0.5 bg-purple-100 text-purple-800 rounded text-xs font-medium">
                  {protocol.category}
                </span>
              )}
              <span>Version {protocol.version}</span>
              <span>Created by {protocol.created_by || 'Unknown'}</span>
              {protocol.model_name && (
                <span>Model: {protocol.model_name}</span>
              )}
            </div>
          </div>
          <div className="flex gap-2">
            <Link
              to={`/testing/protocols/${protocolId}/edit`}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
            >
              Edit
            </Link>
            <button
              onClick={() => navigate(`/testing/protocols/${protocolId}/run`)}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700"
            >
              Run Test
            </button>
          </div>
        </div>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="text-sm text-gray-500">Total Runs</div>
            <div className="text-2xl font-bold text-gray-900">{stats.total_runs}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="text-sm text-gray-500">Pass Rate</div>
            <div className="text-2xl font-bold text-green-600">
              {(stats.pass_rate * 100).toFixed(1)}%
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="text-sm text-gray-500">Passed</div>
            <div className="text-2xl font-bold text-green-600">{stats.passed}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm border p-4">
            <div className="text-sm text-gray-500">Failed</div>
            <div className="text-2xl font-bold text-red-600">{stats.failed}</div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Input Schema */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Input Parameters</h2>
            </div>
            <div className="p-4">
              {protocol.input_schema?.length ? (
                <div className="space-y-2">
                  {protocol.input_schema.map((input, idx) => (
                    <div key={idx} className="flex items-center justify-between py-2 border-b last:border-0">
                      <div>
                        <span className="font-medium text-gray-900">{input.name}</span>
                        {input.required && (
                          <span className="ml-2 text-xs text-red-500">Required</span>
                        )}
                        {input.description && (
                          <p className="text-sm text-gray-500">{input.description}</p>
                        )}
                      </div>
                      <div className="text-sm text-gray-500">
                        {input.default_value !== undefined && (
                          <span>Default: {input.default_value}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No input parameters defined</p>
              )}
            </div>
          </div>

          {/* Output Schema */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Output Parameters</h2>
            </div>
            <div className="p-4">
              {protocol.output_schema?.length ? (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-500 border-b">
                      <th className="pb-2 font-medium">Parameter</th>
                      <th className="pb-2 font-medium">Target</th>
                      <th className="pb-2 font-medium">Tolerance</th>
                      <th className="pb-2 font-medium">Min/Max</th>
                    </tr>
                  </thead>
                  <tbody>
                    {protocol.output_schema.map((output, idx) => (
                      <tr key={idx} className="border-b last:border-0">
                        <td className="py-2">
                          <span className="font-medium text-gray-900">{output.name}</span>
                          {output.description && (
                            <p className="text-xs text-gray-500">{output.description}</p>
                          )}
                        </td>
                        <td className="py-2 text-gray-600">
                          {output.target !== undefined ? output.target : '-'}
                        </td>
                        <td className="py-2 text-gray-600">
                          {output.tolerance_pct !== undefined ? `±${output.tolerance_pct}%` : '-'}
                        </td>
                        <td className="py-2 text-gray-600">
                          {output.min_value !== undefined || output.max_value !== undefined
                            ? `${output.min_value ?? '-'} / ${output.max_value ?? '-'}`
                            : '-'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p className="text-gray-500 text-sm">No output parameters defined</p>
              )}
            </div>
          </div>

          {/* Procedure */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Procedure</h2>
            </div>
            <div className="p-4">
              {protocol.procedure ? (
                <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-700">
                  {protocol.procedure}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No procedure documented</p>
              )}
            </div>
          </div>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Recent Runs */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Recent Runs</h2>
              <Link
                to={`/testing/protocols/${protocolId}/run`}
                className="text-sm text-indigo-600 hover:underline"
              >
                Run new test
              </Link>
            </div>
            <div className="p-4">
              {protocol.recent_runs?.length ? (
                <div className="space-y-3">
                  {protocol.recent_runs.map((run) => (
                    <Link
                      key={run.id}
                      to={`/testing/runs/${run.id}`}
                      className="block p-3 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-medium text-gray-900">
                          Run #{run.run_number || run.id}
                        </span>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded ${
                          run.result ? RESULT_COLORS[run.result] : STATUS_COLORS[run.status]
                        }`}>
                          {run.result || run.status}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {run.operator && <span>{run.operator} • </span>}
                        {run.started_at && (
                          <span>{new Date(run.started_at).toLocaleDateString()}</span>
                        )}
                      </div>
                    </Link>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-sm">No runs yet</p>
              )}
            </div>
          </div>

          {/* Equipment */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Equipment</h2>
            </div>
            <div className="p-4">
              {protocol.equipment?.length ? (
                <ul className="space-y-2">
                  {protocol.equipment.map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-sm text-gray-700">
                      <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      {item}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500 text-sm">No equipment listed</p>
              )}
            </div>
          </div>

          {/* Metadata */}
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="px-4 py-3 border-b">
              <h2 className="text-lg font-semibold text-gray-900">Metadata</h2>
            </div>
            <div className="p-4 space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">Created</span>
                <span className="text-gray-900">
                  {new Date(protocol.created_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Updated</span>
                <span className="text-gray-900">
                  {new Date(protocol.updated_at).toLocaleDateString()}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Version</span>
                <span className="text-gray-900">{protocol.version}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Status</span>
                <span className={protocol.is_active ? 'text-green-600' : 'text-gray-500'}>
                  {protocol.is_active ? 'Active' : 'Inactive'}
                </span>
              </div>
              {stats?.avg_duration_minutes && (
                <div className="flex justify-between">
                  <span className="text-gray-500">Avg Duration</span>
                  <span className="text-gray-900">
                    {stats.avg_duration_minutes.toFixed(1)} min
                  </span>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProtocolDetail;
