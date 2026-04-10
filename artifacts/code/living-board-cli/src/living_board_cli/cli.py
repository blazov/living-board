"""Argparse entrypoint for living-board-cli.

Exposed as both `living-board` and `lb` via [project.scripts] in pyproject.toml.
"""

from __future__ import annotations

import argparse
import sys
from typing import Sequence

from . import __version__, commands
from .client import Client, Config, LivingBoardError


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="living-board",
        description=(
            "Terminal client for the Living Board autonomous agent schema. "
            "Reads goals, tasks, execution log, learnings, and snapshots "
            "from a Supabase PostgREST endpoint using only the anon key."
        ),
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    # goals
    p = sub.add_parser("goals", help="list goals")
    p.add_argument(
        "--status",
        nargs="+",
        metavar="STATUS",
        help="statuses to include (default: in_progress pending)",
    )
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--json", action="store_true", help="output raw JSON")
    p.set_defaults(func=commands.cmd_goals)

    # tasks
    p = sub.add_parser("tasks", help="list tasks")
    p.add_argument("--goal", metavar="GOAL_ID", help="filter by goal id (full UUID)")
    p.add_argument(
        "--status",
        nargs="+",
        metavar="STATUS",
        help="statuses to include (default: in_progress pending)",
    )
    p.add_argument("--limit", type=int, default=100)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=commands.cmd_tasks)

    # log
    p = sub.add_parser("log", help="show recent execution log entries")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=commands.cmd_log)

    # learnings
    p = sub.add_parser("learnings", help="list learnings")
    p.add_argument("--goal", metavar="GOAL_ID", help="filter by goal id (full UUID)")
    p.add_argument("--category", help="filter by category")
    p.add_argument("--limit", type=int, default=25)
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=commands.cmd_learnings)

    # snapshot
    p = sub.add_parser("snapshot", help="show the most recent snapshot")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=commands.cmd_snapshot)

    # stats
    p = sub.add_parser("stats", help="show summary counts for the board")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=commands.cmd_stats)

    # comment
    p = sub.add_parser("comment", help="add a comment to a goal")
    p.add_argument("goal", help="goal id (full UUID)")
    p.add_argument("content", help="comment body")
    p.add_argument(
        "--type",
        choices=["note", "question", "direction_change", "feedback"],
        default="note",
    )
    p.set_defaults(func=commands.cmd_comment)

    # check
    p = sub.add_parser("check", help="verify Supabase credentials and connectivity")
    p.set_defaults(func=commands.cmd_check)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        config = Config.from_env()
        client = Client(config)
        args.func(client, args)
    except LivingBoardError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("aborted", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
