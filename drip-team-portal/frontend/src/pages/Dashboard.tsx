import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { DashboardStats } from '../types';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const Dashboard: React.FC = () => {
  const api = useAuthenticatedApi();
  
  const { data: stats, isLoading, error } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/reports/dashboard-stats');
      return response.data;
    },
    refetchInterval: 30000, // Refresh every 30 seconds
    retry: 1,
    onError: (error) => {
      console.error('Failed to load dashboard stats:', error);
    },
  });

  const { data: recentActivity } = useQuery({
    queryKey: ['recent-activity'],
    queryFn: async () => {
      const response = await api.get('/api/v1/reports/recent-activity');
      return response.data;
    },
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-2">⚠️ Failed to load dashboard</div>
          <p className="text-gray-600">Please try refreshing the page or contact support.</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700"
          >
            Refresh Page
          </button>
        </div>
      </div>
    );
  }

  const statusColors: { [key: string]: string } = {
    NOT_TESTED: '#9CA3AF',
    IN_TESTING: '#3B82F6',
    VERIFIED: '#10B981',
    FAILED: '#EF4444',
  };

  const getStatusColor = (status: string): string => statusColors[status] || '#6B7280';

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
      
      {/* Overall Progress */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Validation Progress</h2>
        <div className="space-y-4">
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Components Verified</span>
              <span>{stats?.componentsVerified}/{stats?.totalComponents}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-green-500 h-2 rounded-full"
                style={{
                  width: `${((stats?.componentsVerified || 0) / (stats?.totalComponents || 1)) * 100}%`,
                }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Tests Complete</span>
              <span>{stats?.testsComplete}/{stats?.totalTests}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full"
                style={{
                  width: `${((stats?.testsComplete || 0) / (stats?.totalTests || 1)) * 100}%`,
                }}
              />
            </div>
          </div>
          
          <div>
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Physics Validation</span>
              <span>{stats?.physicsValidated ? '✓ Complete' : '✗ Incomplete'}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`${stats?.physicsValidated ? 'bg-green-500' : 'bg-red-500'} h-2 rounded-full`}
                style={{ width: stats?.physicsValidated ? '100%' : '0%' }}
              />
            </div>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Campaign Progress */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Test Campaign Progress</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats?.campaignProgress || []}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="completed" stroke="#10B981" name="Completed" />
              <Line type="monotone" dataKey="planned" stroke="#3B82F6" strokeDasharray="5 5" name="Planned" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Component Status */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Component Status</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={stats?.componentsByStatus || []}
                dataKey="count"
                nameKey="status"
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
              >
                {stats?.componentsByStatus?.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getStatusColor(entry.status)} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Critical Path and Risk Assessment */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Critical Path */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Critical Path</h2>
          <p className="text-sm text-gray-600 mb-3">Next tests required for progress</p>
          <div className="space-y-2 max-h-64 overflow-y-auto">
            {stats?.criticalPath?.map((test) => (
              <div key={test.id} className="flex items-center justify-between p-2 border rounded">
                <div>
                  <span className="font-mono text-sm">{test.test_id}</span>
                  <span className="ml-2 text-sm text-gray-600">{test.name}</span>
                </div>
                <span className={`px-2 py-1 text-xs font-medium rounded ${
                  test.blocked 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-green-100 text-green-800'
                }`}>
                  {test.blocked ? 'Blocked' : 'Ready'}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Risk Assessment */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Risk Assessment</h2>
          <div className="space-y-3 max-h-64 overflow-y-auto">
            {stats?.risks?.map((risk, index) => (
              <div key={index} className="border rounded p-3">
                <div className="flex items-start justify-between">
                  <h3 className="text-sm font-medium text-gray-900">{risk.category}</h3>
                  <span className={`px-2 py-1 text-xs font-medium rounded ${
                    risk.severity === 'high' 
                      ? 'bg-red-100 text-red-800'
                      : risk.severity === 'medium'
                      ? 'bg-yellow-100 text-yellow-800'
                      : 'bg-green-100 text-green-800'
                  }`}>
                    {risk.severity}
                  </span>
                </div>
                <p className="text-sm text-gray-600 mt-1">{risk.description}</p>
                <p className="text-sm text-gray-500 mt-2">
                  <span className="font-medium">Mitigation:</span> {risk.mitigation}
                </p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h2>
        <div className="space-y-2 max-h-64 overflow-y-auto">
          {recentActivity?.map((activity: any) => (
            <div key={activity.id} className="flex items-center justify-between py-2 border-b">
              <div className="flex-1">
                <p className="text-sm text-gray-900">{activity.action}</p>
                <p className="text-xs text-gray-500">
                  {activity.user} • {new Date(activity.timestamp).toLocaleString()}
                </p>
              </div>
              <span className="text-xs px-2 py-1 bg-gray-100 text-gray-600 rounded">
                {activity.type}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;