import React, { useMemo } from 'react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  useTimeSummary,
  useUsers,
  useProjectSummary,
  User,
  ProjectGroup,
} from '../../hooks/useTimeTracking';
import ActiveTimersBar from './ActiveTimersBar';

function formatHours(seconds: number): string {
  const hours = seconds / 3600;
  return `${hours.toFixed(1)}h`;
}

function getWeekDates() {
  const now = new Date();
  const dayOfWeek = now.getDay();
  const startOfWeek = new Date(now);
  startOfWeek.setDate(now.getDate() - dayOfWeek);
  startOfWeek.setHours(0, 0, 0, 0);

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);

  return {
    start: startOfWeek.toISOString().split('T')[0],
    end: endOfWeek.toISOString().split('T')[0],
  };
}

// Color palette for team members
const COLORS = ['#6366f1', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4'];

const TeamTimeView: React.FC = () => {
  const weekDates = useMemo(() => getWeekDates(), []);

  // Fetch team summary data (all users)
  const { data: userSummary, isLoading: usersLoading } = useTimeSummary(
    {
      start_date: weekDates.start,
      end_date: weekDates.end,
      group_by: 'user',
    },
    false // myEntriesOnly = false for team view
  );

  // Fetch user list for color mapping
  const { data: users } = useUsers();

  // Fetch project summary with user breakdown
  const { data: projectSummary, isLoading: projectsLoading } = useProjectSummary({
    start_date: weekDates.start,
    end_date: weekDates.end,
  });

  // Create user color map
  const userColorMap = useMemo(() => {
    const map: Record<string, string> = {};
    users?.forEach((user: User, i: number) => {
      map[user.email] = COLORS[i % COLORS.length];
    });
    return map;
  }, [users]);

  // Transform user summary for bar chart
  const userChartData = useMemo(() => {
    if (!userSummary?.groups) return [];
    return userSummary.groups.map((group) => ({
      name: group.name || group.key.split('@')[0],
      hours: Number((group.total_seconds / 3600).toFixed(1)),
      entries: group.entry_count,
    }));
  }, [userSummary]);

  // Transform project summary for bar chart
  const projectChartData = useMemo(() => {
    if (!projectSummary?.groups) return [];

    return projectSummary.groups.slice(0, 10).map((project: ProjectGroup) => ({
      name: project.project_name,
      hours: Math.round(project.total_seconds / 3600 * 10) / 10,
      issues: project.issue_count,
    }));
  }, [projectSummary]);

  if (usersLoading || projectsLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Active Timers */}
      <ActiveTimersBar />

      {/* Team Hours This Week */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Team Hours This Week
        </h2>
        {userChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={userChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="h" />
              <YAxis type="category" dataKey="name" width={100} />
              <Tooltip
                formatter={(value: number) => [`${value}h`, 'Hours']}
                labelFormatter={(label) => `${label}`}
              />
              <Bar dataKey="hours" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No time entries this week
          </div>
        )}
      </div>

      {/* Time by Project */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">
          Time by Project (Top 10)
        </h2>
        {projectChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={projectChartData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" unit="h" />
              <YAxis type="category" dataKey="name" width={150} />
              <Tooltip
                formatter={(value: number, name: string) => [
                  name === 'hours' ? `${value}h` : `${value} issues`,
                  name === 'hours' ? 'Hours' : 'Issues'
                ]}
              />
              <Bar dataKey="hours" fill="#6366f1" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        ) : (
          <div className="text-center py-8 text-gray-500">
            No project data available
          </div>
        )}
      </div>

      {/* Team Summary Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b">
          <h2 className="text-lg font-semibold text-gray-900">Team Summary</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Team Member
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Hours
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Entries
                </th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg/Entry
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {userSummary?.groups?.map((group) => (
                <tr key={group.key}>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div
                        className="w-3 h-3 rounded-full mr-3"
                        style={{ backgroundColor: userColorMap[group.key] || '#6366f1' }}
                      />
                      <span className="text-sm font-medium text-gray-900">
                        {group.name || group.key.split('@')[0]}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900">
                    {formatHours(group.total_seconds)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {group.entry_count}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-500">
                    {group.entry_count > 0
                      ? formatHours(group.total_seconds / group.entry_count)
                      : '-'}
                  </td>
                </tr>
              ))}
              {(!userSummary?.groups || userSummary.groups.length === 0) && (
                <tr>
                  <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                    No team data available for this week
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default TeamTimeView;
