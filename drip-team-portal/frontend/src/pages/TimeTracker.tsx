import React, { useMemo, useState } from 'react';
import TimerWidget from '../components/time/TimerWidget';
import TimeEntryList from '../components/time/TimeEntryList';
import ManualEntryForm from '../components/time/ManualEntryForm';
import StopTimerModal from '../components/time/StopTimerModal';
import { useTimeSummary, useCreateManualEntry, ManualEntryBreak } from '../hooks/useTimeTracking';

type EntryMode = 'timer' | 'manual';

interface PendingManualEntry {
  started_at: string;
  stopped_at: string;
  breaks: ManualEntryBreak[];
}

function formatHoursMinutes(totalSeconds: number): string {
  const hours = Math.floor(totalSeconds / 3600);
  const minutes = Math.floor((totalSeconds % 3600) / 60);

  if (hours > 0) {
    return `${hours}h ${minutes}m`;
  }
  return `${minutes}m`;
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

const TimeTracker: React.FC = () => {
  const [mode, setMode] = useState<EntryMode>('timer');
  const [pendingManualEntry, setPendingManualEntry] = useState<PendingManualEntry | null>(null);

  const weekDates = useMemo(() => getWeekDates(), []);
  const createManualEntry = useCreateManualEntry();

  const { data: summaryData, isLoading: summaryLoading } = useTimeSummary({
    start_date: weekDates.start,
    end_date: weekDates.end,
    group_by: 'user',
  });

  // Calculate total time for the week
  const weeklyTotal = summaryData?.groups?.reduce(
    (acc, group) => acc + group.total_seconds,
    0
  ) || 0;

  const weeklyEntryCount = summaryData?.groups?.reduce(
    (acc, group) => acc + group.entry_count,
    0
  ) || 0;

  const handleManualEntrySubmit = (data: PendingManualEntry) => {
    setPendingManualEntry(data);
  };

  const handleManualEntryCategorize = async (categorization: {
    linear_issue_id?: string;
    linear_issue_title?: string;
    resource_id?: number;
    description?: string;
    is_uncategorized?: boolean;
    component_id?: number;
  }) => {
    if (!pendingManualEntry) return;

    try {
      await createManualEntry.mutateAsync({
        ...pendingManualEntry,
        ...categorization,
      });
      setPendingManualEntry(null);
      setMode('timer');
    } catch (error) {
      console.error('Failed to create manual entry:', error);
      alert('Failed to create entry. Please try again.');
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Time Tracking</h1>
          <p className="mt-1 text-sm text-gray-500">
            Track your time and categorize your work
          </p>
        </div>
      </div>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Timer/Manual Entry Widget */}
        <div className="lg:col-span-1">
          {/* Mode Toggle */}
          <div className="bg-white rounded-lg shadow mb-4">
            <div className="flex">
              <button
                onClick={() => setMode('timer')}
                className={`flex-1 py-3 px-4 text-sm font-medium rounded-l-lg transition-colors ${
                  mode === 'timer'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Timer
              </button>
              <button
                onClick={() => setMode('manual')}
                className={`flex-1 py-3 px-4 text-sm font-medium rounded-r-lg transition-colors ${
                  mode === 'manual'
                    ? 'bg-indigo-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                Manual Entry
              </button>
            </div>
          </div>

          {/* Timer or Manual Entry Form */}
          {mode === 'timer' ? (
            <TimerWidget />
          ) : (
            <ManualEntryForm
              onSubmit={handleManualEntrySubmit}
              onCancel={() => setMode('timer')}
            />
          )}

          {/* Weekly Summary Card */}
          <div className="bg-white rounded-lg shadow p-6 mt-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">This Week</h2>
            {summaryLoading ? (
              <div className="flex items-center justify-center h-16">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-indigo-600"></div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Total Time</span>
                  <span className="text-2xl font-bold text-indigo-600">
                    {formatHoursMinutes(weeklyTotal)}
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-sm text-gray-600">Entries</span>
                  <span className="text-lg font-semibold text-gray-900">
                    {weeklyEntryCount}
                  </span>
                </div>
                {weeklyTotal > 0 && (
                  <div className="pt-2 border-t">
                    <div className="text-xs text-gray-500 mb-2">Daily Average</div>
                    <div className="text-lg font-medium text-gray-700">
                      {formatHoursMinutes(Math.round(weeklyTotal / 7))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Time Entries */}
        <div className="lg:col-span-2">
          <TimeEntryList />
        </div>
      </div>

      {/* Categorization Modal for Manual Entry */}
      {pendingManualEntry && (
        <StopTimerModal
          onClose={() => setPendingManualEntry(null)}
          onSubmit={handleManualEntryCategorize}
          isSubmitting={createManualEntry.isPending}
        />
      )}
    </div>
  );
};

export default TimeTracker;
