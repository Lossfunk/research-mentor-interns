"""
Caching and cost monitoring utilities for guidelines tool.

Provides file-based caching with TTL and basic cost tracking.
"""

from __future__ import annotations

import json
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional
import hashlib

from .config import GuidelinesConfig


class GuidelinesCache:
    """File-based cache for guidelines search results."""
    
    def __init__(self, config: GuidelinesConfig):
        self.config = config
        self.cache_dir = Path.home() / ".cache" / "academic-research-mentor" / "guidelines"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cost_tracker = CostTracker()
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key for a query."""
        # Use hash of query to ensure valid filename
        return hashlib.md5(query.encode()).hexdigest()
    
    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{cache_key}.json"
    
    def _is_cache_valid(self, cache_path: Path) -> bool:
        """Check if cache file is still valid based on TTL."""
        if not cache_path.exists():
            return False
        
        stat = cache_path.stat()
        cache_time = datetime.fromtimestamp(stat.st_mtime)
        expiry_time = datetime.now() - timedelta(hours=self.config.CACHE_TTL_HOURS)
        
        return cache_time > expiry_time
    
    def get(self, query: str) -> Optional[Dict[str, Any]]:
        """Get cached result for query."""
        if not self.config.ENABLE_CACHING:
            return None
        
        cache_key = self._get_cache_key(query)
        cache_path = self._get_cache_path(cache_key)
        
        if not self._is_cache_valid(cache_path):
            return None
        
        try:
            with open(cache_path, 'r') as f:
                cached_data = json.load(f)
            
            # Track cache hit
            self.cost_tracker.record_cache_hit()
            return cached_data
            
        except Exception:
            # Cache corrupted or unreadable
            return None
    
    def set(self, query: str, result: Dict[str, Any]) -> None:
        """Cache result for query."""
        if not self.config.ENABLE_CACHING:
            return
        
        cache_key = self._get_cache_key(query)
        cache_path = self._get_cache_path(cache_key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(result, f, indent=2)
            
            # Track cache write
            self.cost_tracker.record_cache_write()
            
        except Exception:
            # Failed to write cache
            pass
    
    def clear(self) -> None:
        """Clear all cached results."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
        
        self.cost_tracker.reset()


class CostTracker:
    """Track usage costs and cache statistics."""
    
    def __init__(self):
        self.stats_file = Path.home() / ".cache" / "academic-research-mentor" / "guidelines_stats.json"
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self._load_stats()
    
    def _load_stats(self) -> None:
        """Load statistics from file."""
        try:
            if self.stats_file.exists():
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
            else:
                self.stats = self._get_default_stats()
        except Exception:
            self.stats = self._get_default_stats()
    
    def _get_default_stats(self) -> Dict[str, Any]:
        """Get default statistics structure."""
        return {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_writes": 0,
            "search_queries": 0,
            "total_cost_estimate": 0.0,
            "last_updated": datetime.now().isoformat()
        }
    
    def _save_stats(self) -> None:
        """Save statistics to file."""
        try:
            self.stats["last_updated"] = datetime.now().isoformat()
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception:
            pass
    
    def record_cache_hit(self) -> None:
        """Record a cache hit."""
        self.stats["cache_hits"] += 1
        self._save_stats()
    
    def record_cache_miss(self) -> None:
        """Record a cache miss."""
        self.stats["cache_misses"] += 1
        self._save_stats()
    
    def record_cache_write(self) -> None:
        """Record a cache write."""
        self.stats["cache_writes"] += 1
        self._save_stats()
    
    def record_search_query(self, cost_estimate: float = 0.01) -> None:
        """Record a search query with estimated cost."""
        self.stats["search_queries"] += 1
        self.stats["total_cost_estimate"] += cost_estimate
        self._save_stats()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics."""
        return self.stats.copy()
    
    def get_cache_hit_rate(self) -> float:
        """Calculate cache hit rate."""
        total_requests = self.stats["cache_hits"] + self.stats["cache_misses"]
        if total_requests == 0:
            return 0.0
        return self.stats["cache_hits"] / total_requests
    
    def reset(self) -> None:
        """Reset all statistics."""
        self.stats = self._get_default_stats()
        self._save_stats()