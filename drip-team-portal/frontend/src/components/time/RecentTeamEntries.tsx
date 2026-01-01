interface TimeEntry {
  id: number;
  user_id: string;
  started_at: string;
  stopped_at?: string | null;
  duration_seconds?: number | null;
  linear_issue_id?: string | null;
  linear_issue_title?: string | null;
  description?: string | null;
}

interface RecentTeamEntriesProps {
  entries: TimeEntry[];
  limit?: number;
}

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(yesterday.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
}

export default function RecentTeamEntries({ entries, limit = 8 }: RecentTeamEntriesProps) {
  // Sort by most recent, limit
  const recent = [...entries]
    .filter(e => e.stopped_at)  // Only completed entries
    .sort((a, b) => new Date(b.started_at).getTime() - new Date(a.started_at).getTime())
    .slice(0, limit);

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between">
        <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide">
          Recent Entries
        </h3>
        <span className="text-xs text-gray-400">{entries.length} total</span>
      </div>

      <div className="divide-y divide-gray-50">
        {recent.map(entry => {
          const name = entry.user_id.split('@')[0];

          return (
            <div key={entry.id} className="px-4 py-2 flex items-center gap-3 hover:bg-gray-50">
              <span className="w-16 text-sm font-medium text-indigo-600 capitalize">
                {name}
              </span>
              <span className="w-20 text-xs text-gray-400">
                {formatDate(entry.started_at)}
              </span>
              <span className="w-20 text-sm font-mono whitespace-nowrap">
                {formatDuration(entry.duration_seconds || 0)}
              </span>
              {entry.linear_issue_id ? (
                <a
                  href={`https://linear.app/drip-team/issue/${entry.linear_issue_id}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-indigo-600 hover:underline"
                  onClick={e => e.stopPropagation()}
                >
                  {entry.linear_issue_id}
                </a>
              ) : null}
              <span className="flex-1 text-sm text-gray-600 truncate">
                {entry.description || entry.linear_issue_title || ''}
              </span>
            </div>
          );
        })}

        {recent.length === 0 && (
          <p className="text-sm text-gray-400 text-center py-6">No entries yet</p>
        )}
      </div>
    </div>
  );
}
