"""Memory tools -- semantic search/store via Qdrant + Ollama (no subprocess)."""

from __future__ import annotations

import json
import logging
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

from ..config import MemoryConfig
from .base import Tool, ToolResult

log = logging.getLogger(__name__)


class _MemoryBackend:
    """Shared HTTP client for Qdrant and Ollama.

    Extracted so both MemorySearchTool and MemoryStoreTool can share
    connection details and the embedding function.
    """

    def __init__(self, config: MemoryConfig) -> None:
        self.qdrant_url = config.qdrant_url.rstrip("/")
        self.ollama_url = config.ollama_url.rstrip("/")
        self.collection = config.qdrant_collection
        self.embed_model = config.embed_model
        self._available: bool | None = None

    # ── HTTP helpers ──

    def _request(
        self,
        url: str,
        data: Any = None,
        method: str | None = None,
    ) -> Any:
        body = json.dumps(data).encode() if data is not None else None
        headers = {"Content-Type": "application/json"} if body else {}
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=30) as resp:
            text = resp.read().decode()
            return json.loads(text) if text else None

    def is_available(self) -> bool:
        """Check if both Qdrant and Ollama are reachable."""
        if self._available is not None:
            return self._available
        try:
            self._request(f"{self.qdrant_url}/collections")
            self._request(f"{self.ollama_url}/api/tags")
            self._available = True
        except Exception:
            log.info("Memory backend unavailable (Qdrant/Ollama not reachable)")
            self._available = False
        return self._available

    # ── Embedding ──

    def get_embedding(self, text: str) -> list[float]:
        result = self._request(
            f"{self.ollama_url}/api/embeddings",
            {"model": self.embed_model, "prompt": text},
        )
        return result["embedding"]

    # ── Collection management ──

    def ensure_collection(self) -> None:
        try:
            self._request(f"{self.qdrant_url}/collections/{self.collection}")
        except (urllib.error.HTTPError, Exception):
            self._request(
                f"{self.qdrant_url}/collections/{self.collection}",
                {"vectors": {"size": 1024, "distance": "Cosine"}},
                method="PUT",
            )
            log.info("Created Qdrant collection: %s", self.collection)


class MemorySearchTool(Tool):
    """Semantic search over stored memories."""

    name = "memory_search"
    description = (
        "Search stored memories using semantic similarity. "
        "Returns the most relevant memories for a given query, "
        "optionally filtered by category."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query text.",
            },
            "limit": {
                "type": "integer",
                "minimum": 1,
                "maximum": 50,
                "description": "Maximum number of results to return. Defaults to 10.",
            },
            "threshold": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Minimum similarity score (0-1). Defaults to 0.5.",
            },
            "category": {
                "type": ["string", "null"],
                "enum": [
                    "domain_knowledge",
                    "strategy",
                    "operational",
                    "meta",
                    None,
                ],
                "description": "Filter by category, or null for all categories.",
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def __init__(self, backend: _MemoryBackend) -> None:
        self._backend = backend

    def execute(
        self,
        query: str,
        limit: int = 10,
        threshold: float = 0.5,
        category: str | None = None,
    ) -> ToolResult:
        if not self._backend.is_available():
            return ToolResult(
                success=False,
                output="",
                error="Memory backend unavailable (Qdrant/Ollama not running).",
            )

        try:
            self._backend.ensure_collection()
            embedding = self._backend.get_embedding(query)

            search_body: dict[str, Any] = {
                "vector": embedding,
                "limit": limit,
                "score_threshold": threshold,
                "with_payload": True,
            }
            if category:
                search_body["filter"] = {
                    "must": [{"key": "category", "match": {"value": category}}]
                }

            result = self._backend._request(
                f"{self._backend.qdrant_url}/collections/{self._backend.collection}/points/search",
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

            output = json.dumps(memories, indent=2)
            return ToolResult(success=True, output=output, data=memories)

        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


class MemoryStoreTool(Tool):
    """Store a new memory with embedding in Qdrant."""

    name = "memory_store"
    description = (
        "Store a new memory/learning in the semantic memory system. "
        "The text is embedded and stored for future semantic search."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "The memory content to store.",
            },
            "category": {
                "type": "string",
                "enum": [
                    "domain_knowledge",
                    "strategy",
                    "operational",
                    "meta",
                ],
                "description": "Category of the memory. Defaults to domain_knowledge.",
            },
            "confidence": {
                "type": "number",
                "minimum": 0.0,
                "maximum": 1.0,
                "description": "Confidence score from 0.0 to 1.0. Defaults to 0.8.",
            },
            "goal_id": {
                "type": ["string", "null"],
                "description": "Related goal UUID, or null for global memories.",
            },
            "task_id": {
                "type": ["string", "null"],
                "description": "Related task UUID, if applicable.",
            },
        },
        "required": ["text"],
        "additionalProperties": False,
    }

    def __init__(self, backend: _MemoryBackend) -> None:
        self._backend = backend

    def execute(
        self,
        text: str,
        category: str = "domain_knowledge",
        confidence: float = 0.8,
        goal_id: str | None = None,
        task_id: str | None = None,
    ) -> ToolResult:
        if not self._backend.is_available():
            return ToolResult(
                success=False,
                output="",
                error="Memory backend unavailable (Qdrant/Ollama not running).",
            )

        try:
            self._backend.ensure_collection()
            embedding = self._backend.get_embedding(text)
            point_id = str(uuid.uuid4())

            payload: dict[str, Any] = {
                "content": text,
                "category": category,
                "confidence": confidence,
                "goal_id": goal_id,
                "task_id": task_id,
                "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "validated_count": 0,
                "agent_id": "living-board",
            }

            self._backend._request(
                f"{self._backend.qdrant_url}/collections/{self._backend.collection}/points",
                {"points": [{"id": point_id, "vector": embedding, "payload": payload}]},
                method="PUT",
            )

            result_data = {"id": point_id, "status": "stored", "content": text[:120]}
            return ToolResult(
                success=True,
                output=json.dumps(result_data, indent=2),
                data=result_data,
            )

        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))


def create_memory_tools(config: MemoryConfig) -> list[Tool]:
    """Create memory tools from a MemoryConfig.

    Returns an empty list if the backend is not reachable, so callers
    can safely register whatever is returned.
    """
    backend = _MemoryBackend(config)
    return [MemorySearchTool(backend), MemoryStoreTool(backend)]
