"use client";

import { useState } from "react";
import { supabase } from "@/lib/supabase";
import { ModelSelector } from "@/components/ModelSelector";

interface Props {
  onClose: () => void;
  onAdded: () => void;
}

export function AddGoalForm({ onClose, onAdded }: Props) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState(5);
  const [model, setModel] = useState("");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;

    setSaving(true);
    const metadata: Record<string, unknown> = {};
    if (model) metadata.model = model;

    const { error } = await supabase.from("goals").insert({
      title: title.trim(),
      description: description.trim() || null,
      priority,
      status: "pending",
      created_by: "user",
      metadata,
    });

    if (!error) {
      onAdded();
    }
    setSaving(false);
  }

  return (
    <div className="fixed inset-0 bg-black/60 flex items-center justify-center z-50" onClick={onClose}>
      <div
        className="bg-[#111] border border-white/10 rounded-xl p-6 w-full max-w-md"
        onClick={(e) => e.stopPropagation()}
      >
        <h2 className="text-lg font-semibold mb-4">Add Goal</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-white/40 mb-1">Title</label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g., Build large Substack following"
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
              autoFocus
            />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="What should the agent work towards? Be specific about the desired outcome."
              rows={3}
              className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30 resize-none"
            />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Priority (1 = highest)</label>
            <input
              type="number"
              min={1}
              max={10}
              value={priority}
              onChange={(e) => setPriority(Number(e.target.value))}
              className="w-20 px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30"
            />
          </div>
          <div>
            <label className="block text-xs text-white/40 mb-1">Model (optional)</label>
            <ModelSelector value={model} onChange={setModel} />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-sm text-white/50 hover:text-white transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={!title.trim() || saving}
              className="px-4 py-2 text-sm bg-white text-black rounded-md hover:bg-white/90 disabled:opacity-50 transition-colors"
            >
              {saving ? "Adding..." : "Add Goal"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
