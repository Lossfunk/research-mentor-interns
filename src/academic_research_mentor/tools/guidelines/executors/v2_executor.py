from __future__ import annotations

from typing import Any, Dict, List, Optional

from ..cache import GuidelinesCache
from ..evidence_collector import EvidenceCollector
from ..formatter import GuidelinesFormatter
from ..search_providers import BaseSearchProvider
from ..citation_handler import GuidelinesCitationHandler


class GuidelinesV2Executor:
    """Handle guidelines execution when FF_GUIDELINES_V2 is enabled."""

    def __init__(
        self,
        evidence_collector: EvidenceCollector,
        formatter: GuidelinesFormatter,
        citation_handler: GuidelinesCitationHandler,
        cache: Optional[GuidelinesCache],
        search_tool: Optional[BaseSearchProvider],
    ) -> None:
        self._evidence_collector = evidence_collector
        self._formatter = formatter
        self._citation_handler = citation_handler
        self._cache = cache
        self._search_tool = search_tool

    def run(
        self,
        topic: str,
        mode: str,
        max_per_source: int,
        response_format: str,
        page_size: int,
        next_token: Optional[str],
        cache_key: str,
    ) -> Dict[str, Any]:
        curated = self._evidence_collector.collect_curated_evidence(topic)
        evidence: List[Dict[str, Any]] = list(curated)
        sources_covered = sorted(
            {
                entry.get("domain", "")
                for entry in curated
                if entry.get("domain")
            }
        )

        if self._search_tool:
            searched, covered = self._evidence_collector.collect_structured_evidence(
                topic, mode, max_per_source
            )
            evidence.extend(searched)
            for domain in covered:
                if domain and domain not in sources_covered:
                    sources_covered.append(domain)

        if not evidence:
            result: Dict[str, Any] = {
                "topic": topic,
                "total_evidence": 0,
                "sources_covered": sources_covered,
                "evidence": [],
                "pagination": {"has_more": False, "next_token": None},
                "cached": False,
                "note": "No evidence found",
            }
            if self._cache:
                self._cache.set(cache_key, result)
            return result

        result = self._formatter.format_v2_response(
            topic, evidence, sources_covered, response_format, page_size, next_token
        )
        result = self._citation_handler.add_citation_metadata(result, evidence)

        if self._cache:
            self._cache.set(cache_key, result)
        return result
