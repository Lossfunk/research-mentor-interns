"""
Web scraping functionality for searchthearxiv.com.

Handles HTTP requests, retry logic, and response processing.
"""

from __future__ import annotations

import time
from typing import Optional
from urllib.parse import quote, urljoin

import httpx


class SearchTheArxivScraper:
    """Handles web scraping for searchthearxiv.com."""
    
    def __init__(self, timeout: float = 15.0, retry_delay: float = 1.0, max_retries: int = 3):
        self.base_url = "https://searchthearxiv.com/"
        self.search_url = urljoin(self.base_url, "search")
        self.timeout = timeout
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.client: Optional[httpx.Client] = None
    
    def initialize(self) -> None:
        """Initialize the HTTP client."""
        self.client = httpx.Client(
            timeout=self.timeout,
            headers={
                "User-Agent": "AcademicResearchMentor/1.0 (https://github.com/Lossfunk/academic-research-mentor)",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.5",
                "Accept-Encoding": "gzip, deflate",
                "DNT": "1",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            }
        )
    
    def cleanup(self) -> None:
        """Clean up HTTP client."""
        if self.client:
            self.client.close()
            self.client = None
    
    def search(self, query: str) -> Optional[str]:
        """Perform search with retry logic."""
        if not self.client:
            return None
        
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                # Encode query for URL
                encoded_query = quote(query)
                search_url = f"{self.search_url}?q={encoded_query}"
                
                # Make request with exponential backoff
                delay = self.retry_delay * (2 ** attempt)
                if attempt > 0:
                    time.sleep(delay)
                
                response = self.client.get(search_url)
                response.raise_for_status()
                
                return response.text
                
            except Exception as e:
                last_error = e
                if attempt == self.max_retries - 1:
                    break
                continue
        
        # All retries failed
        if last_error:
            raise Exception(f"Search failed after {self.max_retries} attempts: {last_error}")
        
        return None