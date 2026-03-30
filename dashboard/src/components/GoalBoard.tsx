import type { Goal, Task } from "@/lib/types";

const STATUS_ORDER = ["in_progress", "pending", "blocked", "done", "archived"] as const;

const STATUS_BADGE: Record<string, string> = {
  pending: "bg-yellow-500/20 text-yellow-400",
  in_progress: "bg-blue-500/20 text-blue-400",
  done: "bg-green-500/20 text-green-400",
  blocked: "bg-red-500/20 text-red-400",
  archived: "bg-white/10 text-white/30",
};

interface Props {
  goals: Goal[];
  tasks: Task[];
  selectedGoalId: string | null;
  onSelectGoal: (id: string | null) => void;
}

export function GoalBoard({ goals, tasks, selectedGoalId, onSelectGoal }: Props) {
  const grouped = STATUS_ORDER.map((status) => ({
    status,
    goals: goals.filter((g) => g.status === status),
  })).filter((g) => g.goals.length > 0);

  return (
    <div className="space-y-6">
      {grouped.map(({ status, goals: statusGoals }) => (
        <div key={status}>
          <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-2">
            {status.replace("_", " ")} ({statusGoals.length})
          </h3>
          <div className="space-y-2">
            {statusGoals.map((goal) => {
              const goalTasks = tasks.filter((t) => t.goal_id === goal.id);
              const doneTasks = goalTasks.filter((t) => t.status === "done").length;
              const totalTasks = goalTasks.length;
              const isSelected = selectedGoalId === goal.id;

              return (
                <button
                  key={goal.id}
                  onClick={() => onSelectGoal(isSelected ? null : goal.id)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    isSelected
                      ? "border-white/30 bg-white/5"
                      : "border-white/5 hover:border-white/15 hover:bg-white/[0.02]"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <span className="text-sm font-medium leading-tight">{goal.title}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0 ${STATUS_BADGE[goal.status]}`}>
                      {goal.status.replace("_", " ")}
                    </span>
                  </div>
                  {totalTasks > 0 && (
                    <div className="mt-2">
                      <div className="flex items-center gap-2">
                        <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-green-500/60 rounded-full transition-all"
                            style={{ width: `${(doneTasks / totalTasks) * 100}%` }}
                          />
                        </div>
                        <span className="text-[10px] text-white/30 font-mono">
                          {doneTasks}/{totalTasks}
                        </span>
                      </div>
                    </div>
                  )}
                  {totalTasks === 0 && goal.status !== "done" && (
                    <p className="text-[10px] text-white/20 mt-1">No tasks yet -- agent will decompose</p>
                  )}
                  {goal.metadata?.model === "opus" && (
                    <span className="inline-block mt-1 text-[10px] text-purple-400 bg-purple-500/10 px-1.5 py-0.5 rounded">
                      opus
                    </span>
                  )}
                </button>
              );
            })}
          </div>
        </div>
      ))}
      {goals.length === 0 && (
        <p className="text-sm text-white/30 text-center py-8">No goals yet. Click &quot;+ Add Goal&quot; to start.</p>
      )}
    </div>
  );
}
