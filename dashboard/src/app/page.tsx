"use client";

import { useEffect, useState, useCallback } from "react";
import { supabase } from "@/lib/supabase";
import type { Goal, Task, ExecutionLog, Learning, GoalComment } from "@/lib/types";
import { GoalBoard } from "@/components/GoalBoard";
import { TaskPanel } from "@/components/TaskPanel";
import { ActivityFeed } from "@/components/ActivityFeed";
import { LearningsPanel } from "@/components/LearningsPanel";
import { AddGoalForm } from "@/components/AddGoalForm";
import { GoalSummary } from "@/components/GoalSummary";
import { CommentsPanel } from "@/components/CommentsPanel";

export default function Home() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [learnings, setLearnings] = useState<Learning[]>([]);
  const [comments, setComments] = useState<GoalComment[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<string | null>(null);
  const [showAddGoal, setShowAddGoal] = useState(false);
  const [activeTab, setActiveTab] = useState<"summary" | "tasks" | "activity" | "learnings" | "comments">("tasks");

  const fetchAll = useCallback(async () => {
    const [goalsRes, tasksRes, logsRes, learningsRes, commentsRes] = await Promise.all([
      supabase.from("goals").select("*").order("priority", { ascending: true }),
      supabase.from("tasks").select("*").order("sort_order", { ascending: true }),
      supabase.from("execution_log").select("*").order("created_at", { ascending: false }).limit(50),
      supabase.from("learnings").select("*").order("confidence", { ascending: false }),
      supabase.from("goal_comments").select("*").order("created_at", { ascending: false }),
    ]);
    if (goalsRes.data) setGoals(goalsRes.data);
    if (tasksRes.data) setTasks(tasksRes.data);
    if (logsRes.data) setLogs(logsRes.data);
    if (learningsRes.data) setLearnings(learningsRes.data);
    if (commentsRes.data) setComments(commentsRes.data);
  }, []);

  useEffect(() => {
    fetchAll();

    const channel = supabase
      .channel("realtime-all")
      .on("postgres_changes", { event: "*", schema: "public", table: "goals" }, () => fetchAll())
      .on("postgres_changes", { event: "*", schema: "public", table: "tasks" }, () => fetchAll())
      .on("postgres_changes", { event: "*", schema: "public", table: "execution_log" }, () => fetchAll())
      .on("postgres_changes", { event: "*", schema: "public", table: "learnings" }, () => fetchAll())
      .on("postgres_changes", { event: "*", schema: "public", table: "goal_comments" }, () => fetchAll())
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [fetchAll]);

  const selectedGoal = goals.find((g) => g.id === selectedGoalId) ?? null;
  const selectedTasks = tasks.filter((t) => t.goal_id === selectedGoalId);
  const selectedLogs = selectedGoalId
    ? logs.filter((l) => l.goal_id === selectedGoalId)
    : logs;
  const selectedLearnings = selectedGoalId
    ? learnings.filter((l) => l.goal_id === selectedGoalId)
    : learnings;
  const selectedComments = selectedGoalId
    ? comments.filter((c) => c.goal_id === selectedGoalId)
    : [];
  const unacknowledgedCount = selectedComments.filter((c) => !c.acknowledged_at && c.author === "user").length;

  return (
    <div className="flex flex-col h-screen">
      {/* Header */}
      <header className="flex items-center justify-between px-6 py-4 border-b border-white/10">
        <div>
          <h1 className="text-xl font-semibold tracking-tight">Living Board</h1>
          <p className="text-sm text-white/40">Autonomous goal execution</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-white/30 font-mono">
            {goals.filter((g) => g.status === "in_progress").length} active /
            {" "}{goals.filter((g) => g.status === "done").length} done
          </span>
          <button
            onClick={() => setShowAddGoal(true)}
            className="px-3 py-1.5 text-sm bg-white text-black rounded-md hover:bg-white/90 transition-colors"
          >
            + Add Goal
          </button>
        </div>
      </header>

      {/* Main content */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left: Goal Board */}
        <div className="w-80 border-r border-white/10 overflow-y-auto p-4 flex-shrink-0">
          <GoalBoard
            goals={goals}
            tasks={tasks}
            selectedGoalId={selectedGoalId}
            onSelectGoal={setSelectedGoalId}
          />
        </div>

        {/* Right: Detail Panel */}
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-white/10 px-4">
            {(["summary", "tasks", "activity", "learnings", "comments"] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-3 text-sm capitalize transition-colors flex items-center gap-1.5 ${
                  activeTab === tab
                    ? "text-white border-b-2 border-white"
                    : "text-white/40 hover:text-white/60"
                }`}
              >
                {tab}
                {tab === "comments" && unacknowledgedCount > 0 && (
                  <span className="text-[10px] bg-orange-500/20 text-orange-400 px-1.5 py-0.5 rounded-full leading-none">
                    {unacknowledgedCount}
                  </span>
                )}
              </button>
            ))}
          </div>

          {/* Tab content */}
          <div className="flex-1 overflow-y-auto p-4">
            {activeTab === "summary" && (
              <GoalSummary goal={selectedGoal} tasks={selectedTasks} logs={selectedLogs} learnings={selectedLearnings} />
            )}
            {activeTab === "tasks" && (
              <TaskPanel goal={selectedGoal} tasks={selectedTasks} onChanged={fetchAll} onGoalDeleted={() => setSelectedGoalId(null)} />
            )}
            {activeTab === "activity" && (
              <ActivityFeed logs={selectedGoalId ? selectedLogs : logs} goals={goals} />
            )}
            {activeTab === "learnings" && (
              <LearningsPanel learnings={selectedGoalId ? selectedLearnings : learnings} goals={goals} />
            )}
            {activeTab === "comments" && selectedGoalId && (
              <CommentsPanel comments={selectedComments} goalId={selectedGoalId} onChanged={fetchAll} />
            )}
            {activeTab === "comments" && !selectedGoalId && (
              <div className="flex items-center justify-center h-full">
                <p className="text-white/30 text-sm">Select a goal to view or add comments</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Add Goal Modal */}
      {showAddGoal && (
        <AddGoalForm
          onClose={() => setShowAddGoal(false)}
          onAdded={() => {
            fetchAll();
            setShowAddGoal(false);
          }}
        />
      )}
    </div>
  );
}
