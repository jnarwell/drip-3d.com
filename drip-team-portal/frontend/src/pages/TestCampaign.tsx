import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { TestStatus } from '../types';
import type { Test } from '../types';
import TestResultForm from '../components/TestResultForm';
import TestForm from '../components/TestForm';

const TestCampaign: React.FC = () => {
  const api = useAuthenticatedApi();
  const queryClient = useQueryClient();
  const [selectedTest, setSelectedTest] = useState<Test | null>(null);
  const [showResultForm, setShowResultForm] = useState(false);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [editingTest, setEditingTest] = useState<Test | null>(null);

  const { data: tests, isLoading } = useQuery<Test[]>({
    queryKey: ['tests'],
    queryFn: async () => {
      const response = await api.get('/api/v1/tests');
      return response.data;
    },
  });

  const { data: criticalPath } = useQuery({
    queryKey: ['critical-path'],
    queryFn: async () => {
      const response = await api.get('/api/v1/tests/critical-path');
      return response.data;
    },
  });

  const createTest = useMutation({
    mutationFn: async (data: any) => {
      return await api.post('/api/v1/tests', data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] });
      setShowCreateForm(false);
    },
  });

  const updateTest = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      return await api.patch(`/api/v1/tests/${id}`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] });
      setEditingTest(null);
    },
  });

  const deleteTest = useMutation({
    mutationFn: async (testId: string) => {
      return await api.delete(`/api/v1/tests/${testId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] });
    },
  });

  const submitResult = useMutation({
    mutationFn: async (data: any) => {
      return await api.post(`/api/v1/tests/${data.test_id}/results`, data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['tests'] });
      setShowResultForm(false);
      setSelectedTest(null);
    },
  });

  const statusColors: { [key: string]: string } = {
    NOT_STARTED: 'bg-gray-100 text-gray-800',
    IN_PROGRESS: 'bg-blue-100 text-blue-800',
    COMPLETED: 'bg-green-100 text-green-800',
    BLOCKED: 'bg-red-100 text-red-800',
  };

  const getCategoryIcon = (category: string) => {
    const icons: { [key: string]: string } = {
      'Acoustic': '🔊',
      'Thermal': '🌡️',
      'Mechanical': '⚙️',
      'Electrical': '⚡',
      'Material': '🧪',
    };
    return icons[category] || '📋';
  };

  const getStatusIcon = (status: TestStatus) => {
    switch (status) {
      case TestStatus.NOT_STARTED:
        return '⚪';
      case TestStatus.IN_PROGRESS:
        return '🔵';
      case TestStatus.COMPLETED:
        return '🟢';
      case TestStatus.BLOCKED:
        return '🔴';
      default:
        return '⚪';
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Test Campaign</h1>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700"
        >
          Add Test
        </button>
      </div>

      {/* Critical Path Alert */}
      {criticalPath && criticalPath.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-sm font-medium text-yellow-800 mb-2">Critical Path Tests</h3>
          <p className="text-sm text-yellow-700">
            These tests are blocking others and should be prioritized:
          </p>
          <ul className="mt-2 text-sm text-yellow-700 list-disc list-inside">
            {criticalPath.slice(0, 3).map((test: any) => (
              <li key={test.test_id}>
                {test.test_id}: {test.name} (blocking {test.blocked_count} tests)
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Test Grid */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {tests?.map(test => (
            <div key={test.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center">
                  <span className="text-2xl mr-2">{getCategoryIcon(test.category || 'Unknown')}</span>
                  <div>
                    <h3 className="text-lg font-medium text-gray-900">{test.name}</h3>
                    <p className="text-sm text-gray-500 font-mono">{test.test_id}</p>
                  </div>
                </div>
                <select
                  value={test.status}
                  onChange={(e) => {
                    updateTest.mutate({
                      id: test.test_id,
                      data: { status: e.target.value }
                    });
                  }}
                  className={`px-2 py-1 text-xs font-medium rounded cursor-pointer ${statusColors[test.status]}`}
                >
                  <option value={TestStatus.NOT_STARTED}>NOT STARTED</option>
                  <option value={TestStatus.IN_PROGRESS}>IN PROGRESS</option>
                  <option value={TestStatus.COMPLETED}>COMPLETED</option>
                </select>
              </div>

              {test.purpose && (
                <p className="text-sm text-gray-600 mb-3">{test.purpose}</p>
              )}

              <dl className="space-y-1 text-sm text-gray-600 mb-4">
                {test.duration_hours && (
                  <div className="flex justify-between">
                    <dt>Duration:</dt>
                    <dd>{test.duration_hours} hours</dd>
                  </div>
                )}
                {test.engineer && (
                  <div className="flex justify-between">
                    <dt>Engineer:</dt>
                    <dd>{test.engineer.split('@')[0]}</dd>
                  </div>
                )}
                {test.executed_date && (
                  <div className="flex justify-between">
                    <dt>Executed:</dt>
                    <dd>{new Date(test.executed_date).toLocaleDateString()}</dd>
                  </div>
                )}
                {test.linear_issue_id && (
                  <div className="flex justify-between">
                    <dt>Linear:</dt>
                    <dd className="text-indigo-600">Connected</dd>
                  </div>
                )}
              </dl>


              {test.status === TestStatus.IN_PROGRESS && (
                <button
                  onClick={() => {
                    setSelectedTest(test);
                    setShowResultForm(true);
                  }}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded hover:bg-blue-700"
                >
                  Submit Result
                </button>
              )}

              {/* Action buttons */}
              <div className="flex gap-2 mt-2">
                <button
                  onClick={() => setEditingTest(test)}
                  className="flex-1 px-3 py-1 text-xs font-medium text-indigo-600 border border-indigo-600 rounded hover:bg-indigo-50"
                >
                  Edit
                </button>
                <button
                  onClick={() => {
                    if (confirm('Are you sure you want to delete this test?')) {
                      deleteTest.mutate(test.test_id);
                    }
                  }}
                  className="flex-1 px-3 py-1 text-xs font-medium text-red-600 border border-red-600 rounded hover:bg-red-50"
                >
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Test Result Form Modal */}
      {showResultForm && selectedTest && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Submit Test Result: {selectedTest.name}
              </h2>
              <TestResultForm
                testId={selectedTest.test_id}
                onSubmit={(data) => {
                  submitResult.mutate({
                    test_id: selectedTest.test_id,
                    ...data,
                  });
                }}
                onCancel={() => {
                  setShowResultForm(false);
                  setSelectedTest(null);
                }}
              />
            </div>
          </div>
        </div>
      )}

      {/* Create Test Modal */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Add New Test
              </h2>
              <TestForm
                onSubmit={(data) => {
                  // Generate test ID
                  const testCount = tests?.length || 0;
                  const testId = `TST-${String(testCount + 1).padStart(3, '0')}`;
                  createTest.mutate({
                    test_id: testId,
                    ...data,
                    status: TestStatus.NOT_STARTED,
                  });
                }}
                onCancel={() => setShowCreateForm(false)}
              />
            </div>
          </div>
        </div>
      )}

      {/* Edit Test Modal */}
      {editingTest && (
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <h2 className="text-lg font-medium text-gray-900 mb-4">
                Edit Test
              </h2>
              <TestForm
                initialData={editingTest}
                onSubmit={(data) => {
                  updateTest.mutate({
                    id: editingTest.test_id,
                    data,
                  });
                }}
                onCancel={() => setEditingTest(null)}
                isEdit
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TestCampaign;