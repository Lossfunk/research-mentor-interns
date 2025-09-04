from __future__ import annotations

"""
Fallback policy for tool execution (WS3 extension).

Provides sophisticated retry, circuit breaker, and degraded mode logic
for robust tool execution when primary tools fail.
"""

from typing import Dict, Any, List, Tuple, Optional
import time
import random
from dataclasses import dataclass, field
from enum import Enum


class ToolState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CIRCUIT_OPEN = "circuit_open"


@dataclass
class ToolHealth:
    """Track health metrics for circuit breaker logic."""
    name: str
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    state: ToolState = ToolState.HEALTHY
    consecutive_failures: int = 0
    circuit_open_until: Optional[float] = None


@dataclass
class FallbackPolicy:
    """Configuration for fallback behavior."""
    max_retries: int = 2
    base_backoff_ms: int = 1000
    max_backoff_ms: int = 10000
    circuit_failure_threshold: int = 3
    circuit_recovery_time_s: int = 60
    jitter_factor: float = 0.1
    health_tracking: Dict[str, ToolHealth] = field(default_factory=dict)


class FallbackExecutor:
    """Sophisticated fallback execution with circuit breaker and retry logic."""
    
    def __init__(self, policy: Optional[FallbackPolicy] = None):
        self.policy = policy or FallbackPolicy()
    
    def execute_with_fallback(
        self, 
        candidates: List[Tuple[str, float]], 
        tools: Dict[str, Any],
        inputs: Dict[str, Any], 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute task with sophisticated fallback logic."""
        if not candidates:
            return self._no_tools_result()
        
        execution_log = []
        
        for i, (tool_name, score) in enumerate(candidates):
            # Check circuit breaker
            if self._is_circuit_open(tool_name):
                execution_log.append({
                    "tool": tool_name,
                    "skipped": True,
                    "reason": "circuit_breaker_open",
                    "score": score
                })
                continue
            
            # Try execution with retries
            result = self._execute_with_retries(
                tool_name, score, tools, inputs, context, execution_log
            )
            
            if result["success"]:
                self._record_success(tool_name)
                return {
                    "execution": {
                        "executed": True,
                        "tool_used": tool_name,
                        "tool_score": score,
                        "success": True,
                        "attempt_number": i + 1,
                        "execution_log": execution_log
                    },
                    "results": result["data"],
                    "note": f"Task executed successfully with {tool_name}"
                }
            else:
                self._record_failure(tool_name)
        
        # All tools failed - return degraded result
        return self._all_tools_failed_result(execution_log)
    
    def _execute_with_retries(
        self, 
        tool_name: str, 
        score: float,
        tools: Dict[str, Any],
        inputs: Dict[str, Any], 
        context: Optional[Dict[str, Any]],
        execution_log: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute a single tool with retry logic."""
        tool = tools.get(tool_name)
        
        if not tool or not hasattr(tool, "execute"):
            execution_log.append({
                "tool": tool_name,
                "success": False,
                "reason": "tool_not_executable",
                "score": score
            })
            return {"success": False, "error": "Tool not executable"}
        
        for retry in range(self.policy.max_retries + 1):
            try:
                if retry > 0:
                    # Apply backoff with jitter
                    backoff_ms = min(
                        self.policy.base_backoff_ms * (2 ** (retry - 1)),
                        self.policy.max_backoff_ms
                    )
                    jitter = random.uniform(-self.policy.jitter_factor, self.policy.jitter_factor)
                    actual_backoff = backoff_ms * (1 + jitter)
                    time.sleep(actual_backoff / 1000)
                    
                    print(f"🔄 Retrying {tool_name} (attempt {retry + 1}/{self.policy.max_retries + 1})")
                
                execution_result = tool.execute(inputs, context)
                
                execution_log.append({
                    "tool": tool_name,
                    "success": True,
                    "retry_attempt": retry,
                    "score": score
                })
                
                return {"success": True, "data": execution_result}
                
            except Exception as e:
                execution_log.append({
                    "tool": tool_name,
                    "success": False,
                    "retry_attempt": retry,
                    "error": str(e),
                    "score": score
                })
                
                if retry == self.policy.max_retries:
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    def _is_circuit_open(self, tool_name: str) -> bool:
        """Check if circuit breaker is open for this tool."""
        health = self.policy.health_tracking.get(tool_name)
        if not health:
            return False
        
        if health.state != ToolState.CIRCUIT_OPEN:
            return False
        
        # Check if recovery time has passed
        if health.circuit_open_until and time.time() > health.circuit_open_until:
            health.state = ToolState.DEGRADED
            health.circuit_open_until = None
            print(f"🔧 Circuit breaker for {tool_name} entering recovery mode")
            return False
        
        return True
    
    def _record_success(self, tool_name: str) -> None:
        """Record successful tool execution."""
        health = self.policy.health_tracking.setdefault(tool_name, ToolHealth(tool_name))
        health.success_count += 1
        health.consecutive_failures = 0
        health.last_success_time = time.time()
        
        # Recovery from degraded state
        if health.state == ToolState.DEGRADED and health.success_count % 3 == 0:
            health.state = ToolState.HEALTHY
            print(f"✅ Tool {tool_name} restored to healthy state")
    
    def _record_failure(self, tool_name: str) -> None:
        """Record failed tool execution and update circuit breaker state."""
        health = self.policy.health_tracking.setdefault(tool_name, ToolHealth(tool_name))
        health.failure_count += 1
        health.consecutive_failures += 1
        health.last_failure_time = time.time()
        
        # Open circuit breaker if threshold exceeded
        if health.consecutive_failures >= self.policy.circuit_failure_threshold:
            health.state = ToolState.CIRCUIT_OPEN
            health.circuit_open_until = time.time() + self.policy.circuit_recovery_time_s
            print(f"⚠️  Circuit breaker opened for {tool_name} (too many failures)")
    
    def _no_tools_result(self) -> Dict[str, Any]:
        """Return result when no tools are available."""
        return {
            "execution": {"executed": False, "reason": "No suitable tools found"},
            "results": None,
            "note": "No tools available for execution"
        }
    
    def _all_tools_failed_result(self, execution_log: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Return result when all tools have failed."""
        failed_tools = [entry["tool"] for entry in execution_log if not entry.get("skipped")]
        skipped_tools = [entry["tool"] for entry in execution_log if entry.get("skipped")]
        
        return {
            "execution": {
                "executed": False,
                "reason": "All available tools failed or were skipped",
                "failed_tools": failed_tools,
                "skipped_tools": skipped_tools,
                "execution_log": execution_log
            },
            "results": None,
            "note": "All tools failed - consider degraded mode or manual intervention"
        }
    
    def get_tool_health_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all tool health states."""
        return {
            name: {
                "state": health.state.value,
                "success_rate": health.success_count / max(health.success_count + health.failure_count, 1),
                "consecutive_failures": health.consecutive_failures,
                "last_failure": health.last_failure_time,
                "last_success": health.last_success_time
            }
            for name, health in self.policy.health_tracking.items()
        }