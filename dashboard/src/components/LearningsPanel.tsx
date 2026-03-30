import type { Learning, Goal } from "@/lib/types";

const CATEGORY_COLOR: Record<string, string> = {
  success_pattern: "text-green-400 bg-green-500/10",
  failure_pattern: "text-red-400 bg-red-500/10",
  tool_insight: "text-blue-400 bg-blue-500/10",
  domain_knowledge: "text-yellow-400 bg-yellow-500/10",
};

interface Props {
  learnings: Learning[];
  goals: Goal[];
}

export function LearningsPanel({ learnings, goals }: Props) {
  const goalMap = new Map(goals.map((g) => [g.id, g]));

  if (learnings.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <p className="text-white/30 text-sm">No learnings yet</p>
          <p className="text-white/20 text-xs mt-1">
            The agent extracts insights as it works -- they will appear here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl space-y-2">
      {learnings.map((learning) => {
        const goal = learning.goal_id ? goalMap.get(learning.goal_id) : null;
        const colorClass = CATEGORY_COLOR[learning.category] ?? "text-white/40 bg-white/5";

        return (
          <div key={learning.id} className="p-3 rounded-lg border border-white/5">
            <div className="flex items-start justify-between gap-2">
              <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${colorClass}`}>
                {learning.category.replace(/_/g, " ")}
              </span>
              <div className="flex items-center gap-2">
                <div className="flex items-center gap-1">
                  <div className="w-12 h-1 bg-white/10 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-white/40 rounded-full"
                      style={{ width: `${learning.confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-[10px] text-white/20">{Math.round(learning.confidence * 100)}%</span>
                </div>
              </div>
            </div>
            <p className="text-sm mt-2">{learning.content}</p>
            {goal && (
              <p className="text-[10px] text-white/20 mt-1">From: {goal.title}</p>
            )}
          </div>
        );
      })}
    </div>
  );
}
