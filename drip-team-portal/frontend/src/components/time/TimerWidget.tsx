import React, { useState, useEffect } from 'react';
import { useActiveTimer, useStartTimer, useStartBreak, useStopBreak } from '../../hooks/useTimeTracking';
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
  const startBreak = useStartBreak();
  const stopBreak = useStopBreak();
  const [showStopModal, setShowStopModal] = useState(false);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);

  // Live counter effect
  useEffect(() => {
    if (!activeTimer?.started_at) {
      setElapsedSeconds(0);
      return;
    }

    const startTime = new Date(activeTimer.started_at).getTime();
    const totalBreakSeconds = activeTimer.total_break_seconds || 0;

    const updateElapsed = () => {
      const now = Date.now();
      const elapsed = Math.floor((now - startTime) / 1000) - totalBreakSeconds;
      setElapsedSeconds(Math.max(0, elapsed));
    };

    updateElapsed();
    const interval = setInterval(updateElapsed, 1000);

    return () => clearInterval(interval);
  }, [activeTimer?.started_at, activeTimer?.total_break_seconds]);

  const handleStart = () => {
    startTimer.mutate({});
  };

  const handleStop = () => {
    setShowStopModal(true);
  };

  const handleModalClose = () => {
    setShowStopModal(false);
  };

  const handleStartBreak = () => {
    if (activeTimer) {
      startBreak.mutate({ entryId: activeTimer.id });
    }
  };

  const handleEndBreak = () => {
    if (activeTimer) {
      const activeBreak = activeTimer.breaks?.find(b => !b.stopped_at);
      if (activeBreak) {
        stopBreak.mutate({ entryId: activeTimer.id, breakId: activeBreak.id });
      }
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

  const isRunning = !!activeTimer;
  const isOnBreak = activeTimer?.on_break || false;

  return (
    <>
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex flex-col items-center space-y-4">
          {/* Timer display */}
          <div className="text-center">
            <div className={`text-5xl font-mono font-bold ${
              isOnBreak ? 'text-yellow-500' : isRunning ? 'text-indigo-600' : 'text-gray-400'
            }`}>
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

          {/* Break status */}
          {isOnBreak && (
            <div className="text-yellow-600 font-medium animate-pulse">
              On Break
            </div>
          )}
          {activeTimer && (activeTimer.total_break_seconds || 0) > 0 && !isOnBreak && (
            <div className="text-sm text-gray-500">
              Total breaks: {formatDuration(activeTimer.total_break_seconds || 0)} ({activeTimer.breaks?.length || 0})
            </div>
          )}

          {/* Buttons */}
          {!isRunning ? (
            // Start button (when no timer running)
            <button
              onClick={handleStart}
              disabled={startTimer.isPending}
              className={`w-32 h-32 rounded-full flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 bg-indigo-600 hover:bg-indigo-700 focus:ring-indigo-200 ${
                startTimer.isPending ? 'opacity-50 cursor-not-allowed' : ''
              }`}
            >
              <svg className="w-12 h-12 text-white ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </button>
          ) : (
            // Stop and Break buttons (when timer running)
            <div className="flex gap-4 justify-center">
              {/* Stop button */}
              <button
                onClick={handleStop}
                className="w-20 h-20 rounded-full bg-red-500 hover:bg-red-600 flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-red-200"
              >
                <svg className="w-8 h-8 text-white" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="1" />
                </svg>
              </button>

              {/* Break button */}
              {isOnBreak ? (
                <button
                  onClick={handleEndBreak}
                  disabled={stopBreak.isPending}
                  className={`w-20 h-20 rounded-full bg-yellow-500 hover:bg-yellow-600 flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-yellow-200 ${
                    stopBreak.isPending ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <span className="text-white text-xs font-medium">End Break</span>
                </button>
              ) : (
                <button
                  onClick={handleStartBreak}
                  disabled={startBreak.isPending}
                  className={`w-20 h-20 rounded-full bg-gray-200 hover:bg-gray-300 flex items-center justify-center transition-all transform hover:scale-105 focus:outline-none focus:ring-4 focus:ring-gray-100 ${
                    startBreak.isPending ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  <span className="text-gray-700 text-xs font-medium">Break</span>
                </button>
              )}
            </div>
          )}

          <div className="text-sm text-gray-500">
            {isOnBreak
              ? 'Click End Break to resume'
              : isRunning
                ? 'Click stop to categorize, or take a break'
                : 'Click to start tracking'
            }
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
