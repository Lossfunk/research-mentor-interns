from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..cache import CostTracker, GuidelinesCache
from ..config import GuidelinesConfig
from ..formatter import GuidelinesFormatter
from ..query_builder import QueryBuilder
from ..search_providers import BaseSearchProvider


class GuidelinesV1Executor:
    """Handle legacy guidelines execution flow."""

    def __init__(
        self,
        config: GuidelinesConfig,
        search_tool: Optional[BaseSearchProvider],
        query_builder: QueryBuilder,
        formatter: GuidelinesFormatter,
        cache: Optional[GuidelinesCache],
        cost_tracker: Optional[CostTracker],
    ) -> None:
        self._config = config
        self._search_tool = search_tool
        self._query_builder = query_builder
        self._formatter = formatter
        self._cache = cache
        self._cost_tracker = cost_tracker

    def run(self, topic: str, cache_key: str) -> Dict[str, Any]:
        search_queries = self._query_builder.get_prioritized_queries(topic)[
            : self._config.MAX_SEARCH_QUERIES
        ]
        retrieved: List[Dict[str, Any]] = []

        for query_str in search_queries:
            try:
                results = None
                if self._search_tool and getattr(self._search_tool, "supports_text", False):
                    results = self._search_tool.search_text(query_str)
                elif self._search_tool:
                    results = self._search_tool.run(query_str)

                if results and len(results) > 20:
                    source_type = self._query_builder.identify_source_type(query_str)
                    guide_id = f"guide_{hash(results) & 0xfffff:05x}"
                    source_domain = self._query_builder.extract_domain(query_str)
                    retrieved.append(
                        {
                            "guide_id": guide_id,
                            "source_type": source_type,
                            "source_domain": source_domain,
                            "content": results[:500],
                            "search_query": query_str,
                        }
                    )
                    if self._cost_tracker:
                        self._cost_tracker.record_search_query(0.01)
            except Exception:
                continue

        if not retrieved:
            result: Dict[str, Any] = {
                "retrieved_guidelines": [],
                "formatted_content": (
                    f"No guidelines found for '{topic}' in curated sources. Try rephrasing your query."
                ),
                "total_guidelines": 0,
                "note": "No guidelines retrieved from search",
                "cached": False,
            }
            if self._cache:
                self._cache.set(cache_key, result)
            return result

        formatted_content = self._formatter.format_guidelines_for_agent(topic, retrieved)
        result: Dict[str, Any] = {
            "retrieved_guidelines": retrieved,
            "formatted_content": formatted_content,
            "total_guidelines": len(retrieved),
            "topic": topic,
            "note": f"Retrieved {len(retrieved)} relevant guidelines for agent reasoning",
            "cached": False,
        }
        if self._cache:
            self._cache.set(cache_key, result)
        return result
