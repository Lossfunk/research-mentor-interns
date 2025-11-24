"""
Lightweight citation lint checks for mentor responses.

Heuristics:
- If citations exist, require a legend ("Sources —").
- Numeric claims should be followed by a citation within a short window.
"""

from __future__ import annotations

import re
from typing import Dict, List

from .enforcer import CITATION_PATTERN


def lint_response(text: str) -> Dict[str, List[str]]:
    """Return lint findings for a response string."""
    issues: List[str] = []
    if not text:
        return {"issues": ["empty_response"]}

    citations = list(CITATION_PATTERN.finditer(text))
    has_cites = bool(citations)

    if has_cites and "Sources —" not in text:
        issues.append("legend_missing")

    if has_cites:
        # Heuristic: numbers (percentages/years) should be cited
        numeric_tokens = list(re.finditer(r"\b\d[\d,]*(?:\.\d+)?%?", text))
        for m in numeric_tokens:
            tail = text[m.end() : m.end() + 18]
            if not CITATION_PATTERN.search(tail):
                issues.append("number_without_citation")
                break

    return {"issues": issues}
