from __future__ import annotations

from academic_research_mentor.core import Orchestrator, TransparencyStore


def test_orchestrator_scaffold_runs_noop() -> None:
    orch = Orchestrator()
    out = orch.run_task("noop", context={"a": 1})
    assert out.get("ok") is True
    assert out.get("task") == "noop"
    assert out.get("context_keys") == ["a"]


def test_transparency_store_in_memory() -> None:
    store = TransparencyStore()
    run = store.start_run("demo", run_id="r1", metadata={"k": "v"})
    assert run.tool_name == "demo"
    store.append_event("r1", "started", {"n": 1})
    store.end_run("r1", success=True, extra_metadata={"done": True})
    got = store.get_run("r1")
    assert got is not None and got.status == "success"
    assert any(evt.event_type == "started" for evt in got.events)
