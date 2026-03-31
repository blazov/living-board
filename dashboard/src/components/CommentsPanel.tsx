"use client";

import { useState } from "react";
import type { GoalComment } from "@/lib/types";
import { supabase } from "@/lib/supabase";
import { formatTimeAgo } from "@/lib/utils";

const TYPE_COLOR: Record<string, string> = {
  question: "text-purple-400 bg-purple-500/10",
  direction_change: "text-orange-400 bg-orange-500/10",
  feedback: "text-green-400 bg-green-500/10",
  note: "text-white/40 bg-white/5",
};

const TYPE_LABELS: Record<string, string> = {
  question: "question",
  direction_change: "direction",
  feedback: "feedback",
  note: "note",
};

const COMMENT_TYPES = ["note", "question", "direction_change", "feedback"] as const;

interface Props {
  comments: GoalComment[];
  goalId: string;
  onChanged: () => void;
}

export function CommentsPanel({ comments, goalId, onChanged }: Props) {
  const [content, setContent] = useState("");
  const [commentType, setCommentType] = useState<GoalComment["comment_type"]>("note");
  const [saving, setSaving] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!content.trim()) return;
    setSaving(true);
    await supabase.from("goal_comments").insert({
      goal_id: goalId,
      author: "user",
      comment_type: commentType,
      content: content.trim(),
    });
    setContent("");
    setCommentType("note");
    setSaving(false);
    onChanged();
  }

  return (
    <div className="max-w-2xl space-y-4">
      {/* Add comment form */}
      <form onSubmit={handleSubmit} className="p-3 rounded-lg border border-white/10 bg-white/[0.02] space-y-3">
        <textarea
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Add a comment, question, or direction change..."
          rows={3}
          className="w-full px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-sm focus:outline-none focus:border-white/30 resize-none placeholder:text-white/20"
        />
        <div className="flex items-center justify-between">
          <div className="flex gap-1.5">
            {COMMENT_TYPES.map((type) => (
              <button
                key={type}
                type="button"
                onClick={() => setCommentType(type)}
                className={`text-[10px] px-2 py-1 rounded transition-colors ${
                  commentType === type
                    ? TYPE_COLOR[type] + " ring-1 ring-white/20"
                    : "text-white/30 bg-white/5 hover:bg-white/10"
                }`}
              >
                {TYPE_LABELS[type]}
              </button>
            ))}
          </div>
          <button
            type="submit"
            disabled={!content.trim() || saving}
            className="px-3 py-1.5 text-xs bg-white text-black rounded-md hover:bg-white/90 disabled:opacity-50 transition-colors"
          >
            {saving ? "Sending..." : "Send"}
          </button>
        </div>
      </form>

      {/* Comments list */}
      {comments.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-white/30 text-sm">No comments yet</p>
          <p className="text-white/20 text-xs mt-1">
            Add a comment to give the agent direction, ask questions, or leave feedback
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          {comments.map((comment) => {
            const typeColor = TYPE_COLOR[comment.comment_type] ?? "text-white/40 bg-white/5";
            const isAgent = comment.author === "agent";
            const isPending = !comment.acknowledged_at && comment.author === "user";

            return (
              <div
                key={comment.id}
                className={`p-3 rounded-lg border ${
                  isAgent ? "border-blue-500/10 bg-blue-500/[0.02]" : "border-white/5"
                }`}
              >
                <div className="flex items-start gap-2 mb-1.5">
                  {/* Author badge */}
                  <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${
                    isAgent ? "text-blue-400 bg-blue-500/10" : "text-white/50 bg-white/10"
                  }`}>
                    {comment.author}
                  </span>
                  {/* Type badge */}
                  <span className={`text-[10px] px-1.5 py-0.5 rounded flex-shrink-0 ${typeColor}`}>
                    {TYPE_LABELS[comment.comment_type] ?? comment.comment_type}
                  </span>
                  <span className="flex-1" />
                  {/* Pending indicator */}
                  {isPending && (
                    <span className="flex items-center gap-1 text-[10px] text-orange-400/60">
                      <span className="w-1.5 h-1.5 rounded-full bg-orange-400/60" />
                      pending
                    </span>
                  )}
                  <span className="text-[10px] text-white/20 flex-shrink-0">
                    {formatTimeAgo(comment.created_at)}
                  </span>
                </div>

                {/* Content */}
                <p className="text-sm text-white/70 leading-relaxed">{comment.content}</p>

                {/* Agent response */}
                {comment.agent_response && (
                  <div className="mt-2 ml-3 pl-3 border-l-2 border-blue-500/20">
                    <div className="flex items-center gap-1.5 mb-0.5">
                      <span className="text-[10px] text-blue-400/60">agent response</span>
                      {comment.acknowledged_at && (
                        <span className="text-[10px] text-white/20">
                          {formatTimeAgo(comment.acknowledged_at)}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-white/50 leading-relaxed">{comment.agent_response}</p>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
