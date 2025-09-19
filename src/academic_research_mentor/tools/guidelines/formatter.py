"""
Content formatting utilities for guidelines tool.

Handles formatting of guidelines content for agent reasoning
and user presentation.
"""

from typing import Any, Dict, List, Optional


class GuidelinesFormatter:
    """Handles content formatting for research guidelines."""
    
    def format_guidelines_for_agent(self, topic: str, guidelines: List[Dict[str, Any]]) -> str:
        """Format retrieved guidelines for agent reasoning (RAG-style)."""
        content_parts = [
            f"Retrieved {len(guidelines)} research guidelines for topic: '{topic}'\n"
        ]
        
        for guideline in guidelines:
            guide_id = guideline["guide_id"]
            source_type = guideline["source_type"] 
            content = guideline["content"]
            
            content_parts.extend([
                f"GUIDELINE [{guide_id}]:",
                f"Source: {source_type}",
                f"Content: {content}",
                "---"
            ])
        
        content_parts.append(
            "\nINSTRUCTION: Use the above guidelines to provide evidence-based research advice. "
            "When referencing guidelines in your response, cite them as '[guide_id]' so users "
            "can see which specific sources influenced your advice."
        )
        
        return "\n".join(content_parts)
    
    def format_v2_response(self, topic: str, evidence: List[Dict[str, Any]], 
                          sources_covered: List[str], response_format: str, 
                          page_size: int, next_token: Optional[str] = None) -> Dict[str, Any]:
        """Format V2 structured response with pagination."""
        # Apply response format
        if response_format == "concise":
            # Trim snippets
            concise_evidence = [
                {
                    **item,
                    "snippet": item.get("snippet", "")[:300]
                } for item in evidence
            ]
        else:
            concise_evidence = evidence

        # Deduplicate by URL
        seen = set()
        deduped = []
        for item in concise_evidence:
            url = item.get("url")
            if url and url not in seen:
                seen.add(url)
                deduped.append(item)

        capped_all = deduped[: self.config.RESULT_CAP]

        # Pagination via index token
        start_index = 0
        if next_token and next_token.isdigit():
            start_index = int(next_token)
        end_index = min(start_index + page_size, len(capped_all))
        page_items = capped_all[start_index:end_index]
        new_next_token = str(end_index) if end_index < len(capped_all) else None

        return {
            "topic": topic,
            "total_evidence": len(deduped),
            "sources_covered": sources_covered,
            "evidence": page_items,
            "pagination": {"has_more": new_next_token is not None, "next_token": new_next_token},
            "cached": False
        }
    
    def __init__(self, config):
        self.config = config
