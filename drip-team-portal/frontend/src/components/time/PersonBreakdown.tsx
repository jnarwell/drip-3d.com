interface PersonGroup {
  key: string;      // email
  name?: string;
  total_seconds: number;
  entry_count: number;
}

interface PersonBreakdownProps {
  groups: PersonGroup[];
  totalSeconds: number;
}

const PERSON_COLORS: Record<string, string> = {
  'jamie': '#6366f1',
  'emma': '#8b5cf6',
  'pierce': '#06b6d4',
  'alex': '#10b981',
};

function getColor(email: string): string {
  const name = email.split('@')[0].toLowerCase();
  return PERSON_COLORS[name] || '#94a3b8';
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export default function PersonBreakdown({ groups, totalSeconds }: PersonBreakdownProps) {
  // Sort by hours descending
  const sorted = [...groups].sort((a, b) => b.total_seconds - a.total_seconds);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
        By Person
      </h3>
      <div className="space-y-3">
        {sorted.map(group => {
          const percent = totalSeconds > 0 ? (group.total_seconds / totalSeconds) * 100 : 0;
          const name = group.name || group.key.split('@')[0];
          const color = getColor(group.key);

          return (
            <div key={group.key}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-medium capitalize">{name}</span>
                <span className="text-gray-500">
                  {formatDuration(group.total_seconds)} ({Math.round(percent)}%)
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full rounded-full transition-all duration-300"
                  style={{ width: `${percent}%`, backgroundColor: color }}
                />
              </div>
            </div>
          );
        })}

        {sorted.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-4">No time logged</p>
        )}
      </div>
    </div>
  );
}
