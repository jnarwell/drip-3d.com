import React, { useState } from 'react';
import { useFeedbackList, useUpdateFeedback, useExportFeedback, FeedbackSubmission } from '../../hooks/useFeedback';

const FeedbackTriage: React.FC = () => {
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [typeFilter, setTypeFilter] = useState<string>('');
  const [urgencyFilter, setUrgencyFilter] = useState<string>('');
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState<Record<number, string>>({});

  const { data, isLoading, error } = useFeedbackList({
    status: statusFilter || undefined,
    type: typeFilter || undefined,
    urgency: urgencyFilter || undefined,
  });

  const updateFeedback = useUpdateFeedback();
  const exportFeedback = useExportFeedback({
    status: statusFilter || undefined,
    type: typeFilter || undefined,
    urgency: urgencyFilter || undefined,
  });

  const handleStatusChange = async (id: number, newStatus: string, currentStatus: string) => {
    // If changing to resolved or wont_fix, require resolution notes
    if ((newStatus === 'resolved' || newStatus === 'wont_fix') && !resolutionNotes[id]?.trim()) {
      alert('Please add resolution notes before marking as resolved or wont fix.');
      return;
    }

    const updates: { status: string; resolution_notes?: string } = { status: newStatus };

    // Include resolution notes if provided
    if (resolutionNotes[id]?.trim()) {
      updates.resolution_notes = resolutionNotes[id].trim();
    }

    try {
      await updateFeedback.mutateAsync({ id, updates });
      // Clear resolution notes after successful update
      setResolutionNotes((prev) => {
        const next = { ...prev };
        delete next[id];
        return next;
      });
    } catch (error) {
      console.error('Failed to update feedback:', error);
      alert('Failed to update status. Please try again.');
    }
  };

  const getTypeBadge = (type: string) => {
    const styles = {
      bug: 'bg-red-100 text-red-800',
      feature: 'bg-blue-100 text-blue-800',
      question: 'bg-indigo-100 text-indigo-800',
    };
    const icons = {
      bug: '🐛',
      feature: '✨',
      question: '❓',
    };
    return (
      <span className={`inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${styles[type as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        <span>{icons[type as keyof typeof icons] || '📝'}</span>
        {type}
      </span>
    );
  };

  const getUrgencyBadge = (urgency: string) => {
    const styles = {
      need_now: 'bg-orange-100 text-orange-800',
      nice_to_have: 'bg-green-100 text-green-800',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[urgency as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        {urgency === 'need_now' ? 'Need Now' : 'Nice to Have'}
      </span>
    );
  };

  const getStatusBadge = (status: string) => {
    const styles = {
      new: 'bg-yellow-100 text-yellow-800',
      reviewed: 'bg-blue-100 text-blue-800',
      in_progress: 'bg-purple-100 text-purple-800',
      resolved: 'bg-green-100 text-green-800',
      wont_fix: 'bg-gray-100 text-gray-800',
    };
    return (
      <span className={`px-2 py-1 rounded text-xs font-medium ${styles[status as keyof typeof styles] || 'bg-gray-100 text-gray-800'}`}>
        {status.replace('_', ' ')}
      </span>
    );
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8">
        <p className="text-red-600">Failed to load feedback submissions</p>
      </div>
    );
  }

  const feedback = data?.feedback || [];

  return (
    <div className="space-y-4">
      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">All Statuses</option>
          <option value="new">New</option>
          <option value="reviewed">Reviewed</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="wont_fix">Wont Fix</option>
        </select>

        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
          className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">All Types</option>
          <option value="bug">Bug</option>
          <option value="feature">Feature</option>
          <option value="question">Question</option>
        </select>

        <select
          value={urgencyFilter}
          onChange={(e) => setUrgencyFilter(e.target.value)}
          className="border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500"
        >
          <option value="">All Urgency</option>
          <option value="need_now">Need Now</option>
          <option value="nice_to_have">Nice to Have</option>
        </select>

        <div className="flex-1"></div>

        <button
          onClick={exportFeedback}
          className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 rounded-md hover:bg-indigo-700 transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* Feedback Table */}
      {feedback.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-8 text-center text-gray-500">
          No feedback submissions found
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Type
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Urgency
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  User
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Description
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {feedback.map((item: FeedbackSubmission) => (
                <React.Fragment key={item.id}>
                  <tr
                    className="hover:bg-gray-50 cursor-pointer transition-colors"
                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  >
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getTypeBadge(item.type)}
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      {getUrgencyBadge(item.urgency)}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {item.user_id.split('@')[0]}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-700">
                      <div className="max-w-md truncate">{item.description}</div>
                    </td>
                    <td className="px-4 py-3 whitespace-nowrap" onClick={(e) => e.stopPropagation()}>
                      <select
                        value={item.status}
                        onChange={(e) => handleStatusChange(item.id, e.target.value, item.status)}
                        className="border border-gray-300 rounded-md shadow-sm px-2 py-1 text-sm focus:ring-indigo-500 focus:border-indigo-500"
                        disabled={updateFeedback.isPending}
                      >
                        <option value="new">New</option>
                        <option value="reviewed">Reviewed</option>
                        <option value="in_progress">In Progress</option>
                        <option value="resolved">Resolved</option>
                        <option value="wont_fix">Wont Fix</option>
                      </select>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                  {expandedId === item.id && (
                    <tr>
                      <td colSpan={6} className="px-4 py-4 bg-gray-50">
                        <div className="space-y-3">
                          <div>
                            <div className="text-xs font-medium text-gray-500 mb-1">Full Description</div>
                            <div className="text-sm text-gray-900 whitespace-pre-wrap">{item.description}</div>
                          </div>
                          <div className="grid grid-cols-2 gap-3">
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-1">Page URL</div>
                              <a
                                href={item.page_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-sm text-indigo-600 hover:text-indigo-800 truncate block"
                              >
                                {item.page_url}
                              </a>
                            </div>
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-1">Browser Info</div>
                              <div className="text-sm text-gray-700">
                                {item.browser_info.viewportWidth}x{item.browser_info.viewportHeight}
                              </div>
                            </div>
                          </div>
                          {item.status === 'resolved' || item.status === 'wont_fix' ? (
                            item.resolution_notes && (
                              <div>
                                <div className="text-xs font-medium text-gray-500 mb-1">Resolution Notes</div>
                                <div className="text-sm text-gray-900 bg-white p-3 rounded border border-gray-200">
                                  {item.resolution_notes}
                                </div>
                                {item.resolved_by && (
                                  <div className="text-xs text-gray-500 mt-1">
                                    Resolved by {item.resolved_by.split('@')[0]} on{' '}
                                    {new Date(item.resolved_at!).toLocaleDateString()}
                                  </div>
                                )}
                              </div>
                            )
                          ) : (
                            <div>
                              <div className="text-xs font-medium text-gray-500 mb-1">
                                Resolution Notes
                              </div>
                              <textarea
                                value={resolutionNotes[item.id] || ''}
                                onChange={(e) =>
                                  setResolutionNotes((prev) => ({ ...prev, [item.id]: e.target.value }))
                                }
                                placeholder="Add resolution notes (required when marking as resolved/wont_fix)..."
                                rows={3}
                                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 text-sm focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                              />
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};

export default FeedbackTriage;
