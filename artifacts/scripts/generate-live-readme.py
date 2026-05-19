#!/usr/bin/env python3
"""Generate the live-state section of README.md from the latest snapshot."""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOT_PATH = REPO_ROOT / "artifacts" / "state" / "latest-snapshot.json"
README_PATH = REPO_ROOT / "README.md"

START_MARKER = "<!-- LIVE-STATE-START -->"
END_MARKER = "<!-- LIVE-STATE-END -->"


def progress_bar(pct, width=10):
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def format_timestamp(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (ValueError, AttributeError):
        return ts_str or "unknown"


def format_date_short(ts_str):
    try:
        dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        return dt.strftime("%b %d")
    except (ValueError, AttributeError):
        return ts_str or ""


def generate_live_section(snapshot):
    cycle = snapshot.get("cycle_count", "?")
    updated = format_timestamp(snapshot.get("exported_at", ""))
    focus = snapshot.get("current_focus", "")
    if focus and len(focus) > 120:
        cut = focus[:120].rfind(" ")
        focus = focus[:cut] + "..." if cut > 60 else focus[:117] + "..."

    lines = [
        START_MARKER,
        "",
        "## Agent Pulse",
        "",
        f"> **Cycle {cycle}** · Last updated: {updated}",
        "",
    ]

    if focus:
        lines.append(f"**Current focus:** {focus}")
        lines.append("")

    goals = snapshot.get("active_goals", [])
    in_progress = [g for g in goals if g.get("status") == "in_progress"]
    pending = [g for g in goals if g.get("status") == "pending"]

    if in_progress or pending:
        lines.append("| Goal | Progress |")
        lines.append("|------|----------|")
        for g in in_progress:
            pct = g.get("progress_pct", 0)
            bar = progress_bar(pct)
            lines.append(f"| {g['title']} | `{bar}` {pct}% |")
        for g in pending:
            lines.append(f"| {g['title']} | `{'░' * 10}` pending |")
        lines.append("")

    outcomes = snapshot.get("recent_outcomes", [])
    if outcomes:
        lines.append("**Recent activity:**")
        for o in outcomes[:3]:
            date = format_date_short(o.get("timestamp", ""))
            marker = "+" if o.get("success") else "x"
            lines.append(f"- [{marker}] {o['summary']} *({date})*")
        lines.append("")

    blockers = snapshot.get("open_blockers", [])
    if blockers:
        lines.append("<details><summary>Open blockers</summary>")
        lines.append("")
        for b in blockers:
            lines.append(f"- {b['description']}")
        lines.append("")
        lines.append("</details>")
        lines.append("")

    lines.append(END_MARKER)
    return "\n".join(lines)


def main():
    if not SNAPSHOT_PATH.exists():
        print(f"error: {SNAPSHOT_PATH} not found", file=sys.stderr)
        sys.exit(1)

    data = json.loads(SNAPSHOT_PATH.read_text())
    snapshot = data.get("snapshot", data)
    if "exported_at" not in snapshot and "exported_at" in data:
        snapshot["exported_at"] = data["exported_at"]
    live_section = generate_live_section(snapshot)

    readme = README_PATH.read_text()
    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )

    if pattern.search(readme):
        updated = pattern.sub(live_section, readme)
    else:
        insert_point = readme.find("\n---\n")
        if insert_point == -1:
            updated = live_section + "\n\n" + readme
        else:
            updated = (
                readme[: insert_point + 5]
                + "\n"
                + live_section
                + "\n"
                + readme[insert_point + 5 :]
            )

    README_PATH.write_text(updated)
    print(f"README.md updated with cycle {snapshot.get('cycle_count', '?')} state")



if __name__ == "__main__":
    main()
