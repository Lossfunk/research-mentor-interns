from __future__ import annotations

"""
Tool execution engine with retry logic (WS3 extension).

Handles the actual tool execution with retries, keeping orchestrator.py under 200 LOC.
"""

from typing import Dict, Any, Optional
import time


def execute_with_policy(selection_result: Dict[str, Any], strategy: Dict[str, Any], 
                       inputs: Dict[str, Any], context: Optional[Dict[str, Any]], 
                       policy, list_tools_func) -> Dict[str, Any]:
    """Execute tools using fallback policy."""
    if list_tools_func is None:
        return {
            **selection_result,
            "execution": {"executed": False, "reason": "No tools available"},
            "results": None
        }
    
    tools = list_tools_func()
    primary_name, primary_score = strategy["primary"]
    
    # Try primary tool with retries
    execution_result = try_tool_with_retries(
        tools, primary_name, primary_score, inputs, context, policy
    )
    
    if execution_result["success"]:
        return {
            **selection_result,
            **execution_result,
            "fallback_strategy": strategy
        }
    
    # Primary failed, try fallback if available
    fallback_info = strategy.get("fallback")
    if fallback_info:
        fallback_name, fallback_score = fallback_info
        print(f"⚠️  {primary_name} failed, trying fallback {fallback_name}")
        
        fallback_result = try_tool_with_retries(
            tools, fallback_name, fallback_score, inputs, context, policy
        )
        
        if fallback_result["success"]:
            fallback_result["execution"]["primary_failed"] = primary_name
            fallback_result["execution"]["fallback_used"] = True
            return {
                **selection_result,
                **fallback_result,
                "fallback_strategy": strategy
            }
    
    # All tools failed
    policy.record_failure(primary_name, execution_result["execution"]["reason"])
    return {
        **selection_result,
        "execution": {
            "executed": False,
            "reason": f"All available tools failed. Primary: {execution_result['execution']['reason']}",
            "strategy_used": strategy["strategy"]
        },
        "results": None,
        "fallback_strategy": strategy
    }


def try_tool_with_retries(tools: Dict[str, Any], tool_name: str, score: float,
                         inputs: Dict[str, Any], context: Optional[Dict[str, Any]], policy) -> Dict[str, Any]:
    """Try executing a tool with retry logic."""
    tool = tools.get(tool_name)
    if not tool or not hasattr(tool, "execute"):
        return {
            "success": False,
            "execution": {"executed": False, "reason": f"Tool {tool_name} not executable"}
        }
    
    attempt = 0
    last_error = ""
    
    while attempt < 3:  # Max 3 attempts total
        try:
            if attempt == 0:
                print(f"🔧 Executing with {tool_name} (score: {score:.1f})")
            else:
                print(f"🔄 Retry {attempt} for {tool_name}")
            
            execution_result = tool.execute(inputs, context)
            
            # Success!
            policy.record_success(tool_name)
            return {
                "success": True,
                "execution": {
                    "executed": True,
                    "tool_used": tool_name,
                    "tool_score": score,
                    "success": True,
                    "attempts": attempt + 1
                },
                "results": execution_result,
                "note": f"Task executed with {tool_name}" + (f" (attempt {attempt + 1})" if attempt > 0 else "")
            }
            
        except Exception as e:
            last_error = str(e)
            attempt += 1
            
            # Check if we should retry
            should_retry, delay = policy.should_retry(tool_name, attempt, last_error)
            if should_retry and attempt < 3:
                print(f"🕐 Retrying {tool_name} in {delay:.1f}s...")
                time.sleep(delay)
                continue
            else:
                break
    
    # All retries failed
    policy.record_failure(tool_name, last_error)
    return {
        "success": False,
        "execution": {
            "executed": False,
            "reason": f"{tool_name} failed after {attempt} attempts: {last_error}",
            "attempts": attempt
        }
    }