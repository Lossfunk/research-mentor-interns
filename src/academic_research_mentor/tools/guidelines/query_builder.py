"""
Query building and prioritization utilities for guidelines tool.

Handles search query generation, source type identification,
and domain extraction for research guidance searches.
"""

import re
from typing import List

from .config import GuidelinesConfig


class QueryBuilder:
    """Handles query generation and prioritization for research guidelines."""
    
    def __init__(self, config: GuidelinesConfig):
        self.config = config
    
    def get_prioritized_queries(self, topic: str) -> List[str]:
        """Generate prioritized search queries based on topic keywords."""
        topic_lower = topic.lower()
        base_queries = self.config.get_search_queries(topic)
        
        # Prioritize queries based on topic content
        if any(keyword in topic_lower for keyword in ['problem', 'choose', 'select', 'pick']):
            # Prioritize problem selection sources
            return [
                f"site:lesswrong.com {topic} research project",
                f"site:gwern.net {topic} research methodology",
                f"site:letters.lossfunk.com {topic} research methodology",
                f"site:alignmentforum.org {topic} research process",
                f"site:michaelnielsen.org {topic} research principles"
            ]
        elif any(keyword in topic_lower for keyword in ['taste', 'judgment', 'quality', 'good']):
            # Prioritize research taste sources  
            return [
                f"site:colah.github.io {topic} research taste",
                f"site:01.me {topic} research taste",
                f"site:cuhk.edu.hk {topic} research taste",
                f"site:letters.lossfunk.com {topic} research methodology",
                f"site:thoughtforms.life {topic} research advice"
            ]
        elif any(keyword in topic_lower for keyword in ['method', 'process', 'approach', 'how']):
            # Prioritize methodology sources
            return [
                f"site:michaelnielsen.org {topic} research principles",
                f"site:gwern.net {topic} research methodology",
                f"site:letters.lossfunk.com {topic} research methodology",
                f"site:alignmentforum.org {topic} research process",
                f"site:neelnanda.io {topic} research methodology"
            ]
        else:
            # Default to diverse mix
            return base_queries[:6]
    
    def identify_source_type(self, query: str) -> str:
        """Identify the source type based on the search query."""
        if "gwern.net" in query:
            return "Hamming's research methodology"
        elif "lesswrong.com" in query:
            return "Research project selection"
        elif "colah.github.io" in query:
            return "Research taste and judgment"
        elif "michaelnielsen.org" in query:
            return "Research methodology principles"
        elif "letters.lossfunk.com" in query:
            return "Research methodology and good science"
        elif "alignmentforum.org" in query:
            return "Research process and ML guidance"
        elif "neelnanda.io" in query:
            return "Mechanistic interpretability methodology"
        elif "joschu.net" in query:
            return "ML research methodology"
        elif "arxiv.org" in query:
            return "Academic research papers"
        else:
            return "Research guidance"
    
    def extract_domain(self, query_str: str) -> str:
        """Extract domain from site: query."""
        match = re.search(r'site:(\S+)', query_str)
        return match.group(1) if match else "unknown"
