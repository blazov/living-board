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
  onGoalDeleted: () => void;
}

export function TaskPanel({ goal, tasks, onChanged, onGoalDeleted }: Props) {
  const [showAddTask, setShowAddTask] = useState(false);
  const [newTitle, setNewTitle] = useState("");
  const [newDesc, setNewDesc] = useState("");
  const [newModel, setNewModel] = useState<string>("");
  const [saving, setSaving] = useState(false);
  const [editingGoal, setEditingGoal] = useState(false);
  const [goalTitle, setGoalTitle] = useState("");
  const [goalDesc, setGoalDesc] = useState("");
  const [goalPriority, setGoalPriority] = useState(5);
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null);
  const [editTaskTitle, setEditTaskTitle] = useState("");
  const [editTaskDesc, setEditTaskDesc] = useState("");
  const [triggeringTaskId, setTriggeringTaskId] = useState<string | null>(null);
  const [triggerStatus, setTriggerStatus] = useState<string | null>(null);

  if (!goal) {
    return (
      <div className="flex items-center justify-center h-full">
        <p className="text-white/30 text-sm">Select a goal to see its tasks</p>
      </div>
    );
  }

  const goalModel = (goal.metadata?.model as string) ?? "";

  // --- Goal actions ---

  function startEditGoal() {
    setGoalTitle(goal!.title);
    setGoalDesc(goal!.description ?? "");
    setGoalPriority(goal!.priority);
    setEditingGoal(true);
  }

  async function saveGoal() {
    if (!goal || !goalTitle.trim()) return;
    await supabase.from("goals").update({
      title: goalTitle.trim(),
      description: goalDesc.trim() || null,
      priority: goalPriority,
    }).eq("id", goal.id);
    setEditingGoal(false);
    onChanged();
  }

  async function deleteGoal() {
    if (!goal) return;
    if (!confirm(`Delete goal "${goal.title}" and all its tasks?`)) return;
    await supabase.from("tasks").delete().eq("goal_id", goal.id);
    await supabase.from("goals").delete().eq("id", goal.id);
    onGoalDeleted();
    onChanged();
  }

  async function handleGoalModelChange(model: string) {
    if (!goal) return;
    const newMeta = { ...goal.metadata, model: model || undefined };
    if (!model) delete newMeta.model;
    await supabase.from("goals").update({ metadata: newMeta }).eq("id", goal.id);
    onChanged();
  }

  // --- Task actions ---

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
    setNewTitle(""); setNewDesc(""); setNewModel("");
    setShowAddTask(false); setSaving(false);
    onChanged();
  }

  function startEditTask(task: Task) {
    setEditingTaskId(task.id);
    setEditTaskTitle(task.title);
    setEditTaskDesc(task.description ?? "");
  }

  async function saveTask(taskId: string) {
    if (!editTaskTitle.trim()) return;
    await supabase.from("tasks").update({
      title: editTaskTitle.trim(),
      description: editTaskDesc.trim() || null,
    }).eq("id", taskId);
    setEditingTaskId(null);
    onChanged();
  }

  async function deleteTask(task: Task) {
    if (!confirm(`Delete task "${task.title}"?`)) return;
    await supabase.from("tasks").delete().eq("id", task.id);
    onChanged();
  }

  async function handleTaskModelChange(task: Task, model: string) {
    const newMeta = { ...task.metadata, model: model || undefined };
    if (!model) delete newMeta.model;
    await supabase.from("tasks").update({ metadata: newMeta }).eq("id", task.id);
    onChanged();
  }

  async function triggerTask(task: Task) {
    setTriggeringTaskId(task.id);
    setTriggerStatus(null);
    try {
      const res = await fetch("/api/trigger", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ task_id: task.id }),
      });
      if (res.ok) {
        setTriggerStatus("Agent triggered -- task queued as active");
      } else {
        const data = await res.json().catch(() => ({}));
        if (res.status === 503) {
          // No trigger configured, but task is still marked in_progress
          await supabase.from("tasks").update({
            status: "in_progress",
            started_at: new Date().toISOString(),
          }).eq("id", task.id);
          setTriggerStatus("Task marked active -- agent will pick it up next cycle");
        } else {
          setTriggerStatus(`Error: ${data.error || "Failed to trigger"}`);
        }
      }
    } catch {
      setTriggerStatus("Network error");
    }
    onChanged();
    setTimeout(() => { setTriggeringTaskId(null); setTriggerStatus(null); }, 4000);
  }

  return (
    <div className="max-w-2xl">
      {/* Goal header */}
      <div className="mb-6">
        {editingGoal ? (
          <div className="space-y-2 p-3 rounded-lg border border-white/10 bg-white/[0.02]">
            <input
              value={goalTitle}
              onChange={(e) => setGoalTitle(e.target.value)}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
              autoFocus
            />
            <textarea
              value={goalDesc}
              onChange={(e) => setGoalDesc(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30 resize-none"
            />
            <div className="flex items-center gap-3">
              <label className="text-xs text-white/30">Priority:</label>
              <input
                type="number" min={1} max={10} value={goalPriority}
                onChange={(e) => setGoalPriority(Number(e.target.value))}
                className="w-16 px-2 py-1 bg-white/5 border border-white/10 rounded text-xs focus:outline-none focus:border-white/30"
              />
              <div className="flex-1" />
              <button onClick={() => setEditingGoal(false)} className="px-3 py-1 text-xs text-white/40 hover:text-white/60">Cancel</button>
              <button onClick={saveGoal} className="px-3 py-1 text-xs bg-white text-black rounded hover:bg-white/90">Save</button>
            </div>
          </div>
        ) : (
          <>
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
              <span className="text-white/10">|</span>
              <button onClick={startEditGoal} className="text-white/30 hover:text-white/60 transition-colors">edit</button>
              <button onClick={deleteGoal} className="text-red-400/40 hover:text-red-400 transition-colors">delete</button>
            </div>
          </>
        )}
      </div>

      {/* Tasks list */}
      {tasks.length === 0 && !showAddTask ? (
        <div className="border border-dashed border-white/10 rounded-lg p-6 text-center">
          <p className="text-sm text-white/30">No tasks yet</p>
          <p className="text-xs text-white/20 mt-1">The agent will decompose this goal into tasks on its next cycle</p>
          <button onClick={() => setShowAddTask(true)} className="mt-3 text-xs text-white/40 hover:text-white/60 transition-colors">
            + Add task manually
          </button>
        </div>
      ) : (
        <div className="space-y-1">
          {tasks.map((task) => {
            const taskModel = (task.metadata?.model as string) ?? "";
            const isEditing = editingTaskId === task.id;
            const isTriggering = triggeringTaskId === task.id;

            return (
              <div
                key={task.id}
                className={`p-3 rounded-lg border border-white/5 ${
                  task.status === "in_progress" ? "bg-blue-500/5 border-blue-500/20" : ""
                }`}
              >
                {isEditing ? (
                  <div className="space-y-2">
                    <input
                      value={editTaskTitle}
                      onChange={(e) => setEditTaskTitle(e.target.value)}
                      className="w-full px-2 py-1.5 bg-white/5 border border-white/10 rounded text-sm focus:outline-none focus:border-white/30"
                      autoFocus
                      onKeyDown={(e) => { if (e.key === "Enter") saveTask(task.id); if (e.key === "Escape") setEditingTaskId(null); }}
                    />
                    <textarea
                      value={editTaskDesc}
                      onChange={(e) => setEditTaskDesc(e.target.value)}
                      rows={2}
                      className="w-full px-2 py-1.5 bg-white/5 border border-white/10 rounded text-xs focus:outline-none focus:border-white/30 resize-none"
                    />
                    <div className="flex justify-end gap-2">
                      <button onClick={() => setEditingTaskId(null)} className="px-2 py-1 text-[10px] text-white/40 hover:text-white/60">Cancel</button>
                      <button onClick={() => saveTask(task.id)} className="px-2 py-1 text-[10px] bg-white text-black rounded hover:bg-white/90">Save</button>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-start gap-3">
                    <span className={`text-sm mt-0.5 ${STATUS_COLOR[task.status]}`}>
                      {STATUS_ICON[task.status]}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between gap-2">
                        <p className={`text-sm font-medium ${task.status === "done" ? "text-white/40 line-through" : ""}`}>
                          {task.title}
                        </p>
                        <div className="flex items-center gap-1.5 flex-shrink-0">
                          {task.status !== "done" && (
                            <ModelSelector value={taskModel} onChange={(m) => handleTaskModelChange(task, m)} size="sm" />
                          )}
                        </div>
                      </div>
                      {task.description && (
                        <p className="text-xs text-white/30 mt-0.5">{task.description}</p>
                      )}
                      {task.result && (
                        <p className="text-xs text-green-400/70 mt-1 bg-green-500/5 px-2 py-1 rounded">{task.result}</p>
                      )}
                      {task.blocked_reason && (
                        <p className="text-xs text-red-400/70 mt-1 bg-red-500/5 px-2 py-1 rounded">Blocked: {task.blocked_reason}</p>
                      )}
                      {isTriggering && triggerStatus && (
                        <p className="text-xs text-blue-400/70 mt-1 bg-blue-500/5 px-2 py-1 rounded">{triggerStatus}</p>
                      )}
                      <div className="flex items-center gap-2 mt-1.5 text-[10px] text-white/20">
                        {task.attempts > 0 && <span>Attempts: {task.attempts}/{task.max_attempts}</span>}
                        {task.completed_at && <span>Done: {new Date(task.completed_at).toLocaleString()}</span>}
                        <span className="flex-1" />
                        {task.status !== "done" && (
                          <button
                            onClick={() => triggerTask(task)}
                            disabled={isTriggering}
                            className="text-blue-400/50 hover:text-blue-400 transition-colors disabled:opacity-30"
                          >
                            {isTriggering ? "triggering..." : "run now"}
                          </button>
                        )}
                        <button onClick={() => startEditTask(task)} className="text-white/20 hover:text-white/50 transition-colors">edit</button>
                        <button onClick={() => deleteTask(task)} className="text-red-400/30 hover:text-red-400 transition-colors">delete</button>
                      </div>
                    </div>
                  </div>
                )}
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
            type="text" value={newTitle} onChange={(e) => setNewTitle(e.target.value)}
            placeholder="Task title"
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
            autoFocus
          />
          <textarea
            value={newDesc} onChange={(e) => setNewDesc(e.target.value)}
            placeholder="Description (optional)" rows={2}
            className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30 resize-none"
          />
          <div className="flex items-center justify-between">
            <ModelSelector value={newModel} onChange={setNewModel} label="Model" />
            <div className="flex gap-2">
              <button type="button" onClick={() => { setShowAddTask(false); setNewTitle(""); setNewDesc(""); setNewModel(""); }} className="px-3 py-1.5 text-xs text-white/40 hover:text-white/60">Cancel</button>
              <button type="submit" disabled={!newTitle.trim() || saving} className="px-3 py-1.5 text-xs bg-white text-black rounded-md hover:bg-white/90 disabled:opacity-50">{saving ? "Adding..." : "Add"}</button>
            </div>
          </div>
        </form>
      )}
    </div>
  );
}
