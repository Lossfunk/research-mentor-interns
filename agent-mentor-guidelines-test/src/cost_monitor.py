import json
import os
from datetime import datetime
from typing import Dict, Any
from .config import Config

class CostMonitor:
    """Track API usage and costs"""
    
    def __init__(self, config: Config):
        self.config = config
        self.usage_file = "data/usage_log.json"
        self.usage_data = self._load_usage_data()
        
        # GPT-5-nano pricing (approximate)
        self.input_cost_per_1k = 0.00015  # $0.15 per 1M tokens
        self.output_cost_per_1k = 0.0006   # $0.60 per 1M tokens
        
    def _load_usage_data(self) -> dict:
        """Load usage data from file"""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                return {'total_cost': 0.0, 'sessions': []}
        return {'total_cost': 0.0, 'sessions': []}
    
    def _save_usage_data(self):
        """Save usage data to file"""
        os.makedirs(os.path.dirname(self.usage_file), exist_ok=True)
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def log_request(self, input_tokens: int, output_tokens: int, query: str = ""):
        """Log a request and calculate cost"""
        if not self.config.ENABLE_COST_MONITORING:
            return
            
        input_cost = (input_tokens / 1000) * self.input_cost_per_1k
        output_cost = (output_tokens / 1000) * self.output_cost_per_1k
        total_cost = input_cost + output_cost
        
        session = {
            'timestamp': datetime.now().isoformat(),
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'query': query[:100]  # Truncate long queries
        }
        
        self.usage_data['sessions'].append(session)
        self.usage_data['total_cost'] += total_cost
        self._save_usage_data()
        
        return total_cost
    
    def get_cost_summary(self) -> dict:
        """Get cost summary"""
        sessions = self.usage_data['sessions']
        if not sessions:
            return {'total_cost': 0.0, 'session_count': 0, 'avg_cost_per_session': 0.0}
        
        total_cost = self.usage_data['total_cost']
        session_count = len(sessions)
        avg_cost = total_cost / session_count
        
        return {
            'total_cost': round(total_cost, 4),
            'session_count': session_count,
            'avg_cost_per_session': round(avg_cost, 4),
            'estimated_monthly_cost': round(total_cost * 30, 2)  # Rough estimate
        }
    
    def get_daily_usage(self, days: int = 7) -> list:
        """Get usage for the last N days"""
        sessions = self.usage_data['sessions']
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        
        recent_sessions = [
            s for s in sessions 
            if datetime.fromisoformat(s['timestamp']).timestamp() > cutoff_date
        ]
        
        return recent_sessions
