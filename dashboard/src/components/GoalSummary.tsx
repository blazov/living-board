import type { Goal, Task, ExecutionLog, Learning } from "@/lib/types";
import { formatTimeAgo } from "@/lib/utils";

const CATEGORY_COLOR: Record<string, string> = {
  success_pattern: "text-green-400 bg-green-500/10",
  failure_pattern: "text-red-400 bg-red-500/10",
  tool_insight: "text-blue-400 bg-blue-500/10",
  domain_knowledge: "text-yellow-400 bg-yellow-500/10",
  strategy: "text-purple-400 bg-purple-500/10",
  operational: "text-cyan-400 bg-cyan-500/10",
};

interface Props {
  goal: Goal | null;
  tasks: Task[];
  logs: ExecutionLog[];
  learnings: Learning[];
}

function extractLinks(tasks: Task[], logs: ExecutionLog[]): string[] {
  const links: string[] = [];
  const urlRegex = /https?:\/\/[^\s"'<>]+/g;

  for (const task of tasks) {
    if (task.result) {
      const matches = task.result.match(urlRegex);
      if (matches) links.push(...matches);
    }
  }

  for (const log of logs) {
    const details = log.details;
    if (details?.artifacts && Array.isArray(details.artifacts)) {
      links.push(...(details.artifacts as string[]));
    }
    const detailStr = JSON.stringify(details);
    const matches = detailStr.match(urlRegex);
    if (matches) links.push(...matches);
  }

  return [...new Set(links)];
}

export function GoalSummary({ goal, tasks, logs, learnings }: Props) {
  if (!goal) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-white/30 text-sm">Select a goal to see its summary</p>
      </div>
    );
  }

  const doneTasks = tasks.filter((t) => t.status === "done");
  const pendingTasks = tasks.filter((t) => t.status === "pending" || t.status === "in_progress");
  const blockedTasks = tasks.filter((t) => t.status === "blocked");
  const totalTasks = tasks.length;
  const progressPct = totalTasks > 0 ? Math.round((doneTasks.length / totalTasks) * 100) : 0;
  const links = extractLinks(tasks, logs);
  const daysActive = Math.floor(
    (Date.now() - new Date(goal.created_at).getTime()) / (1000 * 60 * 60 * 24)
  );

  return (
    <div className="max-w-2xl space-y-6">
      {/* Description */}
      {goal.description && (
        <div>
          <p className="text-sm text-white/70 leading-relaxed">{goal.description}</p>
        </div>
      )}

      {/* Progress */}
      <div className="p-4 rounded-lg border border-white/5 bg-white/[0.02]">
        <div className="flex items-center justify-between mb-2">
          <span className="text-xs text-white/40 uppercase tracking-wider">Progress</span>
          <span className="text-sm font-mono text-white/60">
            {doneTasks.length}/{totalTasks} tasks
          </span>
        </div>
        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500/60 rounded-full transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
        <div className="flex items-center gap-4 mt-2 text-[10px] text-white/30">
          <span>{progressPct}% complete</span>
          <span>{daysActive}d active</span>
          <span>Created by: {goal.created_by}</span>
          {goal.completed_at && (
            <span>Completed: {new Date(goal.completed_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {/* What's been accomplished */}
      {doneTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Accomplished</h3>
          <div className="space-y-1.5">
            {doneTasks.map((task) => (
              <div key={task.id} className="p-2.5 rounded-lg border border-white/5">
                <div className="flex items-start gap-2">
                  <span className="text-green-400 text-sm mt-0.5">{"\u25CF"}</span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-white/60">{task.title}</p>
                    {task.result && (
                      <p className="text-xs text-green-400/60 mt-0.5 bg-green-500/5 px-2 py-1 rounded">
                        {task.result}
                      </p>
                    )}
                    {task.completed_at && (
                      <span className="text-[10px] text-white/20 mt-0.5 block">
                        {formatTimeAgo(task.completed_at)}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Next steps */}
      {pendingTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Next Steps</h3>
          <div className="space-y-1.5">
            {pendingTasks.slice(0, 3).map((task, i) => (
              <div key={task.id} className={`p-2.5 rounded-lg border ${
                task.status === "in_progress"
                  ? "border-blue-500/20 bg-blue-500/5"
                  : "border-white/5"
              }`}>
                <div className="flex items-start gap-2">
                  <span className={`text-sm mt-0.5 ${
                    task.status === "in_progress" ? "text-blue-400" : "text-white/30"
                  }`}>
                    {task.status === "in_progress" ? "\u25D4" : `${i + 1}.`}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm">{task.title}</p>
                    {task.description && (
                      <p className="text-xs text-white/30 mt-0.5">{task.description}</p>
                    )}
                  </div>
                </div>
              </div>
            ))}
            {pendingTasks.length > 3 && (
              <p className="text-[10px] text-white/20 pl-6">
                +{pendingTasks.length - 3} more pending tasks
              </p>
            )}
          </div>
        </div>
      )}

      {/* Blockers */}
      {blockedTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-red-400/60 uppercase tracking-wider mb-2">Blockers</h3>
          <div className="space-y-1.5">
            {blockedTasks.map((task) => (
              <div key={task.id} className="p-2.5 rounded-lg border border-red-500/10 bg-red-500/5">
                <p className="text-sm">{task.title}</p>
                {task.blocked_reason && (
                  <p className="text-xs text-red-400/60 mt-0.5">{task.blocked_reason}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Artifacts & Links */}
      {links.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Artifacts & Links</h3>
          <div className="space-y-1">
            {links.map((link, i) => (
              <div key={i} className="flex items-center gap-2 text-xs">
                <span className="text-white/20">{"\u2192"}</span>
                {link.startsWith("http") ? (
                  <a
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400/70 hover:text-blue-400 truncate transition-colors"
                  >
                    {link}
                  </a>
                ) : (
                  <span className="text-white/40 font-mono truncate">{link}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Key Learnings */}
      {learnings.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">
            Key Learnings ({learnings.length})
          </h3>
          <div className="space-y-1.5">
            {learnings.slice(0, 5).map((learning) => {
              const colorClass = CATEGORY_COLOR[learning.category] ?? "text-white/40 bg-white/5";
              return (
                <div key={learning.id} className="p-2.5 rounded-lg border border-white/5">
                  <div className="flex items-start justify-between gap-2">
                    <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${colorClass}`}>
                      {learning.category.replace(/_/g, " ")}
                    </span>
                    <div className="flex items-center gap-1">
                      <div className="w-8 h-1 bg-white/10 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-white/40 rounded-full"
                          style={{ width: `${learning.confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-[10px] text-white/20">
                        {Math.round(learning.confidence * 100)}%
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-white/60 mt-1">{learning.content}</p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
