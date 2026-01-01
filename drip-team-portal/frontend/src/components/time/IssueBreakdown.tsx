interface IssueGroup {
  key: string;
  name: string;
  total_seconds: number;
  entry_count: number;
}

interface IssueBreakdownProps {
  groups: IssueGroup[];
  totalSeconds: number;
}

const ISSUE_COLORS = [
  '#8b5cf6',  // violet
  '#06b6d4',  // cyan
  '#10b981',  // emerald
  '#f59e0b',  // amber
  '#ef4444',  // red
  '#6366f1',  // indigo
];

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export default function IssueBreakdown({ groups, totalSeconds }: IssueBreakdownProps) {
  // Sort by hours descending, take top 6
  const sorted = [...groups]
    .sort((a, b) => b.total_seconds - a.total_seconds)
    .slice(0, 6);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
        By Issue
      </h3>
      <div className="space-y-3">
        {sorted.map((group, index) => {
          const percent = totalSeconds > 0 ? (group.total_seconds / totalSeconds) * 100 : 0;
          const color = ISSUE_COLORS[index % ISSUE_COLORS.length];
          const issueId = group.key;
          const issueName = group.name || 'Untitled';

          return (
            <div key={issueId || 'uncategorized'}>
              <div className="flex items-center justify-between text-sm mb-1">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  {issueId ? (
                    <a
                      href={`https://linear.app/drip-team/issue/${issueId}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-indigo-600 hover:underline flex-shrink-0"
                    >
                      {issueId}
                    </a>
                  ) : (
                    <span className="text-gray-400 flex-shrink-0">No Issue</span>
                  )}
                  <span className="text-gray-600 truncate" title={issueName}>
                    {issueName}
                  </span>
                </div>
                <span className="text-gray-500 flex-shrink-0 ml-2">
                  {formatDuration(group.total_seconds)}
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
          <p className="text-sm text-gray-400 text-center py-4">No issues tracked</p>
        )}
      </div>
    </div>
  );
}
