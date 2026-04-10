"""Smoke tests for the argparse wiring.

We patch Config.from_env so main() doesn't need real credentials, and we stub
Client.query so nothing touches the network.
"""

from __future__ import annotations

from typing import Any

import pytest

from living_board_cli import cli
from living_board_cli.client import Client, Config, LivingBoardError


class FakeClient:
    def __init__(self, *_: Any, **__: Any) -> None:
        pass

    def query(self, table: str, **kwargs: Any) -> list[dict[str, Any]]:
        return []

    def insert(self, table: str, rows: Any) -> list[dict[str, Any]]:
        return []

    def check(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def _stub_config_and_client(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cli, "Config", type("C", (), {"from_env": staticmethod(lambda: Config(url="x", anon_key="y"))}))
    monkeypatch.setattr(cli, "Client", FakeClient)


def test_help_runs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--help"])
    assert exc.value.code == 0
    assert "goals" in capsys.readouterr().out


def test_version_runs(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        cli.main(["--version"])
    assert exc.value.code == 0


def test_goals_dispatch(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["goals"])
    assert rc == 0
    # Empty query → "(no rows)" from the table renderer.
    assert "(no rows)" in capsys.readouterr().out


def test_stats_dispatch(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["stats"])
    assert rc == 0
    out = capsys.readouterr().out
    assert "goals" in out
    assert "tasks" in out


def test_check_command(capsys: pytest.CaptureFixture[str]) -> None:
    rc = cli.main(["check"])
    assert rc == 0
    assert "OK" in capsys.readouterr().out


def test_missing_credentials_returns_nonzero(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    def boom() -> Config:
        raise LivingBoardError("missing creds")

    monkeypatch.setattr(cli, "Config", type("C", (), {"from_env": staticmethod(boom)}))
    rc = cli.main(["goals"])
    assert rc == 1
    assert "missing creds" in capsys.readouterr().err
