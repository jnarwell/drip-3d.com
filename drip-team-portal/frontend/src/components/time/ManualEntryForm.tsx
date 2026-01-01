import React, { useState } from 'react';
import { ManualEntryBreak } from '../../hooks/useTimeTracking';

interface ManualEntryFormProps {
  onSubmit: (data: {
    started_at: string;
    stopped_at: string;
    breaks: ManualEntryBreak[];
  }) => void;
  onCancel: () => void;
}

interface BreakInput {
  id: string;
  startTime: string;
  endTime: string;
  note: string;
}

function getDefaultDate(): string {
  const today = new Date();
  return today.toISOString().split('T')[0];
}

function getDefaultStartTime(): string {
  return '09:00';
}

function getDefaultEndTime(): string {
  const now = new Date();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  return `${hours}:${minutes}`;
}

function generateId(): string {
  return Math.random().toString(36).substring(2, 9);
}

const ManualEntryForm: React.FC<ManualEntryFormProps> = ({ onSubmit, onCancel }) => {
  const [date, setDate] = useState(getDefaultDate());
  const [startTime, setStartTime] = useState(getDefaultStartTime());
  const [endTime, setEndTime] = useState(getDefaultEndTime());
  const [breaks, setBreaks] = useState<BreakInput[]>([]);
  const [error, setError] = useState<string | null>(null);

  const addBreak = () => {
    setBreaks([
      ...breaks,
      {
        id: generateId(),
        startTime: '12:00',
        endTime: '12:30',
        note: '',
      },
    ]);
  };

  const updateBreak = (id: string, field: keyof BreakInput, value: string) => {
    setBreaks(breaks.map((b) =>
      b.id === id ? { ...b, [field]: value } : b
    ));
  };

  const removeBreak = (id: string) => {
    setBreaks(breaks.filter((b) => b.id !== id));
  };

  const validateAndSubmit = () => {
    setError(null);

    // Combine date and times into ISO strings
    const startedAt = new Date(`${date}T${startTime}`);
    const stoppedAt = new Date(`${date}T${endTime}`);

    // Handle overnight entries
    if (stoppedAt <= startedAt) {
      // If end time is before start time, assume it's the next day
      stoppedAt.setDate(stoppedAt.getDate() + 1);
    }

    // Validate breaks are within entry range
    const formattedBreaks: ManualEntryBreak[] = [];
    for (const b of breaks) {
      const breakStart = new Date(`${date}T${b.startTime}`);
      const breakEnd = new Date(`${date}T${b.endTime}`);

      // Handle overnight breaks
      if (breakEnd <= breakStart) {
        breakEnd.setDate(breakEnd.getDate() + 1);
      }

      // Check if break is within entry time range
      if (breakStart < startedAt || breakEnd > stoppedAt) {
        setError('Break times must be within the entry time range');
        return;
      }

      if (breakEnd <= breakStart) {
        setError('Break end time must be after start time');
        return;
      }

      formattedBreaks.push({
        started_at: breakStart.toISOString(),
        stopped_at: breakEnd.toISOString(),
        note: b.note || undefined,
      });
    }

    onSubmit({
      started_at: startedAt.toISOString(),
      stopped_at: stoppedAt.toISOString(),
      breaks: formattedBreaks,
    });
  };

  // Calculate duration for display
  const calculateDuration = (): string => {
    try {
      const startedAt = new Date(`${date}T${startTime}`);
      const stoppedAt = new Date(`${date}T${endTime}`);

      if (stoppedAt <= startedAt) {
        stoppedAt.setDate(stoppedAt.getDate() + 1);
      }

      let totalSeconds = Math.floor((stoppedAt.getTime() - startedAt.getTime()) / 1000);

      // Subtract breaks
      for (const b of breaks) {
        const breakStart = new Date(`${date}T${b.startTime}`);
        const breakEnd = new Date(`${date}T${b.endTime}`);
        if (breakEnd > breakStart) {
          totalSeconds -= Math.floor((breakEnd.getTime() - breakStart.getTime()) / 1000);
        }
      }

      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);

      if (hours > 0) {
        return `${hours}h ${minutes}m`;
      }
      return `${minutes}m`;
    } catch {
      return '--';
    }
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-semibold text-gray-900">Manual Time Entry</h2>
        <button
          onClick={onCancel}
          className="text-sm text-gray-500 hover:text-gray-700"
        >
          Cancel
        </button>
      </div>

      <div className="space-y-6">
        {/* Date */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Date
          </label>
          <input
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
          />
        </div>

        {/* Time Range */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Time
            </label>
            <input
              type="time"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Time
            </label>
            <input
              type="time"
              value={endTime}
              onChange={(e) => setEndTime(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
        </div>

        {/* Duration Preview */}
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <span>Duration:</span>
          <span className="font-mono font-medium">{calculateDuration()}</span>
          {breaks.length > 0 && (
            <span className="text-gray-400">(after breaks)</span>
          )}
        </div>

        {/* Breaks Section */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="block text-sm font-medium text-gray-700">
              Breaks
            </label>
            <button
              type="button"
              onClick={addBreak}
              className="text-sm text-indigo-600 hover:text-indigo-800"
            >
              + Add Break
            </button>
          </div>

          {breaks.length === 0 ? (
            <p className="text-sm text-gray-400 italic">No breaks added</p>
          ) : (
            <div className="space-y-3">
              {breaks.map((b) => (
                <div
                  key={b.id}
                  className="flex items-start gap-3 p-3 bg-gray-50 rounded-md border border-gray-200"
                >
                  <div className="flex-1 grid grid-cols-2 gap-2">
                    <input
                      type="time"
                      value={b.startTime}
                      onChange={(e) => updateBreak(b.id, 'startTime', e.target.value)}
                      className="border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Start"
                    />
                    <input
                      type="time"
                      value={b.endTime}
                      onChange={(e) => updateBreak(b.id, 'endTime', e.target.value)}
                      className="border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="End"
                    />
                    <input
                      type="text"
                      value={b.note}
                      onChange={(e) => updateBreak(b.id, 'note', e.target.value)}
                      className="col-span-2 border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                      placeholder="Note (optional)"
                    />
                  </div>
                  <button
                    type="button"
                    onClick={() => removeBreak(b.id)}
                    className="p-1 text-gray-400 hover:text-red-600"
                    title="Remove break"
                  >
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Error */}
        {error && (
          <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-md p-3">
            {error}
          </div>
        )}

        {/* Actions */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            type="button"
            onClick={onCancel}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={validateAndSubmit}
            className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 transition-colors"
          >
            Continue to Categorization
          </button>
        </div>
      </div>
    </div>
  );
};

export default ManualEntryForm;
