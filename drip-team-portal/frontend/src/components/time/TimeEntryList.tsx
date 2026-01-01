import React, { useState } from 'react';
import { useTimeEntries, useDeleteTimeEntry, TimeEntry, TimeBreak, EditHistoryEntry } from '../../hooks/useTimeTracking';
import EditEntryModal from './EditEntryModal';

function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '--:--';

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

function formatTime(dateString: string | null): string {
  if (!dateString) return '--:--';
  const date = new Date(dateString);
  return date.toLocaleTimeString('en-US', {
    hour: 'numeric',
    minute: '2-digit',
  });
}

function formatDateTime(dateString: string): string {
  const date = new Date(dateString);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
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
  const [expandedIds, setExpandedIds] = useState<Set<number>>(new Set());
  const [editingEntry, setEditingEntry] = useState<TimeEntry | null>(null);

  const toggleExpand = (id: number) => {
    setExpandedIds(prev => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  };

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
    <>
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
              {groupedEntries[dateKey].map((entry) => {
                const isExpanded = expandedIds.has(entry.id);
                const hasDetails = (entry.breaks && entry.breaks.length > 0) ||
                                   (entry.edit_history && entry.edit_history.length > 0);

                return (
                  <div key={entry.id} className="border-b border-gray-100 last:border-b-0">
                    {/* Main row */}
                    <div
                      className={`px-6 py-3 flex items-center justify-between ${
                        hasDetails ? 'cursor-pointer hover:bg-gray-50' : ''
                      }`}
                      onClick={() => hasDetails && toggleExpand(entry.id)}
                    >
                      <div className="flex items-center gap-4 min-w-0 flex-1">
                        {/* Expand arrow */}
                        {hasDetails ? (
                          <span className="text-gray-400 w-4 flex-shrink-0">
                            {isExpanded ? '▼' : '▶'}
                          </span>
                        ) : (
                          <span className="w-4 flex-shrink-0"></span>
                        )}

                        {/* Time range */}
                        <div className="text-sm text-gray-500 whitespace-nowrap w-32">
                          {formatTime(entry.started_at)}
                          {entry.stopped_at && (
                            <>
                              <span className="mx-1">-</span>
                              {formatTime(entry.stopped_at)}
                            </>
                          )}
                        </div>

                        {/* Duration */}
                        <div className="font-mono text-sm font-medium text-gray-900 whitespace-nowrap w-16">
                          {formatDuration(entry.duration_seconds)}
                        </div>

                        {/* Break indicator */}
                        {(entry.total_break_seconds || 0) > 0 && (
                          <span className="text-gray-400 text-xs whitespace-nowrap">
                            ({formatDuration(entry.total_break_seconds)} break)
                          </span>
                        )}

                        {/* Edited indicator */}
                        {entry.was_edited && (
                          <span className="text-gray-400 text-xs">[edited]</span>
                        )}

                        {/* Categorization */}
                        <div className="min-w-0 flex-1 flex items-center gap-2">
                          {/* Linear issue - CLICKABLE */}
                          {entry.linear_issue_id && (
                            <a
                              href={`https://linear.app/drip-team/issue/${entry.linear_issue_id}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="font-mono text-sm font-medium text-indigo-600 hover:text-indigo-800 hover:underline"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {entry.linear_issue_id}
                            </a>
                          )}

                          {/* Resource - CLICKABLE if has URL */}
                          {entry.resource?.url ? (
                            <a
                              href={entry.resource.url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-sm text-indigo-600 hover:text-indigo-800 hover:underline truncate"
                              onClick={(e) => e.stopPropagation()}
                            >
                              {entry.resource.title}
                            </a>
                          ) : entry.resource ? (
                            <span className="text-sm text-gray-600 truncate">
                              {entry.resource.title}
                            </span>
                          ) : entry.description ? (
                            <span className="text-sm text-gray-600 truncate">
                              {entry.description}
                            </span>
                          ) : entry.is_uncategorized ? (
                            <span className="text-sm text-gray-400 italic">Uncategorized</span>
                          ) : !entry.linear_issue_id ? (
                            <span className="text-sm text-gray-400">-</span>
                          ) : null}
                        </div>

                        {/* Component */}
                        {entry.component_name && (
                          <span className="text-xs px-2 py-0.5 bg-gray-100 text-gray-600 rounded flex-shrink-0">
                            {entry.component_name}
                          </span>
                        )}
                      </div>

                      {/* Actions */}
                      <div className="flex items-center gap-2 ml-4 flex-shrink-0">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingEntry(entry);
                          }}
                          className="p-1 text-gray-400 hover:text-indigo-600 hover:bg-gray-100 rounded transition-colors"
                          title="Edit entry"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                          </svg>
                        </button>
                        {deleteConfirmId === entry.id ? (
                          <>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handleDelete(entry.id);
                              }}
                              disabled={deleteEntry.isPending}
                              className="text-xs text-red-600 hover:text-red-800 font-medium"
                            >
                              {deleteEntry.isPending ? 'Deleting...' : 'Confirm'}
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setDeleteConfirmId(null);
                              }}
                              className="text-xs text-gray-500 hover:text-gray-700"
                            >
                              Cancel
                            </button>
                          </>
                        ) : (
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setDeleteConfirmId(entry.id);
                            }}
                            className="p-1 text-gray-400 hover:text-red-600 hover:bg-gray-100 rounded transition-colors"
                            title="Delete entry"
                          >
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                            </svg>
                          </button>
                        )}
                      </div>
                    </div>

                    {/* Expanded details */}
                    {isExpanded && (
                      <div className="pl-14 pr-6 pb-3 text-sm text-gray-500 bg-gray-50">
                        {/* Breaks */}
                        {entry.breaks && entry.breaks.length > 0 && (
                          <div className="mb-2">
                            <div className="font-medium text-gray-700 mb-1">Breaks:</div>
                            {entry.breaks.map((b: TimeBreak) => (
                              <div key={b.id} className="flex items-center gap-2 py-1 pl-2 border-l-2 border-yellow-300">
                                <span>{formatTime(b.started_at)}</span>
                                <span>-</span>
                                <span>{formatTime(b.stopped_at)}</span>
                                <span className="text-gray-400">({formatDuration(b.duration_seconds)})</span>
                                {b.note && <span className="italic text-gray-400">{b.note}</span>}
                              </div>
                            ))}
                          </div>
                        )}

                        {/* Edit history */}
                        {entry.edit_history && entry.edit_history.length > 0 && (
                          <div>
                            <div className="font-medium text-gray-700 mb-1">Edit History:</div>
                            {entry.edit_history.map((edit: EditHistoryEntry, i: number) => (
                              <div key={i} className="py-1 pl-2 border-l-2 border-gray-300 mb-1">
                                <div>
                                  <span className="font-medium">Reason:</span> &quot;{edit.reason}&quot;
                                  <span className="text-gray-400 ml-2">- {edit.edited_by}, {formatDateTime(edit.edited_at)}</span>
                                </div>
                                <div className="text-gray-400">
                                  Changed {edit.field}: {edit.old_value || '(empty)'} &rarr; {edit.new_value || '(empty)'}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          ))}
        </div>
      </div>

      {/* Edit Modal */}
      {editingEntry && (
        <EditEntryModal
          entry={editingEntry}
          onClose={() => setEditingEntry(null)}
        />
      )}
    </>
  );
};

export default TimeEntryList;
