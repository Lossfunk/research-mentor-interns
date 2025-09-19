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
    
    def collect_structured_evidence(self, topic: str, mode: str, max_per_source: int) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Collect structured evidence across curated sources.

        Returns tuple of (evidence_list, sources_covered)
        """
        evidence: List[Dict[str, Any]] = []
        sources_covered: List[str] = []
        # Iterate curated domains
        start_time = time.time()
        global_deadline = start_time + float(getattr(self.config, "GLOBAL_RETRIEVAL_BUDGET_SECS", 8.0))
        
        for domain in self.config.GUIDELINE_SOURCES.keys():
            if time.time() > global_deadline:
                break
            queries = GuidelinesConfig.build_queries(topic, domain, mode)
            items_for_domain: List[Dict[str, Any]] = []
            domain_deadline = time.time() + float(getattr(self.config, "PER_DOMAIN_SOFT_BUDGET_SECS", 1.5))
            
            for q in queries:
                if time.time() > global_deadline or time.time() > domain_deadline:
                    break
                try:
                    raw = self._search_tool.run(q)
                    if not raw or len(raw) < 20:
                        continue
                    # We do not have a parser; treat the text blob as snippet and associate URL heuristically
                    # In future, switch to a search API that returns structured results
                    now_iso = datetime.utcnow().isoformat() + "Z"
                    # Prefer a curated URL from our source list when available, to improve grounding/citation
                    url = self._select_curated_url(domain, topic, q) or f"https://{domain}"
                    search_url = f"https://duckduckgo.com/?q={q.replace(' ', '+')}"
                    evidence_id = f"ev_{hash((domain, q, url)) & 0xfffffff:x}"
                    item = {
                        "evidence_id": evidence_id,
                        "domain": domain,
                        "url": url,
                        "search_url": search_url,
                        "title": f"{domain} — result",
                        "snippet": raw[:800],
                        "query_used": q,
                        "retrieved_at": now_iso,
                    }
                    items_for_domain.append(item)
                    if self._cost_tracker:
                        self._cost_tracker.record_search_query(0.01)
                    if len(items_for_domain) >= max_per_source:
                        break
                except Exception:
                    continue
            if items_for_domain:
                evidence.extend(items_for_domain)
                sources_covered.append(domain)
            if len(evidence) >= self.config.RESULT_CAP:
                break
        return evidence, sources_covered

    def collect_curated_evidence(self, topic: str) -> List[Dict[str, Any]]:
        """Return curated evidence items ranked by simple relevance to the topic.

        Uses the configured GUIDELINE_URLS to ensure we always provide full, stable
        links for citation. Relevance is estimated via token overlap between the
        topic and the URL path (and domain description when available). No network.
        """
        items: List[Dict[str, Any]] = []
        try:
            topic_text = (topic or "").lower()
            topic_tokens = {t for t in re.split(r"[^a-z0-9]+", topic_text) if t}
            by_domain = GuidelinesConfig.urls_by_domain()
            domain_desc = getattr(self.config, "GUIDELINE_SOURCES", {})

            scored: List[tuple[int, Dict[str, Any]]] = []
            now_iso = datetime.utcnow().isoformat() + "Z"
            for domain, urls in by_domain.items():
                desc_tokens = {t for t in re.split(r"[^a-z0-9]+", str(domain_desc.get(domain, "")).lower()) if t}
                for u in urls:
                    u_lower = u.lower()
                    path = re.sub(r"https?://", "", u_lower)
                    path_tokens = {t for t in re.split(r"[^a-z0-9]+", path) if t}
                    overlap = len(topic_tokens & (path_tokens | desc_tokens))
                    # Prefer deeper paths (more specific) on ties
                    tie_break = len(path)
                    score = overlap * 1000 + tie_break
                    title = self._title_from_url(u)
                    thesis = GuidelinesConfig.thesis_for_url(u)
                    ev_id = f"cv_{hash((domain, u)) & 0xfffffff:x}"
                    scored.append((score, {
                        "evidence_id": ev_id,
                        "domain": domain,
                        "url": u,
                        "search_url": None,
                        "title": title,
                        "snippet": thesis or f"Curated source from {domain}: {domain_desc.get(domain, 'research guidance')}",
                        "thesis": thesis,
                        "relevance_score": score,
                        "query_used": topic,
                        "retrieved_at": now_iso,
                    }))
            # Sort high to low by score
            for _score, item in sorted(scored, key=lambda x: x[0], reverse=True):
                items.append(item)
            # Respect global cap
            return items[: self.config.RESULT_CAP]
        except Exception:
            return items

    def _title_from_url(self, url: str) -> str:
        try:
            # Use last non-empty path component or domain as title stub
            m = re.sub(r"https?://", "", url)
            parts = [p for p in m.split("/") if p]
            if not parts:
                return url
            last = parts[-1]
            # Clean common query fragments
            last = last.split("?")[0]
            last = last.replace("-", " ").replace("_", " ")
            # For arXiv
            if "arxiv.org" in url and "/abs/" in url:
                return f"arXiv {parts[-1]}"
            # Title-case basic tokens
            return last.title()
        except Exception:
            return url

    def _select_curated_url(self, domain: str, topic: str, query_used: str) -> Optional[str]:
        """Select a curated URL for a domain that best matches the topic/query.

        Uses a simple token-overlap heuristic to avoid extra dependencies while
        providing reasonable semantic grounding from our curated list.
        """
        try:
            by_domain = GuidelinesConfig.urls_by_domain()
            urls = by_domain.get(domain.lower()) or []
            if not urls:
                return None
            text = f"{topic} {query_used}".lower()
            text_tokens = {t for t in re.split(r"[^a-z0-9]+", text) if t}
            best_url: Optional[str] = None
            best_score: int = -1
            for u in urls:
                u_lower = u.lower()
                # Tokenize path/title-ish parts of the URL for rough matching
                path = re.sub(r"https?://", "", u_lower)
                path_tokens = {t for t in re.split(r"[^a-z0-9]+", path) if t}
                score = len(text_tokens & path_tokens)
                # Prefer longer URLs (more specific) on ties
                if score > best_score or (score == best_score and best_url and len(u) > len(best_url)):
                    best_score = score
                    best_url = u
            return best_url or urls[0]
        except Exception:
            return None
