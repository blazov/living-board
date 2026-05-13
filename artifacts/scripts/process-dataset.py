#!/usr/bin/env python3
"""
Process raw Supabase SQL query results into clean JSON dataset files
for the Living Board open execution dataset.

Input: Temp files containing JSON arrays with {type: "text", text: "<json>"}
Output: Clean, sanitized JSON files in artifacts/data/
"""

import json
import re
import os
from datetime import datetime, timezone

# ── Config ──────────────────────────────────────────────────────────────────

BASE_DIR = "/home/user/living-board"
OUTPUT_DIR = os.path.join(BASE_DIR, "artifacts/data")
TOOL_RESULTS_DIR = (
    "/root/.claude/projects/-home-user-living-board"
    "/a8425ae2-b445-4db6-958d-e0eb154527e6/tool-results"
)

INPUT_FILES = {
    "goals":         "mcp-Supabase-execute_sql-1778688743833.txt",
    "tasks":         "mcp-Supabase-execute_sql-1778688747887.txt",
    "execution_log": "mcp-Supabase-execute_sql-1778688751493.txt",
    "snapshots":     "mcp-Supabase-execute_sql-1778688757854.txt",
    "learnings":     "mcp-Supabase-execute_sql-1778688767483.txt",
}

# ── Sanitization patterns ────────────────────────────────────────────────────

# Email addresses
EMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}",
    re.IGNORECASE,
)

# API keys / tokens – generic high-entropy patterns
# Covers: Bearer tokens, sk-/pk-/eyJ (JWT) prefixes, hex/base64 long strings
API_KEY_PATTERNS = [
    # OpenAI-style sk-... or pk-...
    re.compile(r"\b(sk|pk)-[A-Za-z0-9_\-]{20,}", re.IGNORECASE),
    # JWT (eyJ...)
    re.compile(r"\beyJ[A-Za-z0-9_\-]{20,}(?:\.[A-Za-z0-9_\-]+){1,2}"),
    # Generic bearer/token/key = value patterns
    re.compile(
        r"(?i)(api[_\-]?key|bearer|token|secret|password|auth)[\"']?\s*[:=]\s*[\"']?([A-Za-z0-9_\-\.]{16,})[\"']?",
    ),
    # Supabase anon/service keys (long base64, typically 100+ chars)
    re.compile(r"[A-Za-z0-9+/=]{100,}"),
]

# Agentmail-specific address pattern (keep domain but redact local part)
AGENTMAIL_RE = re.compile(
    r"[a-zA-Z0-9._%+\-]+@(?:agentmail\.to|agent\.email)",
    re.IGNORECASE,
)

REDACTED_EMAIL = "[redacted-email]"
REDACTED_KEY   = "[redacted-key]"


def sanitize_string(value: str) -> str:
    """Apply all sanitization rules to a string value."""
    # Agentmail addresses first (subset of email but worth calling out)
    value = AGENTMAIL_RE.sub(REDACTED_EMAIL, value)
    # Generic emails
    value = EMAIL_RE.sub(REDACTED_EMAIL, value)
    # API key / token patterns
    for pat in API_KEY_PATTERNS:
        value = pat.sub(REDACTED_KEY, value)
    return value


def sanitize_value(obj):
    """Recursively sanitize all string leaves in a JSON-like structure."""
    if isinstance(obj, str):
        return sanitize_string(obj)
    if isinstance(obj, dict):
        return {k: sanitize_value(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_value(item) for item in obj]
    # numbers, booleans, None — pass through unchanged
    return obj


# ── Parsing ──────────────────────────────────────────────────────────────────

# The untrusted-data tag uses a random UUID suffix; match any variant.
UNTRUSTED_OPEN_RE  = re.compile(r"<untrusted-data-[^>]+>")
UNTRUSTED_CLOSE_RE = re.compile(r"</untrusted-data-[^>]+>")


def extract_rows(file_path: str) -> list:
    """Read a temp file and extract the SQL result rows."""
    with open(file_path, "r", encoding="utf-8") as fh:
        outer = json.load(fh)

    text_entry = next(
        (item for item in outer if isinstance(item, dict) and item.get("type") == "text"),
        None,
    )
    if text_entry is None:
        raise ValueError(f"No text entry found in {file_path}")

    raw_text = text_entry["text"]

    try:
        inner = json.loads(raw_text)
        if isinstance(inner, dict) and "result" in inner:
            result_str = inner["result"]
        elif isinstance(inner, str):
            result_str = inner
        else:
            result_str = raw_text
    except (json.JSONDecodeError, TypeError):
        result_str = raw_text

    # Find the JSON array directly — more reliable than tag extraction
    # since the untrusted-data tags appear multiple times in the preamble
    start = result_str.index("[{")
    end = result_str.rindex("}]") + 2
    json_block = result_str[start:end]

    rows = json.loads(json_block)
    if not isinstance(rows, list):
        raise ValueError(f"Expected a JSON array, got {type(rows)} in {file_path}")

    return rows


# ── Date range helper ─────────────────────────────────────────────────────────

DATE_FIELDS = ("created_at", "updated_at", "completed_at", "started_at")


def find_date_range(all_tables: dict) -> dict:
    """Return the min/max created_at across all tables."""
    dates = []
    for rows in all_tables.values():
        for row in rows:
            for field in DATE_FIELDS:
                val = row.get(field)
                if val and isinstance(val, str) and val != "null":
                    dates.append(val)
    if not dates:
        return {"earliest": None, "latest": None}
    dates.sort()
    return {"earliest": dates[0], "latest": dates[-1]}


# ── Schema summaries (hand-written, based on DB) ─────────────────────────────

SCHEMA_INFO = {
    "goals": {
        "description": "High-level objectives the agent pursues. Each goal has tasks.",
        "key_fields": ["id", "title", "description", "status", "priority",
                       "metadata", "created_at", "updated_at"],
        "status_values": ["pending", "in_progress", "done", "blocked"],
    },
    "tasks": {
        "description": "Concrete work items inside a goal, executed one per agent cycle.",
        "key_fields": ["id", "goal_id", "title", "description", "status",
                       "sort_order", "attempts", "max_attempts", "result",
                       "blocked_reason", "created_at", "completed_at"],
        "status_values": ["pending", "in_progress", "done", "blocked"],
    },
    "execution_log": {
        "description": "Append-only log of every agent action: execute, reflect, orient, etc.",
        "key_fields": ["id", "goal_id", "task_id", "action", "summary",
                       "details", "created_at"],
        "action_values": ["execute", "reflect", "orient", "decompose", "comment"],
    },
    "learnings": {
        "description": "Structured knowledge extracted by the agent from task outcomes.",
        "key_fields": ["id", "goal_id", "task_id", "category", "content",
                       "confidence", "created_at", "updated_at"],
        "category_values": ["domain_knowledge", "strategy", "operational", "meta"],
    },
    "snapshots": {
        "description": "Per-cycle compressed state: active goals, focus, outcomes, learnings.",
        "key_fields": ["id", "content", "active_goals", "current_focus",
                       "recent_outcomes", "open_blockers", "key_learnings",
                       "cycle_count", "created_at"],
    },
}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    tables: dict[str, list] = {}

    for table_name, filename in INPUT_FILES.items():
        file_path = os.path.join(TOOL_RESULTS_DIR, filename)
        print(f"Processing {table_name} from {filename} …")
        rows = extract_rows(file_path)
        rows = sanitize_value(rows)
        tables[table_name] = rows
        print(f"  → {len(rows)} rows")

    # ── Write individual table files ─────────────────────────────────────────
    for table_name, rows in tables.items():
        out_path = os.path.join(OUTPUT_DIR, f"{table_name}.json")
        with open(out_path, "w", encoding="utf-8") as fh:
            json.dump(rows, fh, indent=2, ensure_ascii=False)
        print(f"Wrote {out_path}  ({len(rows)} rows)")

    # ── Write combined dataset.json ──────────────────────────────────────────
    date_range = find_date_range(tables)
    metadata = {
        "export_date": datetime.now(timezone.utc).isoformat(),
        "description": (
            "Open execution dataset from the Living Board autonomous AI agent. "
            "Covers 234 cycles (~44 days) of autonomous goal planning, task "
            "decomposition, execution, and learning. All email addresses and "
            "API keys have been redacted."
        ),
        "tables": {
            name: {
                "row_count": len(rows),
                "schema": SCHEMA_INFO.get(name, {}),
            }
            for name, rows in tables.items()
        },
        "date_range": date_range,
        "total_rows": sum(len(r) for r in tables.values()),
        "agent_cycles": 234,
        "duration_days": 44,
    }

    dataset = {"metadata": metadata, **tables}
    dataset_path = os.path.join(OUTPUT_DIR, "dataset.json")
    with open(dataset_path, "w", encoding="utf-8") as fh:
        json.dump(dataset, fh, indent=2, ensure_ascii=False)
    print(f"\nWrote {dataset_path}")
    print(f"  Total rows across all tables: {metadata['total_rows']}")

    # ── Summary ──────────────────────────────────────────────────────────────
    print("\n── Summary ──────────────────────────────────────────────────────")
    for name, rows in tables.items():
        print(f"  {name:<16} {len(rows):>4} rows")
    print(f"  {'TOTAL':<16} {metadata['total_rows']:>4} rows")
    print(f"\n  Date range: {date_range['earliest']}  →  {date_range['latest']}")
    print(f"  Export date: {metadata['export_date']}")
    print("─────────────────────────────────────────────────────────────────")


if __name__ == "__main__":
    main()
