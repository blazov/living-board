"""Minimal Supabase PostgREST client — stdlib only, no external deps.

This is intentionally a small subset of the schema: the read/write paths the
CLI actually needs. The full runner uses pydantic models; the CLI uses plain
dicts to keep the dependency surface at zero.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Iterable


class LivingBoardError(RuntimeError):
    """Any failure talking to Supabase."""


@dataclass(frozen=True)
class Config:
    url: str
    anon_key: str

    @classmethod
    def from_env(cls) -> "Config":
        url = os.getenv("LIVING_BOARD_SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL", "")
        key = os.getenv("LIVING_BOARD_SUPABASE_KEY") or os.getenv("NEXT_PUBLIC_SUPABASE_ANON_KEY", "")
        if not url or not key:
            raise LivingBoardError(
                "Supabase credentials not found. Set either:\n"
                "  LIVING_BOARD_SUPABASE_URL + LIVING_BOARD_SUPABASE_KEY, or\n"
                "  NEXT_PUBLIC_SUPABASE_URL + NEXT_PUBLIC_SUPABASE_ANON_KEY\n"
                "(the latter matches the dashboard/.env.local conventions)."
            )
        return cls(url=url.rstrip("/"), anon_key=key)


class Client:
    """Tiny PostgREST client.

    Only exposes query(), insert(), update() — enough to implement every
    CLI command. Higher-level helpers live in commands.py.
    """

    def __init__(self, config: Config, timeout: float = 30.0) -> None:
        self._config = config
        self._timeout = timeout

    def query(
        self,
        table: str,
        select: str = "*",
        filters: dict[str, str] | None = None,
        order: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        params: list[tuple[str, str]] = [("select", select)]
        if filters:
            for key, value in filters.items():
                params.append((key, value))
        if order:
            params.append(("order", order))
        if limit is not None:
            params.append(("limit", str(limit)))
        path = f"{table}?{urllib.parse.urlencode(params)}"
        result = self._request(path)
        if not isinstance(result, list):
            raise LivingBoardError(f"Expected list from {table}, got {type(result).__name__}")
        return result

    def insert(self, table: str, rows: Iterable[dict[str, Any]] | dict[str, Any]) -> list[dict[str, Any]]:
        payload = [rows] if isinstance(rows, dict) else list(rows)
        result = self._request(table, method="POST", data=payload)
        return result if isinstance(result, list) else []

    def update(self, table: str, filters: dict[str, str], fields: dict[str, Any]) -> list[dict[str, Any]]:
        if not filters:
            raise LivingBoardError("update() requires at least one filter — refusing to update all rows")
        params = urllib.parse.urlencode(filters)
        path = f"{table}?{params}"
        result = self._request(path, method="PATCH", data=fields)
        return result if isinstance(result, list) else []

    def check(self) -> bool:
        """Return True if Supabase responds. Raises LivingBoardError on failure."""
        self.query("goals", select="id", limit=1)
        return True

    # ── internals ─────────────────────────────────────────────

    def _request(self, path: str, method: str = "GET", data: Any = None) -> Any:
        url = f"{self._config.url}/rest/v1/{path}"
        body = json.dumps(data).encode() if data is not None else None
        headers = {
            "apikey": self._config.anon_key,
            "Authorization": f"Bearer {self._config.anon_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode(errors="replace") if exc.fp else str(exc)
            raise LivingBoardError(f"Supabase HTTP {exc.code}: {detail}") from exc
        except urllib.error.URLError as exc:
            raise LivingBoardError(f"Network error talking to Supabase: {exc}") from exc
