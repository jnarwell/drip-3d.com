interface TeamStatsRowProps {
  totalSeconds: number;
  totalEntries: number;
  activeMembers: number;
  totalMembers: number;
  targetHoursPerWeek?: number;  // default 40 * memberCount
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export default function TeamStatsRow({
  totalSeconds,
  totalEntries,
  activeMembers,
  totalMembers,
  targetHoursPerWeek
}: TeamStatsRowProps) {
  const totalHours = totalSeconds / 3600;
  const target = targetHoursPerWeek || (totalMembers * 40);
  const percentOfTarget = target > 0 ? Math.round((totalHours / target) * 100) : 0;
  const avgPerPerson = activeMembers > 0 ? totalSeconds / activeMembers : 0;

  return (
    <div className="grid grid-cols-4 gap-3">
      <div className="bg-white rounded-lg shadow p-3">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Total Hours</div>
        <div className="text-2xl font-bold text-indigo-600">{formatDuration(totalSeconds)}</div>
      </div>

      <div className="bg-white rounded-lg shadow p-3">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Entries</div>
        <div className="text-2xl font-bold">{totalEntries}</div>
      </div>

      <div className="bg-white rounded-lg shadow p-3">
        <div className="text-xs text-gray-500 uppercase tracking-wide">Avg / Person</div>
        <div className="text-2xl font-bold">{formatDuration(avgPerPerson)}</div>
      </div>

      <div className="bg-white rounded-lg shadow p-3">
        <div className="text-xs text-gray-500 uppercase tracking-wide">vs Target</div>
        <div className="flex items-baseline gap-1">
          <span className={`text-2xl font-bold ${percentOfTarget >= 80 ? 'text-green-600' : percentOfTarget >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
            {percentOfTarget}%
          </span>
          <span className="text-xs text-gray-400">of {target}h</span>
        </div>
      </div>
    </div>
  );
}
