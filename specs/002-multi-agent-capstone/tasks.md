---
description: "Implementation tasks for the Multi-Agent Capstone Project"
---

# Tasks: Multi-Agent Capstone Project

**Input**: Design documents from `/specs/002-multi-agent-capstone/`

**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/

**Organization**: Tasks grouped by user story per spec.md priorities (US1=P1, US2=P1, US3=P2, US4=P3).

## Path Conventions

All paths relative to repository root:
- Source: `src/langgraph_course/module_4/labs/capstone/`
- Tests: `tests/module_4/test_capstone/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and package scaffolding

- [ ] T001 Create module_4/labs/capstone/ directory structure with `__init__.py` files — src subtree: `state.py`, `graph.py`, `nodes/` (5 agents + `__init__`), `coordination/` (router, conflict + `__init__`), `telemetry/` (events + `__init__`)
- [ ] T002 Create test directory `tests/module_4/test_capstone/` with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core state schema, telemetry infrastructure, and test helpers — MUST complete before any user story

- [ ] T003 Implement all entity models in `src/langgraph_course/module_4/labs/capstone/state.py` — `ResearchRequest`, `Agent` (with `failure_count`), `Finding` (with `dimension_tags`), `Conflict` (with `dimension`, `resolution_method`), `SharedState`, `SynthesisReport` (with `data_gaps`), `SteeringInstruction`, `TelemetryEvent`, plus enums for status/state/conflict resolution/event type
- [ ] T004 Implement telemetry helpers in `src/langgraph_course/module_4/labs/capstone/telemetry/events.py` — `TelemetryEvent` factory functions, `@timed_node` integration wrapper
- [ ] T005 Create shared test fixtures in `tests/module_4/test_capstone/__init__.py` — factory functions for `ResearchRequest`, `Finding`, `Agent`, `SharedState`, `Conflict`, `SynthesisReport` with sensible defaults

**Checkpoint**: State schema, telemetry infra, and test helpers ready — user story implementation can begin

---

## Phase 3: User Story 1 — Multi-Agent System with Emergent Intelligence (Priority: P1) 🎯 MVP

**Goal**: Implement 5 specialized agents (Research, Financial, Market, Risk, Synthesis) coordinated through shared state with sequential round-based activation and a cyclic loop.

**Independent Test**: Submit a sample business problem (`run_capstone(topic="...", domain_tags=["..."])`) and verify the output synthesizes contributions from all agents with cross-referencing and attribution.

### Implementation for User Story 1

- [ ] T006 [P] [US1] Implement coordination router in `src/langgraph_course/module_4/labs/capstone/coordination/router.py` — `validate_request()` (specificity heuristics), `activate_agents_router()` (directs validated requests to first agent or refinement), `synthesis_router()` (checks confidence/synthesis triggers), `check_execution_budget()` (`time.monotonic()` vs `max_execution_minutes`), `should_synthesize()` (threshold: ≥0.8 confidence with ≥10 findings, or max budget)
- [ ] T007 [P] [US1] Implement ResearchAgent node in `src/langgraph_course/module_4/labs/capstone/nodes/research.py` — receives `SharedState`, calls LLM via `LLMFactory.create(provider="openrouter")`, produces `Finding` entries with factual data, `dimension_tags`, and source attribution; sets `execution_state=completed` or `failed`
- [ ] T008 [P] [US1] Implement FinancialAgent node in `src/langgraph_course/module_4/labs/capstone/nodes/financial.py` — receives ResearchAgent findings, produces quantitative findings (revenue projections, cost structures, ratios), populates `provenance_chain` referencing Research findings
- [ ] T009 [P] [US1] Implement MarketAgent node in `src/langgraph_course/module_4/labs/capstone/nodes/market.py` — receives Research + Financial findings, produces market analysis (competitive landscape, segments, trends), populates `provenance_chain` and `cross_references`
- [ ] T010 [P] [US1] Implement RiskAgent node in `src/langgraph_course/module_4/labs/capstone/nodes/risk.py` — receives Research + Financial + Market findings, produces risk assessment findings, identifies contradictory claims for Synthesis
- [ ] T011 [US1] Implement SynthesisAgent node in `src/langgraph_course/module_4/labs/capstone/nodes/synthesis.py` — receives all upstream findings + conflict records + `degraded_agents` metadata, produces `SynthesisReport` with `sections`, `cross_references`, `conflict_disclosures`, `data_gaps`, `provenance_trace`; uses LLM to generate narrative
- [ ] T012 [US1] Implement graph composition in `src/langgraph_course/module_4/labs/capstone/graph.py` — `ResearchGraph` class wrapping `StateGraph(SharedState)` with `register_node()`, `add_edge()`, `add_conditional_edges()`, `set_entry_point()`, `set_finish_point()`, `compile()`, `invoke()` (with `model_validate` dict handling), `stream()`; also `create_full_graph()` wiring all 5 agents + validation + refinement in sequential loop: `validate_request` → `research` → `financial` → `market` → `risk` → conditional (synthesize or loop back); and `run_capstone()` / `stream_capstone()` public entry points
- [ ] T013 [P] [US1] Test state model validation in `tests/module_4/test_capstone/test_state.py` — verify all entity models validate correctly, edge cases (empty content, confidence out of range, missing required fields), state transitions
- [ ] T014 [US1] Test agent nodes in `tests/module_4/test_capstone/test_nodes.py` — unit-test each node with mock LLM responses via `LLMFactory` monkey-patch; verify findings are produced with correct `agent_role` and schema compliance

**Checkpoint**: All 5 agents execute in sequence; `run_capstone()` returns a complete `SharedState` with `SynthesisReport`; output contains contributions from all agents

---

## Phase 4: User Story 2 — State Management & Observability (Priority: P1)

**Goal**: Full provenance tracking, `@timed_node` decoration on all nodes, and `TelemetryEvent` recording for every agent execution.

**Independent Test**: Inspect `state.telemetry_events` for recorded events (latency, confidence, failures) and verify every finding has `agent_role`, `confidence`, `timestamp`, and `provenance_chain`.

### Implementation for User Story 2

- [ ] T015 [P] [US2] Add provenance tracking to ResearchAgent in `src/langgraph_course/module_4/labs/capstone/nodes/research.py` — populate `provenance_chain` with source finding IDs when building on upstream work
- [ ] T016 [P] [US2] Add provenance tracking to FinancialAgent in `src/langgraph_course/module_4/labs/capstone/nodes/financial.py`
- [ ] T017 [P] [US2] Add provenance tracking to MarketAgent in `src/langgraph_course/module_4/labs/capstone/nodes/market.py`
- [ ] T018 [P] [US2] Add provenance tracking to RiskAgent in `src/langgraph_course/module_4/labs/capstone/nodes/risk.py`
- [ ] T019 Apply `@timed_node` decorator to all 5 agent node functions in their respective files — `research_node`, `financial_node`, `market_node`, `risk_node`, `synthesis_node`
- [ ] T020 [US2] Add `TelemetryEvent` recording in `src/langgraph_course/module_4/labs/capstone/coordination/router.py` — record events for `agent_latency`, `output_confidence`, `failure`, `stop_triggered`, `circuit_broken` at each routing decision point
- [ ] T021 [P] [US2] Test telemetry event recording in `tests/module_4/test_capstone/test_telemetry.py` — verify events are recorded for each agent with correct roles, event types, and values

**Checkpoint**: Every finding attributable to source agent with provenance chain; telemetry events recorded for all agent nodes and routing decisions

---

## Phase 5: User Story 3 — Conditional Routing & Error Recovery (Priority: P2)

**Goal**: Circuit breaker, input refinement, execution budget enforcement, conflict detection/resolution, graceful degradation, and retry with exponential backoff.

**Independent Test**: Inject failure scenarios (empty response via constrained input, contradictory findings via conflicting domain_tags) and verify system recovers or degrades gracefully.

### Implementation for User Story 3

- [ ] T022 [US3] Implement input validation refinement logic in `src/langgraph_course/module_4/labs/capstone/coordination/router.py` — refine `validate_request()` to check topic length (≥10 words) and domain_tags presence; return status=needs_refinement with guidance text; halt graph execution before agent activation
- [ ] T023 [US3] Implement circuit breaker in `src/langgraph_course/module_4/labs/capstone/coordination/router.py` — per-agent `failure_count` tracking in `agent_states`; after 3 consecutive FAILED states, route around the agent to next in sequence; reset counter on successful execution; record `circuit_broken` telemetry event
- [ ] T024 [US3] Implement execution budget enforcement in `src/langgraph_course/module_4/labs/capstone/coordination/router.py` — `check_execution_budget()` compares elapsed time against `max_execution_minutes`; at 80% trigger threshold, force-synthesize via synthesis router; record `stop_triggered` telemetry event
- [ ] T025 [US3] Implement conflict detection and resolution in `src/langgraph_course/module_4/labs/capstone/coordination/conflict.py` — two-phase: (1) rule-based overlap on `dimension_tags` with contradictory content/numeric mismatches, (2) LLM-based judgment for ambiguous pairs; confidence delta >0.3 → higher confidence wins; otherwise escalate with both perspectives surfaced
- [ ] T026 [US3] Integrate graceful degradation in SynthesisAgent — `src/langgraph_course/module_4/labs/capstone/nodes/synthesis.py` reads `execution_metadata["degraded_agents"]` and includes `data_gaps` section documenting which agents were bypassed; implement retry with exponential backoff in each agent node (wrap LLM call in retry loop with `logger.warning` on retry attempts)
- [ ] T027 [P] [US3] Test router logic in `tests/module_4/test_capstone/test_router.py` — validate refinement detection, budget trigger thresholds, synthesis decision logic, circuit breaker state transitions (3 failures → bypass, reset on success)
- [ ] T028 [P] [US3] Test conflict detection + resolution in `tests/module_4/test_capstone/test_conflict.py` — overlapping dimension_tags with numeric contradictions, contradictory conclusions, non-overlapping findings (no conflict), LLM-based resolution with confidence-weighted tie-breaking

**Checkpoint**: Circuit breaker bypasses failing agents; input refinement catches vague topics; budget exhaustion forces synthesis; conflicts detected and resolved or surfaced; `degraded_agents` and `data_gaps` populated when agents fail

---

## Phase 6: User Story 4 — Documentation & Demo (Priority: P3)

**Goal**: Architecture documentation, integration tests (3+ workflow paths), reflection report, and validation sign-off.

**Independent Test**: Review architecture docs for agent relationships, state schema, workflow logic, and design decisions; run integration tests; verify reflection report.

### Implementation for User Story 4

- [ ] T029 [US4] Create integration tests in `tests/module_4/test_capstone/test_integration.py` covering 3+ distinct workflow paths: (1) normal execution — all agents succeed with cross-referenced output, (2) agent failure — circuit breaker bypasses failing agent, synthesis includes data gaps, (3) conflict detection — conflicting findings detected and resolved/escalated
- [ ] T030 [US4] Create architecture documentation in `src/langgraph_course/module_4/labs/capstone/ARCHITECTURE.md` — agent relationships diagram (text/ascii), shared state schema, workflow logic/activation order, conditional routing decisions, design trade-offs (circuit breaker vs timeout, LLM vs rule-based conflict resolution, sequential vs parallel topology)
- [ ] T031 [US4] Create reflection report in `src/langgraph_course/module_4/labs/capstone/REFLECTION.md` — 1000-1500 words covering: design decisions and rationale, trade-offs encountered, challenges faced, future opportunities for improvement, emergent intelligence observations
- [ ] T032 [US4] Run all 5 quickstart.md validation scenarios end-to-end and record results

**Checkpoint**: All test paths pass; architecture documentation readable; reflection report complete; validation scenarios verified

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Linting, quality checks, and final verification

- [ ] T033 Run `poetry run ruff check .` across all new files and fix any lint violations
- [ ] T034 Update `README.md` with new `module_4/labs/capstone/` project structure
- [ ] T035 Run full test suite: `poetry run python -m unittest discover -v tests/module_4/test_capstone/`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — start immediately
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories (state schema required everywhere)
- **US1 (Phase 3)**: Depends on Foundational — BLOCKS US2 (agents must exist before adding telemetry)
- **US2 (Phase 4)**: Depends on US1 (adds telemetry/provenance to existing agents)
- **US3 (Phase 5)**: Depends on US1 (adds error handling to existing routing and agents)
- **US4 (Phase 6)**: Depends on US1+US2+US3 (tests/documentation cover complete system)
- **Polish (Phase 7)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — No dependencies on other stories
- **US2 (P1)**: Depends on US1 (telemetry woven into agent nodes) but can be implemented in parallel with US3
- **US3 (P2)**: Depends on US1 (extends routing logic and agent error handling) — can parallel with US2
- **US4 (P3)**: Depends on US1+US2+US3 complete

### Parallel Opportunities

- T006-T010 (router + 4 agent nodes) are all [P] — can write coordination/router.py and all 4 upstream agent nodes simultaneously
- T015-T018 (provenance per agent) are all [P] — can add provenance to all agents simultaneously
- T007-T010 can parallel with T006 (router)
- T013-T014 (state + node tests) can be written in parallel with implementation
- T027-T028 (router + conflict tests) can be written in parallel
- US2 (Phase 4) and US3 (Phase 5) can be developed in parallel by different developers

### Within Each User Story

- Coordination/router before graph (graph uses router functions)
- Agent nodes before graph (graph registers nodes)
- Tests can be written alongside or after implementation
- Core implementation before integration

---

## Parallel Example: User Story 1

```bash
# Launch router + all 4 upstream agent nodes in parallel:
Task: "T006 - coordination/router.py"
Task: "T007 - nodes/research.py"
Task: "T008 - nodes/financial.py"
Task: "T009 - nodes/market.py"
Task: "T010 - nodes/risk.py"

# After those complete, sequential synthesis + graph:
Task: "T011 - nodes/synthesis.py"  (needs to know all agent interfaces)
Task: "T012 - graph.py"            (needs all nodes registered)

# Tests can run after implementation:
Task: "T013 - test_state.py"
Task: "T014 - test_nodes.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: US1 — Multi-agent system
4. **STOP and VALIDATE**: `run_capstone()` with sample business problem
5. Basic workflow works — agents execute, synthesis produces report

### Incremental Delivery

1. Setup + Foundational → State schema ready
2. Add US1 → Core multi-agent workflow works (MVP!)
3. Add US2 → Provenance and telemetry visible
4. Add US3 → Resilience in place
5. Add US4 → Documented, tested, validated

---

## Notes

- [P] tasks = different files, no dependencies — can run in parallel
- [US1] through [US4] map tasks to spec.md user stories
- Each user story is independently testable after its phase completes
- All configuration via `Settings` class and `.env` — no hardcoded API keys or model names
- LLM calls use `LLMFactory.create(provider="openrouter")` per project convention
- All nodes use `@timed_node` decorator and `loguru` for logging per constitution Article III
- State schema uses `pydantic.BaseModel` per constitution Article I
- All tests use `unittest` per constitution Article V
