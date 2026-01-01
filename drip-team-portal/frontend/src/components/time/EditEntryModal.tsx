import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { TimeEntry, TimeBreak, useUpdateTimeEntry } from '../../hooks/useTimeTracking';

interface EditEntryModalProps {
  entry: TimeEntry;
  onClose: () => void;
}

interface BreakEditInput {
  id?: number;  // undefined for new breaks
  tempId: string;  // for React key
  startTime: string;  // HH:MM format
  endTime: string;
  date: string;  // YYYY-MM-DD
  note: string;
}

const EDIT_REASONS = [
  'Forgot to stop timer',
  'Started earlier than recorded',
  'Ended earlier than recorded',
  'Wrong categorization',
  'Adding/editing breaks',
  'Other',
];

function formatForInput(dateString: string): string {
  const date = new Date(dateString);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const hours = String(date.getHours()).padStart(2, '0');
  const minutes = String(date.getMinutes()).padStart(2, '0');
  return `${year}-${month}-${day}T${hours}:${minutes}`;
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

function getDateFromIso(isoString: string): string {
  return new Date(isoString).toISOString().split('T')[0];
}

function getTimeFromIso(isoString: string): string {
  const date = new Date(isoString);
  return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
}

function generateTempId(): string {
  return Math.random().toString(36).substring(2, 9);
}

function initializeBreaks(breaks?: TimeBreak[]): BreakEditInput[] {
  if (!breaks || breaks.length === 0) return [];
  return breaks.map((b) => ({
    id: b.id,
    tempId: generateTempId(),
    date: getDateFromIso(b.started_at),
    startTime: getTimeFromIso(b.started_at),
    endTime: b.stopped_at ? getTimeFromIso(b.stopped_at) : '',
    note: b.note || '',
  }));
}

const EditEntryModal: React.FC<EditEntryModalProps> = ({ entry, onClose }) => {
  const [startedAt, setStartedAt] = useState(formatForInput(entry.started_at));
  const [stoppedAt, setStoppedAt] = useState(entry.stopped_at ? formatForInput(entry.stopped_at) : '');
  const [breaks, setBreaks] = useState<BreakEditInput[]>(() => initializeBreaks(entry.breaks));
  const [reason, setReason] = useState('');
  const [customReason, setCustomReason] = useState('');

  const updateEntry = useUpdateTimeEntry();

  // Escape key handler
  const handleEscape = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Escape') {
      onClose();
    }
  }, [onClose]);

  useEffect(() => {
    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [handleEscape]);

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const addBreak = () => {
    // Default to entry date and 12:00-12:30
    const entryDate = new Date(startedAt).toISOString().split('T')[0];
    setBreaks([
      ...breaks,
      {
        tempId: generateTempId(),
        date: entryDate,
        startTime: '12:00',
        endTime: '12:30',
        note: '',
      },
    ]);
  };

  const updateBreak = (tempId: string, field: keyof BreakEditInput, value: string) => {
    setBreaks(breaks.map((b) =>
      b.tempId === tempId ? { ...b, [field]: value } : b
    ));
  };

  const removeBreak = (tempId: string) => {
    setBreaks(breaks.filter((b) => b.tempId !== tempId));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const finalReason = reason === 'Other' ? customReason : reason;
    if (!finalReason) {
      alert('Please select a reason for editing');
      return;
    }

    const updates: Record<string, unknown> = {};

    // Only include changed fields
    const newStartedAt = new Date(startedAt).toISOString();
    if (newStartedAt !== entry.started_at) {
      updates.started_at = newStartedAt;
    }

    if (stoppedAt) {
      const newStoppedAt = new Date(stoppedAt).toISOString();
      if (newStoppedAt !== entry.stopped_at) {
        updates.stopped_at = newStoppedAt;
      }
    }

    // Check if breaks changed
    const originalBreakCount = entry.breaks?.length || 0;
    const breaksChanged = breaks.length !== originalBreakCount ||
      breaks.some((b, i) => {
        const orig = entry.breaks?.[i];
        if (!orig) return true;
        return b.startTime !== getTimeFromIso(orig.started_at) ||
               b.endTime !== (orig.stopped_at ? getTimeFromIso(orig.stopped_at) : '') ||
               b.note !== (orig.note || '');
      });

    if (breaksChanged) {
      // Convert breaks to ISO format for backend
      updates.breaks = breaks.map((b) => ({
        started_at: new Date(`${b.date}T${b.startTime}`).toISOString(),
        stopped_at: new Date(`${b.date}T${b.endTime}`).toISOString(),
        note: b.note || null,
      }));
    }

    if (Object.keys(updates).length === 0) {
      alert('No changes detected');
      return;
    }

    try {
      await updateEntry.mutateAsync({
        entryId: entry.id,
        updates,
        edit_reason: finalReason,
      });
      onClose();
    } catch (error) {
      console.error('Failed to update entry:', error);
      alert('Failed to update entry. Please try again.');
    }
  };

  const hasStartedAtChanged = formatForInput(entry.started_at) !== startedAt;
  const hasStoppedAtChanged = entry.stopped_at && formatForInput(entry.stopped_at) !== stoppedAt;
  const canSubmit = reason && (reason !== 'Other' || customReason);

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Edit Time Entry</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Start Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Start Time
            </label>
            <input
              type="datetime-local"
              value={startedAt}
              onChange={(e) => setStartedAt(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {hasStartedAtChanged && (
              <p className="text-sm text-gray-400 mt-1">
                was {formatDateTime(entry.started_at)}
              </p>
            )}
          </div>

          {/* End Time */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              End Time
            </label>
            <input
              type="datetime-local"
              value={stoppedAt}
              onChange={(e) => setStoppedAt(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
            {hasStoppedAtChanged && entry.stopped_at && (
              <p className="text-sm text-gray-400 mt-1">
                was {formatDateTime(entry.stopped_at)}
              </p>
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
              <p className="text-sm text-gray-400 italic">No breaks</p>
            ) : (
              <div className="space-y-3">
                {breaks.map((b) => (
                  <div
                    key={b.tempId}
                    className="flex items-start gap-3 p-3 bg-gray-50 rounded-md border border-gray-200"
                  >
                    <div className="flex-1 grid grid-cols-2 gap-2">
                      <input
                        type="time"
                        value={b.startTime}
                        onChange={(e) => updateBreak(b.tempId, 'startTime', e.target.value)}
                        className="border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Start"
                      />
                      <input
                        type="time"
                        value={b.endTime}
                        onChange={(e) => updateBreak(b.tempId, 'endTime', e.target.value)}
                        className="border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="End"
                      />
                      <input
                        type="text"
                        value={b.note}
                        onChange={(e) => updateBreak(b.tempId, 'note', e.target.value)}
                        className="col-span-2 border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        placeholder="Note (optional)"
                      />
                    </div>
                    <button
                      type="button"
                      onClick={() => removeBreak(b.tempId)}
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

          {/* Reason dropdown */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Why are you editing? <span className="text-red-500">*</span>
            </label>
            <select
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
            >
              <option value="">Select a reason...</option>
              {EDIT_REASONS.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </div>

          {/* Custom reason input */}
          {reason === 'Other' && (
            <div>
              <input
                type="text"
                placeholder="Enter reason..."
                value={customReason}
                onChange={(e) => setCustomReason(e.target.value)}
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={updateEntry.isPending || !canSubmit}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {updateEntry.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
};

export default EditEntryModal;
