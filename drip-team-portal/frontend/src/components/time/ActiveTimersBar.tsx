import React, { useState, useEffect } from 'react';
import { useAllActiveTimers, TimeEntry } from '../../hooks/useTimeTracking';

function formatDuration(startedAt: string): string {
  const startTime = new Date(startedAt).getTime();
  const now = Date.now();
  const seconds = Math.floor((now - startTime) / 1000);

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
}

function getDisplayName(entry: TimeEntry): string {
  if (entry.user_name) {
    return entry.user_name.split(' ')[0]; // First name only
  }
  if (entry.user_id) {
    // user_id is email in this system
    return entry.user_id.split('@')[0];
  }
  return 'Someone';
}

const ActiveTimersBar: React.FC = () => {
  const { data, isLoading } = useAllActiveTimers();
  const [, setTick] = useState(0);

  // Force re-render every second to update durations
  useEffect(() => {
    const interval = setInterval(() => {
      setTick((t) => t + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  if (isLoading) {
    return null; // Don't show anything while loading
  }

  const activeEntries = data?.active_timers || [];

  if (activeEntries.length === 0) {
    return null; // Don't show bar if no one is tracking
  }

  return (
    <div className="bg-indigo-50 border border-indigo-100 rounded-lg px-4 py-2 mb-4">
      <div className="flex items-center gap-4 flex-wrap">
        <span className="text-sm font-medium text-indigo-700">Active Timers:</span>
        {activeEntries.map((entry) => (
          <div
            key={entry.id}
            className="flex items-center gap-2 text-sm"
          >
            <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
            <span className="font-medium text-gray-700">{getDisplayName(entry)}</span>
            <span className="font-mono text-indigo-600">{formatDuration(entry.started_at)}</span>
            {entry.linear_issue_id && (
              <span className="text-gray-500">{entry.linear_issue_id}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActiveTimersBar;
