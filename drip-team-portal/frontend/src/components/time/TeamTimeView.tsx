import { useState } from 'react';
import { useTimeSummary, useProjectSummary, useTimeEntries, useUsers } from '../../hooks/useTimeTracking';
import ActiveTimersSidebar from './ActiveTimersSidebar';
import TeamStatsRow from './TeamStatsRow';
import ProjectBreakdown from './ProjectBreakdown';
import IssueBreakdown from './IssueBreakdown';
import RecentTeamEntries from './RecentTeamEntries';
import DateRangeSelector, { DateRange } from './DateRangeSelector';

function getWeekStart() {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now);
  monday.setDate(diff);
  monday.setHours(0, 0, 0, 0);
  return monday.toISOString().split('T')[0];
}

function getToday() {
  return new Date().toISOString().split('T')[0];
}

export default function TeamTimeView() {
  const [dateRange, setDateRange] = useState<DateRange>({
    start_date: getWeekStart(),
    end_date: getToday(),
    label: 'Week'
  });

  const { data: users } = useUsers();
  const { data: userSummary, isLoading } = useTimeSummary(
    { start_date: dateRange.start_date, end_date: dateRange.end_date, group_by: 'user' },
    false
  );
  const { data: projectSummary } = useProjectSummary({
    start_date: dateRange.start_date,
    end_date: dateRange.end_date
  });
  const { data: issueSummary } = useTimeSummary(
    { start_date: dateRange.start_date, end_date: dateRange.end_date, group_by: 'linear_issue' },
    false
  );
  const { data: entries } = useTimeEntries(
    { start_date: dateRange.start_date, end_date: dateRange.end_date },
    false
  );

  const allUsers = users || [];
  const groups = userSummary?.groups || [];
  const totalSeconds = groups.reduce((sum, g) => sum + g.total_seconds, 0);
  const totalEntries = groups.reduce((sum, g) => sum + g.entry_count, 0);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="flex gap-6">
      {/* LEFT: Active Timers Sidebar */}
      <div className="w-64 flex-shrink-0">
        <div className="sticky top-6">
          <ActiveTimersSidebar />
        </div>
      </div>

      {/* RIGHT: Main content */}
      <div className="flex-1 space-y-4 min-w-0">
        {/* Header row */}
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold text-gray-900">Team Overview</h2>
          <DateRangeSelector value={dateRange} onChange={setDateRange} />
        </div>

        {/* Stats row */}
        <TeamStatsRow
          totalSeconds={totalSeconds}
          totalEntries={totalEntries}
          activeMembers={groups.length}
          totalMembers={allUsers.length}
        />

        {/* Two column: Project + Issue */}
        <div className="grid grid-cols-2 gap-4">
          <ProjectBreakdown
            groups={projectSummary?.groups || []}
            totalSeconds={totalSeconds}
          />
          <IssueBreakdown
            groups={issueSummary?.groups || []}
            totalSeconds={totalSeconds}
          />
        </div>

        {/* Recent entries */}
        <RecentTeamEntries entries={entries?.entries || []} />
      </div>
    </div>
  );
}
