# Implementation Plan: Sequential Multi-Agent Blog Workflow

**Branch**: `004-sequential-agent-blog-workflow` | **Date**: 2026-08-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-sequential-agent-blog-workflow/spec.md`

## Summary

Build a Python implementation of the Module 2 "Mastering Sequential Agent Workflows" lab for ContentCraft Marketing. A single topic flows through a strictly linear chain of three specialist agents — **Researcher → Writer → SEO Analyst** — producing a 5-point outline, a multi-paragraph draft, then SEO feedback (title options + keywords). The graph is implemented with LangGraph `StateGraph` (one linear path, no branches), engineered prompts live in `prompts.py`, and the lab's three deliverables (prompt-engineering document + communication-protocol analysis, the third being a submission that mirrors the Flowise canvas) are compiled by an export module. This mirrors the Flowise "Simple Sequential Chain" the lab mandates while staying inside the repo's LangGraph/LangChain conventions so it can be unit-tested offline.

## Technical Context

**Language/Version**: Python 3.10+ (locked by `pyproject.toml`)

**Primary Dependencies**: langgraph ^1.2 (orchestration), langchain + langchain-openai (LLM calls via `LLMFactory`), pydantic (state/entity schemas), pydantic-settings (config via `Settings`), loguru (logging). **No new dependencies** — the entire lab compiles to markdown, no PDF needed. The Flowise canvas screenshot is produced by the user in Flowise, not by code.

**Storage**: N/A — stateless per run, no persistence

**Testing**: unittest (stdlib) — test files under `tests/multiagent-governance_course/test_module_2_multiagents/test_*.py` mirroring source structure

**Target Platform**: Python/CLI runnable headlessly; LLM nodes callable for real inference or stubbed for deterministic tests

**Project Type**: Library / CLI pipeline (educational lab implementation)

**Performance Goals**: Each agent node < 15s (network-bound LLM); full linear chain < 45s for a single run; prompt/analysis export < 1s

**Constraints**: Linear one-way flow only (all info flow forward, only the draft/outline/SEO state passed; no feedback loop). All prompt text in English. LLM calls MUST go through `LLMFactory` (never direct `ChatOpenAI`). Plain (non-method) node functions MUST record latency manually with `time.monotonic()` — the `@timed_node` decorator assumes a classmethod signature (`args[1]`) and must NOT be applied. State schema MUST use a pydantic `BaseModel`; no `Annotated[list, add_messages]` needed (streaming message accumulate not required). All config (provider, model, api key) via `.env` + `Settings`.

**Scale/Scope**: Single-user educational tool; 3 user stories, 9 functional requirements, 5 success criteria; 3 specialist agents; 1 linear graph; markdown-only export (no PDF).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Notes |
|-----------|-------|-------|
| I. LangGraph Architecture | ✅ PASS | `StateGraph` with linear `add_edge` chain; typed pydantic state schema (`BlogState`); no branching → no `ConditionalEdge` needed; no message reducer (`Annotated[list, add_messages]`) since we pass single values, not chat history |
| II. Configuration-Driven | ✅ PASS | All model names / provider from `Settings` in `config.py`; `.env` drives LLM provider; zero hardcoded keys |
| III. Observability | ✅ PASS | Manual `time.monotonic()` latency per node (plain functions, not classmethods — `@timed_node` inapplicable); `loguru` logging (imported via package `__init__`); `ErrorRecord` TypedDict for failures with `processing_outcome="partial"` |
| IV. LLM Abstraction | ✅ PASS | All LLM interactions via `LLMFactory.create()`; no direct model instantiation anywhere |
| V. Test Discipline | ✅ PASS | unittest; tests mirror source at `tests/multiagent-governance_course/test_module_2_multiagents/`; one TestCase class per module; stub LLM for deterministic tests |
| VI. Dependency Discipline | ✅ PASS | No new dependencies — uses existing internal stack (langgraph, langchain, pydantic, pydantic-settings, loguru). No PDF generation needed (submission canvas is user-produced in Flowise) |
| Total | ✅ ALL PASS | No violations; Complexity Tracking not required |

## Project Structure

### Documentation (this feature)

```text
specs/004-sequential-agent-blog-workflow/
├── plan.md              # This file (/speckkit.plan command output)
├── research.md          # Phase 0 output (/speckkit.plan command)
├── data-model.md        # Phase 1 output (/speckkit.plan command)
├── quickstart.md        # Phase 1 output (/speckkit.plan command)
├── contracts/           # Phase 1 output (/speckkit.plan command)
│   └── workflow.md      # Linear graph contract & prompt-interface contract
├── checklists/
│   └── requirements.md  # Quality checklist
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
src/multiagent-governance_course/module_2_multiagents/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── prompts.py        # Template strings: researcher, writer, seo (use {topic} / state fields)
│   ├── researcher.py     # Node: topic → outline
│   ├── writer.py         # Node: outline → draft
│   └── seo.py            # Node: draft → seo_feedback
├── state.py              # BlogState (pydantic) + imports of LLMFactory
├── workflow.py           # build_workflow() -> CompiledStateGraph (linear chain)
├── runtime.py            # run_pipeline(topic) façade that builds + invokes the graph
└── export.py             # build_prompts_doc() + build_analysis_doc(md, word_count)

tests/multiagent-governance_course/test_module_2_multiagents/
├── __init__.py
├── test_state.py
├── test_prompts.py
├── test_agents.py
├── test_workflow.py
└── test_export.py
```

**Structure Decision**: Single-project layout with feature modules under `module_2_multiagents/`. Tests mirror the source at `tests/multiagent-governance_course/test_module_2_multiagents/`. This extends the convention established by `module_1_foundations/` and house-style used across `src/langgraph_course/module_*/`.

## Complexity Tracking

Not required — all constitution checks pass without violations.

## Phase 0: Research

See [research.md](research.md) for resolved unknowns and technology decisions (linear LangGraph vs. supervisor/parallel; state schema shape; prompt-handoff design; no-new-dependency decision).

## Phase 1: Design & Contracts

- **Data Model**: [data-model.md](data-model.md) — entities (`Topic`, `Outline`, `ArticleDraft`, `SeoFeedback`, `BlogState`, `NodeResult`), fields, validation
- **Contracts**: [contracts/workflow.md](contracts/workflow.md) — the graph contract (node signature, state mutation), prompt interface contract, and export format
- **Quickstart**: [quickstart.md](quickstart.md) — runnable validation scenarios with commands and expected outputs