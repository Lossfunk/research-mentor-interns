import json
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Any
from .config import Config

class ResponseCache:
    """Simple file-based cache for API responses to reduce costs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.cache_dir = "data/response_cache"
        self.cache_file = os.path.join(self.cache_dir, "responses.json")
        self._ensure_cache_dir()
        self.cache_data = self._load_cache()
    
    def _ensure_cache_dir(self):
        """Create cache directory if it doesn't exist"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _load_cache(self) -> dict:
        """Load cache from file"""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {}
        return {}
    
    def _save_cache(self):
        """Save cache to file"""
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache_data, f, indent=2)
    
    def _get_cache_key(self, query: str) -> str:
        """Generate cache key from query"""
        return hashlib.md5(query.lower().strip().encode()).hexdigest()
    
    def get(self, query: str) -> Optional[dict]:
        """Get cached response if available and not expired"""
        if not self.config.ENABLE_CACHING:
            return None
            
        cache_key = self._get_cache_key(query)
        if cache_key in self.cache_data:
            cached_item = self.cache_data[cache_key]
            cached_time = datetime.fromisoformat(cached_item['timestamp'])
            
            # Check if cache is still valid
            if datetime.now() - cached_time < timedelta(hours=self.config.CACHE_TTL_HOURS):
                return cached_item['response']
            else:
                # Remove expired cache entry
                del self.cache_data[cache_key]
                self._save_cache()
        
        return None
    
    def set(self, query: str, response: dict):
        """Cache a response"""
        if not self.config.ENABLE_CACHING:
            return
            
        cache_key = self._get_cache_key(query)
        self.cache_data[cache_key] = {
            'response': response,
            'timestamp': datetime.now().isoformat(),
            'query': query
        }
        self._save_cache()
    
    def clear_expired(self):
        """Remove all expired cache entries"""
        now = datetime.now()
        expired_keys = []
        
        for key, item in self.cache_data.items():
            cached_time = datetime.fromisoformat(item['timestamp'])
            if now - cached_time >= timedelta(hours=self.config.CACHE_TTL_HOURS):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.cache_data[key]
        
        if expired_keys:
            self._save_cache()
    
    def get_stats(self) -> dict:
        """Get cache statistics"""
        total_entries = len(self.cache_data)
        now = datetime.now()
        valid_entries = 0
        
        for item in self.cache_data.values():
            cached_time = datetime.fromisoformat(item['timestamp'])
            if now - cached_time < timedelta(hours=self.config.CACHE_TTL_HOURS):
                valid_entries += 1
        
        return {
            'total_entries': total_entries,
            'valid_entries': valid_entries,
            'expired_entries': total_entries - valid_entries,
            'cache_hit_rate': f"{(valid_entries / max(total_entries, 1)) * 100:.1f}%"
        }
