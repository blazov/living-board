"""Plain-text renderers. No external deps — no rich, no tabulate."""

from __future__ import annotations

import shutil
import textwrap
from typing import Any, Sequence


def term_width(default: int = 100) -> int:
    try:
        return shutil.get_terminal_size((default, 20)).columns
    except OSError:
        return default


def truncate(value: Any, width: int) -> str:
    text = "" if value is None else str(value)
    text = text.replace("\n", " ").replace("\t", " ")
    if len(text) <= width:
        return text
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def render_table(headers: Sequence[str], rows: Sequence[Sequence[Any]]) -> str:
    """Render an ASCII table that auto-fits to the terminal width.

    Columns share the remaining width proportionally to the longest value in
    each column, with a minimum of 4 chars per column.
    """
    if not rows:
        return f"{'  '.join(headers)}\n(no rows)"

    col_count = len(headers)
    raw_widths = [len(h) for h in headers]
    for row in rows:
        for i in range(col_count):
            cell = "" if i >= len(row) or row[i] is None else str(row[i])
            raw_widths[i] = max(raw_widths[i], len(cell.splitlines()[0]) if cell else 0)

    available = max(term_width() - (2 * (col_count - 1)), col_count * 4)
    total_raw = sum(raw_widths) or 1
    if total_raw <= available:
        widths = raw_widths
    else:
        # Scale proportionally but keep a minimum floor of 4.
        widths = []
        remaining = available
        for i, rw in enumerate(raw_widths):
            if i == col_count - 1:
                widths.append(max(4, remaining))
            else:
                share = max(4, int(available * (rw / total_raw)))
                widths.append(share)
                remaining -= share

    def fmt_row(cells: Sequence[Any]) -> str:
        parts: list[str] = []
        for i in range(col_count):
            cell = "" if i >= len(cells) or cells[i] is None else str(cells[i])
            parts.append(truncate(cell, widths[i]).ljust(widths[i]))
        return "  ".join(parts).rstrip()

    lines: list[str] = [fmt_row(headers)]
    lines.append("  ".join("-" * w for w in widths))
    for row in rows:
        lines.append(fmt_row(row))
    return "\n".join(lines)


def render_kv(pairs: Sequence[tuple[str, Any]]) -> str:
    if not pairs:
        return "(empty)"
    key_width = max(len(str(k)) for k, _ in pairs)
    wrap_width = max(term_width() - key_width - 2, 20)
    out: list[str] = []
    for key, value in pairs:
        text = "" if value is None else str(value)
        if "\n" in text or len(text) > wrap_width:
            wrapped = textwrap.fill(
                text,
                width=wrap_width,
                subsequent_indent=" " * (key_width + 2),
            )
            out.append(f"{str(key).ljust(key_width)}  {wrapped}")
        else:
            out.append(f"{str(key).ljust(key_width)}  {text}")
    return "\n".join(out)


def short_id(value: Any, length: int = 8) -> str:
    text = str(value) if value is not None else ""
    return text[:length] if text else ""


def short_ts(value: Any) -> str:
    """Return the first 16 chars of an ISO 8601 timestamp (YYYY-MM-DD HH:MM)."""
    text = str(value) if value is not None else ""
    if len(text) < 16:
        return text
    # Replace the 'T' so it reads naturally in a table.
    return text[:10] + " " + text[11:16]
