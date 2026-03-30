import type { Goal, Task } from "@/lib/types";

const STATUS_ICON: Record<string, string> = {
  pending: "\u25CB",
  in_progress: "\u25D4",
  done: "\u25CF",
  blocked: "\u2717",
  skipped: "\u2014",
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-white/30",
  in_progress: "text-blue-400",
  done: "text-green-400",
  blocked: "text-red-400",
  skipped: "text-white/20",
};

interface Props {
  goal: Goal | null;
  tasks: Task[];
}

export function TaskPanel({ goal, tasks }: Props) {
  if (!goal) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-white/30 text-sm">Select a goal to see its tasks</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <h2 className="text-lg font-semibold">{goal.title}</h2>
        {goal.description && (
          <p className="text-sm text-white/50 mt-1">{goal.description}</p>
        )}
        <div className="flex items-center gap-3 mt-2 text-xs text-white/30">
          <span>Priority: {goal.priority}</span>
          <span>Created by: {goal.created_by}</span>
          {goal.completed_at && (
            <span>Completed: {new Date(goal.completed_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {tasks.length === 0 ? (
        <div className="border border-dashed border-white/10 rounded-lg p-6 text-center">
          <p className="text-sm text-white/30">No tasks yet</p>
          <p className="text-xs text-white/20 mt-1">
            The agent will decompose this goal into tasks on its next cycle
          </p>
        </div>
      ) : (
        <div className="space-y-1">
          {tasks.map((task) => (
            <div
              key={task.id}
              className={`p-3 rounded-lg border border-white/5 ${
                task.status === "in_progress" ? "bg-blue-500/5 border-blue-500/20" : ""
              }`}
            >
              <div className="flex items-start gap-3">
                <span className={`text-sm mt-0.5 ${STATUS_COLOR[task.status]}`}>
                  {STATUS_ICON[task.status]}
                </span>
                <div className="flex-1 min-w-0">
                  <p className={`text-sm font-medium ${task.status === "done" ? "text-white/40 line-through" : ""}`}>
                    {task.title}
                  </p>
                  {task.description && (
                    <p className="text-xs text-white/30 mt-0.5">{task.description}</p>
                  )}
                  {task.result && (
                    <p className="text-xs text-green-400/70 mt-1 bg-green-500/5 px-2 py-1 rounded">
                      {task.result}
                    </p>
                  )}
                  {task.blocked_reason && (
                    <p className="text-xs text-red-400/70 mt-1 bg-red-500/5 px-2 py-1 rounded">
                      Blocked: {task.blocked_reason}
                    </p>
                  )}
                  <div className="flex items-center gap-3 mt-1 text-[10px] text-white/20">
                    {task.attempts > 0 && <span>Attempts: {task.attempts}/{task.max_attempts}</span>}
                    {task.completed_at && (
                      <span>Done: {new Date(task.completed_at).toLocaleString()}</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
