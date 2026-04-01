"""Web search tool using duckduckgo-search."""

from __future__ import annotations

import json
import logging
from typing import Any

from .base import Tool, ToolResult

log = logging.getLogger(__name__)


class WebSearchTool(Tool):
    """Search the web using DuckDuckGo (default) and return results."""

    name = "web_search"
    description = (
        "Search the web and return top results with titles, URLs, and snippets. "
        "Uses DuckDuckGo by default. Good for research, fact-checking, and discovery."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query.",
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 20,
                "description": "Maximum number of results to return. Defaults to 5.",
            },
            "region": {
                "type": "string",
                "description": (
                    "Region code for search (e.g. 'us-en', 'uk-en'). "
                    "Defaults to 'wt-wt' (no region)."
                ),
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    }

    def execute(
        self,
        query: str,
        max_results: int = 5,
        region: str = "wt-wt",
    ) -> ToolResult:
        try:
            from duckduckgo_search import DDGS
        except ImportError:
            return ToolResult(
                success=False,
                output="",
                error=(
                    "duckduckgo-search package not installed. "
                    "Install with: pip install duckduckgo-search"
                ),
            )

        try:
            with DDGS() as ddgs:
                raw_results = list(
                    ddgs.text(query, region=region, max_results=max_results)
                )

            results = []
            for r in raw_results:
                results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", ""),
                })

            if not results:
                return ToolResult(
                    success=True,
                    output="No results found.",
                    data=[],
                )

            output = json.dumps(results, indent=2)
            return ToolResult(success=True, output=output, data=results)

        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))
