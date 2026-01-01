import React, { useState, useEffect } from 'react';
import { useAllActiveTimers, TimeEntry } from '../../hooks/useTimeTracking';

function formatDuration(startedAt: string, totalBreakSeconds?: number): string {
  const startTime = new Date(startedAt).getTime();
  const now = Date.now();
  const totalSeconds = Math.floor((now - startTime) / 1000);
  const activeSeconds = totalSeconds - (totalBreakSeconds || 0);
  const seconds = Math.max(0, activeSeconds);

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function getDisplayName(entry: TimeEntry): string {
  if (entry.user_name) {
    const firstName = entry.user_name.split(' ')[0];
    return firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
  }
  if (entry.user_id) {
    const name = entry.user_id.split('@')[0];
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
  }
  return 'Someone';
}

function getTaskLabel(entry: TimeEntry): string {
  if (entry.linear_issue_title) {
    return entry.linear_issue_title;
  }
  if (entry.linear_issue_id) {
    return entry.linear_issue_id;
  }
  if (entry.description) {
    return entry.description;
  }
  if (entry.component_name) {
    return entry.component_name;
  }
  return 'Working...';
}

const ActiveTimersSidebar: React.FC = () => {
  const { data, isLoading } = useAllActiveTimers();
  const [, setTick] = useState(0);

  // Force re-render every second to update durations
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const activeEntries = data?.active_timers || [];

  return (
    <div className="bg-white rounded-lg shadow h-fit">
      <div className="px-4 py-3 border-b border-gray-200">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
          <h3 className="text-sm font-semibold text-gray-900">Active Timers</h3>
          <span className="ml-auto text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">
            {activeEntries.length}
          </span>
        </div>
      </div>

      <div className="p-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-indigo-600"></div>
          </div>
        ) : activeEntries.length === 0 ? (
          <div className="text-center py-6">
            <div className="text-gray-400 mb-2">
              <svg className="w-8 h-8 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-sm text-gray-500">No active timers</p>
            <p className="text-xs text-gray-400 mt-1">Start tracking to appear here</p>
          </div>
        ) : (
          <div className="space-y-3">
            {activeEntries.map((entry) => (
              <div
                key={entry.id}
                className="p-3 bg-gray-50 rounded-lg border border-gray-100 hover:border-indigo-200 transition-colors"
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-2 min-w-0">
                    <span className={`w-2 h-2 rounded-full flex-shrink-0 ${
                      entry.on_break
                        ? 'bg-yellow-500 animate-pulse'
                        : 'bg-green-500 animate-pulse'
                    }`}></span>
                    <span className="font-medium text-gray-900 text-sm truncate">
                      {getDisplayName(entry)}
                    </span>
                  </div>
                  <span className="font-mono text-sm text-indigo-600 flex-shrink-0">
                    {formatDuration(entry.started_at, entry.total_break_seconds)}
                  </span>
                </div>
                <div className="mt-1.5 pl-4">
                  <p className="text-xs text-gray-600 truncate" title={getTaskLabel(entry)}>
                    {getTaskLabel(entry)}
                  </p>
                  {entry.on_break && (
                    <span className="inline-block mt-1 text-xs text-yellow-700 bg-yellow-100 px-1.5 py-0.5 rounded">
                      On break
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ActiveTimersSidebar;
