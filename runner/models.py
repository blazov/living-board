"""Pydantic models matching the Supabase schema."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class Goal(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str = "pending"
    priority: int = 5
    parent_id: str | None = None
    created_by: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class Task(BaseModel):
    id: str
    goal_id: str
    title: str
    description: str | None = None
    status: str = "pending"
    sort_order: int = 10
    attempts: int = 0
    max_attempts: int = 3
    result: str | None = None
    blocked_reason: str | None = None
    depends_on: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None


class ExecutionLog(BaseModel):
    id: str | None = None
    goal_id: str | None = None
    task_id: str | None = None
    action: str
    summary: str
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime | None = None


class Learning(BaseModel):
    id: str | None = None
    goal_id: str | None = None
    task_id: str | None = None
    category: str = "domain_knowledge"
    content: str
    confidence: float = 0.8
    times_validated: int = 0
    created_at: datetime | None = None


class Snapshot(BaseModel):
    id: str | None = None
    content: str
    active_goals: str | None = None
    current_focus: str | None = None
    recent_outcomes: str | None = None
    open_blockers: str | None = None
    key_learnings: str | None = None
    cycle_count: int = 0
    created_at: datetime | None = None


class GoalComment(BaseModel):
    id: str
    goal_id: str
    comment_type: str  # question, direction_change, feedback, note
    content: str
    acknowledged_at: datetime | None = None
    agent_response: str | None = None
    created_at: datetime | None = None
    goal_title: str | None = None


class AgentContext(BaseModel):
    """Assembled context from the Orient phase."""
    snapshot: Snapshot | None = None
    goals: list[Goal] = Field(default_factory=list)
    tasks: list[Task] = Field(default_factory=list)
    recent_logs: list[ExecutionLog] = Field(default_factory=list)
    learnings: list[Learning] = Field(default_factory=list)
    comments: list[GoalComment] = Field(default_factory=list)
    memory_results: list[dict[str, Any]] = Field(default_factory=list)
    needs_reflection: bool = False
    needs_email_check: bool = False


class Decision(BaseModel):
    """Output of the Decide phase."""
    action: str  # "execute_task", "decompose_goal", "mark_goal_done", "reflect"
    goal_id: str | None = None
    task_id: str | None = None
    reasoning: str = ""
    new_tasks: list[dict[str, Any]] = Field(default_factory=list)


class CycleResult(BaseModel):
    """Result of a full agent cycle."""
    action: str
    goal_id: str | None = None
    task_id: str | None = None
    summary: str = ""
    learnings: list[str] = Field(default_factory=list)
    duration_ms: int = 0
    success: bool = True
