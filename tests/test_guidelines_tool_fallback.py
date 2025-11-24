from __future__ import annotations


def test_guidelines_tool_fn_uses_offline_fallback(monkeypatch):
    """When orchestrator can't run, guidelines tool should still return cached guidance."""
    from academic_research_mentor.runtime import tool_impls
    from academic_research_mentor.core import orchestrator as orch_mod
    from academic_research_mentor import tools as tools_mod

    class DummyOrchestrator:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def execute_task(self, *args, **kwargs):
            return {"execution": {"executed": False, "reason": "blocked"}, "results": None}

    monkeypatch.setattr(orch_mod, "Orchestrator", DummyOrchestrator)
    monkeypatch.setattr(tools_mod, "auto_discover", lambda: None)

    output = tool_impls.guidelines_tool_fn("research taste")

    assert "Guidelines fallback" in output
    assert "research" in output.lower()
