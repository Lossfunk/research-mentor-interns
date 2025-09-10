# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an Academic Research Mentor application that provides AI-powered assistance for academic research tasks. It's built with Python using LangChain for LLM integration and Rich for enhanced console formatting. The application supports multiple LLM providers (OpenRouter, OpenAI, Google, Anthropic, Mistral) with O3-powered literature review capabilities.

## Development Environment

### Package Management
- **Primary tool**: `uv` (preferred)
- **Installation**: `uv sync` or `pip install -e .`
- **Python version**: >=3.11

### Environment Configuration
The application automatically loads environment variables from `.env` files. Required configuration:
- **API Keys**: At least one of `OPENROUTER_API_KEY` (recommended), `OPENAI_API_KEY`, `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`
- **Agent Mode**: `LC_AGENT_MODE` (default: "react", options: "chat", "react", "router")
- **Prompt Variant**: `ARM_PROMPT` or `LC_PROMPT` (default: "mentor", options: "mentor", "system")

### Testing
```bash
# Run all tests
uv run pytest -q

# Run specific test file
uv run pytest tests/test_specific_file.py -q

# Run with verbose output
uv run pytest -v
```

### Running the Application
```bash
# Main CLI entrypoint
uv run academic-research-mentor

# Alternative via main.py shim
uv run python main.py

# Check environment configuration
uv run academic-research-mentor --check-env

# List available tools
uv run academic-research-mentor --list-tools
```

## Architecture

### Core Components

1. **CLI Entry Point**: `src/academic_research_mentor/cli.py:main`
   - Handles argument parsing, environment loading, and main REPL loop
   - Supports different agent modes (chat, react, router)
   - Integrates with tool registry and orchestrator

2. **Agent Runtime**: `src/academic_research_mentor/runtime.py`
   - Provides `_LangChainAgentWrapper` for consistent agent interface
   - Handles streaming responses and conversation history
   - Supports multiple LLM providers through LangChain

3. **Core Orchestrator**: `src/academic_research_mentor/core/orchestrator.py`
   - Coordinates tool selection and execution
   - Implements intelligent fallback policies
   - Provides task-based execution with circuit breakers

4. **Tool Registry**: `src/academic_research_mentor/tools/__init__.py`
   - Manages tool registration and discovery
   - Provides `BaseTool` interface for consistent tool implementation
   - Auto-discovers tools in subpackages

### Tool System

**Base Tool Interface**: `src/academic_research_mentor/tools/base_tool.py`
- Standard interface for all tools with lifecycle methods
- Required methods: `execute()`, `can_handle()`, `get_metadata()`
- Optional methods: `initialize()`, `cleanup()`

**Tool Structure**:
```
tools/
├── base_tool.py          # BaseTool interface
├── __init__.py          # Registry and auto-discovery
├── guidelines/          # Guidelines injection tools
├── legacy/              # Legacy tools (arXiv, etc.)
├── o3_search/           # O3 search implementation
├── searchthearxiv/      # arXiv search tools
└── utils/               # Shared utilities
```

### Agent Modes

1. **React Mode** (`LC_AGENT_MODE=react`):
   - Agent decides which tools to use automatically
   - Uses LangChain's agent framework
   - Supports tool calling and streaming

2. **Chat Mode** (`LC_AGENT_MODE=chat`):
   - Manual tool routing via `route_and_maybe_run_tool()`
   - Conversational approach with research context building
   - Fallback to simple responses when tools aren't needed

### Guidelines Engine

Located in `src/academic_research_mentor/guidelines_engine/`:
- Injects research guidelines into system prompts
- Supports dynamic and cached guideline modes
- Configurable through environment variables

### Transparency Layer

`src/academic_research_mentor/core/transparency.py`:
- In-memory event/run store
- Tracks tool execution and performance
- Provides debugging and monitoring capabilities

## Key Development Patterns

### Code Organization
- **File size limit**: Keep files under 200 lines of code
- **Single responsibility**: Each file has one clear purpose
- **Scaffolding approach**: Minimal implementations first, then incremental enhancement

### Tool Development
1. Create tool class inheriting from `BaseTool`
2. Implement required methods (`execute`, `can_handle`, `get_metadata`)
3. Place in appropriate subdirectory under `tools/`
4. Tool will be auto-discovered via registry

### Testing Patterns
- Tests located in `tests/` directory
- `conftest.py` ensures src/ is importable during testing
- Focus on scaffolding and core functionality tests
- Integration tests for tool registry and orchestrator

### Environment Handling
- Automatic `.env` file loading from current or parent directories
- Graceful fallback when environment variables are missing
- Debug mode via `ARM_DEBUG_ENV=1`

### Error Handling
- Graceful degradation when tools fail
- Circuit breaker patterns for unreliable services
- Comprehensive logging and transparency

## Common Commands

### Development Workflow
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest -q

# Run application
uv run academic-research-mentor

# Check environment
uv run academic-research-mentor --check-env

# List tools
uv run academic-research-mentor --list-tools

# Show tool candidates for a goal
uv run academic-research-mentor --show-candidates "find recent papers on LLMs"

# Get tool recommendation
uv run academic-research-mentor --recommend "search academic literature"
```

### Debugging
```bash
# Enable debug output for environment loading
ARM_DEBUG_ENV=1 uv run academic-research-mentor

# Show recent tool runs
uv run academic-research-mentor --show-runs

# Test specific tool registration
python -c "from src.academic_research_mentor.tools import auto_discover; auto_discover(); print(list_tools().keys())"
```

## Important Notes

- The project uses **uv** as the primary package management tool
- **OpenRouter API key** is strongly recommended for O3-powered literature review
- The tool registry system uses **auto-discovery** - tools are automatically registered when placed in the correct directory structure
- **Agent mode** significantly changes behavior - understand the differences between "chat" and "react" modes
- **Guidelines engine** is optional and will gracefully degrade if not configured
- All tools should implement the **BaseTool interface** for consistency