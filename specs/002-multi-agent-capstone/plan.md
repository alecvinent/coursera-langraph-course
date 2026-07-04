# Implementation Plan: Multi-Agent Capstone Project

**Branch**: `002-multi-agent-capstone` | **Date**: 2026-07-04 | **Spec**: [spec.md](spec.md)

**Input**: Capstone project brief — build a production-ready multi-agent system demonstrating coordinated agent collaboration, persistent state management, conditional routing, error handling, and resilience patterns.

## Summary

Implement a 5-agent LangGraph workflow in a new `module_4/labs/capstone/` package. Agents (Research, Financial, Market, Risk, Synthesis) execute sequentially with a cyclic loop, building shared state via a `pydantic.BaseModel` schema. The system satisfies 15 functional requirements including circuit breaker (FR-014), input refinement (FR-012), conflict resolution (FR-009), graceful degradation (FR-008), execution budget enforcement (FR-011), and full telemetry (FR-010). Tests use `unittest` with 3+ workflow path coverage.

## Technical Context

**Language/Version**: Python 3.10+

**Primary Dependencies**: LangGraph, LangChain, pydantic, loguru, pydantic-settings, LLMFactory (from project utils)

**Storage**: In-memory (LangGraph StateGraph with optional Checkpointer for persistence extension)

**Testing**: unittest (stdlib), tests under `tests/module_4/test_capstone/`

**Target Platform**: Linux server (project standard)

**Project Type**: Library module under `src/langgraph_course/module_4/labs/capstone/`

**Performance Goals**: Workflow completes within 15 minutes (SC-001); graceful degradation within 30s (SC-004)

**Constraints**: 4-6 agents (5 selected), <15min completion, 90%+ finding attribution, circuit breaker after 3 consecutive failures, max execution budget with 80% pre-synthesis threshold

**Scale/Scope**: Single-user capstone evaluation; not production multitenant

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Article | Rule | Compliance | Notes |
|---------|------|-----------|-------|
| I — LangGraph Patterns | StateGraph, pydantic state, Node/Edge/ConditionalEdge | ✅ PASS | Sequential + conditional loop topology maps to LangGraph primitives |
| II — Config-Driven Design | Settings class, .env, no hardcoded values | ✅ PASS | All config (model, budget, thresholds) via Settings + .env; LLMFactory for provider selection |
| III — Observability | @timed_node decorator, loguru, ErrorRecord, exponential backoff | ✅ PASS | 3-layer: @timed_node per node, loguru for structured logs, TelemetryEvent records in state |
| IV — LLM Abstraction | LLMFactory only; no direct ChatOpenAI/etc | ✅ PASS | All 5 agents use LLMFactory.create() via project utils |
| V — Test Discipline | unittest, mirrored structure, 1 class per subject, integration tests | ✅ PASS | Tests under `tests/module_4/test_capstone/` mirroring source structure |

**Verdict**: ALL GATES PASS. No complexity tracking required.

## Research

See [research.md](research.md) for 8 design decisions covering agent specialization, activation topology, circuit breaker, conflict resolution, input refinement, budget enforcement, telemetry, and graceful degradation.

## Project Structure

### Documentation (this feature)

```text
specs/002-multi-agent-capstone/
├── plan.md              # This file
├── research.md          # Phase 0 output — 8 design decisions
├── data-model.md        # Phase 1 output — 8 entities with state transitions
├── quickstart.md        # Phase 1 output — 5 validation scenarios
├── contracts/
│   ├── agent-interfaces.md   # 5 agent contracts + coordination contracts
│   └── api-contracts.md      # Public/ops API contract
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/langgraph_course/
└── module_4/
    └── labs/
        └── capstone/
            ├── __init__.py
            ├── state.py              # All entity models (ResearchRequest, Finding, Conflict, etc.)
            ├── graph.py              # ResearchGraph wrapper + create_full_graph() + run/stream entry points
            ├── nodes/
            │   ├── __init__.py
            │   ├── research.py       # ResearchAgent — raw data gathering
            │   ├── financial.py      # FinancialAgent — quantitative analysis
            │   ├── market.py         # MarketAgent — competitive/market positioning
            │   ├── risk.py           # RiskAgent — threat/risk assessment
            │   └── synthesis.py      # SynthesisAgent — integration + report generation
            ├── coordination/
            │   ├── __init__.py
            │   ├── router.py         # Input validation, circuit breaker, budget check, synthesis triggers
            │   └── conflict.py       # Conflict detection + resolution
            └── telemetry/
                ├── __init__.py
                └── events.py         # TelemetryEvent builders + timed_node integration

tests/
└── module_4/
    └── test_capstone/
        ├── __init__.py
        ├── test_state.py             # Entity validation, state transitions
        ├── test_nodes.py             # Each agent node in isolation
        ├── test_conflict.py          # Conflict detection + resolution
        ├── test_router.py            # Input validation, circuit breaker, budget, synthesis triggers
        ├── test_telemetry.py         # Telemetry event recording
        └── test_integration.py       # End-to-end workflow paths (3+ scenarios)
```

**Structure Decision**: Single library module with nested sub-packages matching the module_3 pattern. This keeps the capstone consistent with the existing codebase structure while adding the new node types (Financial, Market, Risk) and enhanced coordination (circuit breaker, conflict resolution). The topology is sequential with a conditional loop, implemented via `StateGraph` with `add_conditional_edges` for routing decisions after each non-terminal agent.

## Complexity Tracking

Not required — Constitution Check passed with no violations.
