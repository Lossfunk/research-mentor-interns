from langchain.tools import BaseTool, tool
from typing import Optional, Type, List, Dict, Any
from pydantic import BaseModel, Field
from ..config import Config
import re

class GuidelinesSearchInput(BaseModel):
    topic: str = Field(description="What guidance you need (e.g. 'research problem selection', 'methodology evaluation', 'developing research taste')")

@tool("search_research_guidelines", args_schema=GuidelinesSearchInput)
def search_research_guidelines(topic: str) -> str:
    """Search through curated research guidance sources for relevant mentoring advice on research methodology, project selection, and best practices."""
    
    config = Config()
    
    # Create targeted search queries for different guideline sources
    # Prioritize based on topic keywords for better relevance
    topic_lower = topic.lower()
    
    # Base queries for all sources
    base_queries = [
        f"site:gwern.net {topic} research methodology",
        f"site:lesswrong.com {topic} research project", 
        f"site:colah.github.io {topic} research taste",
        f"site:01.me {topic} research taste",
        f"site:michaelnielsen.org {topic} research principles",
        f"site:letters.lossfunk.com {topic} research methodology",
        f"site:alignmentforum.org {topic} research process",
        f"site:neelnanda.io {topic} research methodology",
        f"site:joschu.net {topic} research methodology",
        f"{topic} research methodology site:arxiv.org",
        f"site:lifescied.org {topic} research process",
        f"site:cuhk.edu.hk {topic} research taste",
        f"site:febs.onlinelibrary.wiley.com {topic} research methodology",
        f"site:researchgate.net {topic} research methodology",
        f"site:academic.oup.com {topic} research methodology",
        f"site:thoughtforms.life {topic} research advice"
    ]
    
    # Select most relevant queries based on topic
    if any(keyword in topic_lower for keyword in ['problem', 'choose', 'select', 'pick']):
        # Prioritize problem selection sources
        search_queries = [
            f"site:lesswrong.com {topic} research project",
            f"site:gwern.net {topic} research methodology",
            f"site:letters.lossfunk.com {topic} research methodology",
            f"site:alignmentforum.org {topic} research process",
            f"site:michaelnielsen.org {topic} research principles"
        ]
    elif any(keyword in topic_lower for keyword in ['taste', 'judgment', 'quality', 'good']):
        # Prioritize research taste sources
        search_queries = [
            f"site:colah.github.io {topic} research taste",
            f"site:01.me {topic} research taste",
            f"site:cuhk.edu.hk {topic} research taste",
            f"site:letters.lossfunk.com {topic} research methodology",
            f"site:thoughtforms.life {topic} research advice"
        ]
    elif any(keyword in topic_lower for keyword in ['method', 'process', 'approach', 'how']):
        # Prioritize methodology sources
        search_queries = [
            f"site:michaelnielsen.org {topic} research principles",
            f"site:gwern.net {topic} research methodology",
            f"site:letters.lossfunk.com {topic} research methodology",
            f"site:alignmentforum.org {topic} research process",
            f"site:neelnanda.io {topic} research methodology"
        ]
    else:
        # Default to diverse mix
        search_queries = base_queries[:6]
    
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        search = DuckDuckGoSearchRun()
        
        all_results = []
        seen_urls = set()
        
        for query in search_queries[:config.MAX_SEARCH_QUERIES]:  # Use configurable limit
            try:
                results = search.run(query)
                # Parse and filter results (this is a simplified version)
                # In practice, you'd need more sophisticated parsing
                if results and len(results) > 20:
                    all_results.append({
                        'query': query,
                        'content': results[:500],  # Truncate long results
                        'source_type': _identify_source_type(query),
                        'source': re.search(r'site:(\S+)', query).group(1) if re.search(r'site:(\S+)', query) else query
                    })
            except Exception as e:
                continue
        
        if not all_results:
            return f"No specific guidance found for '{topic}' in curated research sources. Try rephrasing your query."
        
        # Format response
        response_parts = [f"Found {len(all_results)} relevant guidance sources for '{topic}':\n"]
        
        for i, result in enumerate(all_results, 1):
            source_id = f"guide_{hash(result['content'])& 0xfffff:05x}"
            result['source_id'] = source_id
            response_parts.append(f"GUIDELINE [{source_id}]:")
            response_parts.append(f"Source Type: {result['source_type']}")
            response_parts.append(f"Content: {result['content']}")
            response_parts.append("---")
        
        response_parts.append(
            "\nIMPORTANT: When applying these guidelines in your response, "
            "reference them as '[guide_id]' so users can see which specific "
            "guidelines influenced your advice."
        )
        
        return all_results
        
    except Exception as e:
        return f"Error searching guidelines: {str(e)}. Please try rephrasing your query."

def _identify_source_type(query: str) -> str:
    """Identify the type of source based on the query"""
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
        return "Mechanistic interpretability research"
    elif "joschu.net" in query:
        return "ML research methodology"
    elif "thoughtforms.life" in query:
        return "Student research advice"
    elif "febs.onlinelibrary.wiley.com" in query:
        return "Academic research practices"
    elif "researchgate.net" in query:
        return "Research methodology guide"
    elif "academic.oup.com" in query:
        return "Academic research practices"
    elif "arxiv.org" in query:
        return "Academic research paper"
    else:
        return "Research guidance"

# Alternative implementation using web_fetch for specific URLs
@tool("fetch_specific_guideline")
def fetch_specific_guideline(url: str, focus_topic: str = "") -> str:
    """Fetch content from a specific guideline URL and extract relevant sections."""
    
    config = Config()
    
    # Allow either exact URL allowlist OR domain allowlist
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
    except Exception:
        domain = ""
    
    allowed_domains = set(config.GUIDELINE_SOURCES.keys())
    exact_allowed = url in config.GUIDELINE_URLS
    domain_allowed = domain in allowed_domains
    
    if not (exact_allowed or domain_allowed):
        return (
            f"URL not allowed: {url}. Allowed domains: "
            f"{', '.join(sorted(allowed_domains))}"
        )
    
    try:
        # This would use your web_fetch tool
        # content = web_fetch(url)
        
        # For now, return a placeholder
        return f"Would fetch content from {url} focusing on '{focus_topic}'"
        
    except Exception as e:
        return f"Error fetching {url}: {str(e)}"

class GuidelinesToolkit:
    """Collection of guideline-related tools"""
    
    @staticmethod
    def get_tools() -> List[Any]:
        return [
            search_research_guidelines,
            fetch_specific_guideline
        ]
