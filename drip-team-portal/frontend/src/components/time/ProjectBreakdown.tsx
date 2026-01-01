interface ProjectGroup {
  project_id: string | null;
  project_name: string;
  total_seconds: number;
  entry_count: number;
  issue_count?: number;
}

interface ProjectBreakdownProps {
  groups: ProjectGroup[];
  totalSeconds: number;
}

const PROJECT_COLORS = [
  '#6366f1',  // indigo
  '#8b5cf6',  // violet
  '#06b6d4',  // cyan
  '#10b981',  // emerald
  '#f59e0b',  // amber
  '#ef4444',  // red
];

function formatDuration(seconds: number): string {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  if (hours > 0) return `${hours}h ${minutes}m`;
  return `${minutes}m`;
}

export default function ProjectBreakdown({ groups, totalSeconds }: ProjectBreakdownProps) {
  // Sort by hours descending, take top 6
  const sorted = [...groups]
    .sort((a, b) => b.total_seconds - a.total_seconds)
    .slice(0, 6);

  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-sm font-medium text-gray-500 uppercase tracking-wide mb-3">
        By Project
      </h3>
      <div className="space-y-3">
        {sorted.map((group, index) => {
          const percent = totalSeconds > 0 ? (group.total_seconds / totalSeconds) * 100 : 0;
          const color = PROJECT_COLORS[index % PROJECT_COLORS.length];

          return (
            <div key={group.project_id || 'none'}>
              <div className="flex items-center justify-between text-sm mb-1">
                <span className="font-medium truncate max-w-[150px]" title={group.project_name}>
                  {group.project_name}
                </span>
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
          <p className="text-sm text-gray-400 text-center py-4">No projects tracked</p>
        )}
      </div>
    </div>
  );
}
