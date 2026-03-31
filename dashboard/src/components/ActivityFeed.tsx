import type { ExecutionLog, Goal } from "@/lib/types";
import { formatTimeAgo } from "@/lib/utils";

const ACTION_COLOR: Record<string, string> = {
  plan: "text-purple-400 bg-purple-500/10",
  execute: "text-blue-400 bg-blue-500/10",
  reflect: "text-yellow-400 bg-yellow-500/10",
  report: "text-green-400 bg-green-500/10",
  decompose: "text-orange-400 bg-orange-500/10",
};

interface Props {
  logs: ExecutionLog[];
  goals: Goal[];
}

export function ActivityFeed({ logs, goals }: Props) {
  const goalMap = new Map(goals.map((g) => [g.id, g]));

  if (logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-white/30 text-sm">No activity yet</p>
          <p className="text-white/20 text-xs mt-1">
            Activity will appear here as the agent works through goals
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-2">
      {logs.map((log) => {
        const goal = log.goal_id ? goalMap.get(log.goal_id) : null;
        const colorClass = ACTION_COLOR[log.action] ?? "text-white/40 bg-white/5";

        return (
          <div key={log.id} className="flex gap-3 p-3 rounded-lg border border-white/5">
            <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 h-fit ${colorClass}`}>
              {log.action}
            </span>
            <div className="flex-1 min-w-0">
              <p className="text-sm">{log.summary}</p>
              {goal && (
                <p className="text-[10px] text-white/20 mt-0.5">Goal: {goal.title}</p>
              )}
              {log.details && Object.keys(log.details).length > 0 && (
                <details className="mt-1">
                  <summary className="text-[10px] text-white/20 cursor-pointer hover:text-white/40">
                    details
                  </summary>
                  <pre className="text-[10px] text-white/30 mt-1 bg-white/5 p-2 rounded overflow-x-auto">
                    {JSON.stringify(log.details, null, 2)}
                  </pre>
                </details>
              )}
            </div>
            <span className="text-[10px] text-white/20 flex-shrink-0">
              {formatTimeAgo(log.created_at)}
            </span>
          </div>
        );
      })}
    </div>
  );
}

