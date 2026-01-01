import React, { useState } from 'react';
import { useTimeEntries, useDeleteTimeEntry, TimeEntry } from '../../hooks/useTimeTracking';

function formatDuration(seconds: number | null): string {
  if (seconds === null) return '--:--';

  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
}

function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
  });
}

function formatTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
}

function getDateKey(dateString: string): string {
  const date = new Date(dateString);
  return date.toISOString().split('T')[0];
}

interface TimeEntryListProps {
  filters?: {
    start_date?: string;
    end_date?: string;
    limit?: number;
  };
}

const TimeEntryList: React.FC<TimeEntryListProps> = ({ filters = {} }) => {
  const { data, isLoading, error } = useTimeEntries({ ...filters, limit: filters.limit || 50 });
  const deleteEntry = useDeleteTimeEntry();
  const [deleteConfirmId, setDeleteConfirmId] = useState<number | null>(null);

  const handleDelete = async (entryId: number) => {
    try {
      await deleteEntry.mutateAsync(entryId);
      setDeleteConfirmId(null);
    } catch (error) {
      console.error('Failed to delete entry:', error);
    }
  };

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center text-red-600">
          Failed to load time entries
        </div>
      </div>
    );
  }

  const entries = data?.entries || [];

  if (entries.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-8">
          <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No time entries</h3>
          <p className="mt-1 text-sm text-gray-500">Start tracking time to see entries here.</p>
        </div>
      </div>
    );
  }

  // Group entries by date
  const groupedEntries: { [key: string]: TimeEntry[] } = {};
  entries.forEach((entry) => {
    const dateKey = getDateKey(entry.started_at);
    if (!groupedEntries[dateKey]) {
      groupedEntries[dateKey] = [];
    }
    groupedEntries[dateKey].push(entry);
  });

  // Sort date keys in descending order
  const sortedDateKeys = Object.keys(groupedEntries).sort((a, b) => b.localeCompare(a));

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Time Entries</h2>
      </div>
      <div className="divide-y divide-gray-100">
        {sortedDateKeys.map((dateKey) => (
          <div key={dateKey}>
            {/* Date header */}
            <div className="px-6 py-2 bg-gray-50">
              <h3 className="text-sm font-medium text-gray-700">
                {formatDate(groupedEntries[dateKey][0].started_at)}
              </h3>
            </div>
            {/* Entries for this date */}
            {groupedEntries[dateKey].map((entry) => (
              <div
                key={entry.id}
                className="px-6 py-3 hover:bg-gray-50 flex items-center justify-between"
              >
                <div className="flex items-center gap-4 min-w-0 flex-1">
                  {/* Time range */}
                  <div className="text-sm text-gray-500 whitespace-nowrap">
                    {formatTime(entry.started_at)}
                    {entry.stopped_at && (
                      <>
                        <span className="mx-1">-</span>
                        {formatTime(entry.stopped_at)}
                      </>
                    )}
                  </div>

                  {/* Duration */}
                  <div className="font-mono text-sm font-medium text-gray-900 whitespace-nowrap">
                    {formatDuration(entry.duration_seconds)}
                  </div>

                  {/* Categorization */}
                  <div className="min-w-0 flex-1">
                    {entry.linear_issue_id ? (
                      <div className="flex items-center gap-2">
                        <span className="font-mono text-sm font-medium text-indigo-600">
                          {entry.linear_issue_id}
                        </span>
                        {entry.linear_issue_title && (
                          <span className="text-sm text-gray-600 truncate">
                            {entry.linear_issue_title}
                          </span>
                        )}
                      </div>
                    ) : entry.description ? (
                      <span className="text-sm text-gray-600 truncate block">
                        {entry.description}
                      </span>
                    ) : entry.is_uncategorized ? (
                      <span className="text-sm text-gray-400 italic">Uncategorized</span>
                    ) : (
                      <span className="text-sm text-gray-400">—</span>
                    )}
                  </div>

                  {/* Component */}
                  {entry.component_name && (
                    <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded">
                      {entry.component_name}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 ml-4">
                  {deleteConfirmId === entry.id ? (
                    <>
                      <button
                        onClick={() => handleDelete(entry.id)}
                        disabled={deleteEntry.isPending}
                        className="text-xs text-red-600 hover:text-red-800 font-medium"
                      >
                        {deleteEntry.isPending ? 'Deleting...' : 'Confirm'}
                      </button>
                      <button
                        onClick={() => setDeleteConfirmId(null)}
                        className="text-xs text-gray-500 hover:text-gray-700"
                      >
                        Cancel
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setDeleteConfirmId(entry.id)}
                      className="text-gray-400 hover:text-red-600 transition-colors"
                      title="Delete entry"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
};

export default TimeEntryList;
