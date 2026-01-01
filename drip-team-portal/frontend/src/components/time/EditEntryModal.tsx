import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { TimeEntry, useUpdateTimeEntry } from '../../hooks/useTimeTracking';

interface EditEntryModalProps {
  entry: TimeEntry;
  onClose: () => void;
}

const EDIT_REASONS = [
  'Forgot to stop timer',
  'Started earlier than recorded',
  'Ended earlier than recorded',
  'Wrong categorization',
  'Adding break time',
  'Other',
];

function formatForInput(dateString: string): string {
  const date = new Date(dateString);
  // Format as YYYY-MM-DDTHH:MM for datetime-local input
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

const EditEntryModal: React.FC<EditEntryModalProps> = ({ entry, onClose }) => {
  const [startedAt, setStartedAt] = useState(formatForInput(entry.started_at));
  const [stoppedAt, setStoppedAt] = useState(entry.stopped_at ? formatForInput(entry.stopped_at) : '');
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
        className="bg-white rounded-lg shadow-xl w-full max-w-md"
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
