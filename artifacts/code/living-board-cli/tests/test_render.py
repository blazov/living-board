"""Tests for render helpers. No network, no Supabase."""

from __future__ import annotations

import io
import sys

import pytest

from living_board_cli.render import render_kv, render_table, short_id, short_ts, truncate


def test_truncate_shorter_than_width() -> None:
    assert truncate("hello", 10) == "hello"


def test_truncate_longer_than_width_adds_ellipsis() -> None:
    assert truncate("hello world", 7) == "hello …"


def test_truncate_handles_none() -> None:
    assert truncate(None, 5) == ""


def test_truncate_replaces_newlines_and_tabs() -> None:
    assert truncate("a\nb\tc", 10) == "a b c"


def test_render_table_empty_rows() -> None:
    out = render_table(["A", "B"], [])
    assert "(no rows)" in out


def test_render_table_basic() -> None:
    out = render_table(["ID", "NAME"], [["1", "alpha"], ["2", "beta"]])
    lines = out.splitlines()
    # Header, separator, then one line per row.
    assert len(lines) == 4
    assert "ID" in lines[0] and "NAME" in lines[0]
    assert "alpha" in lines[2]
    assert "beta" in lines[3]


def test_render_table_none_cells_become_blank() -> None:
    out = render_table(["A", "B"], [[None, "x"]])
    # None should not appear literally.
    assert "None" not in out


def test_render_kv_empty() -> None:
    assert render_kv([]) == "(empty)"


def test_render_kv_aligns_keys() -> None:
    out = render_kv([("a", 1), ("longer", 2)])
    lines = out.splitlines()
    assert lines[0].startswith("a")
    assert lines[1].startswith("longer")
    # Both values should start at the same column.
    assert lines[0].index("1") == lines[1].index("2")


def test_short_id_truncates() -> None:
    assert short_id("abcdef1234", length=6) == "abcdef"


def test_short_id_handles_none() -> None:
    assert short_id(None) == ""


def test_short_ts_full_iso() -> None:
    assert short_ts("2026-04-10T15:30:45.123Z") == "2026-04-10 15:30"


def test_short_ts_passes_through_when_short() -> None:
    assert short_ts("2026-04-10") == "2026-04-10"


def test_short_ts_none() -> None:
    assert short_ts(None) == ""
