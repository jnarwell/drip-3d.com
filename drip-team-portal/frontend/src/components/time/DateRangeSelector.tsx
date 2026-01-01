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

function getToday(): DateRange {
  const today = formatDate(new Date());
  return {
    start_date: today,
    end_date: today,
    label: 'Today'
  };
}

function getThisWeek(): DateRange {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const monday = new Date(now);
  monday.setDate(diff);
  return {
    start_date: formatDate(monday),
    end_date: formatDate(now),
    label: 'This Week'
  };
}

function getLastWeek(): DateRange {
  const now = new Date();
  const day = now.getDay();
  const diff = now.getDate() - day + (day === 0 ? -6 : 1);
  const thisMonday = new Date(now);
  thisMonday.setDate(diff);

  const lastMonday = new Date(thisMonday);
  lastMonday.setDate(lastMonday.getDate() - 7);

  const lastSunday = new Date(thisMonday);
  lastSunday.setDate(lastSunday.getDate() - 1);

  return {
    start_date: formatDate(lastMonday),
    end_date: formatDate(lastSunday),
    label: 'Last Week'
  };
}

function getThisMonth(): DateRange {
  const now = new Date();
  const firstDay = new Date(now.getFullYear(), now.getMonth(), 1);
  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(now),
    label: 'This Month'
  };
}

function getThisQuarter(): DateRange {
  const now = new Date();
  const quarter = Math.floor(now.getMonth() / 3);
  const firstDay = new Date(now.getFullYear(), quarter * 3, 1);
  return {
    start_date: formatDate(firstDay),
    end_date: formatDate(now),
    label: 'This Quarter'
  };
}

const PRESETS = [
  { label: 'Today', getter: getToday },
  { label: 'This Week', getter: getThisWeek },
  { label: 'Last Week', getter: getLastWeek },
  { label: 'This Month', getter: getThisMonth },
  { label: 'This Quarter', getter: getThisQuarter },
];

export default function DateRangeSelector({ value, onChange }: DateRangeSelectorProps) {
  const [isOpen, setIsOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  // Close on outside click
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleSelect = (preset: typeof PRESETS[0]) => {
    onChange(preset.getter());
    setIsOpen(false);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm bg-white border border-gray-200 rounded-md hover:bg-gray-50 transition-colors"
      >
        <svg className="w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
        <span>{value.label}</span>
        <svg className={`w-4 h-4 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-1 w-40 bg-white border border-gray-200 rounded-md shadow-lg z-10">
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
        </div>
      )}
    </div>
  );
}
