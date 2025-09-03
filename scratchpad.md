# Scratchpad

Purpose: Track decisions and context while executing WS1 and WS2.

Context:
- Current package layout uses `src/academic_research_mentor` with CLI entrypoint via `pyproject.toml` (script: `academic-research-mentor`).
- We'll avoid breaking the existing CLI (`uv run academic-research-mentor`).
- We will introduce `core/` and `tools/` under the package namespace `src/academic_research_mentor/` instead of top-level modules to preserve imports.
- Keep files concise (<200 LOC each).

WS1 Decisions & Actions (completed):
- Created `src/academic_research_mentor/core/` with `orchestrator.py`, `transparency.py`, `agent.py`, and `__init__.py` exports.
- Created `src/academic_research_mentor/tools/` with `base_tool.py`, `__init__.py` (registry), and `utils/`.
- Added root-level `main.py` shim and updated `pyproject.toml` script to `academic_research_mentor.cli:main`.
- Wrote ADR-001/002/003 and tools migration checklist; updated README with new layout.
- Kept runtime behavior unchanged; CLI sanity checks pass.

WS2 Decisions & Actions (in progress):
- Extended `BaseTool` with lifecycle (`initialize`, `cleanup`), `can_handle`, and `get_metadata`.
- Implemented registry `auto_discover()` with validation; added tests.
- Added `tools/o3_search/tool.py` with metadata and `can_handle`.
- Added `tools/legacy/arxiv/tool.py` wrapper for legacy arXiv search (auto-discovered as fallback).
- Added `core/bootstrap.py`; wired CLI to bootstrap registry behind `FF_REGISTRY_ENABLED`.
- Added CLI flags:
  - `--list-tools`: force discovery and list tools.
  - `--show-candidates "<goal>"`: run orchestrator selection-only and print candidates.
- Orchestrator now returns candidates, prioritizing `o3_search` (score 10) and treating `legacy_*` as fallback (score 0.5); reduces O3 score if client unavailable.
- Test suite expanded (5 tests), all passing under uv/conda.

Upcoming WS3 (not started):
- Add recommendation scoring beyond static weights; introduce feature flag `FF_AGENT_RECOMMENDATION`.
- Add fallback policy and begin integrating selection into runtime flow behind a flag.
