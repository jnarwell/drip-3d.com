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
    const firstName = entry.user_name.split(' ')[0];
    return firstName.charAt(0).toUpperCase() + firstName.slice(1).toLowerCase();
  }
  if (entry.user_id) {
    // user_id is email - extract name and capitalize
    const name = entry.user_id.split('@')[0];
    return name.charAt(0).toUpperCase() + name.slice(1).toLowerCase();
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
            <span className="font-mono text-gray-400">{formatDuration(entry.started_at)}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ActiveTimersBar;
