export interface Goal {
  id: string;
  title: string;
  description: string | null;
  status: "pending" | "in_progress" | "done" | "blocked" | "archived";
  priority: number;
  parent_goal_id: string | null;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  created_by: "user" | "agent";
  metadata: Record<string, unknown>;
}

export interface Task {
  id: string;
  goal_id: string;
  title: string;
  description: string | null;
  status: "pending" | "in_progress" | "done" | "blocked" | "skipped";
  sort_order: number;
  attempts: number;
  max_attempts: number;
  result: string | null;
  blocked_reason: string | null;
  depends_on: string[];
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  started_at: string | null;
  metadata: Record<string, unknown>;
}

export interface ExecutionLog {
  id: string;
  trigger_run_id: string | null;
  goal_id: string | null;
  task_id: string | null;
  action: string;
  summary: string;
  details: Record<string, unknown>;
  duration_ms: number | null;
  created_at: string;
}

export interface Learning {
  id: string;
  goal_id: string | null;
  task_id: string | null;
  category: string;
  content: string;
  confidence: number;
  times_validated: number;
  created_at: string;
  updated_at: string;
}
