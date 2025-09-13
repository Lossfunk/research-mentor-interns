I scanned the codebase to identify oversized Python files and hotspots. I’ll propose a concise, phased refactor plan to cap files at ≤200 lines, keep APIs stable, and avoid regressions.

### Goals and constraints
- Cap each non-test Python file at ≤200 LOC.
- No functional changes in Phase 1; behavior and public imports remain stable.
- Keep entrypoint `academic_research_mentor.cli:main` working.
- Use ast-grep for syntax-aware identification and rewrite of imports and targets.

### Oversized files to prioritize (src only)
- runtime/runtime.py (≈747)
- mentor_tools.py (≈641)
- cli.py (≈550)
- literature_review/context_builder.py (≈529)
- tools/guidelines/tool.py (≈336)
- rich_formatter.py (≈256)
- router.py (≈241)
- literature_review/intent_extractor.py (≈239)
- literature_review/synthesis.py (≈234)
- core/execution_engine.py (≈223)
- guidelines_engine/formatter.py (≈212)
- core/transparency.py (≈202)
- guidelines_engine/injector.py (≈201)

### Target high-level structure (post-split)
- academic_research_mentor/
  - cli/
    - main.py (entry wrapper)
    - args.py
    - commands.py
    - repl.py
    - session.py (logging/cleanup)
  - runtime/
    - builder.py (public `build_agent`)
    - models.py (resolve/import chat models)
    - agents/
      - base_chat.py
      - react_agent.py
      - router_agent.py
    - tools_wrappers.py (LangChain Tool wrappers)
  - router/ (if kept)
    - manual_routing.py (or merge with runtime/router_agent triggers)
  - rich_ui/
    - formatter.py (RichFormatter)
    - io_helpers.py (print_* globals)
  - literature_review/
    - build_context.py (public `build_research_context`)
    - search.py (perform searches/orchestrator bridge)
    - fallback.py (llm-only path)
    - context_format.py (agent context assembly)
    - debug.py (debug logging)
  - tools/
    - guidelines/
      - tool.py (just the Tool class glue)
      - search.py (query generation, domain identification)
      - format.py (RAG formatting)
      - adapters.py (DDG adapter)
      - cache.py
      - config.py
    - legacy/
      - arxiv/
        - client.py (HTTP + parse)
        - query.py (tokenize/build query)
        - tool_compat.py (re-export if needed)
  - core/
    - orchestrator.py
    - execution/
      - engine.py
      - policies.py (backoff/circuit)
    - transparency/
      - events.py
      - store.py
  - guidelines_engine/
    - loader.py
    - injector/
      - injector.py
      - render.py
    - formatter.py (or merged into render.py)

### File-by-file split strategy
- runtime.py → runtime/
  - builder.py: `build_agent` (public surface)
  - models.py: `_import_langchain_models`, `_resolve_model`
  - agents/base_chat.py: `_LangChainAgentWrapper`
  - agents/react_agent.py: `_LangChainReActAgentWrapper`
  - agents/router_agent.py: `_LangChainSpecialistRouterWrapper`
  - tools_wrappers.py: `get_langchain_tools` and helper wrappers
  - Keep `runtime/__init__.py` re-exporting `build_agent` (compatibility)

- cli.py → cli/
  - main.py: parse args + dispatch
  - args.py: argparse setup
  - commands.py: `--check-env`, `--env-help`, `--list-tools`, `--show-candidates`, `--recommend`, `--show-runs`
  - repl.py: REPL loop
  - session.py: signal handling + ChatLogger save
  - Keep thin `cli.py` shim that calls `cli.main:main` (retain entrypoint)

- literature_review/context_builder.py → literature_review/
  - build_context.py: orchestrates steps (≤200 LOC)
  - search.py: `_perform_literature_searches`
  - fallback.py: `_llm_only_overview`
  - context_format.py: `_build_agent_context`, `_minimal_research_context`
  - debug.py: `_should_debug_log`, `_init_debug_logging`, `_save_debug_log`

- mentor_tools.py (legacy overlap with tools system)
  - Move HTTP and query utils under `tools/legacy/arxiv/{client.py,query.py}`
  - Re-home `math_ground`, `methodology_validate` under `tools/utils/{math.py,methodology.py}`
  - Keep `mentor_tools.py` as a ≤100 LOC compatibility wrapper re-exporting functions from new modules, then deprecate

- tools/guidelines/tool.py
  - Keep only the Tool class and thin glue; move search/format helpers to `search.py`, `format.py`, `adapters.py`

- rich_formatter.py
  - rich_ui/formatter.py: the class
  - rich_ui/io_helpers.py: globals `print_*`, singleton management

- router.py
  - If needed, split into `router/manual_routing.py` and keep ≤200 LOC. Consider consolidating routing logic into runtime.router_agent if possible.

- core/execution_engine.py and core/transparency.py
  - Split into `core/execution/*` and `core/transparency/*` as outlined above

- guidelines_engine/injector.py and formatter.py
  - Slight trims or split into `injector/injector.py` + `injector/render.py` if still >200 LOC after small extractions

### Refactor safety and migration
- Re-export to preserve imports:
  - `runtime.py` keeps `from .runtime.builder import build_agent` etc.
  - `cli.py` just imports and calls `cli.main:main`
  - `mentor_tools.py` re-exports split functions
- Update internal imports with ast-grep structural rewrites.
- Tests unchanged; any path break is caught by CI. If any test imports old modules, re-exports handle it.

### Enforcement and CI
- Add a lightweight line-count check for `src/**.py` (exclude `tests/**`, `__init__.py` okay if small) in pre-commit and CI.
- Add complexity budget via radon or pylint thresholds for follow-up (optional).

### ast-grep usage (default for structural work)
- Find long functions to extract:
```bash
ast-grep --lang python -p "def $FN($$ARGS):\n    $$BODY"
```
- Rewrite imports after moves:
```bash
ast-grep --lang python -p "from academic_research_mentor.runtime import build_agent" \
  -r "from academic_research_mentor.runtime.builder import build_agent"
```
- Identify class definitions for moving:
```bash
ast-grep --lang python -p "class $C($$BASES):\n    $$BODY"
```

### Phased execution plan
- Phase 0: Repo hygiene
  - Remove `agent-mentor-guidelines-test/` (no references; safe to delete).
  - Add pre-commit hook for line-count guard (src only).
- Phase 1: Non-functional splits with re-exports
  - runtime/ split; keep `build_agent` import path stable.
  - cli/ split; keep entrypoint and `cli.py` shim.
- Phase 2: literature_review splits
  - Move context builder helpers into modules; keep `build_research_context` stable.
- Phase 3: mentor_tools deprecation path
  - Move functions to tools/*; keep wrapper in place; adjust runtime wrappers to prefer registry tools where possible.
- Phase 4: tools/guidelines and rich_ui reductions
  - Extract helpers; keep external tool name and behavior the same.
- Phase 5: core/* and guidelines_engine minor splits
  - Extract execution/transparency submodules; minor injector split if needed.
- Phase 6: Cleanups
  - Update docs (`README.md`, `CLAUDE.md` architecture), run tests, fix any straggler imports with ast-grep.

### Open questions
- Exclude tests from the ≤200 LOC rule? I propose yes (keep tests intact).
- Any external users importing internals beyond documented surfaces? If so, we’ll keep additional re-exports.

If this plan looks good, I’ll start with Phase 0/1 (split `runtime/` and `cli/`), using ast-grep to rewrite imports and keep the code behavior identical.
