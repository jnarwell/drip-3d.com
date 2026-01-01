import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useStopTimer, TimeEntry } from '../../hooks/useTimeTracking';
import { useLinearIssues, LinearIssue } from '../../hooks/useLinearIssues';

interface StopTimerModalProps {
  activeTimer: TimeEntry;
  onClose: () => void;
}

const RESOURCE_TYPES = [
  { value: 'doc', label: 'Document' },
  { value: 'link', label: 'Link' },
  { value: 'paper', label: 'Paper' },
  { value: 'folder', label: 'Folder' },
  { value: 'image', label: 'Image' },
];

const StopTimerModal: React.FC<StopTimerModalProps> = ({ activeTimer, onClose }) => {
  const stopTimer = useStopTimer();
  const { data: linearData, isLoading: issuesLoading } = useLinearIssues({ state: 'active', limit: 50 });

  const [linearIssueId, setLinearIssueId] = useState(activeTimer.linear_issue_id || '');
  const [linearIssueTitle, setLinearIssueTitle] = useState(activeTimer.linear_issue_title || '');
  const [description, setDescription] = useState(activeTimer.description || '');
  const [isUncategorized, setIsUncategorized] = useState(false);
  const [issueSearch, setIssueSearch] = useState('');
  const [showIssueDropdown, setShowIssueDropdown] = useState(false);

  // Resource fields
  const [showResourceForm, setShowResourceForm] = useState(false);
  const [resourceTitle, setResourceTitle] = useState('');
  const [resourceUrl, setResourceUrl] = useState('');
  const [resourceType, setResourceType] = useState('link');

  // Validation
  const hasLinearIssue = linearIssueId.trim() !== '';
  const hasResource = showResourceForm && resourceTitle.trim() !== '';
  const hasDescription = description.trim() !== '';
  const isValid = isUncategorized || hasLinearIssue || hasResource || hasDescription;

  // Filter issues based on search
  const filteredIssues = linearData?.issues?.filter((issue: LinearIssue) =>
    issue.identifier.toLowerCase().includes(issueSearch.toLowerCase()) ||
    issue.title.toLowerCase().includes(issueSearch.toLowerCase())
  ) || [];

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

  // Backdrop click handler
  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      onClose();
    }
  };

  const handleSelectIssue = (issue: LinearIssue) => {
    setLinearIssueId(issue.identifier);
    setLinearIssueTitle(issue.title);
    setIssueSearch('');
    setShowIssueDropdown(false);
  };

  const handleClearIssue = () => {
    setLinearIssueId('');
    setLinearIssueTitle('');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!isValid) return;

    try {
      await stopTimer.mutateAsync({
        linear_issue_id: linearIssueId || undefined,
        linear_issue_title: linearIssueTitle || undefined,
        description: description || undefined,
        is_uncategorized: isUncategorized,
      });
      onClose();
    } catch (error) {
      console.error('Failed to stop timer:', error);
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleBackdropClick}
    >
      <div className="bg-white rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Stop Timer</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close modal"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-5">
          {/* Linear Issue */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Linear Issue
            </label>
            {linearIssueId ? (
              <div className="flex items-center gap-2 p-2 bg-indigo-50 rounded-md">
                <span className="font-mono text-sm font-medium text-indigo-600">{linearIssueId}</span>
                <span className="text-sm text-gray-600 truncate flex-1">{linearIssueTitle}</span>
                <button
                  type="button"
                  onClick={handleClearIssue}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            ) : (
              <div className="relative">
                <input
                  type="text"
                  value={issueSearch}
                  onChange={(e) => {
                    setIssueSearch(e.target.value);
                    setShowIssueDropdown(true);
                  }}
                  onFocus={() => setShowIssueDropdown(true)}
                  placeholder="Search issues (e.g., DRP-156)..."
                  className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500"
                  disabled={isUncategorized}
                />
                {showIssueDropdown && !isUncategorized && (
                  <div className="absolute z-10 mt-1 w-full bg-white border border-gray-200 rounded-md shadow-lg max-h-48 overflow-y-auto">
                    {issuesLoading ? (
                      <div className="p-3 text-center text-gray-500">Loading issues...</div>
                    ) : filteredIssues.length === 0 ? (
                      <div className="p-3 text-center text-gray-500">No issues found</div>
                    ) : (
                      filteredIssues.map((issue: LinearIssue) => (
                        <button
                          key={issue.id}
                          type="button"
                          onClick={() => handleSelectIssue(issue)}
                          className="w-full text-left px-3 py-2 hover:bg-gray-100 flex items-center gap-2"
                        >
                          <span className="font-mono text-sm font-medium text-indigo-600">{issue.identifier}</span>
                          <span className="text-sm text-gray-600 truncate">{issue.title}</span>
                        </button>
                      ))
                    )}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Resource */}
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">
                Resource
              </label>
              {!showResourceForm && (
                <button
                  type="button"
                  onClick={() => setShowResourceForm(true)}
                  disabled={isUncategorized}
                  className="text-sm text-indigo-600 hover:text-indigo-800 disabled:text-gray-400"
                >
                  + Add Resource
                </button>
              )}
            </div>
            {showResourceForm && (
              <div className="space-y-2 p-3 bg-gray-50 rounded-md">
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={resourceTitle}
                    onChange={(e) => setResourceTitle(e.target.value)}
                    placeholder="Resource title"
                    disabled={isUncategorized}
                    className="flex-1 border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                  />
                  <select
                    value={resourceType}
                    onChange={(e) => setResourceType(e.target.value)}
                    disabled={isUncategorized}
                    className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                  >
                    {RESOURCE_TYPES.map((type) => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                </div>
                <input
                  type="url"
                  value={resourceUrl}
                  onChange={(e) => setResourceUrl(e.target.value)}
                  placeholder="URL (optional)"
                  disabled={isUncategorized}
                  className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
                />
                <button
                  type="button"
                  onClick={() => {
                    setShowResourceForm(false);
                    setResourceTitle('');
                    setResourceUrl('');
                  }}
                  className="text-sm text-gray-500 hover:text-gray-700"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What were you working on?"
              rows={3}
              disabled={isUncategorized}
              className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 disabled:bg-gray-100"
            />
          </div>

          {/* N/A Checkbox */}
          <div className="flex items-center">
            <input
              type="checkbox"
              id="uncategorized"
              checked={isUncategorized}
              onChange={(e) => setIsUncategorized(e.target.checked)}
              className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
            />
            <label htmlFor="uncategorized" className="ml-2 text-sm text-gray-700">
              Mark as N/A (uncategorized time)
            </label>
          </div>

          {/* Validation message */}
          {!isValid && (
            <div className="text-sm text-amber-600 flex items-center gap-1">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              Please select an issue, add a resource, write a description, or mark as N/A
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
              disabled={!isValid || stopTimer.isPending}
              className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {stopTimer.isPending ? 'Stopping...' : 'Stop Timer'}
            </button>
          </div>
        </form>
      </div>
    </div>,
    document.body
  );
};

export default StopTimerModal;
