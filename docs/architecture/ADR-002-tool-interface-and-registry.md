# ADR-002: Tool Interface and Registry (Scaffold)

## Status
Accepted (Scaffold for WS1/WS2)

## Context
We are moving from ad-hoc tool functions to a standardized tool system with a common interface and a registry to enable discovery, selection, and orchestration. WS1 introduces minimal scaffolding only, without behavior changes.

## Decision
- Provide a minimal `BaseTool` interface with `execute(inputs, context)`.
- Create a simple in-memory registry with `register_tool`, `get_tool`, and `list_tools`.
- Keep discovery/manual registration out of scope for WS1; will add metadata and auto-discovery in WS2.

## Consequences
- Developers can begin migrating tools incrementally into `src/academic_research_mentor/tools/`.
- The orchestrator can later depend on the registry without touching legacy code.
- No runtime behavior changes yet; CLI and current flows continue to work.

## Next Steps (WS2/WS3)
- Extend interface with lifecycle: `initialize`, `can_handle`, `cleanup`.
- Define metadata schema (capabilities, costs, latency, input/output schemas).
- Implement auto-discovery and validation in `tools/__init__.py`.
- Integrate with `core/orchestrator.py` and future agent selection.
