import { useState, useRef, useEffect } from 'react';

export interface DateRange {
  start_date: string;
  end_date: string;
  label: string;
}

interface DateRangeSelectorProps {
  value: DateRange;
  onChange: (range: DateRange) => void;
}

// Helper to format date as YYYY-MM-DD (API expects this format)
function formatDate(date: Date): string {
  return date.toISOString().split('T')[0];
}

function getWeek(): DateRange {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now);
  monday.setDate(diff);
  return {
    start_date: formatDate(monday),
    end_date: formatDate(now),
    label: 'Week'
  };
}

function getMonth(): DateRange {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(now),
    label: 'Month'
  };
}

function getQuarter(): DateRange {
  const now = new Date();
  const quarter = Math.floor(now.getMonth() / 3);
  const firstDay = new Date(now.getFullYear(), quarter * 3, 1);
  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(now),
    label: 'Quarter'
  };
}

function getYear(): DateRange {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), 0, 1);
  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(now),
    label: 'Year'
  };
}

const PRESETS = [
  { label: 'Week', getter: getWeek },
  { label: 'Month', getter: getMonth },
  { label: 'Quarter', getter: getQuarter },
  { label: 'Year', getter: getYear },
];

export default function DateRangeSelector({ value, onChange }: DateRangeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [showCustom, setShowCustom] = useState(false);
  const [customStart, setCustomStart] = useState(value.start_date);
  const [customEnd, setCustomEnd] = useState(value.end_date);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
        setShowCustom(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (preset: typeof PRESETS[0]) => {
    onChange(preset.getter());
    setIsOpen(false);
    setShowCustom(false);
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onChange({
        start_date: customStart,
        end_date: customEnd,
        label: `${customStart} - ${customEnd}`
      });
      setIsOpen(false);
      setShowCustom(false);
    }
  };

  const displayLabel = value.label.includes('-')
    ? `${value.start_date.slice(5)} to ${value.end_date.slice(5)}`
    : value.label;

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
      >
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{displayLabel}</span>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 bg-white border border-gray-200 rounded-md shadow-lg z-10">
          {!showCustom ? (
            <div className="w-36">
              {PRESETS.map(preset => (
                <button
                  key={preset.label}
                  onClick={() => handleSelect(preset)}
                  className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                    value.label === preset.label ? 'bg-indigo-50 text-indigo-600' : ''
                  }`}
                >
                  {preset.label}
                </button>
              ))}
              <div className="border-t border-gray-100">
                <button
                  onClick={() => setShowCustom(true)}
                  className="w-full text-left px-3 py-2 text-sm hover:bg-gray-50 text-gray-600"
                >
                  Custom...
                </button>
              </div>
            </div>
          ) : (
            <div className="p-3 w-64">
              <div className="text-xs font-medium text-gray-500 uppercase mb-2">Custom Range</div>
              <div className="space-y-2">
                <div>
                  <label className="block text-xs text-gray-500 mb-1">Start</label>
                  <input
                    type="date"
                    value={customStart}
                    onChange={(e) => setCustomStart(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-200 rounded"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-500 mb-1">End</label>
                  <input
                    type="date"
                    value={customEnd}
                    onChange={(e) => setCustomEnd(e.target.value)}
                    className="w-full px-2 py-1 text-sm border border-gray-200 rounded"
                  />
                </div>
              </div>
              <div className="flex gap-2 mt-3">
                <button
                  onClick={() => setShowCustom(false)}
                  className="flex-1 px-2 py-1 text-sm text-gray-600 hover:bg-gray-50 rounded"
                >
                  Back
                </button>
                <button
                  onClick={handleCustomApply}
                  className="flex-1 px-2 py-1 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700"
                >
                  Apply
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
