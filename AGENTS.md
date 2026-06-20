# AGENTS.md — AI Coding Guidelines

This file defines conventions for AI coding assistants (e.g., opencode) working on this repo.

## Project Context

- **Course**: [LangGraph Framework on Coursera](https://www.coursera.org/learn/langgraph-framework)
- **Tech stack**: Python, LangGraph, LangChain, LangSmith (observability)
- **Package manager**: [Poetry](https://python-poetry.org/)

## Coding Conventions

- **Python**: Use Python 3.10+ type hints. Prefer `pydantic` models over dicts for structured state.
- **Imports**: Group by stdlib → third-party → local; alphabetize within each group.
- **Style**: Follow PEP 8. Use `ruff` for linting.
- **LangGraph patterns**: Use `StateGraph`, `MessageGraph`, `Node`, `Edge`, `ConditionalEdge`. Prefer `TypedDict` or `BaseModel` for state schemas.
- **Formatting**: Black-compatible (88 char lines).

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
