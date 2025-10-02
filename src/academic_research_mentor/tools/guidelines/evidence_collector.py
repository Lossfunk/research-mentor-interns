"""
Evidence collection utilities for guidelines tool.

Handles both curated and search-based evidence collection with
timeout management and cost tracking.
"""

from __future__ import annotations

import re
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .config import GuidelinesConfig


class EvidenceCollector:
    """Handles evidence collection from curated and search sources."""

    def __init__(self, config: GuidelinesConfig, search_tool: Any, cost_tracker: Any):
        self.config = config
        self._search_tool = search_tool
        self._cost_tracker = cost_tracker

    def collect_structured_evidence(
        self, topic: str, mode: str, max_per_source: int
    ) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Collect structured (or semi-structured) evidence across curated domains."""

        evidence: List[Dict[str, Any]] = []
        sources_covered: List[str] = []
        provider = self._search_tool
        if not provider:
            return evidence, sources_covered

        supports_structured = bool(getattr(provider, "supports_structured", False))
        supports_text = bool(getattr(provider, "supports_text", False))

        start_time = time.time()
        global_deadline = start_time + float(getattr(self.config, "GLOBAL_RETRIEVAL_BUDGET_SECS", 8.0))

        for domain in self.config.GUIDELINE_SOURCES.keys():
            if time.time() > global_deadline:
                break

            queries = GuidelinesConfig.build_queries(topic, domain, mode)
            items_for_domain: List[Dict[str, Any]] = []
            domain_deadline = time.time() + float(
                getattr(self.config, "PER_DOMAIN_SOFT_BUDGET_SECS", 1.5)
            )

            for q in queries:
                if time.time() > global_deadline or time.time() > domain_deadline:
                    break

                try:
                    now_iso = datetime.utcnow().isoformat() + "Z"

                    if supports_structured:
                        results = provider.search_structured(
                            q, domain=domain, mode=mode, max_results=max_per_source
                        )
                        if not results:
                            continue
                        for res in results:
                            url = str(
                                res.get("url")
                                or self._select_curated_url(domain, topic, q)
                                or f"https://{domain}"
                            )
                            title = str(res.get("title") or f"{domain} — result")
                            snippet = str(
                                res.get("content") or res.get("snippet") or ""
                            )[:800]
                            if not snippet:
                                snippet = self._select_curated_thesis(domain, url, topic)
                            evidence_id = f"ev_{hash((domain, q, url, title)) & 0xfffffff:x}"
                            item = {
                                "evidence_id": evidence_id,
                                "domain": domain,
                                "url": url,
                                "search_url": res.get("raw_url") or url,
                                "title": title,
                                "snippet": snippet,
                                "query_used": q,
                                "retrieved_at": now_iso,
                                "score": res.get("score"),
                            }
                            items_for_domain.append(item)
                            if self._cost_tracker:
                                self._cost_tracker.record_search_query(0.01)
                            if len(items_for_domain) >= max_per_source:
                                break
                    else:
                        raw = None
                        if supports_text and hasattr(provider, "search_text"):
                            raw = provider.search_text(q)
                        elif hasattr(provider, "run"):
                            raw = provider.run(q)

                        if not raw or len(raw) < 20:
                            continue

                        url = (
                            self._select_curated_url(domain, topic, q)
                            or f"https://{domain}"
                        )
                        snippet = str(raw)[:800]
                        title = f"{domain} — result"
                        evidence_id = f"ev_{hash((domain, q, url, title)) & 0xfffffff:x}"
                        search_url = f"https://duckduckgo.com/?q={q.replace(' ', '+')}"
                        item = {
                            "evidence_id": evidence_id,
                            "domain": domain,
                            "url": url,
                            "search_url": search_url,
                            "title": title,
                            "snippet": snippet,
                            "query_used": q,
                            "retrieved_at": now_iso,
                        }
                        items_for_domain.append(item)
                        if self._cost_tracker:
                            self._cost_tracker.record_search_query(0.01)

                except Exception:
                    continue

                if len(items_for_domain) >= max_per_source:
                    break

            if items_for_domain:
                evidence.extend(items_for_domain)
                sources_covered.append(domain)
            if len(evidence) >= self.config.RESULT_CAP:
                break

        return evidence, sources_covered

    def collect_curated_evidence(self, topic: str) -> List[Dict[str, Any]]:
        """Return curated evidence ranked by rough relevance to the topic."""

        items: List[Dict[str, Any]] = []
        try:
            topic_text = (topic or "").lower()
            topic_tokens = {t for t in re.split(r"[^a-z0-9]+", topic_text) if t}
            by_domain = GuidelinesConfig.urls_by_domain()
            domain_desc = getattr(self.config, "GUIDELINE_SOURCES", {})

            scored: List[tuple[int, Dict[str, Any]]] = []
            now_iso = datetime.utcnow().isoformat() + "Z"

            for domain, urls in by_domain.items():
                desc_tokens = {
                    t
                    for t in re.split(
                        r"[^a-z0-9]+", str(domain_desc.get(domain, "")).lower()
                    )
                    if t
                }
                for u in urls:
                    u_lower = u.lower()
                    path = re.sub(r"https?://", "", u_lower)
                    path_tokens = {t for t in re.split(r"[^a-z0-9]+", path) if t}
                    overlap = len(topic_tokens & (path_tokens | desc_tokens))
                    tie_break = len(path)
                    score = overlap * 1000 + tie_break
                    title = self._title_from_url(u)
                    thesis = GuidelinesConfig.thesis_for_url(u)
                    ev_id = f"cv_{hash((domain, u)) & 0xfffffff:x}"
                    scored.append(
                        (
                            score,
                            {
                                "evidence_id": ev_id,
                                "domain": domain,
                                "url": u,
                                "search_url": None,
                                "title": title,
                                "snippet": thesis
                                or f"Curated source from {domain}: {domain_desc.get(domain, 'research guidance')}",
                                "thesis": thesis,
                                "relevance_score": score,
                                "query_used": topic,
                                "retrieved_at": now_iso,
                            },
                        )
                    )

            for _score, item in sorted(scored, key=lambda x: x[0], reverse=True):
                items.append(item)

            return items[: self.config.RESULT_CAP]
        except Exception:
            return items

    def _title_from_url(self, url: str) -> str:
        try:
            cleaned = re.sub(r"https?://", "", url)
            parts = [p for p in cleaned.split("/") if p]
            if not parts:
                return url
            last = parts[-1].split("?")[0]
            last = last.replace("-", " ").replace("_", " ")
            if "arxiv.org" in url and "/abs/" in url:
                return f"arXiv {parts[-1]}"
            return last.title()
        except Exception:
            return url

    def _select_curated_url(self, domain: str, topic: str, query_used: str) -> Optional[str]:
        try:
            by_domain = GuidelinesConfig.urls_by_domain()
            urls = by_domain.get(domain.lower()) or []
            if not urls:
                return None
            text = f"{topic} {query_used}".lower()
            text_tokens = {t for t in re.split(r"[^a-z0-9]+", text) if t}
            best_url: Optional[str] = None
            best_score = -1
            for u in urls:
                u_lower = u.lower()
                path = re.sub(r"https?://", "", u_lower)
                path_tokens = {t for t in re.split(r"[^a-z0-9]+", path) if t}
                score = len(text_tokens & path_tokens)
                if score > best_score or (
                    score == best_score and best_url is not None and len(u) > len(best_url)
                ):
                    best_score = score
                    best_url = u
            return best_url or urls[0]
        except Exception:
            return None

    def _select_curated_thesis(self, domain: str, url: str, topic: str) -> str:
        try:
            thesis = GuidelinesConfig.thesis_for_url(url)
            if thesis:
                return thesis
            return f"Curated source from {domain} relevant to {topic}."
        except Exception:
            return f"Curated source from {domain}."
"""
Evidence collection utilities for guidelines tool.

Handles both curated and search-based evidence collection with
timeout management and cost tracking.
"""

