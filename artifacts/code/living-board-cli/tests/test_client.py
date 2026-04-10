"""Tests for Client URL construction and Config loading.

We stub _request so nothing touches the network.
"""

from __future__ import annotations

from typing import Any

import pytest

from living_board_cli.client import Client, Config, LivingBoardError


class RecordingClient(Client):
    """Captures the (path, method, data) tuple that would be sent."""

    def __init__(self, config: Config, response: Any = None) -> None:
        super().__init__(config)
        self.calls: list[tuple[str, str, Any]] = []
        self._response = response

    def _request(self, path: str, method: str = "GET", data: Any = None) -> Any:
        self.calls.append((path, method, data))
        return self._response


@pytest.fixture()
def config() -> Config:
    return Config(url="https://example.supabase.co", anon_key="anon-key-123")


def test_config_from_env_requires_both(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("NEXT_PUBLIC_SUPABASE_URL", raising=False)
    monkeypatch.delenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", raising=False)
    monkeypatch.delenv("LIVING_BOARD_SUPABASE_URL", raising=False)
    monkeypatch.delenv("LIVING_BOARD_SUPABASE_KEY", raising=False)
    with pytest.raises(LivingBoardError):
        Config.from_env()


def test_config_from_env_prefers_living_board_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LIVING_BOARD_SUPABASE_URL", "https://lb.example.co/")
    monkeypatch.setenv("LIVING_BOARD_SUPABASE_KEY", "lb-key")
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "https://next.example.co")
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "next-key")
    cfg = Config.from_env()
    assert cfg.url == "https://lb.example.co"  # trailing slash stripped
    assert cfg.anon_key == "lb-key"


def test_config_from_env_falls_back_to_next_public(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LIVING_BOARD_SUPABASE_URL", raising=False)
    monkeypatch.delenv("LIVING_BOARD_SUPABASE_KEY", raising=False)
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_URL", "https://next.example.co")
    monkeypatch.setenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "next-key")
    cfg = Config.from_env()
    assert cfg.url == "https://next.example.co"
    assert cfg.anon_key == "next-key"


def test_query_builds_select_and_filters(config: Config) -> None:
    client = RecordingClient(config, response=[])
    client.query(
        "goals",
        select="id,title",
        filters={"status": "in.(in_progress,pending)"},
        order="priority.asc",
        limit=5,
    )
    path, method, data = client.calls[0]
    assert method == "GET"
    assert data is None
    assert path.startswith("goals?")
    assert "select=id%2Ctitle" in path
    assert "status=in." in path
    assert "order=priority.asc" in path
    assert "limit=5" in path


def test_query_raises_when_response_not_list(config: Config) -> None:
    client = RecordingClient(config, response={"not": "a list"})
    with pytest.raises(LivingBoardError):
        client.query("goals")


def test_insert_wraps_single_dict_in_list(config: Config) -> None:
    client = RecordingClient(config, response=[{"id": "1"}])
    client.insert("tasks", {"title": "hello"})
    _, method, data = client.calls[0]
    assert method == "POST"
    assert data == [{"title": "hello"}]


def test_insert_passes_through_list(config: Config) -> None:
    client = RecordingClient(config, response=[])
    client.insert("tasks", [{"title": "a"}, {"title": "b"}])
    _, _, data = client.calls[0]
    assert data == [{"title": "a"}, {"title": "b"}]


def test_update_requires_filters(config: Config) -> None:
    client = RecordingClient(config, response=[])
    with pytest.raises(LivingBoardError):
        client.update("tasks", filters={}, fields={"status": "done"})


def test_update_encodes_filters_and_uses_patch(config: Config) -> None:
    client = RecordingClient(config, response=[])
    client.update("tasks", filters={"id": "eq.abc"}, fields={"status": "done"})
    path, method, data = client.calls[0]
    assert method == "PATCH"
    assert path == "tasks?id=eq.abc"
    assert data == {"status": "done"}
