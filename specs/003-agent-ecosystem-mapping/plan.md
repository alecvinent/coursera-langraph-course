# Implementation Plan: Agent Ecosystem Mapping

**Branch**: `003-agent-ecosystem-mapping` | **Date**: 2026-07-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/003-agent-ecosystem-mapping/spec.md`

## Summary

Build a Streamlit-based educational tool for Coursera's LangGraph course (Module 1) that lets learners classify AI agents (Reactive/Deliberative/Hybrid) using a hybrid rule-based + LLM engine, visualize multi-agent interaction diagrams in Mermaid, analyze trade-offs across 5 architectural dimensions, and model single-agent capability cycles. All 4 deliverables compile into a single .md + .pdf submission file for Coursera upload.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: langgraph ^1.2 (orchestration), langchain + langchain-openai (LLM calls via LLMFactory), pydantic-settings (config), loguru (logging), streamlit ^1.44 (web UI), pymupdf ^1.27 (PDF via `page.insert_htmlbox()` + drawing primitives, already in deps), grandalf (graph layout for PDF diagrams, already in deps), markdown (md→HTML bridge — new dep, justified: no existing dep provides markdown parsing)

**Storage**: N/A — pure computation, stateless per session; no database

**Testing**: unittest (stdlib) — test files under `tests/multiagent-governance_course/test_module_1_foundations/test_*.py` mirroring source structure

**Target Platform**: Web browser via Streamlit (dev), CLI-compatible for headless testing

**Project Type**: Educational web application (Streamlit frontend + LangGraph analysis backend)

**Performance Goals**: Rule-based classification < 1s; LLM fallback < 15s (network-bound); Mermaid diagram generation < 500ms; Submission compilation < 2s

**Constraints**: Rule-based mode must work offline (zero LLM dependency); all user-facing text in English; output files self-contained (no external image assets); LLM calls must use LLMFactory (never direct ChatOpenAI); nodes record manual `time.monotonic()` latency (avoid `@timed_node` — it assumes classmethod args[1]); PDF diagrams must use `grandalf` for graph layout + `pymupdf` drawing primitives (no new external deps); `<pre>` Mermaid blocks stripped from PDF HTML render — Mermaid code preserved in .md export only

**Scale/Scope**: Single-user educational tool; 4 user stories, 12 functional requirements, 10 success criteria; 4+ scenario templates; PDF via PyMuPDF `page.insert_htmlbox()`

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Check | Notes |
|-----------|-------|-------|
| I. LangGraph Architecture | ✅ PASS | StateGraph for classification workflow, conditional edges for rule→LLM routing, Annotated[list, add_messages] not needed (stateless) |
| II. Configuration-Driven | ✅ PASS | Settings class from `config.py`, no hardcoded keys/model names |
| III. Observability | ✅ PASS | manual time.monotonic() latency on nodes, loguru logging, ErrorRecord TypedDict for failures |
| IV. LLM Abstraction | ✅ PASS | LLMFactory.create() for all LLM fallback calls; no direct model instantiation |
| V. Test Discipline | ✅ PASS | unittest, tests/multiagent-governance_course/test_module_1_foundations/, one class per module |
| VI. Dependency Discipline | ✅ PASS | No new deps beyond `markdown` (justified in research.md D3). `grandalf` (graph layout) already in approved stack — used for PDF diagram rendering per research.md D7 |
| Total | ✅ ALL PASS | No violations; Complexity Tracking not required |

## Project Structure

### Documentation (this feature)

```text
specs/003-agent-ecosystem-mapping/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── classifier.md
├── checklists/
│   └── requirements.md  # Quality checklist
└── spec.md              # Feature specification
```

### Source Code (repository root)

```text
src/multiagent-governance_course/module_1_foundations/
├── __init__.py
├── classification/
│   ├── __init__.py
│   ├── rules.py            # Rule-based decision tree engine
│   ├── graph.py            # LangGraph StateGraph (rule → LLM fallback)
│   └── prompts.py          # LLM classification prompt templates
├── interaction_map/
│   ├── __init__.py
│   └── mapper.py           # Mermaid flow chart + capability cycle generator
├── analysis/
│   ├── __init__.py
│   └── tradeoffs.py        # 5-dimension trade-off + side-by-side analysis
├── export/
│   ├── __init__.py
│   ├── submission.py       # .md compilation + .pdf generation (markdown + pymupdf)
│   └── diagram_renderer.py # grandalf graph layout + pymupdf drawing for PDF diagrams
├── scenarios/
│   ├── __init__.py
│   ├── base.py             # Scenario data model
│   ├── traffic.py          # Traffic control scenario (Activity 1)
│   └── task_manager.py     # Personal task manager scenario (Activity 2)
└── app.py                  # Streamlit entry point (4-step wizard)

tests/multiagent-governance_course/test_module_1_foundations/
├── __init__.py
├── test_classification.py
├── test_interaction_map.py
├── test_analysis.py
├── test_export.py
└── test_scenarios.py
```

**Structure Decision**: Single-project layout with feature-based modules under `module_1_foundations/`. Tests mirror source structure at `tests/multiagent-governance_course/test_module_1_foundations/`. This follows the convention used by `src/langgraph_course/module_2/` and `module_3/` in this repo.

## Complexity Tracking

Not required — all constitution checks pass without violations.

## Phase 0: Research

See [research.md](research.md) for resolved unknowns and technology decisions.

## Phase 1: Design & Contracts

- **Data Model**: [data-model.md](data-model.md) — entities, fields, relationships, validation
- **Contracts**: [contracts/](contracts/) — classification API, mapper interface, analysis interface, export interface
- **Quickstart**: [quickstart.md](quickstart.md) — validation scenarios with commands and expected outcomes
