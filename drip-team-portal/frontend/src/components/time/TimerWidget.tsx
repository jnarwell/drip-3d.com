import React, { useState, useEffect } from 'react';
import { useActiveTimer, useStartTimer } from '../../hooks/useTimeTracking';
import StopTimerModal from './StopTimerModal';

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = seconds % 60;

  if (hours > 0) {
    return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
  }
  return `${minutes}:${String(secs).padStart(2, '0')}`;
}

const TimerWidget: React.FC = () => {
  const { data: activeTimer, isLoading } = useActiveTimer();
  const startTimer = useStartTimer();
  const [showStopModal, setShowStopModal] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Live counter effect
  useEffect(() => {
    if (!activeTimer?.started_at) {
      setElapsedSeconds(0);
      return;
    }

    const startTime = new Date(activeTimer.started_at).getTime();

    const updateElapsed = () => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000);
      setElapsedSeconds(elapsed);
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [activeTimer?.started_at]);

  const handleStart = () => {
    startTimer.mutate({});
  };

  const handleStop = () => {
    setShowStopModal(true);
  };

  const handleModalClose = () => {
    setShowStopModal(false);
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

  const isRunning = !!activeTimer;

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col items-center space-y-4">
          {/* Timer display */}
          <div className="text-center">
            <div className={`text-5xl font-mono font-bold ${isRunning ? 'text-indigo-600' : 'text-gray-400'}`}>
              {formatDuration(elapsedSeconds)}
            </div>
            {activeTimer?.linear_issue_id && (
              <div className="mt-2 text-sm text-gray-600">
                <span className="font-medium">{activeTimer.linear_issue_id}</span>
                {activeTimer.linear_issue_title && (
                  <span className="ml-1 text-gray-500">- {activeTimer.linear_issue_title}</span>
                )}
              </div>
            )}
          </div>

          {/* Start/Stop button */}
          <button
            onClick={isRunning ? handleStop : handleStart}
            disabled={startTimer.isPending}
            className={`w-32 h-32 rounded-full flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 ${
              isRunning
                ? 'bg-red-500 hover:bg-red-600 focus:ring-red-200'
                : 'bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-200'
            } ${startTimer.isPending ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {isRunning ? (
              <svg className="w-12 h-12 text-white" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="6" width="12" height="12" rx="1" />
              </svg>
            ) : (
              <svg className="w-12 h-12 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            )}
          </button>

          <div className="text-sm text-gray-500">
            {isRunning ? 'Click to stop and categorize' : 'Click to start tracking'}
          </div>
        </div>
      </div>

      {showStopModal && activeTimer && (
        <StopTimerModal
          activeTimer={activeTimer}
          onClose={handleModalClose}
        />
      )}
    </>
  );
};

export default TimerWidget;
