import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useAuthenticatedApi } from '../services/api';
import { useTimeSummary, TimeSummaryGroup } from '../hooks/useTimeTracking';
import DateRangeSelector, { DateRange } from '../components/time/DateRangeSelector';
import { DashboardStats, ActivityEntry, ResourceStats } from '../types';
import FeedbackTriage from '../components/feedback/FeedbackTriage';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

// Helper to format date as YYYY-MM-DD
function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

function getMonthStart(): string {
  const now = new Date();
  return formatDate(new Date(now.getFullYear(), now.getMonth(), 1));
}

function getToday(): string {
  return formatDate(new Date());
}

// Format seconds to hours and minutes display
function formatHoursMinutes(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (hours === 0) return `${mins}m`;
  return `${hours}h ${mins}m`;
}

// Format total hours as decimal
function formatHours(seconds: number): string {
  return (seconds / 3600).toFixed(1);
}

// Status colors matching Dashboard
const statusColors: Record<string, string> = {
  NOT_TESTED: '#9CA3AF',
  IN_TESTING: '#3B82F6',
  VERIFIED: '#10B981',
  FAILED: '#EF4444',
};

const getStatusColor = (status: string): string => statusColors[status] || '#6B7280';

// Resource type colors
const resourceTypeColors: Record<string, string> = {
  pdf: '#EF4444',
  spreadsheet: '#10B981',
  document: '#3B82F6',
  image: '#F59E0B',
  video: '#8B5CF6',
  link: '#6366F1',
  other: '#6B7280',
};

interface StatCardProps {
  title: string;
  value: number | string;
  subtitle?: string;
  color?: 'default' | 'green' | 'blue' | 'red' | 'yellow';
}

const StatCard: React.FC<StatCardProps> = ({ title, value, subtitle, color = 'default' }) => {
  const colorClasses = {
    default: 'text-gray-900',
    green: 'text-green-600',
    blue: 'text-blue-600',
    red: 'text-red-600',
    yellow: 'text-yellow-600',
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="text-sm font-medium text-gray-500">{title}</div>
      <div className={`text-3xl font-bold mt-1 ${colorClasses[color]}`}>{value}</div>
      {subtitle && <div className="text-sm text-gray-400 mt-1">{subtitle}</div>}
    </div>
  );
};

interface ActivityRowProps {
  activity: ActivityEntry;
}

const ActivityRow: React.FC<ActivityRowProps> = ({ activity }) => {
  const actionColors: Record<string, string> = {
    created: 'bg-green-100 text-green-800',
    updated: 'bg-blue-100 text-blue-800',
    deleted: 'bg-red-100 text-red-800',
  };

  const typeIcons: Record<string, string> = {
    component: 'C',
    test: 'T',
    protocol: 'P',
    resource: 'R',
    time_entry: 'H',
  };

  return (
    <div className="flex items-center gap-3 py-2 border-b border-gray-100 last:border-0">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center text-sm font-medium text-gray-600">
        {typeIcons[activity.type] || activity.type.charAt(0).toUpperCase()}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm text-gray-900 truncate">{activity.action}</p>
        <p className="text-xs text-gray-500">
          {activity.user.split('@')[0]} · {new Date(activity.timestamp).toLocaleString()}
        </p>
      </div>
      <span className={`text-xs px-2 py-1 rounded ${actionColors[activity.action] || 'bg-gray-100 text-gray-600'}`}>
        {activity.type}
      </span>
    </div>
  );
};

const Reports: React.FC = () => {
  const api = useAuthenticatedApi();
  const [downloading, setDownloading] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<DateRange>({
    start_date: getMonthStart(),
    end_date: getToday(),
    label: 'Month',
  });

  // Dashboard stats query
  const {
    data: stats,
    isLoading: statsLoading,
    error: statsError,
  } = useQuery<DashboardStats>({
    queryKey: ['dashboard-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/reports/dashboard-stats');
      return response.data;
    },
    refetchInterval: 60000,
  });

  // Time summary by user (team-wide, not filtered to current user)
  const { data: timeSummary, isLoading: timeLoading } = useTimeSummary(
    {
      start_date: dateRange.start_date,
      end_date: dateRange.end_date,
      group_by: 'user',
    },
    false // myEntriesOnly = false to get all users
  );

  // Recent activity
  const { data: activity } = useQuery<ActivityEntry[]>({
    queryKey: ['recent-activity', 10],
    queryFn: async () => {
      const response = await api.get('/api/v1/reports/recent-activity?limit=10');
      return response.data;
    },
  });

  // Resource stats (may not be available if Instance A hasn't built it yet)
  const { data: resourceStats } = useQuery<ResourceStats>({
    queryKey: ['resource-stats'],
    queryFn: async () => {
      const response = await api.get('/api/v1/reports/resource-stats');
      return response.data;
    },
    retry: false, // Don't retry if endpoint doesn't exist yet
  });

  const downloadReport = async (format: 'pdf' | 'excel') => {
    setDownloading(format);
    try {
      const response = await api.get('/api/v1/reports/validation-report', {
        params: {
          format,
          start_date: dateRange.start_date,
          end_date: dateRange.end_date,
        },
        responseType: 'blob',
      });

      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `drip_validation_report_${dateRange.start_date}_${dateRange.end_date}.${format === 'excel' ? 'xlsx' : 'pdf'}`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
    } finally {
      setDownloading(null);
    }
  };

  // Calculate total hours from time summary
  const totalSeconds = timeSummary?.groups?.reduce((sum, g) => sum + g.total_seconds, 0) || 0;

  // Prepare time data for bar chart (convert seconds to hours)
  const timeChartData = timeSummary?.groups?.map((g: TimeSummaryGroup) => ({
    name: g.name || g.key.split('@')[0],
    hours: parseFloat((g.total_seconds / 3600).toFixed(1)),
  })) || [];

  // Loading state
  if (statsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  // Error state
  if (statsError) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-center">
          <div className="text-red-600 text-xl mb-2">Failed to load reports</div>
          <p className="text-gray-600">Please try refreshing the page.</p>
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

  return (
    <div className="space-y-6">
      {/* Header with Date Range Selector */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Reports</h1>
        <DateRangeSelector value={dateRange} onChange={setDateRange} />
      </div>

      {/* Stats Overview Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard
          title="Components"
          value={stats?.totalComponents || 0}
          subtitle={`${stats?.componentsFailed || 0} failed`}
        />
        <StatCard
          title="Verified"
          value={stats?.componentsVerified || 0}
          color="green"
          subtitle={`${stats?.totalComponents ? Math.round((stats.componentsVerified / stats.totalComponents) * 100) : 0}% complete`}
        />
        <StatCard
          title="Tests Complete"
          value={stats?.testsComplete || 0}
          color="blue"
          subtitle={`of ${stats?.totalTests || 0} total`}
        />
        <StatCard
          title="Hours Logged"
          value={formatHours(totalSeconds)}
          subtitle={formatHoursMinutes(totalSeconds)}
        />
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Component Status Pie Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Component Status</h3>
          <ResponsiveContainer width="100%" height={250}>
            <PieChart>
              <Pie
                data={stats?.componentsByStatus || []}
                dataKey="count"
                nameKey="status"
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                label={({ status, count }) => `${status}: ${count}`}
                labelLine={false}
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

        {/* Time by User Bar Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Hours by Team Member</h3>
          {timeLoading ? (
            <div className="h-[250px] flex items-center justify-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
            </div>
          ) : timeChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={timeChartData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" unit="h" />
                <YAxis dataKey="name" type="category" width={80} tick={{ fontSize: 12 }} />
                <Tooltip formatter={(value) => [`${value}h`, 'Hours']} />
                <Bar dataKey="hours" fill="#6366F1" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-[250px] flex items-center justify-center text-gray-500">
              No time entries for this period
            </div>
          )}
        </div>
      </div>

      {/* Campaign Progress Line Chart */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Test Campaign Progress</h3>
        {stats?.campaignProgress && stats.campaignProgress.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={stats.campaignProgress}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                dataKey="date"
                tick={{ fontSize: 12 }}
                tickFormatter={(date) => new Date(date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
              />
              <YAxis />
              <Tooltip
                labelFormatter={(date) => new Date(date).toLocaleDateString()}
                formatter={(value, name) => [value, name === 'completed' ? 'Completed' : 'Planned']}
              />
              <Legend />
              <Line
                type="monotone"
                dataKey="completed"
                stroke="#10B981"
                strokeWidth={2}
                name="Completed"
                dot={{ r: 3 }}
              />
              <Line
                type="monotone"
                dataKey="planned"
                stroke="#3B82F6"
                strokeWidth={2}
                strokeDasharray="5 5"
                name="Planned"
                dot={{ r: 3 }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="h-[300px] flex items-center justify-center text-gray-500">
            No campaign progress data available
          </div>
        )}
      </div>

      {/* Activity Feed + Resource Stats */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Activity */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Recent Activity</h3>
          <div className="space-y-1 max-h-80 overflow-y-auto">
            {activity && activity.length > 0 ? (
              activity.map((item) => <ActivityRow key={item.id} activity={item} />)
            ) : (
              <div className="text-gray-500 text-sm py-4 text-center">No recent activity</div>
            )}
          </div>
        </div>

        {/* Resource Overview */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Resources</h3>
          {resourceStats ? (
            <div className="space-y-4">
              {/* Summary stats */}
              <div className="grid grid-cols-3 gap-4 mb-4">
                <div className="text-center p-3 bg-gray-50 rounded-lg">
                  <div className="text-2xl font-bold text-gray-900">{resourceStats.total_count}</div>
                  <div className="text-xs text-gray-500">Total</div>
                </div>
                <div className="text-center p-3 bg-yellow-50 rounded-lg">
                  <div className="text-2xl font-bold text-yellow-600">{resourceStats.starred_count}</div>
                  <div className="text-xs text-gray-500">Starred</div>
                </div>
                <div className="text-center p-3 bg-blue-50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{resourceStats.recent_7d_count}</div>
                  <div className="text-xs text-gray-500">Last 7 days</div>
                </div>
              </div>

              {/* By type breakdown */}
              <div>
                <div className="text-sm font-medium text-gray-700 mb-2">By Type</div>
                <div className="space-y-2">
                  {resourceStats.by_type.map((item) => (
                    <div key={item.type} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <div
                          className="w-3 h-3 rounded-full"
                          style={{ backgroundColor: resourceTypeColors[item.type] || '#6B7280' }}
                        />
                        <span className="text-sm text-gray-600 capitalize">{item.type}</span>
                      </div>
                      <span className="text-sm font-medium text-gray-900">{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-gray-500 text-sm py-4 text-center">
              Resource statistics not available
            </div>
          )}
        </div>
      </div>

      {/* Feedback Triage Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Feedback Triage</h3>
        <FeedbackTriage />
      </div>

      {/* Export Section */}
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Export Reports</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* PDF Report */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900">Validation Report (PDF)</h4>
                <p className="text-xs text-gray-500 mt-1">
                  Comprehensive validation report with component status, test results, and physics validation
                </p>
                <button
                  onClick={() => downloadReport('pdf')}
                  disabled={downloading !== null}
                  className="mt-3 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:bg-gray-400"
                >
                  {downloading === 'pdf' ? 'Generating...' : 'Download PDF'}
                </button>
              </div>
            </div>
          </div>

          {/* Excel Report */}
          <div className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <div className="flex-shrink-0 w-10 h-10 rounded-lg bg-green-100 flex items-center justify-center">
                <svg className="w-5 h-5 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div className="flex-1">
                <h4 className="text-sm font-medium text-gray-900">Test Campaign Data (Excel)</h4>
                <p className="text-xs text-gray-500 mt-1">
                  Detailed Excel workbook with all components, tests, results, and physics data
                </p>
                <button
                  onClick={() => downloadReport('excel')}
                  disabled={downloading !== null}
                  className="mt-3 px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded hover:bg-indigo-700 disabled:bg-gray-400"
                >
                  {downloading === 'excel' ? 'Generating...' : 'Download Excel'}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Export Notice */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                clipRule="evenodd"
              />
            </svg>
          </div>
          <div className="ml-3">
            <p className="text-sm text-blue-700">
              Reports are generated in real-time based on current data. The date range filter applies to time
              tracking data and export reports.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Reports;
