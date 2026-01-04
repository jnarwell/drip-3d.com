import React, { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../../services/api';
import MeasurementForm from '../../components/testing/MeasurementForm';
import ValidationDisplay from '../../components/testing/ValidationDisplay';

type RunStatus = 'SETUP' | 'IN_PROGRESS' | 'COMPLETED' | 'ABORTED';
type CompletionResult = 'PASS' | 'PARTIAL' | 'FAIL';

interface ParameterSchema {
  name: string;
  unit_id?: number;
  unit_symbol?: string;  // Denormalized unit symbol
  type?: 'number' | 'string' | 'boolean';
  required?: boolean;
  target?: number;        // Backend uses 'target' not 'target_value'
  tolerance_pct?: number; // Backend uses 'tolerance_pct' not 'tolerance_percent'
  min_value?: number;
  max_value?: number;
  description?: string;
}

interface TestProtocol {
  id: string;
  name: string;
  category: string;
  procedure?: string;        // Backend uses 'procedure' not 'procedure_text'
  equipment?: string[];      // Required equipment (read-only reference)
  setup_checklist?: string[]; // Setup steps to verify before starting
  input_schema: ParameterSchema[];
  output_schema: ParameterSchema[];
}

interface Measurement {
  id: number;
  run_id: number;
  parameter_name: string;
  measured_value: number; // Backend uses 'measured_value' not 'value'
  unit_id?: number;
  unit_symbol?: string;   // Backend uses 'unit_symbol' not 'unit'
  notes?: string;
  timestamp: string;      // Backend uses 'timestamp' not 'recorded_at'
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

interface TestRun {
  id: string;
  protocol_id: string;
  protocol?: TestProtocol;
  component_id?: string;
  component?: { name: string; part_number: string };
  status: RunStatus;
  result?: CompletionResult;
  configuration: Record<string, number | string | boolean>;
  measurements: Measurement[];
  validation_results?: ValidationResult[];
  notes?: string;
  started_at?: string;
  completed_at?: string;
  created_at: string;
}

const STATUS_STYLES: Record<RunStatus, { bg: string; text: string; label: string }> = {
  SETUP: { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Setup' },
  IN_PROGRESS: { bg: 'bg-blue-100', text: 'text-blue-800', label: 'In Progress' },
  COMPLETED: { bg: 'bg-green-100', text: 'text-green-800', label: 'Completed' },
  ABORTED: { bg: 'bg-red-100', text: 'text-red-800', label: 'Aborted' },
};

export default function RunExecution() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();

  const [showAbortConfirm, setShowAbortConfirm] = useState(false);
  const [showCompleteModal, setShowCompleteModal] = useState(false);
  const [checkedEquipment, setCheckedEquipment] = useState<Set<number>>(new Set());
  const [checkedProcedureSteps, setCheckedProcedureSteps] = useState<Set<number>>(new Set());
  const [testNotes, setTestNotes] = useState<string>('');

  // Fetch test run
  const { data: run, isLoading, error } = useQuery<TestRun>({
    queryKey: ['test-run', runId],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/runs/${runId}`);
      return response.data;
    },
    enabled: !!runId,
    refetchInterval: 5000, // Poll for updates
  });

  // Fetch protocol details separately if not included in run response
  const { data: protocol, isLoading: protocolLoading } = useQuery<TestProtocol>({
    queryKey: ['test-protocol', run?.protocol_id],
    queryFn: async () => {
      const response = await api.get(`/api/v1/test-protocols/${run!.protocol_id}`);
      return response.data;
    },
    enabled: !!run?.protocol_id && !run?.protocol,
  });

  // Use fetched protocol if run.protocol is not populated
  const effectiveProtocol = run?.protocol || protocol;
  const isProtocolLoading = !run?.protocol && protocolLoading;

  // Start run mutation
  const startRun = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/api/v1/test-protocols/runs/${runId}/start`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-run', runId] });
    },
  });

  // Add measurement mutation
  const addMeasurement = useMutation({
    mutationFn: async (data: { parameter_name: string; measured_value: number; notes?: string }) => {
      const response = await api.post(`/api/v1/test-protocols/runs/${runId}/measurements`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-run', runId] });
    },
  });

  // Complete run mutation
  const completeRun = useMutation({
    mutationFn: async (result: CompletionResult) => {
      const response = await api.post(`/api/v1/test-protocols/runs/${runId}/complete`, { result });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-run', runId] });
      queryClient.invalidateQueries({ queryKey: ['test-runs'] });
      setShowCompleteModal(false);
    },
  });

  // Abort run mutation
  const abortRun = useMutation({
    mutationFn: async () => {
      const response = await api.post(`/api/v1/test-protocols/runs/${runId}/abort`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-run', runId] });
      queryClient.invalidateQueries({ queryKey: ['test-runs'] });
      setShowAbortConfirm(false);
    },
  });

  // Save notes mutation
  const saveNotes = useMutation({
    mutationFn: async (notes: string) => {
      const response = await api.patch(`/api/v1/test-protocols/runs/${runId}`, { notes });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['test-run', runId] });
    },
  });

  // Sync testNotes with run.notes when run data loads
  React.useEffect(() => {
    if (run?.notes !== undefined && testNotes === '') {
      setTestNotes(run.notes || '');
    }
  }, [run?.notes]);

  const handleMeasurementSubmit = (data: { parameter_name: string; measured_value: number; notes?: string }) => {
    addMeasurement.mutate(data);
  };

  // Calculate suggested result based on measurements vs targets
  const getSuggestedResult = (): { result: CompletionResult; reason: string } => {
    if (!run?.measurements || !effectiveProtocol?.output_schema) {
      return { result: 'PARTIAL', reason: 'Not enough data to determine result' };
    }

    const measurements = run.measurements;
    const outputSchema = effectiveProtocol.output_schema;

    let passCount = 0;
    let failCount = 0;
    let warningCount = 0;
    let checkedCount = 0;

    for (const output of outputSchema) {
      const measurement = measurements.find(m => m.parameter_name === output.name);
      if (!measurement) continue;

      checkedCount++;
      const target = output.target;
      if (target === undefined) {
        passCount++; // No target = assume pass
        continue;
      }

      let toleranceAbs = 0;
      if (output.tolerance_pct !== undefined) {
        toleranceAbs = Math.abs(target * output.tolerance_pct / 100);
      } else {
        toleranceAbs = Math.abs(target * 0.1); // Default 10%
      }

      const error = Math.abs(measurement.measured_value - target);

      if (error <= toleranceAbs) {
        passCount++;
      } else if (error <= toleranceAbs * 1.5) {
        warningCount++;
      } else {
        failCount++;
      }
    }

    if (failCount > 0) {
      return { result: 'FAIL', reason: `${failCount} measurement(s) outside tolerance` };
    } else if (warningCount > 0 || checkedCount < outputSchema.length) {
      return { result: 'PARTIAL', reason: warningCount > 0 ? `${warningCount} measurement(s) near tolerance limit` : 'Some measurements missing' };
    } else {
      return { result: 'PASS', reason: 'All measurements within tolerance' };
    }
  };

  // Get which outputs have been recorded
  const getRecordedParameters = (): Set<string> => {
    if (!run?.measurements) return new Set();
    return new Set(run.measurements.map(m => m.parameter_name));
  };

  const recordedParams = getRecordedParameters();

  // Parse procedure text into numbered steps
  const getProcedureSteps = (): string[] => {
    if (!effectiveProtocol?.procedure) return [];
    const text = effectiveProtocol.procedure;
    // Split by numbered patterns (1., 2., etc.) or newlines
    const lines = text.split(/\n/).filter(line => line.trim());
    return lines.map(line => line.replace(/^\d+\.\s*/, '').trim()).filter(Boolean);
  };

  const procedureSteps = getProcedureSteps();

  // Check if all setup checklist items are checked
  const allSetupChecked = !effectiveProtocol?.setup_checklist?.length ||
    effectiveProtocol.setup_checklist.every((_, idx) => checkedEquipment.has(idx));

  // Toggle equipment check
  const toggleEquipment = (idx: number) => {
    setCheckedEquipment(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  // Toggle procedure step check
  const toggleProcedureStep = (idx: number) => {
    setCheckedProcedureSteps(prev => {
      const next = new Set(prev);
      if (next.has(idx)) {
        next.delete(idx);
      } else {
        next.add(idx);
      }
      return next;
    });
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error || !run) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Error loading test run</p>
          <button
            onClick={() => navigate('/testing')}
            className="text-indigo-600 hover:text-indigo-800"
          >
            Return to Testing
          </button>
        </div>
      </div>
    );
  }

  const isActive = run.status === 'SETUP' || run.status === 'IN_PROGRESS';
  const statusStyle = STATUS_STYLES[run.status];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-6 py-4">
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
                <h1 className="text-xl font-bold text-gray-900">
                  {effectiveProtocol?.name || 'Test Run'}
                </h1>
                <p className="text-sm text-gray-500">
                  {run.component?.name || 'Standalone Test'}
                  {run.component?.part_number && ` (${run.component.part_number})`}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${statusStyle.bg} ${statusStyle.text}`}>
                {statusStyle.label}
              </span>
              {run.status === 'COMPLETED' && (
                <button
                  onClick={() => navigate(`/testing/runs/${runId}`)}
                  className="px-4 py-2 text-sm font-medium text-indigo-600 hover:text-indigo-800"
                >
                  View Details
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Main Content */}
          <div className="lg:col-span-2 space-y-6">
            {/* Required Equipment (read-only reference) */}
            {run.status === 'SETUP' && effectiveProtocol?.equipment && effectiveProtocol.equipment.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Required Equipment</h2>
                <ul className="space-y-2">
                  {effectiveProtocol.equipment.map((item, idx) => (
                    <li key={idx} className="flex items-center gap-2 text-gray-700">
                      <span className="w-1.5 h-1.5 bg-gray-400 rounded-full"></span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Setup Checklist (interactive verification steps) */}
            {run.status === 'SETUP' && effectiveProtocol?.setup_checklist && effectiveProtocol.setup_checklist.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Setup Checklist</h2>
                <p className="text-sm text-gray-600 mb-4">
                  Complete all steps before starting the test
                </p>
                <div className="space-y-3">
                  {effectiveProtocol.setup_checklist.map((item, idx) => (
                    <label
                      key={idx}
                      className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        checkedEquipment.has(idx)
                          ? 'bg-green-50 border-green-200'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checkedEquipment.has(idx)}
                        onChange={() => toggleEquipment(idx)}
                        className="h-5 w-5 rounded text-green-600 focus:ring-green-500"
                      />
                      <span className={checkedEquipment.has(idx) ? 'text-green-800' : 'text-gray-700'}>
                        {item}
                      </span>
                    </label>
                  ))}
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  {checkedEquipment.size} of {effectiveProtocol.setup_checklist.length} steps verified
                </div>
              </div>
            )}

            {/* Status Actions */}
            {run.status === 'SETUP' && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h2 className="text-lg font-semibold text-gray-900">Ready to Start</h2>
                    <p className="text-sm text-gray-600">
                      {allSetupChecked
                        ? 'All setup steps verified. You can now start the test.'
                        : 'Complete the setup checklist above before starting'}
                    </p>
                  </div>
                  <button
                    onClick={() => startRun.mutate()}
                    disabled={startRun.isPending || !allSetupChecked}
                    className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                      allSetupChecked
                        ? 'bg-green-600 text-white hover:bg-green-700 disabled:opacity-50'
                        : 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    }`}
                  >
                    {startRun.isPending ? 'Starting...' : 'Start Test'}
                  </button>
                </div>
              </div>
            )}

            {/* Protocol Loading State */}
            {run.status === 'IN_PROGRESS' && isProtocolLoading && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
                  <span className="ml-3 text-gray-500">Loading protocol...</span>
                </div>
              </div>
            )}

            {/* Measurement Entry (only when in progress) */}
            {run.status === 'IN_PROGRESS' && effectiveProtocol && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Record Measurement</h2>
                <MeasurementForm
                  outputSchema={effectiveProtocol.output_schema}
                  recordedParameters={recordedParams}
                  onSubmit={handleMeasurementSubmit}
                  isSubmitting={addMeasurement.isPending}
                />
                {addMeasurement.isError && (
                  <p className="mt-2 text-sm text-red-600">
                    Failed to record measurement. Please try again.
                  </p>
                )}
              </div>
            )}

            {/* Procedure Checklist (interactive steps during test) */}
            {run.status === 'IN_PROGRESS' && procedureSteps.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Procedure Steps</h2>
                <div className="space-y-2">
                  {procedureSteps.map((step, idx) => (
                    <label
                      key={idx}
                      className={`flex items-start gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                        checkedProcedureSteps.has(idx)
                          ? 'bg-green-50 border-green-200'
                          : 'bg-gray-50 border-gray-200 hover:bg-gray-100'
                      }`}
                    >
                      <input
                        type="checkbox"
                        checked={checkedProcedureSteps.has(idx)}
                        onChange={() => toggleProcedureStep(idx)}
                        className="h-5 w-5 mt-0.5 rounded text-green-600 focus:ring-green-500 flex-shrink-0"
                      />
                      <div className="flex-1">
                        <span className="text-xs text-gray-400 font-mono mr-2">Step {idx + 1}</span>
                        <span className={checkedProcedureSteps.has(idx) ? 'text-green-800' : 'text-gray-700'}>
                          {step}
                        </span>
                      </div>
                    </label>
                  ))}
                </div>
                <div className="mt-4 text-sm text-gray-500">
                  {checkedProcedureSteps.size} of {procedureSteps.length} steps completed
                </div>
              </div>
            )}

            {/* Test Notes Section */}
            {(run.status === 'SETUP' || run.status === 'IN_PROGRESS') && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900">Test Notes</h2>
                  {saveNotes.isPending && (
                    <span className="text-xs text-gray-500">Saving...</span>
                  )}
                  {saveNotes.isSuccess && !saveNotes.isPending && (
                    <span className="text-xs text-green-600">Saved</span>
                  )}
                </div>
                <textarea
                  value={testNotes}
                  onChange={(e) => setTestNotes(e.target.value)}
                  onBlur={() => {
                    if (testNotes !== (run.notes || '')) {
                      saveNotes.mutate(testNotes);
                    }
                  }}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  placeholder="Record observations, issues, or notes during testing..."
                />
                {saveNotes.isError && (
                  <p className="mt-2 text-sm text-red-600">Failed to save notes</p>
                )}
              </div>
            )}

            {/* Expected Outputs Checklist */}
            {effectiveProtocol && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Expected Outputs</h2>
                <div className="space-y-2">
                  {effectiveProtocol.output_schema.map(output => {
                    const isRecorded = recordedParams.has(output.name);
                    return (
                      <div
                        key={output.name}
                        className={`flex items-center justify-between p-3 rounded-lg border ${
                          isRecorded
                            ? 'bg-green-50 border-green-200'
                            : 'bg-gray-50 border-gray-200'
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          {isRecorded ? (
                            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                            </svg>
                          ) : (
                            <div className="w-5 h-5 rounded-full border-2 border-gray-300" />
                          )}
                          <div>
                            <span className="font-medium text-gray-900">{output.name}</span>
                            {output.unit_symbol && (
                              <span className="text-gray-500 ml-2">({output.unit_symbol})</span>
                            )}
                          </div>
                        </div>
                        {output.target !== undefined && (
                          <span className="text-sm text-gray-500">
                            Target: {output.target} {output.unit_symbol || ''}
                            {output.tolerance_pct && ` ±${output.tolerance_pct}%`}
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Recorded Measurements Table */}
            {run.measurements && run.measurements.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Recorded Measurements</h2>
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead>
                      <tr>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Parameter</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Value</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Recorded</th>
                        <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Notes</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-200">
                      {run.measurements.map((measurement, idx) => {
                        // Look up unit from output schema if not on measurement
                        const outputDef = effectiveProtocol?.output_schema?.find(
                          o => o.name === measurement.parameter_name
                        );
                        const unitDisplay = measurement.unit_symbol || outputDef?.unit_symbol || '';
                        return (
                          <tr key={measurement.id || idx}>
                            <td className="px-4 py-3 text-sm font-medium text-gray-900">
                              {measurement.parameter_name}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900 font-mono">
                              {measurement.measured_value} {unitDisplay}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {new Date(measurement.timestamp).toLocaleTimeString()}
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
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
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Validation Results</h2>
                <ValidationDisplay results={run.validation_results} />
              </div>
            )}
          </div>

          {/* Right Column - Sidebar */}
          <div className="space-y-6">
            {/* Configuration Summary */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Configuration</h3>
              <div className="space-y-2">
                {run.configuration && Object.entries(run.configuration).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="text-gray-500">{key}</span>
                    <span className="font-mono text-gray-900">{String(value)}</span>
                  </div>
                ))}
                {!run.configuration && (
                  <p className="text-sm text-gray-400 italic">No configuration</p>
                )}
              </div>
            </div>

            {/* Procedure */}
            {effectiveProtocol?.procedure && (
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Procedure</h3>
                <div className="text-sm text-gray-600 whitespace-pre-wrap max-h-64 overflow-y-auto">
                  {effectiveProtocol.procedure}
                </div>
              </div>
            )}

            {/* Notes */}
            {run.notes && (
              <div className="bg-yellow-50 rounded-lg border border-yellow-200 p-6">
                <h3 className="text-sm font-semibold text-yellow-800 mb-2">Notes</h3>
                <p className="text-sm text-yellow-700">{run.notes}</p>
              </div>
            )}

            {/* Actions */}
            {isActive && (
              <div className="bg-white rounded-lg shadow-sm border p-6 space-y-3">
                <h3 className="text-sm font-semibold text-gray-900 mb-4">Actions</h3>

                {run.status === 'IN_PROGRESS' && (
                  <button
                    onClick={() => setShowCompleteModal(true)}
                    className="w-full px-4 py-2 bg-green-600 text-white rounded-lg font-medium hover:bg-green-700 transition-colors"
                  >
                    Complete Test
                  </button>
                )}

                <button
                  onClick={() => setShowAbortConfirm(true)}
                  className="w-full px-4 py-2 border border-red-300 text-red-600 rounded-lg font-medium hover:bg-red-50 transition-colors"
                >
                  Abort Test
                </button>
              </div>
            )}

            {/* Timestamps */}
            <div className="bg-white rounded-lg shadow-sm border p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Timeline</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">Created</span>
                  <span className="text-gray-900">
                    {new Date(run.created_at).toLocaleString()}
                  </span>
                </div>
                {run.started_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Started</span>
                    <span className="text-gray-900">
                      {new Date(run.started_at).toLocaleString()}
                    </span>
                  </div>
                )}
                {run.completed_at && (
                  <div className="flex justify-between">
                    <span className="text-gray-500">Completed</span>
                    <span className="text-gray-900">
                      {new Date(run.completed_at).toLocaleString()}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Abort Confirmation Modal */}
      {showAbortConfirm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Abort Test Run?</h3>
            <p className="text-gray-600 mb-6">
              This action cannot be undone. All recorded measurements will be preserved but the test will be marked as aborted.
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setShowAbortConfirm(false)}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
              <button
                onClick={() => abortRun.mutate()}
                disabled={abortRun.isPending}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {abortRun.isPending ? 'Aborting...' : 'Abort Test'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Complete Modal */}
      {showCompleteModal && (() => {
        const suggested = getSuggestedResult();
        return (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg shadow-xl p-6 max-w-md w-full mx-4">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Complete Test Run</h3>

              {/* Suggested result banner */}
              <div className={`p-3 rounded-lg mb-4 ${
                suggested.result === 'PASS' ? 'bg-green-50 border border-green-200' :
                suggested.result === 'FAIL' ? 'bg-red-50 border border-red-200' :
                'bg-yellow-50 border border-yellow-200'
              }`}>
                <p className="text-sm font-medium">
                  Suggested: <span className={
                    suggested.result === 'PASS' ? 'text-green-700' :
                    suggested.result === 'FAIL' ? 'text-red-700' : 'text-yellow-700'
                  }>{suggested.result}</span>
                </p>
                <p className="text-xs text-gray-600 mt-0.5">{suggested.reason}</p>
              </div>

              <p className="text-gray-600 mb-4">
                Select the overall result for this test run:
              </p>
              <div className="space-y-3 mb-6">
                <button
                  onClick={() => completeRun.mutate('PASS')}
                  disabled={completeRun.isPending}
                  className={`w-full p-4 border-2 rounded-lg text-left transition-colors ${
                    suggested.result === 'PASS'
                      ? 'border-green-400 bg-green-50 ring-2 ring-green-300'
                      : 'border-green-200 hover:border-green-400 hover:bg-green-50'
                  }`}
                >
                  <span className="font-medium text-green-800">PASS</span>
                  {suggested.result === 'PASS' && <span className="ml-2 text-xs text-green-600">(Recommended)</span>}
                  <p className="text-sm text-green-600">All measurements within tolerance</p>
                </button>
                <button
                  onClick={() => completeRun.mutate('PARTIAL')}
                  disabled={completeRun.isPending}
                  className={`w-full p-4 border-2 rounded-lg text-left transition-colors ${
                    suggested.result === 'PARTIAL'
                      ? 'border-yellow-400 bg-yellow-50 ring-2 ring-yellow-300'
                      : 'border-yellow-200 hover:border-yellow-400 hover:bg-yellow-50'
                  }`}
                >
                  <span className="font-medium text-yellow-800">PARTIAL</span>
                  {suggested.result === 'PARTIAL' && <span className="ml-2 text-xs text-yellow-600">(Recommended)</span>}
                  <p className="text-sm text-yellow-600">Some measurements outside tolerance or incomplete</p>
                </button>
                <button
                  onClick={() => completeRun.mutate('FAIL')}
                  disabled={completeRun.isPending}
                  className={`w-full p-4 border-2 rounded-lg text-left transition-colors ${
                    suggested.result === 'FAIL'
                      ? 'border-red-400 bg-red-50 ring-2 ring-red-300'
                      : 'border-red-200 hover:border-red-400 hover:bg-red-50'
                  }`}
                >
                  <span className="font-medium text-red-800">FAIL</span>
                  {suggested.result === 'FAIL' && <span className="ml-2 text-xs text-red-600">(Recommended)</span>}
                  <p className="text-sm text-red-600">Critical measurements failed or test unsuccessful</p>
                </button>
              </div>
              <button
                onClick={() => setShowCompleteModal(false)}
                className="w-full px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300"
              >
                Cancel
              </button>
            </div>
          </div>
        );
      })()}
    </div>
  );
}
