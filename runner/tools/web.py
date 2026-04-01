"""Web fetch tool -- retrieves a URL and strips HTML to plain text."""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.request
from typing import Any

from .base import Tool, ToolResult

log = logging.getLogger(__name__)

_MAX_CONTENT_LENGTH = 4000


def _strip_html(html: str) -> str:
    """Naive HTML-to-text conversion: strip tags, collapse whitespace."""
    # Remove script and style blocks
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    # Convert <br> and block-level tags to newlines
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div|h[1-6]|li|tr)>", "\n", text, flags=re.IGNORECASE)
    # Strip remaining tags
    text = re.sub(r"<[^>]+>", "", text)
    # Decode common HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")
    text = text.replace("&quot;", '"')
    text = text.replace("&#39;", "'")
    text = text.replace("&nbsp;", " ")
    # Collapse whitespace
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class WebFetchTool(Tool):
    """Fetch a URL and return its content as plain text."""

    name = "web_fetch"
    description = (
        "Fetch a web page by URL. HTML is stripped to plain text and "
        f"truncated to ~{_MAX_CONTENT_LENGTH} characters. "
        "Useful for reading articles, documentation, API responses, etc."
    )
    parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "url": {
                "type": "string",
                "description": "The URL to fetch.",
            },
            "max_length": {
                "type": "integer",
                "minimum": 100,
                "maximum": 20000,
                "description": (
                    f"Maximum characters of content to return. Defaults to {_MAX_CONTENT_LENGTH}."
                ),
            },
        },
        "required": ["url"],
        "additionalProperties": False,
    }

    def execute(
        self,
        url: str,
        max_length: int = _MAX_CONTENT_LENGTH,
    ) -> ToolResult:
        try:
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (compatible; LivingBoardAgent/1.0; "
                        "+https://github.com/living-board)"
                    ),
                    "Accept": "text/html,application/xhtml+xml,application/json,text/plain,*/*",
                },
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                content_type = resp.headers.get("Content-Type", "")
                raw = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"HTTP {e.code}: {e.reason}",
            )
        except urllib.error.URLError as e:
            return ToolResult(
                success=False,
                output="",
                error=f"URL error: {e.reason}",
            )
        except Exception as exc:
            return ToolResult(success=False, output="", error=str(exc))

        # If it looks like HTML, strip to text
        if "html" in content_type.lower() or raw.lstrip().startswith("<!"):
            text = _strip_html(raw)
        else:
            text = raw

        # Truncate
        if len(text) > max_length:
            text = text[:max_length] + f"\n\n[Truncated at {max_length} characters]"

        return ToolResult(success=True, output=text, data={"url": url, "length": len(text)})
