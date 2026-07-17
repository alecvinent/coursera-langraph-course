# AGENTS.md — AI Coding Guidelines

This file defines conventions for AI coding assistants (e.g., opencode) working on this repo.

## Project Context

- **Course**: [LangGraph Framework on Coursera](https://www.coursera.org/learn/langgraph-framework)
- **Tech stack**: Python, LangGraph, LangChain, LangSmith (observability)
- **Package manager**: [Poetry](https://python-poetry.org/)
- **Module 1 Foundations**: Implemented at `src/multiagent-governance_course/module_1_foundations/` (imported as `from module_1_foundations...`). Tests at `tests/multiagent-governance_course/test_module_1_foundations/`. Requires `sys.path` to include `src/multiagent-governance_course/` (for `module_1_foundations`) and `src/` (for `utils`, `langgraph_course`).

## Coding Conventions

- **Python**: Use Python 3.10+ type hints. Prefer `pydantic` models over dicts for structured state.
- **Imports**: Group by stdlib → third-party → local; alphabetize within each group.
- **Style**: Follow PEP 8. Use `ruff` for linting.
- **LangGraph patterns**: Use `StateGraph`, `MessageGraph`, `Node`, `Edge`, `ConditionalEdge`. Prefer `TypedDict` or `BaseModel` for state schemas. Use `Annotated[list, add_messages]` reducer for message fields.
- **Formatting**: Black-compatible (88 char lines).
- **No hardcoded values**: Never hardcode API keys, model names, URLs, or environment-specific config. Use `config.py`'s `Settings` class (powered by `pydantic-settings`) and `.env` for all configurable values.
- **Logging**: Use `loguru` (`from loguru import logger`). Configured once in `src/langgraph_course/log.py` (imported automatically at package init via `__init__.py`). Use `logger.info()`, `logger.warning()`, etc.
- **LLM Factory**: Use `LLMFactory` in `utils/llm.py` to create LLM instances. Supports provider registry pattern — new providers are added via `@register_provider` decorator in `utils/providers/`. Provider selection driven by `settings.llm_provider` (default: `"auto"`) or explicit `LLMFactory.create(provider="...")`.
- **Telemetry**: Use the shared `timed_node` decorator from `utils/decorators.py` to automatically record per-node latencies and execution paths. Apply it as `@timed_node('node_name')` on each node function. **Note**: The decorator assumes classmethod signature (`args[1]` is state). Use manual `time.monotonic()` latency tracking for plain functions.
- **Error handling**: Structure error logs as `list[ErrorRecord]` TypedDict with step, error_type, message, and timestamp. Use exponential backoff retry for transient API failures and tag degraded outputs with `processing_outcome="partial"`. Human escalation is triggered only after retry exhaustion or unrecoverable content.

## Testing

- Tests live in `tests/` mirroring the source structure.
- Use `unittest` (stdlib). Each test file contains `unittest.TestCase` subclasses.
- Shared test helpers and fixtures live in `tests/base.py`.
- Test files: `test_*.py`.
- Run: `poetry run python -m unittest discover -v`.

## Agent Behavior

- Read existing files before editing to understand conventions.
- Do not introduce dependencies beyond the LangChain/LangGraph ecosystem unless necessary.
- Prefer editing existing files over creating new ones unless the task explicitly requires a new file.
- Never commit changes unless explicitly asked.
- Always keep `README.md` in sync with the current state of the project. When adding, renaming, or removing files or features, update the relevant sections (project structure, setup, usage, etc.).
