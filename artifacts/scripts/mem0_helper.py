#!/usr/bin/env python3
"""
mem0 helper for Living Board agent.
Talks directly to local Qdrant (vector search) + Ollama (embeddings).

Usage:
  python3 artifacts/scripts/mem0_helper.py store "learning content" [--category CAT] [--goal_id ID] [--confidence F]
  python3 artifacts/scripts/mem0_helper.py search "query text" [--limit N] [--threshold F]
  python3 artifacts/scripts/mem0_helper.py list [--limit N] [--category CAT]
  python3 artifacts/scripts/mem0_helper.py delete <point_id>
  python3 artifacts/scripts/mem0_helper.py update <point_id> --confidence F [--content TEXT]

Environment:
  QDRANT_URL       (default: http://localhost:6333)
  QDRANT_COLLECTION (default: mem0_mcp_selfhosted)
  OLLAMA_URL       (default: http://localhost:11434)
  EMBED_MODEL      (default: bge-m3)
"""

import argparse
import json
import sys
import urllib.request
import urllib.error
import uuid
import time

QDRANT_URL = "http://localhost:6333"
QDRANT_COLLECTION = "living_board_memories"
OLLAMA_URL = "http://localhost:11434"
EMBED_MODEL = "bge-m3"

# Override from env
import os
QDRANT_URL = os.environ.get("QDRANT_URL", QDRANT_URL)
QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", QDRANT_COLLECTION)
OLLAMA_URL = os.environ.get("OLLAMA_URL", OLLAMA_URL)
EMBED_MODEL = os.environ.get("EMBED_MODEL", EMBED_MODEL)


def _request(url, data=None, method=None):
    """Make HTTP request, return parsed JSON."""
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"} if body else {},
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode() if e.fp else str(e)
        print(f"HTTP {e.code}: {err}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"Connection error: {e.reason}", file=sys.stderr)
        print("Are Qdrant and Ollama running?", file=sys.stderr)
        sys.exit(1)


def get_embedding(text):
    """Generate embedding via Ollama."""
    result = _request(f"{OLLAMA_URL}/api/embeddings", {
        "model": EMBED_MODEL,
        "prompt": text,
    })
    return result["embedding"]


def ensure_collection():
    """Create collection if it doesn't exist."""
    try:
        _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}")
    except SystemExit:
        _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}", {
            "vectors": {"size": 1024, "distance": "Cosine"},
        }, method="PUT")
        print(f"Created collection: {QDRANT_COLLECTION}", file=sys.stderr)


def cmd_store(args):
    """Store a new memory."""
    ensure_collection()
    embedding = get_embedding(args.text)
    point_id = str(uuid.uuid4())
    payload = {
        "content": args.text,
        "category": args.category or "domain_knowledge",
        "confidence": args.confidence,
        "goal_id": args.goal_id,
        "task_id": args.task_id,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "validated_count": 0,
        "agent_id": "living-board",
    }
    if args.metadata:
        payload["extra"] = json.loads(args.metadata)

    _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points", {
        "points": [{
            "id": point_id,
            "vector": embedding,
            "payload": payload,
        }]
    }, method="PUT")

    result = {"id": point_id, "status": "stored", "content": args.text[:100]}
    print(json.dumps(result, indent=2))


def cmd_search(args):
    """Semantic search for memories."""
    ensure_collection()
    embedding = get_embedding(args.query)

    search_body = {
        "vector": embedding,
        "limit": args.limit,
        "score_threshold": args.threshold,
        "with_payload": True,
    }

    if args.category:
        search_body["filter"] = {
            "must": [{"key": "category", "match": {"value": args.category}}]
        }

    result = _request(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/search",
        search_body,
    )

    memories = []
    for point in result.get("result", []):
        payload = point.get("payload", {})
        memories.append({
            "id": point["id"],
            "score": round(point["score"], 4),
            "content": payload.get("content", ""),
            "category": payload.get("category", ""),
            "confidence": payload.get("confidence", 0),
            "goal_id": payload.get("goal_id"),
            "created_at": payload.get("created_at", ""),
            "validated_count": payload.get("validated_count", 0),
        })

    print(json.dumps(memories, indent=2))


def cmd_list(args):
    """List memories with optional filters."""
    ensure_collection()

    scroll_body = {"limit": args.limit, "with_payload": True}

    if args.category:
        scroll_body["filter"] = {
            "must": [{"key": "category", "match": {"value": args.category}}]
        }

    result = _request(
        f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/scroll",
        scroll_body,
    )

    memories = []
    for point in result.get("result", {}).get("points", []):
        payload = point.get("payload", {})
        memories.append({
            "id": point["id"],
            "content": payload.get("content", ""),
            "category": payload.get("category", ""),
            "confidence": payload.get("confidence", 0),
            "goal_id": payload.get("goal_id"),
            "created_at": payload.get("created_at", ""),
            "validated_count": payload.get("validated_count", 0),
        })

    print(json.dumps(memories, indent=2))


def cmd_delete(args):
    """Delete a memory by ID."""
    _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/delete", {
        "points": [args.point_id],
    }, method="POST")
    print(json.dumps({"status": "deleted", "id": args.point_id}))


def cmd_update(args):
    """Update a memory's payload fields."""
    updates = {}
    if args.confidence is not None:
        updates["confidence"] = args.confidence
    if args.content:
        updates["content"] = args.content
        # Re-embed if content changed
        embedding = get_embedding(args.content)
        _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points", {
            "points": [{
                "id": args.point_id,
                "vector": embedding,
            }]
        }, method="PUT")
    if args.validate:
        # Increment validated_count — need to read current first
        scroll = _request(f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/{args.point_id}")
        current = scroll.get("result", {}).get("payload", {})
        updates["validated_count"] = current.get("validated_count", 0) + 1

    if updates:
        _request(
            f"{QDRANT_URL}/collections/{QDRANT_COLLECTION}/points/payload",
            {"payload": updates, "points": [args.point_id]},
            method="POST",
        )

    print(json.dumps({"status": "updated", "id": args.point_id, "updates": updates}))


def main():
    parser = argparse.ArgumentParser(description="Living Board memory helper")
    subs = parser.add_subparsers(dest="command", required=True)

    # store
    p_store = subs.add_parser("store", help="Store a new memory")
    p_store.add_argument("text", help="Memory content")
    p_store.add_argument("--category", default="domain_knowledge")
    p_store.add_argument("--goal_id", default=None)
    p_store.add_argument("--task_id", default=None)
    p_store.add_argument("--confidence", type=float, default=0.8)
    p_store.add_argument("--metadata", default=None, help="Extra JSON metadata")

    # search
    p_search = subs.add_parser("search", help="Semantic search")
    p_search.add_argument("query", help="Search query")
    p_search.add_argument("--limit", type=int, default=10)
    p_search.add_argument("--threshold", type=float, default=0.5)
    p_search.add_argument("--category", default=None)

    # list
    p_list = subs.add_parser("list", help="List memories")
    p_list.add_argument("--limit", type=int, default=20)
    p_list.add_argument("--category", default=None)

    # delete
    p_del = subs.add_parser("delete", help="Delete a memory")
    p_del.add_argument("point_id", help="Point UUID to delete")

    # update
    p_upd = subs.add_parser("update", help="Update a memory")
    p_upd.add_argument("point_id", help="Point UUID to update")
    p_upd.add_argument("--confidence", type=float, default=None)
    p_upd.add_argument("--content", default=None)
    p_upd.add_argument("--validate", action="store_true", help="Increment validated_count")

    args = parser.parse_args()

    if args.command == "store":
        cmd_store(args)
    elif args.command == "search":
        cmd_search(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "delete":
        cmd_delete(args)
    elif args.command == "update":
        cmd_update(args)


if __name__ == "__main__":
    main()
