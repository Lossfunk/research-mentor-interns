"""
HTML parsing functionality for searchthearxiv.com results.

Extracts paper information from search result pages.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from urllib.parse import urljoin

from bs4 import BeautifulSoup


class SearchTheArxivParser:
    """Parses search results from searchthearxiv.com HTML."""
    
    def __init__(self, base_url: str = "https://searchthearxiv.com/"):
        self.base_url = base_url
    
    def parse_results(self, html_content: str, limit: int) -> List[Dict[str, Any]]:
        """Parse search results from HTML content."""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            papers = []
            
            # Try to find paper results - this will need to be adapted based on actual HTML structure
            # Common patterns for paper listings
            paper_selectors = [
                '.paper-item', '.result-item', '.search-result',
                'article', '.paper', '.entry',
                '[class*="paper"]', '[class*="result"]'
            ]
            
            for selector in paper_selectors:
                results = soup.select(selector)
                if results:
                    papers.extend(self._extract_paper_info(results))
                    break
            
            # If no structured results found, try to find links that look like papers
            if not papers:
                papers = self._extract_papers_from_links(soup)
            
            # Limit results and ensure unique papers
            unique_papers = []
            seen_urls = set()
            
            for paper in papers[:limit * 2]:  # Get more initially to account for duplicates
                url = paper.get('url', '')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_papers.append(paper)
                    if len(unique_papers) >= limit:
                        break
            
            return unique_papers
            
        except Exception as e:
            # If parsing fails, return empty list rather than raising
            return []
    
    def _extract_paper_info(self, elements: List[Any]) -> List[Dict[str, Any]]:
        """Extract paper information from HTML elements."""
        papers = []
        
        for element in elements:
            try:
                # Try to extract title
                title_elem = element.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if not title_elem:
                    title_elem = element.find(['a', 'span', 'div'], class_=lambda x: x and 'title' in x.lower())
                
                title = title_elem.get_text(strip=True) if title_elem else "Unknown Title"
                
                # Try to extract URL
                url_elem = element.find('a', href=True)
                url = url_elem['href'] if url_elem else ""
                
                # Ensure URL is absolute
                if url and not url.startswith('http'):
                    if url.startswith('/'):
                        url = urljoin(self.base_url, url)
                    else:
                        url = urljoin(self.base_url, f"/{url}")
                
                # Try to extract authors
                authors_elem = element.find(class_=lambda x: x and any(word in x.lower() for word in ['author', 'by']))
                authors = []
                if authors_elem:
                    author_text = authors_elem.get_text(strip=True)
                    # Simple author parsing
                    authors = [author.strip() for author in author_text.split(',')[:3]]
                
                # Try to extract abstract/description
                abstract_elem = element.find(class_=lambda x: x and any(word in x.lower() for word in ['abstract', 'description', 'summary']))
                abstract = abstract_elem.get_text(strip=True)[:500] if abstract_elem else ""
                
                # Try to extract year
                year_elem = element.find(class_=lambda x: x and any(word in x.lower() for word in ['year', 'date', 'published']))
                year = None
                if year_elem:
                    year_text = year_elem.get_text(strip=True)
                    # Extract 4-digit year
                    year_match = re.search(r'\b(20\d{2})\b', year_text)
                    if year_match:
                        year = int(year_match.group(1))
                
                paper = {
                    "title": title,
                    "url": url,
                    "authors": authors,
                    "abstract": abstract,
                    "year": year,
                    "source": "searchthearxiv",
                    "venue": "arXiv"  # Since searchthearxiv searches arXiv
                }
                
                papers.append(paper)
                
            except Exception:
                # Skip malformed elements
                continue
        
        return papers
    
    def _extract_papers_from_links(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract paper information from links when structured data is not available."""
        papers = []
        
        # Find links that might be papers
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            # Check if link looks like a paper (contains arXiv or paper-related keywords)
            if (any(keyword in href.lower() for keyword in ['arxiv', 'pdf', 'paper']) or
                any(keyword in link.get_text().lower() for keyword in ['arxiv', 'paper'])):
                
                title = link.get_text(strip=True)
                if len(title) > 10:  # Avoid very short titles
                    # Ensure URL is absolute
                    if not href.startswith('http'):
                        if href.startswith('/'):
                            href = urljoin(self.base_url, href)
                        else:
                            href = urljoin(self.base_url, f"/{href}")
                    
                    paper = {
                        "title": title,
                        "url": href,
                        "authors": [],
                        "abstract": "",
                        "year": None,
                        "source": "searchthearxiv",
                        "venue": "arXiv"
                    }
                    
                    papers.append(paper)
        
        return papers