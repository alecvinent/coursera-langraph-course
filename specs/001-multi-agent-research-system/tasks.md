# Tasks: Multi-Agent Research System

**Input**: Design documents from `specs/001-multi-agent-research-system/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Test tasks are included for all user stories.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create directory structure and scaffolding for the multi-agent research system

- [x] T001 Create package structure under `src/langgraph_course/module_3/multi_agent_research/` with `__init__.py`
- [x] T002 [P] Create node package under `src/langgraph_course/module_3/multi_agent_research/nodes/__init__.py`
- [x] T003 [P] Create coordination package under `src/langgraph_course/module_3/multi_agent_research/coordination/__init__.py`
- [x] T004 [P] Create telemetry package under `src/langgraph_course/module_3/multi_agent_research/telemetry/__init__.py`
- [x] T005 [P] Create test package under `tests/module_3/test_multi_agent_research/__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 Define shared state schema in `src/langgraph_course/module_3/multi_agent_research/state.py` with pydantic models for all entities from data-model.md
- [x] T007 Define enums for AgentRole, ResearchRequestStatus, ConflictStatus, ExecutionState, TelemetryEventType in `src/langgraph_course/module_3/multi_agent_research/state.py`
- [x] T008 Implement telemetry event recording in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T009 Create LangGraph StateGraph definition in `src/langgraph_course/module_3/multi_agent_research/graph.py` with shared state and node registration entry points
- [x] T010 Implement provenance tracking utility in `src/langgraph_course/module_3/multi_agent_research/coordination/provenance.py`
- [x] T010.5 [P] Create FastAPI application entry point in `src/langgraph_course/module_3/multi_agent_research/api.py`
- [x] T010.6 Implement POST /research endpoint (submit request) in `src/langgraph_course/module_3/multi_agent_research/api.py`
- [x] T010.7 Implement GET /research/{id}/findings endpoint (intermediate findings) in `src/langgraph_course/module_3/multi_agent_research/api.py`
- [x] T010.8 Implement POST /research/{id}/steer endpoint in `src/langgraph_course/module_3/multi_agent_research/api.py`
- [x] T010.9 Implement GET /research/{id}/report endpoint in `src/langgraph_course/module_3/multi_agent_research/api.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Core Research Workflow (Priority: P1) 🎯 MVP

**Goal**: Analyst submits a research request, relevant agents are activated, they collaborate through shared state, and the synthesis agent produces a coherent report with provenance attribution.

**Independent Test**: Submit a well-scoped research question and verify output report contains findings from at least 3 specialized agents with cross-references and provenance attribution.

### Tests for User Story 1

- [x] T011 [P] [US1] Test state schema creation and validation in `tests/module_3/test_multi_agent_research/test_state.py`
- [x] T012 [P] [US1] Integration test: submit research request and verify report contains 3+ agent contributions in `tests/module_3/test_multi_agent_research/test_workflow.py`
- [x] T013 [P] [US1] Test provenance tracking: verify each claim is attributable to a source agent in `tests/module_3/test_multi_agent_research/test_provenance.py`

### Implementation for User Story 1

- [x] T014 [P] [US1] Implement WebResearchAgent node in `src/langgraph_course/module_3/multi_agent_research/nodes/web_research.py`
- [x] T015 [P] [US1] Implement DataAnalysisAgent node in `src/langgraph_course/module_3/multi_agent_research/nodes/data_analysis.py`
- [x] T016 [P] [US1] Implement TrendAnalysisAgent node in `src/langgraph_course/module_3/multi_agent_research/nodes/trend_analysis.py`
- [x] T017 [P] [US1] Implement CompetitiveIntelligenceAgent node in `src/langgraph_course/module_3/multi_agent_research/nodes/competitive_intel.py`
- [x] T018 [US1] Implement Router in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py` — decides which agents to activate, parallel vs sequential, based on domain_tags and request complexity
- [x] T019 [US1] Wire up StateGraph with agent nodes, parallel fan-out, and conditional edges in `src/langgraph_course/module_3/multi_agent_research/graph.py`
- [x] T020 [US1] Implement SynthesisAgent node with report generation, cross-referencing, and provenance attribution in `src/langgraph_course/module_3/multi_agent_research/nodes/synthesis.py`
- [x] T020.5 [US1] Handle empty agent findings in synthesis — when an agent returns zero findings, the report documents the gap as "insufficient data from [agent_role]" in `src/langgraph_course/module_3/multi_agent_research/nodes/synthesis.py`
- [x] T021 [US1] Implement synthesis stop criteria (three-tier trigger: all agents complete, confidence threshold met, max budget exhausted) in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`
- [x] T022 [US1] Implement basic conflict detection (surface contradictory findings transparently without re-investigation) in `src/langgraph_course/module_3/multi_agent_research/nodes/synthesis.py`
- [x] T023 [US1] Implement overly-broad request detection and refinement request in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`
- [x] T024 [US1] Implement maximum execution budget enforcement per agent and per workflow in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`
- [x] T025 [US1] Add logging for all major workflow events (agent activation, finding production, stop trigger) in `src/langgraph_course/module_3/multi_agent_research/graph.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently. An analyst can submit a research topic and receive a synthesized, attributed report.

---

## Phase 4: User Story 2 - Steering & Intermediate Visibility (Priority: P2)

**Goal**: Analyst can view intermediate findings from any agent mid-workflow and submit steering instructions that cause targeted agents to re-focus before synthesis completes.

**Independent Test**: Submit a request, view intermediate findings, add a steering instruction, and verify the final report reflects the steering direction.

### Tests for User Story 2

- [x] T026 [P] [US2] Test intermediate findings retrieval in `tests/module_3/test_multi_agent_research/test_workflow.py`
- [x] T027 [P] [US2] Test steering instruction application: verify targeted agents incorporate new direction in `tests/module_3/test_multi_agent_research/test_workflow.py`

### Implementation for User Story 2

- [x] T028 [P] [US2] Implement intermediate findings query endpoint/logic in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T029 [US2] Implement SteeringInstruction model and validation in `src/langgraph_course/module_3/multi_agent_research/state.py`
- [x] T030 [US2] Implement steering instruction handler: pause workflow, re-trigger targeted agents, resume in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`
- [x] T031 [US2] Wire steering into StateGraph: detect pending instructions mid-workflow and branch in `src/langgraph_course/module_3/multi_agent_research/graph.py`
- [x] T032 [US2] Add steering report note: final report documents how intermediate intervention affected outcome in `src/langgraph_course/module_3/multi_agent_research/nodes/synthesis.py`
- [x] T033 [US2] Add logging for steering events in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`

**Checkpoint**: User Story 2 independently functional. Analyst can steer research mid-workflow.

---

## Phase 5: User Story 3 - Advanced Conflict Resolution (Priority: P2)

**Goal**: System automatically detects contradictory findings, triggers re-investigation by affected agents, and if unresolvable, presents both perspectives with supporting evidence and flagged uncertainty.

**Independent Test**: Seed known contradictory data sources and verify the system either resolves through re-investigation or presents both sides transparently.

### Tests for User Story 3

- [x] T034 [P] [US3] Test conflict detection with seeded contradictions in `tests/module_3/test_multi_agent_research/test_conflict.py`
- [x] T035 [P] [US3] Test re-investigation loop: verify agents are re-triggered with conflict context in `tests/module_3/test_multi_agent_research/test_conflict.py`
- [x] T036 [P] [US3] Test escalation: verify unresolved conflicts are surfaced with both perspectives in `tests/module_3/test_multi_agent_research/test_conflict.py`

### Implementation for User Story 3

- [x] T037 [P] [US3] Implement Conflict model and validation in `src/langgraph_course/module_3/multi_agent_research/state.py`
- [x] T038 [US3] Implement conflict detection logic (compare overlapping Finding dimensions for contradictory values) in `src/langgraph_course/module_3/multi_agent_research/coordination/conflict.py`
- [x] T039 [US3] Implement conflict resolution: re-investigation trigger with conflict context passed to affected agents in `src/langgraph_course/module_3/multi_agent_research/coordination/conflict.py`
- [x] T040 [US3] Wire conflict resolution into StateGraph: detect conflicts, pause synthesis, trigger re-investigation, resume in `src/langgraph_course/module_3/multi_agent_research/graph.py`
- [x] T041 [US3] Add escalated conflict disclosure to synthesis report in `src/langgraph_course/module_3/multi_agent_research/nodes/synthesis.py`
- [x] T042 [US3] Add logging for conflict detection, resolution, and escalation events in `src/langgraph_course/module_3/multi_agent_research/coordination/conflict.py`

**Checkpoint**: User Story 3 independently functional. System handles contradictory findings robustly.

---

## Phase 6: User Story 4 - Telemetry & Operations (Priority: P3)

**Goal**: Operations team monitors per-agent latencies, conflict counts, stop conditions, and failure rates. Alerts fire on agent failure or timeout. Manual intervention (resume/restart/abort) is supported.

**Independent Test**: Process a research request, then verify telemetry dashboard shows per-agent metrics. Force an agent failure and verify alert fires.

### Tests for User Story 4

- [x] T043 [P] [US4] Test telemetry event recording and retrieval in `tests/module_3/test_multi_agent_research/test_telemetry.py`
- [x] T044 [P] [US4] Test agent failure detection and alert in `tests/module_3/test_multi_agent_research/test_telemetry.py`
- [x] T045 [P] [US4] Test manual workflow intervention (resume/restart/abort) in `tests/module_3/test_multi_agent_research/test_workflow.py`

### Implementation for User Story 4

- [x] T046 [P] [US4] Implement TelemetryEvent buffer with windowed query support in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T047 [US4] Implement per-agent telemetry: latency, output confidence, contribution count in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T048 [US4] Implement agent failure detection and alert dispatch in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T049 [US4] Implement manual workflow intervention API (resume/restart/abort) in `src/langgraph_course/module_3/multi_agent_research/coordination/router.py`
- [x] T050 [US4] Wire intervention handlers into StateGraph in `src/langgraph_course/module_3/multi_agent_research/graph.py`
- [x] T051 [US4] Add logging for telemetry events and interventions in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T051.5 [US4] Add timing instrumentation to measure report generation latency (SC-001: <10 min) in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T051.6 [US4] Add timing instrumentation to measure steering response latency (SC-004: <2 min extra) in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`
- [x] T051.7 [US4] Add timing instrumentation to measure telemetry update latency (SC-005: <5 sec) in `src/langgraph_course/module_3/multi_agent_research/telemetry/events.py`

**Checkpoint**: User Story 4 independently functional. Operations visibility and alerting operational.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T052 Run quickstart.md validation scenarios and fix any issues
- [x] T053 [P] Add input validation for all API contracts per `contracts/api-contracts.md`
- [x] T054 [P] Add error handling and user-friendly error messages for all failure modes
- [x] T055 Code cleanup and refactoring across all agent nodes
- [x] T056 [P] Documentation: update `AGENTS.md` with multi-agent research system conventions if applicable
- [x] T057 Run full test suite: `poetry run python -m unittest discover -v tests/module_3/test_multi_agent_research/`
- [x] T057.5 Run performance validation: verify SC-001, SC-004, SC-005 targets are met using the timing instrumentation

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - US1 (Phase 3) must complete before US3 (Phase 5) since US3 adds to US1's synthesis agent
  - US2 (Phase 4) is independent of US1's core — can proceed in parallel
  - US3 (Phase 5) builds on US1's synthesis agent — requires Phase 3 completion
  - US4 (Phase 6) is independent — relies on telemetry events emitted by all stories
- **Polish (Phase 7)**: Depends on all user story phases being complete

### User Story Dependencies

- **User Story 1 (P1)**: No dependencies on other stories — MVP
- **User Story 2 (P2)**: No dependencies on other stories — independent feature
- **User Story 3 (P2)**: Depends on US1 (synthesis agent must exist to augment)
- **User Story 4 (P3)**: No code-level dependencies — relies on telemetry events emitted by other stories but can be developed in parallel

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Models before services
- Core node logic before coordination wiring
- Logging added alongside feature implementation

---

## Parallel Opportunities

- T002, T003, T004, T005 can run in parallel
- T011, T012, T013 can run in parallel (US1 tests)
- T014, T015, T016, T017 can run in parallel (US1 agent nodes)
- T026, T027 can run in parallel (US2 tests)
- T034, T035, T036 can run in parallel (US3 tests)
- T043, T044, T045 can run in parallel (US4 tests)
- US2 (Phase 4) and US1 (Phase 3) can proceed in parallel after Foundation completes
- US4 (Phase 6) can proceed in parallel with US2

---

## Parallel Example: User Story 1

```bash
# Launch all tests together:
poetry run python -m unittest tests/module_3/test_multi_agent_research/test_state.py &
poetry run python -m unittest tests/module_3/test_multi_agent_research/test_workflow.py &
poetry run python -m unittest tests/module_3/test_multi_agent_research/test_provenance.py &

# Launch all agent node implementations together:
# T014, T015, T016, T017 — all independent agent node files
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test US1 independently — submit research request, verify synthesized report
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 → Test independently → Deploy/Demo (MVP!)
3. Add US2 (steering) + US3 (conflict resolution) in parallel → Test each independently → Deploy
4. Add US4 (telemetry) → Test independently → Deploy
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Phase 1 + Phase 2 together
2. Once Foundation is done:
   - Developer A: User Story 1 (core workflow)
   - Developer B: User Story 2 (steering) — independent
   - Developer C: User Story 4 (telemetry) — independent
3. After US1 completes, Developer A continues with User Story 3
4. Stories integrate and validate independently

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Stop at any checkpoint to validate story independently
- Follow LangGraph patterns per AGENTS.md: StateGraph, Annotated[list, add_messages], @timed_node decorator
- Use LLMFactory for all LLM creation per project conventions
- Use loguru for all logging
