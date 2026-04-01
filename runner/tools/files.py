"""File tools -- read and write files, sandboxed to a safe directory."""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Any

from .base import Tool, ToolResult

log = logging.getLogger(__name__)


def _resolve_sandboxed(sandbox: Path, path: str) -> Path | None:
    """Resolve a path within the sandbox.  Returns None if it escapes."""
    try:
        resolved = (sandbox / path).resolve()
        sandbox_resolved = sandbox.resolve()
        # Ensure the resolved path is within or equal to the sandbox
        if resolved == sandbox_resolved or str(resolved).startswith(
            str(sandbox_resolved) + os.sep
        ):
            return resolved
        return None
    except (ValueError, OSError):
        return None


class ReadFileTool(Tool):
    """Read a file from the sandboxed artifacts directory."""

    name = "read_file"
    description = (
        "Read the contents of a file. The path is relative to the artifacts "
        "sandbox directory. Returns the file contents as text."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "File path relative to the sandbox directory "
                    "(e.g. 'content/article.md', 'scripts/helper.py')."
                ),
            },
            "offset": {
                "type": "integer",
                "minimum": 0,
                "description": "Line number to start reading from (0-based). Defaults to 0.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "description": "Maximum number of lines to read. Defaults to 500.",
            },
        },
        "required": ["path"],
        "additionalProperties": False,
    }

    def __init__(self, sandbox: str) -> None:
        self._sandbox = Path(sandbox)

    def execute(
        self,
        path: str,
        offset: int = 0,
        limit: int = 500,
    ) -> ToolResult:
        resolved = _resolve_sandboxed(self._sandbox, path)
        if resolved is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Path traversal denied: {path}",
            )
        if not resolved.exists():
            return ToolResult(
                success=False,
                output="",
                error=f"File not found: {path}",
            )
        if not resolved.is_file():
            return ToolResult(
                success=False,
                output="",
                error=f"Not a file: {path}",
            )

        try:
            text = resolved.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines(keepends=True)
            selected = lines[offset : offset + limit]
            content = "".join(selected)
            total = len(lines)
            header = f"[{path}] lines {offset + 1}-{min(offset + limit, total)} of {total}\n"
            return ToolResult(
                success=True,
                output=header + content,
                data={"path": path, "total_lines": total},
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class WriteFileTool(Tool):
    """Write content to a file in the sandboxed artifacts directory."""

    name = "write_file"
    description = (
        "Write content to a file. The path is relative to the artifacts "
        "sandbox directory. Creates parent directories if needed. "
        "Overwrites the file if it already exists."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": (
                    "File path relative to the sandbox directory "
                    "(e.g. 'content/article.md', 'data/results.json')."
                ),
            },
            "content": {
                "type": "string",
                "description": "The full content to write to the file.",
            },
            "append": {
                "type": "boolean",
                "description": "If true, append to existing file instead of overwriting. Defaults to false.",
            },
        },
        "required": ["path", "content"],
        "additionalProperties": False,
    }

    def __init__(self, sandbox: str) -> None:
        self._sandbox = Path(sandbox)

    def execute(
        self,
        path: str,
        content: str,
        append: bool = False,
    ) -> ToolResult:
        resolved = _resolve_sandboxed(self._sandbox, path)
        if resolved is None:
            return ToolResult(
                success=False,
                output="",
                error=f"Path traversal denied: {path}",
            )

        try:
            resolved.parent.mkdir(parents=True, exist_ok=True)
            mode = "a" if append else "w"
            with open(resolved, mode, encoding="utf-8") as f:
                f.write(content)

            action = "Appended to" if append else "Wrote"
            return ToolResult(
                success=True,
                output=f"{action} {path} ({len(content)} chars)",
                data={"path": path, "chars": len(content)},
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


def create_file_tools(sandbox: str) -> list[Tool]:
    """Create file tools sandboxed to the given directory."""
    return [ReadFileTool(sandbox), WriteFileTool(sandbox)]
