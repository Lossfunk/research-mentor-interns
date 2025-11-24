from __future__ import annotations

import re
from typing import Any

from ..rich_formatter import print_agent_reasoning


def guidelines_tool_fn(query: str, *, internal_delimiters: tuple[str, str] | None = None) -> str:
    """Search for research methodology and mentorship guidelines from curated sources."""
    begin, end = internal_delimiters or ("", "")

    def _fallback_guidelines_block(note: str | None = None) -> str:
        """Return a concise offline guidelines block when live search fails."""
        try:
            from ..guidelines_engine.loader import GuidelinesLoader
            from ..guidelines_engine.formatter import GuidelinesFormatter
            from ..citations.enforcer import enforce_citation_schema

            loader = GuidelinesLoader()
            guidelines = loader.load_guidelines()

            # Lightweight relevance filter on title/content/tags/category
            q_words = [
                w for w in re.split(r"[^a-z0-9]+", query.lower())
                if len(w) > 3
            ]
            filtered = []
            if q_words:
                for g in guidelines:
                    haystack = " ".join(
                        [
                            str(g.get("title", "")),
                            str(g.get("content", "")),
                            " ".join(g.get("tags") or []),
                            str(g.get("category", "")),
                        ]
                    ).lower()
                    if any(word in haystack for word in q_words):
                        filtered.append(g)
            if not filtered:
                filtered = guidelines[:5]

            formatter = GuidelinesFormatter(max_guidelines=5)
            formatted = formatter.format_guidelines_for_prompt(
                filtered,
                format_style="compact",
            )
            # Inject [G#] IDs for clarity
            lines = ["Guidelines fallback (offline cache)"]
            if note:
                lines.append(f"Note: {note}")
            for i, g in enumerate(filtered, 1):
                title = g.get("title", "guideline")
                content = g.get("content", "").strip()
                snippet = content[:220] + ("…" if len(content) > 220 else "")
                lines.append(f"[G{i}] {title}: {snippet}")
            reasoning = "\n".join(lines)
            reasoning = enforce_citation_schema(reasoning, add_legend=True)
            print_agent_reasoning(reasoning)
            return f"{begin}{reasoning}{end}" if begin or end else reasoning
        except Exception as exc:  # pragma: no cover - defensive fallback
            minimal = [
                "Validate the problem is important before optimizing the solution.",
                "Write down crisp hypotheses and success metrics before running experiments.",
                "Prefer simple, controlled baselines before complex systems.",
                "Limit concurrent changes; isolate variables to avoid confounds.",
                "Document assumptions and failure modes; pre-mortem major risks.",
            ]
            lines = ["Guidelines fallback (minimal cache)"]
            if note:
                lines.append(f"Note: {note}")
            for i, item in enumerate(minimal, 1):
                lines.append(f"[G{i}] {item}")
            lines.append(f"(offline cache unavailable: {exc})")
            reasoning = "\n".join(lines)
            reasoning = enforce_citation_schema(reasoning, add_legend=True)
            return f"{begin}{reasoning}{end}" if begin or end else reasoning

    try:
        from ..core.orchestrator import Orchestrator
        from ..tools import auto_discover
        from ..citations import CitationMerger

        # Ensure tools are discovered
        auto_discover()

        orch = Orchestrator()
        # Request a larger page to surface more curated sources with full URLs
        result = orch.execute_task(
            task="research_guidelines",
            inputs={
                "query": query,
                "topic": query,
                "response_format": "concise",
                "page_size": 30,
                "mode": "fast",
            },
            context={"goal": f"research mentorship guidance about {query}"}
        )

        if result["execution"]["executed"] and result["results"]:
            tool_result = result["results"]

            # Support both V2 structured evidence and V1 legacy output
            evidence_items = tool_result.get("evidence") or []
            guidelines = tool_result.get("retrieved_guidelines", [])

            if not evidence_items and not guidelines:
                return _fallback_guidelines_block(
                    "No specific guidelines found in live search."
                )

            # Use citation merger for unified formatting
            merger = CitationMerger()
            merged_result = merger.merge_citations(
                papers=[],  # No papers from guidelines tool
                guidelines=evidence_items + guidelines,
                max_guidelines=30
            )

            reasoning_block = merged_result["context"]
            # Print as Agent's reasoning panel for TUI differentiation
            print_agent_reasoning(reasoning_block)
            return f"{begin}{reasoning_block}{end}" if begin or end else reasoning_block
        else:
            return _fallback_guidelines_block("Guidelines search temporarily unavailable.")

    except Exception as e:
        return _fallback_guidelines_block(f"Error searching guidelines: {str(e)}")
