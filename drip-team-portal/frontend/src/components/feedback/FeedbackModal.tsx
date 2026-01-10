import React, { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useCreateFeedback } from '../../hooks/useFeedback';

interface FeedbackModalProps {
  onClose: () => void;
}

const FeedbackModal: React.FC<FeedbackModalProps> = ({ onClose }) => {
  const [type, setType] = useState<'bug' | 'feature' | 'question'>('bug');
  const [urgency, setUrgency] = useState<'need_now' | 'nice_to_have'>('nice_to_have');
  const [description, setDescription] = useState('');
  const [showSuccess, setShowSuccess] = useState(false);

  const createFeedback = useCreateFeedback();

  // Escape key handler
  const handleEscape = useCallback(
    (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
      }
    },
    [onClose]
  );

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

    if (!description.trim()) {
      alert('Please provide a description');
      return;
    }

    try {
      await createFeedback.mutateAsync({
        type,
        urgency,
        description: description.trim(),
        page_url: window.location.href,
        browser_info: {
          userAgent: navigator.userAgent,
          viewportWidth: window.innerWidth,
          viewportHeight: window.innerHeight,
        },
      });

      // Show success state
      setShowSuccess(true);

      // Close after 1.5 seconds
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      alert('Failed to submit feedback. Please try again.');
    }
  };

  return createPortal(
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black bg-opacity-50 p-4"
      onClick={handleBackdropClick}
    >
      <div
        className="bg-white rounded-lg shadow-xl w-full max-w-lg"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b flex justify-between items-center">
          <h2 className="text-lg font-semibold text-gray-900">Send Feedback</h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Success State */}
        {showSuccess ? (
          <div className="p-8 text-center">
            <div className="mx-auto w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Feedback Submitted!</h3>
            <p className="text-sm text-gray-500">Thank you for helping us improve.</p>
          </div>
        ) : (
          /* Form */
          <form onSubmit={handleSubmit} className="p-6 space-y-5">
            {/* Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                What type of feedback?
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setType('bug')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                    type === 'bug'
                      ? 'border-red-500 bg-red-50 text-red-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">Bug</div>
                  <div className="text-xs text-gray-500">Something broken</div>
                </button>
                <button
                  type="button"
                  onClick={() => setType('feature')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                    type === 'feature'
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">Feature</div>
                  <div className="text-xs text-gray-500">Request new</div>
                </button>
                <button
                  type="button"
                  onClick={() => setType('question')}
                  className={`flex-1 px-4 py-3 rounded-lg border-2 transition-all ${
                    type === 'question'
                      ? 'border-indigo-500 bg-indigo-50 text-indigo-700'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium">Question</div>
                  <div className="text-xs text-gray-500">Need help</div>
                </button>
              </div>
            </div>

            {/* Urgency Toggle */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Urgency
              </label>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => setUrgency('need_now')}
                  className={`flex-1 px-4 py-2 rounded-lg border-2 transition-all ${
                    urgency === 'need_now'
                      ? 'border-orange-500 bg-orange-50 text-orange-700 font-medium'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Need Now
                </button>
                <button
                  type="button"
                  onClick={() => setUrgency('nice_to_have')}
                  className={`flex-1 px-4 py-2 rounded-lg border-2 transition-all ${
                    urgency === 'nice_to_have'
                      ? 'border-green-500 bg-green-50 text-green-700 font-medium'
                      : 'border-gray-200 bg-white text-gray-700 hover:border-gray-300'
                  }`}
                >
                  Nice to Have
                </button>
              </div>
            </div>

            {/* Description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description <span className="text-red-500">*</span>
              </label>
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe your feedback..."
                rows={5}
                className="w-full border border-gray-300 rounded-md shadow-sm px-3 py-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none"
                required
              />
              <p className="text-xs text-gray-500 mt-1">
                Context captured: {window.location.pathname}
              </p>
            </div>

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
                disabled={createFeedback.isPending || !description.trim()}
                className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {createFeedback.isPending ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>,
    document.body
  );
};

export default FeedbackModal;
