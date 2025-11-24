"""
Citation schema enforcer and helper utilities.

Goals:
- Uniform IDs across tools: [A#] attachments, [P#] papers, [G#] guidelines, [W#] web/news.
- Add a legend footer when citations are present.
- Optionally inject first‑mention micro‑metadata when provided.
- Safe to run on free‑form LLM output; leaves text unchanged if no citations.
"""

from __future__ import annotations

import re
from typing import Iterable, List, Dict, Any, Tuple


CITATION_PATTERN = re.compile(r"\[(?P<prefix>[APGW])(?P<idx>\d+)(?P<suffix>[^\]]*)\]")

DEFAULT_LEGEND = (
    "Sources — A: attachments; P: papers/arxiv/unified; G: research guidelines; "
    "W: web/news. Strength flags: †strong (peer-reviewed/curated), †weak (blog/forum)."
)


def _normalize_id(prefix: str, idx: str, suffix: str) -> str:
    """Normalize a citation token."""
    suffix_clean = suffix or ""
    return f"[{prefix}{int(idx)}{suffix_clean}]"


def enforce_citation_schema(
    text: str,
    *,
    source_metadata: Iterable[Dict[str, Any]] | None = None,
    add_legend: bool = True,
) -> str:
    """Normalize citation IDs and append a legend if citations are present.

    Args:
        text: The agent/tool output.
        source_metadata: Optional iterable of dicts with keys:
            id (e.g., 'P1'), title, venue/domain, year, strength ('strong'|'weak').
        add_legend: Whether to add a legend footer.

    Returns:
        Possibly modified text with normalized citations and legend.
    """
    if not text:
        return text

    matches = list(CITATION_PATTERN.finditer(text))
    if not matches:
        return text

    normalized_ids: List[str] = []
    output = text
    for m in matches:
        old = m.group(0)
        new = _normalize_id(m.group("prefix"), m.group("idx"), m.group("suffix"))
        if old != new:
            output = output.replace(old, new)
        normalized_ids.append(new)

    # Inject first-mention micro-metadata when available
    if source_metadata:
        meta_map = {str(item.get("id")): item for item in source_metadata}
        seen: set[str] = set()

        def _build_meta(item: Dict[str, Any]) -> str:
            title = str(item.get("title") or "").strip()
            venue = str(item.get("venue") or item.get("domain") or "").strip()
            year = str(item.get("year") or "").strip()
            parts = [p for p in (title, venue, year) if p]
            suffix = " | ".join(parts) if parts else ""
            strength = item.get("strength")
            if strength in {"strong", "weak"}:
                suffix = f"{suffix} [{strength}]" if suffix else f"[{strength}]"
            return suffix

        def _attach_meta(match: re.Match) -> str:
            cid = f"{match.group('prefix')}{int(match.group('idx'))}"
            token = match.group(0)
            if cid in seen or cid not in meta_map:
                return token
            seen.add(cid)
            meta = _build_meta(meta_map[cid])
            if not meta:
                return token
            return f"{token} ({meta})"

        output = CITATION_PATTERN.sub(_attach_meta, output)

    # Append legend if not present
    if add_legend and "Sources —" not in output:
        output = output.rstrip() + "\n\n" + DEFAULT_LEGEND

    return output


def summarize_sources_for_footer(sources: List[Dict[str, Any]]) -> str:
    """Produce a concise footer line describing sources by tool/bucket."""
    if not sources:
        return ""

    buckets: Dict[str, List[str]] = {"A": [], "P": [], "G": [], "W": []}
    for src in sources:
        cid = str(src.get("id") or "")
        if not cid:
            continue
        bucket = cid[0]
        buckets.setdefault(bucket, [])
        title = str(src.get("title") or src.get("domain") or src.get("venue") or "").strip()
        if title:
            buckets[bucket].append(title[:80])

    parts = []
    for prefix, names in buckets.items():
        if names:
            parts.append(f"{prefix}: {', '.join(names[:3])}")

    return "Sources by bucket — " + "; ".join(parts)
