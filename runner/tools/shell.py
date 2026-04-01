"""Shell tool -- run commands via subprocess with safety controls."""

from __future__ import annotations

import logging
import subprocess
from typing import Any

from .base import Tool, ToolResult

log = logging.getLogger(__name__)

# Commands that are always blocked regardless of config
_BLOCKED_PATTERNS = [
    "rm -rf /",
    "rm -rf /*",
    "mkfs",
    ":(){",  # fork bomb
    "> /dev/sda",
    "dd if=/dev/zero of=/dev",
]


class ShellTool(Tool):
    """Run a shell command via subprocess."""

    name = "run_shell"
    description = (
        "Execute a shell command and return its stdout and stderr. "
        "Commands run with a configurable timeout. Use for git operations, "
        "API calls via curl, running scripts, package management, etc."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": "The shell command to execute.",
            },
            "timeout": {
                "type": "integer",
                "minimum": 1,
                "maximum": 300,
                "description": "Timeout in seconds. Defaults to the configured shell_timeout.",
            },
            "cwd": {
                "type": "string",
                "description": (
                    "Working directory for the command. "
                    "Defaults to the project root."
                ),
            },
        },
        "required": ["command"],
        "additionalProperties": False,
    }

    def __init__(self, allowed: bool = True, default_timeout: int = 60) -> None:
        self._allowed = allowed
        self._default_timeout = default_timeout

    def execute(
        self,
        command: str,
        timeout: int | None = None,
        cwd: str | None = None,
    ) -> ToolResult:
        if not self._allowed:
            return ToolResult(
                success=False,
                output="",
                error="Shell execution is disabled in configuration.",
            )

        # Safety check
        cmd_lower = command.lower().strip()
        for pattern in _BLOCKED_PATTERNS:
            if pattern in cmd_lower:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Blocked dangerous command pattern: {pattern}",
                )

        effective_timeout = timeout or self._default_timeout

        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=effective_timeout,
                cwd=cwd,
            )

            output_parts = []
            if result.stdout:
                output_parts.append(result.stdout)
            if result.stderr:
                output_parts.append(f"[stderr]\n{result.stderr}")

            output = "\n".join(output_parts) if output_parts else "(no output)"

            # Truncate very long output
            if len(output) > 10000:
                output = output[:10000] + f"\n\n[Truncated at 10000 characters]"

            if result.returncode == 0:
                return ToolResult(
                    success=True,
                    output=output,
                    data={"returncode": result.returncode},
                )
            else:
                return ToolResult(
                    success=False,
                    output=output,
                    error=f"Command exited with code {result.returncode}",
                    data={"returncode": result.returncode},
                )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                output="",
                error=f"Command timed out after {effective_timeout}s",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))
