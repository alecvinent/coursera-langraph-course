<!--
  Sync Impact Report
  ===================
  Version change: 1.0.0 → 1.1.0
  Modified principles: N/A
  Added sections: Core Principles (VI. Dependency Discipline)
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md → ✅ no changes needed
    - .specify/templates/spec-template.md → ✅ no changes needed
    - .specify/templates/tasks-template.md → ✅ no changes needed
  Follow-up TODOs: None
-->

# langgraph-course Constitution

## Core Principles

### I. LangGraph Architecture Patterns

All graph workflows MUST use LangGraph primitives as the sole orchestration layer:
`StateGraph` or `MessageGraph` for graph definitions, typed state schemas
(defined via `pydantic.BaseModel` or `TypedDict`), and `Node`/`Edge`/
`ConditionalEdge` for topology. Message-carrying state fields MUST use
`Annotated[list, add_messages]` reducer. Conditional edges MUST be
preferred over hard-coded branching within nodes.

**Rationale**: LangGraph is the framework's core contract. Adhering to its
primitives keeps workflows inspectable, serializable, and compatible with
LangSmith tracing and checkpointing.

### II. Configuration-Driven Design

Every configurable value (API keys, model names, URLs, environment-specific
switches) MUST be externalized. Use the `Settings` class in `src/.../config.py`
(powered by `pydantic-settings`) and a `.env` file. Never hardcode secrets,
model identifiers, or environment-dependent constants in source code.

**Rationale**: Hardcoded values create production incidents, block testing
across environments, and violate the principle of separating code from
configuration.

### III. Observability By Default

All runtime behavior MUST be observable without code changes. Every node
function MUST use the `@timed_node('node_name')` decorator to record per-node
latency. All logging MUST go through `loguru` (`from loguru import logger`).
Error conditions MUST be captured as `list[ErrorRecord]` TypedDict entries
with step, error_type, message, and timestamp. Transient API failures MUST
use exponential backoff retry; degraded outputs MUST be tagged with
`processing_outcome="partial"`.

**Rationale**: Non-observable systems cannot be debugged in production.
The `@timed_node` decorator and structured error records provide a uniform
telemetry surface without per-developer ceremony.

### IV. LLM Abstraction Layer

All Large Language Model interactions MUST go through `LLMFactory`
(in `utils/llm.py`). Direct instantiation of model classes (e.g., `ChatOpenAI`,
`ChatAnthropic`) in business logic is forbidden. New providers MUST be added
via the `@register_provider` decorator in `utils/providers/`. Provider
selection is driven by `settings.llm_provider` (default: `"auto"`) or
explicit `LLMFactory.create(provider="...")`.

**Rationale**: Direct LLM coupling makes provider swaps, cost tracking, and
fallback logic impossible to implement without touching every call site.
The factory pattern enables centralized configuration, retry, and
observability injection.

### V. Test Discipline

Tests MUST use the `unittest` framework from the standard library. Test files
live in `tests/`, mirroring the source structure. Every module under `src/`
MUST have a corresponding test file prefixed `test_`. Each `TestCase` subclass
tests exactly one class or function — do not combine multiple subjects in a
single test class. Shared fixtures and test helpers go in `tests/base.py`.
Integration tests MUST cover inter-agent communication and shared schema
contracts.

**Rationale**: Standard-library testing guarantees zero extra dependencies.
Mirrored structure makes it trivial to find tests for any source file.
Independent test cases prevent cascading failures and keep the test suite
diagnostic.

### VI. Dependency Discipline

New external dependencies MUST NOT be added without justification. Before
adding any new package, evaluate whether an existing dependency can fulfill
the requirement. If a new dependency is necessary, document the justification
in the implementation plan's Technical Context section referencing which
existing packages were evaluated and why they were insufficient.

Approved existing dependency stack (prefer these first):
- `pymupdf` — PDF reading and creation (use for PDF generation via
  `page.insert_htmlbox()`)
- `grandalf` — graph layout algorithms
- `langchain`, `langchain-community`, `langchain-openai` — LLM orchestration
- `fastapi` — web API endpoints
- `streamlit` — interactive web UI (dev dependency)

**Rationale**: Each dependency adds maintenance burden, security surface area,
and lockfile churn. The existing stack already covers most needs for this
project (PDF via pymupdf, LLM via langchain, UI via streamlit, API via
fastapi). Constraining additions prevents bloat and keeps the project
lightweight.

## Development Workflow

- **Feature lifecycle**: Specify (`/speckit.specify`) → Plan (`/speckit.plan`)
  → Tasks (`/speckit.tasks`) → Implement → Test → Polish.
- **AI assistant onboarding**: AI agents (opencode) MUST read `AGENTS.md`
  and this constitution before editing any file.
- **Dependency hygiene**: Follow Principle VI (Dependency Discipline). New
  external dependencies require documented justification in the plan's
  Technical Context section referencing evaluated existing alternatives.
- **File modification**: Prefer editing existing files over creating new ones
  unless the task explicitly requires a new file. Never commit changes unless
  explicitly asked.
- **Documentation**: `README.md` MUST be kept in sync with the current
  project structure. When adding, renaming, or removing files or features,
  update the relevant sections.

## Code Quality & Review

- **Linting**: All code MUST pass `ruff` linting before merge. Run
  `poetry run ruff check .` as a quality gate.
- **Formatting**: Code MUST conform to Black-compatible formatting with
  88-character line width. No trailing whitespace.
- **Type hints**: All public functions and methods MUST have Python 3.10+
  type hints. Use `from __future__ import annotations` where needed.
- **Import ordering**: Group imports by stdlib → third-party → local;
  alphabetize within each group.
- **Review gates**: Every PR or change set must verify:
  - Constitution compliance (no violated MUST rules)
  - Test coverage for new/modified logic
  - No hardcoded configuration values
  - No unjustified new dependencies (Principle VI)
  - Proof of `ruff` compliance

## Governance

This constitution supersedes all other practice documents (including
`AGENTS.md`) in case of conflict. Amendments to this document require:

1. A proposed diff (explicit changes to this file).
2. Approval from the project maintainer.
3. A version bump following semver:
   - MAJOR: Backward-incompatible principle removal or redefinition.
   - MINOR: New principle or materially expanded guidance.
   - PATCH: Clarifications, wording fixes, non-semantic refinements.
4. Update of `LAST_AMENDED_DATE` to today and version increment in the
   version line below.

All PRs and `/speckit.plan` constitution checks MUST verify compliance
with this document. Complexity introduced without constitutional
justification in the plan's Complexity Tracking section is grounds for
rejection. Runtime development guidance lives in `AGENTS.md` and must not
contradict this constitution.

**Version**: 1.1.0 | **Ratified**: 2026-07-04 | **Last Amended**: 2026-07-17
