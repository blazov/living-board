import type { Goal, Task, ExecutionLog, Learning } from "@/lib/types";

interface Props {
  goal: Goal | null;
  tasks: Task[];
  logs: ExecutionLog[];
  learnings: Learning[];
}

/** Extract real URLs from task results and log details, skip local file paths */
function extractLinks(tasks: Task[], logs: ExecutionLog[]): { url: string; label: string }[] {
  const seen = new Set<string>();
  const links: { url: string; label: string }[] = [];
  const urlRegex = /https?:\/\/[^\s"'<>)]+/g;

  function addUrl(url: string) {
    // Clean trailing punctuation
    const cleaned = url.replace(/[.,;:!?)]+$/, "");
    if (seen.has(cleaned)) return;
    seen.add(cleaned);
    // Generate a friendly label from the URL
    let label = cleaned;
    try {
      const u = new URL(cleaned);
      const host = u.hostname.replace(/^www\./, "");
      const path = u.pathname === "/" ? "" : u.pathname;
      label = host + path;
    } catch { /* keep raw url */ }
    links.push({ url: cleaned, label });
  }

  for (const task of tasks) {
    if (task.result) {
      const matches = task.result.match(urlRegex);
      if (matches) matches.forEach(addUrl);
    }
  }

  for (const log of logs) {
    const detailStr = JSON.stringify(log.details ?? {});
    const matches = detailStr.match(urlRegex);
    if (matches) matches.forEach(addUrl);
  }

  return links;
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

  return (
    <div className="max-w-2xl space-y-5">
      {/* Description */}
      {goal.description && (
        <p className="text-sm text-white/70 leading-relaxed">{goal.description}</p>
      )}

      {/* Progress bar */}
      <div className="p-3 rounded-lg border border-white/5 bg-white/[0.02]">
        <div className="flex items-center justify-between mb-1.5">
          <span className="text-xs text-white/40">Progress</span>
          <span className="text-xs text-white/50">
            {doneTasks.length} of {totalTasks} done
          </span>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500/60 rounded-full transition-all"
            style={{ width: `${progressPct}%` }}
          />
        </div>
      </div>

      {/* Links — shown prominently near the top */}
      {links.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Links</h3>
          <div className="space-y-1.5">
            {links.map((link, i) => (
              <a
                key={i}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-blue-400/80 hover:text-blue-400 transition-colors"
              >
                <span className="text-blue-400/40">{"↗"}</span>
                <span className="truncate">{link.label}</span>
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Accomplished — compact list, no verbose results */}
      {doneTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Done</h3>
          <ul className="space-y-1">
            {doneTasks.map((task) => (
              <li key={task.id} className="flex items-start gap-2 text-sm text-white/50">
                <span className="text-green-400/70 mt-0.5">{"✓"}</span>
                <span>{task.title}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Next steps — compact */}
      {pendingTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Up Next</h3>
          <ul className="space-y-1">
            {pendingTasks.slice(0, 4).map((task) => (
              <li key={task.id} className="flex items-start gap-2 text-sm">
                <span className={task.status === "in_progress" ? "text-blue-400" : "text-white/20"}>
                  {task.status === "in_progress" ? "▸" : "○"}
                </span>
                <span className={task.status === "in_progress" ? "text-blue-400/80" : "text-white/50"}>
                  {task.title}
                </span>
              </li>
            ))}
            {pendingTasks.length > 4 && (
              <li className="text-xs text-white/20 pl-5">
                +{pendingTasks.length - 4} more
              </li>
            )}
          </ul>
        </div>
      )}

      {/* Blockers */}
      {blockedTasks.length > 0 && (
        <div>
          <h3 className="text-xs text-red-400/60 uppercase tracking-wider mb-2">Blocked</h3>
          <ul className="space-y-1">
            {blockedTasks.map((task) => (
              <li key={task.id} className="text-sm text-red-400/60">
                {task.title}{task.blocked_reason ? ` — ${task.blocked_reason}` : ""}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Learnings — simplified, no confidence bars or category badges */}
      {learnings.length > 0 && (
        <div>
          <h3 className="text-xs text-white/40 uppercase tracking-wider mb-2">Learnings</h3>
          <ul className="space-y-1">
            {learnings.slice(0, 5).map((learning) => (
              <li key={learning.id} className="text-sm text-white/50 flex items-start gap-2">
                <span className="text-white/20 mt-0.5">{"•"}</span>
                <span>{learning.content}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
