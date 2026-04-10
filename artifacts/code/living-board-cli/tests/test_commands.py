"""Smoke tests for commands. We inject a fake client; no network."""

from __future__ import annotations

import argparse
from typing import Any

import pytest

from living_board_cli import commands
from living_board_cli.client import Client, Config


class FakeClient:
    """A minimal Client stand-in that returns canned rows."""

    def __init__(self, tables: dict[str, list[dict[str, Any]]]) -> None:
        self._tables = tables
        self.inserts: list[tuple[str, list[dict[str, Any]]]] = []

    def query(self, table: str, **kwargs: Any) -> list[dict[str, Any]]:
        return list(self._tables.get(table, []))

    def insert(self, table: str, rows: Any) -> list[dict[str, Any]]:
        payload = [rows] if isinstance(rows, dict) else list(rows)
        self.inserts.append((table, payload))
        return payload

    def check(self) -> bool:
        return True


def _ns(**kwargs: Any) -> argparse.Namespace:
    return argparse.Namespace(**kwargs)


def test_cmd_goals_renders_table(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "goals": [
                {
                    "id": "aaaaaaaa-1111",
                    "title": "Ship the CLI",
                    "status": "in_progress",
                    "priority": 2,
                    "created_by": "agent",
                    "created_at": "2026-04-10T12:00:00Z",
                }
            ]
        }
    )
    commands.cmd_goals(client, _ns(status=None, limit=10, json=False))
    captured = capsys.readouterr().out
    assert "Ship the CLI" in captured
    assert "P2" in captured
    assert "aaaaaaaa" in captured
    assert "1 goal(s)" in captured


def test_cmd_goals_json(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(tables={"goals": [{"id": "x", "title": "t"}]})
    commands.cmd_goals(client, _ns(status=None, limit=10, json=True))
    out = capsys.readouterr().out
    assert '"title": "t"' in out


def test_cmd_tasks_shows_attempts(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "tasks": [
                {
                    "id": "tid",
                    "goal_id": "gid",
                    "title": "Do thing",
                    "status": "pending",
                    "sort_order": 10,
                    "attempts": 1,
                    "max_attempts": 3,
                    "created_at": "2026-04-10T12:00:00Z",
                }
            ]
        }
    )
    commands.cmd_tasks(client, _ns(goal=None, status=None, limit=10, json=False))
    out = capsys.readouterr().out
    assert "Do thing" in out
    assert "1/3" in out


def test_cmd_log_shows_action(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "execution_log": [
                {
                    "id": "lid",
                    "action": "execute",
                    "summary": "Wrote article #8",
                    "goal_id": "gid",
                    "task_id": "tid",
                    "created_at": "2026-04-10T15:00:00Z",
                }
            ]
        }
    )
    commands.cmd_log(client, _ns(limit=10, json=False))
    out = capsys.readouterr().out
    assert "execute" in out
    assert "Wrote article #8" in out


def test_cmd_learnings_shows_confidence(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "learnings": [
                {
                    "id": "lrid",
                    "category": "strategy",
                    "content": "Build more CLIs",
                    "confidence": 0.87,
                    "goal_id": "gid",
                    "created_at": "2026-04-10T12:00:00Z",
                }
            ]
        }
    )
    commands.cmd_learnings(client, _ns(goal=None, category=None, limit=10, json=False))
    out = capsys.readouterr().out
    assert "0.87" in out
    assert "Build more CLIs" in out


def test_cmd_snapshot_empty(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(tables={"snapshots": []})
    commands.cmd_snapshot(client, _ns(json=False))
    assert "(no snapshots yet)" in capsys.readouterr().out


def test_cmd_snapshot_shows_fields(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "snapshots": [
                {
                    "content": "Operating in degraded mode",
                    "current_focus": "Build CLI",
                    "cycle_count": 53,
                    "created_at": "2026-04-10T15:00:00Z",
                }
            ]
        }
    )
    commands.cmd_snapshot(client, _ns(json=False))
    out = capsys.readouterr().out
    assert "Build CLI" in out
    assert "53" in out
    assert "Operating in degraded mode" in out


def test_cmd_stats_aggregates_counts(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(
        tables={
            "goals": [
                {"status": "in_progress"},
                {"status": "in_progress"},
                {"status": "done"},
            ],
            "tasks": [
                {"status": "pending"},
                {"status": "done"},
            ],
            "execution_log": [
                {"action": "execute"},
                {"action": "execute"},
                {"action": "reflect"},
            ],
            "learnings": [{"id": "1"}, {"id": "2"}],
        }
    )
    commands.cmd_stats(client, _ns(json=False))
    out = capsys.readouterr().out
    assert "in_progress=2" in out
    assert "done=1" in out
    assert "execute=2" in out
    assert "reflect=1" in out
    assert "2" in out  # learnings total


def test_cmd_comment_inserts_and_prints(capsys: pytest.CaptureFixture[str]) -> None:
    client = FakeClient(tables={})
    commands.cmd_comment(
        client,
        _ns(goal="goal-uuid-1234", type="direction_change", content="focus on CLI"),
    )
    out = capsys.readouterr().out
    assert "direction_change" in out
    assert "focus on CLI" in out
    assert client.inserts == [
        (
            "goal_comments",
            [
                {
                    "goal_id": "goal-uuid-1234",
                    "author": "user",
                    "comment_type": "direction_change",
                    "content": "focus on CLI",
                }
            ],
        )
    ]
