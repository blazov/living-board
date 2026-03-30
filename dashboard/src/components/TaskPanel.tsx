"use client";

import { useState } from "react";
import type { Goal, Task } from "@/lib/types";
import { supabase } from "@/lib/supabase";
import { ModelSelector } from "@/components/ModelSelector";

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
  onChanged: () => void;
}

export function TaskPanel({ goal, tasks, onChanged }: Props) {
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newModel, setNewModel] = useState<string>("");
  const [saving, setSaving] = useState(false);

  if (!goal) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-white/30 text-sm">Select a goal to see its tasks</p>
      </div>
    );
  }

  const goalModel = (goal.metadata?.model as string) ?? "";

  async function handleAddTask(e: React.FormEvent) {
    e.preventDefault();
    if (!newTitle.trim() || !goal) return;
    setSaving(true);

    const maxOrder = tasks.reduce((max, t) => Math.max(max, t.sort_order), 0);
    const metadata: Record<string, unknown> = { created_by: "user" };
    if (newModel) metadata.model = newModel;

    await supabase.from("tasks").insert({
      goal_id: goal.id,
      title: newTitle.trim(),
      description: newDesc.trim() || null,
      sort_order: maxOrder + 10,
      metadata,
    });

    setNewTitle("");
    setNewDesc("");
    setNewModel("");
    setShowAddTask(false);
    setSaving(false);
    onChanged();
  }

  async function handleGoalModelChange(model: string) {
    if (!goal) return;
    const newMeta = { ...goal.metadata, model: model || undefined };
    if (!model) delete newMeta.model;
    await supabase.from("goals").update({ metadata: newMeta }).eq("id", goal.id);
    onChanged();
  }

  async function handleTaskModelChange(task: Task, model: string) {
    const newMeta = { ...task.metadata, model: model || undefined };
    if (!model) delete newMeta.model;
    await supabase.from("tasks").update({ metadata: newMeta }).eq("id", task.id);
    onChanged();
  }

  return (
    <div className="max-w-2xl">
      <div className="mb-6">
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1">
            <h2 className="text-lg font-semibold">{goal.title}</h2>
            {goal.description && (
              <p className="text-sm text-white/50 mt-1">{goal.description}</p>
            )}
          </div>
          <ModelSelector value={goalModel} onChange={handleGoalModelChange} label="Goal model" />
        </div>
        <div className="flex items-center gap-3 mt-2 text-xs text-white/30">
          <span>Priority: {goal.priority}</span>
          <span>Created by: {goal.created_by}</span>
          {goal.completed_at && (
            <span>Completed: {new Date(goal.completed_at).toLocaleDateString()}</span>
          )}
        </div>
      </div>

      {tasks.length === 0 && !showAddTask ? (
        <div className="border border-dashed border-white/10 rounded-lg p-6 text-center">
          <p className="text-sm text-white/30">No tasks yet</p>
          <p className="text-xs text-white/20 mt-1">
            The agent will decompose this goal into tasks on its next cycle
          </p>
          <button
            onClick={() => setShowAddTask(true)}
            className="mt-3 text-xs text-white/40 hover:text-white/60 transition-colors"
          >
            + Add task manually
          </button>
        </div>
      ) : (
        <div className="space-y-1">
          {tasks.map((task) => {
            const taskModel = (task.metadata?.model as string) ?? "";
            return (
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
                    <div className="flex items-start justify-between gap-2">
                      <p className={`text-sm font-medium ${task.status === "done" ? "text-white/40 line-through" : ""}`}>
                        {task.title}
                      </p>
                      {task.status !== "done" && (
                        <ModelSelector
                          value={taskModel}
                          onChange={(m) => handleTaskModelChange(task, m)}
                          size="sm"
                        />
                      )}
                    </div>
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
            );
          })}

          {!showAddTask && (
            <button
              onClick={() => setShowAddTask(true)}
              className="w-full p-2 text-xs text-white/30 hover:text-white/50 hover:bg-white/[0.02] rounded-lg border border-dashed border-white/5 transition-colors"
            >
              + Add task
            </button>
          )}
        </div>
      )}

      {showAddTask && (
        <form onSubmit={handleAddTask} className="mt-2 p-3 rounded-lg border border-white/10 bg-white/[0.02] space-y-3">
          <input
            type="text"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Task title"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
            autoFocus
          />
          <textarea
            value={newDesc}
            onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)"
            rows={2}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30 resize-none"
          />
          <div className="flex items-center justify-between">
            <ModelSelector value={newModel} onChange={setNewModel} label="Model" />
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => { setShowAddTask(false); setNewTitle(""); setNewDesc(""); setNewModel(""); }}
                className="px-3 py-1.5 text-xs text-white/40 hover:text-white/60"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={!newTitle.trim() || saving}
                className="px-3 py-1.5 text-xs bg-white text-black rounded-md hover:bg-white/90 disabled:opacity-50"
              >
                {saving ? "Adding..." : "Add"}
              </button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
