"""Search provider adapters for the guidelines tool."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class BaseSearchProvider:
    """Minimal interface for search providers used by the guidelines tool."""

    supports_structured: bool = False
    supports_text: bool = False

    def search_structured(
        self,
        query: str,
        *,
        domain: Optional[str] = None,
        mode: str = "fast",
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        """Return structured results for a query.

        Each result should contain url/title/content/score keys where available.
        """

        return []

    def search_text(self, query: str) -> Optional[str]:
        """Return a plain-text snippet for legacy (V1) flow."""

        return None

    def run(self, query: str) -> Optional[str]:
        """DuckDuckGo-style compatibility shim used by legacy code/tests."""

        return self.search_text(query)


class TavilySearchProvider(BaseSearchProvider):
    """Wrapper around Tavily's search API."""

    supports_structured = True
    supports_text = True

    def __init__(self, api_key: str | None = None) -> None:
        from tavily import TavilyClient  # type: ignore

        resolved_key = api_key or os.getenv("TAVILY_API_KEY", "").strip()
        if not resolved_key:
            raise ValueError("TAVILY_API_KEY not provided")
        self._client = TavilyClient(api_key=resolved_key)

    def search_structured(
        self,
        query: str,
        *,
        domain: Optional[str] = None,
        mode: str = "fast",
        max_results: int = 3,
    ) -> List[Dict[str, Any]]:
        search_depth = "advanced" if mode == "exhaustive" else "basic"
        include_domains = [domain] if domain else None
        try:
            response = self._client.search(
                query=query,
                max_results=max(1, max_results),
                search_depth=search_depth,
                include_domains=include_domains,
                include_raw_content=True,
            )
        except Exception:
            return []

        results = response.get("results") if isinstance(response, dict) else None
        if not isinstance(results, list):
            return []
        return [r for r in results if isinstance(r, dict)]

    def search_text(self, query: str) -> Optional[str]:
        try:
            response = self._client.search(
                query=query,
                max_results=3,
                search_depth="basic",
                include_raw_content=True,
            )
        except Exception:
            return None

        results = response.get("results") if isinstance(response, dict) else None
        if not isinstance(results, list):
            return None

        snippets: List[str] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            content = item.get("content") or item.get("snippet") or ""
            if content:
                snippets.append(str(content))
        if not snippets:
            return None
        return "\n".join(snippets)[:1000]


class DuckDuckGoSearchProvider(BaseSearchProvider):
    """Adapter around langchain's DuckDuckGo search tool."""

    supports_structured = False
    supports_text = True

    def __init__(self) -> None:
        from langchain_community.tools import DuckDuckGoSearchRun

        self._tool = DuckDuckGoSearchRun()

    def search_text(self, query: str) -> Optional[str]:
        try:
            result = self._tool.run(query)
        except Exception:
            return None
        return str(result) if result else None
