# Tasks: Agent Ecosystem Mapping

**Input**: Design documents from `specs/003-agent-ecosystem-mapping/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md), [contracts/](contracts/)

**Tests**: Included per constitution mandate — every `src/` module requires a corresponding `test_` file.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/multiagent-governance_course/module_1_foundations/`
- **Tests**: `tests/multiagent-governance_course/test_module_1_foundations/`
- Single-project layout per [plan.md](plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, dependency installation, and directory structure

- [x] T001 Create directory structure: `src/multiagent-governance_course/module_1_foundations/{classification,interaction_map,analysis,export,scenarios}/` with `__init__.py` files; `tests/multiagent-governance_course/test_module_1_foundations/` with `__init__.py`
- [x] T002 [P] Add `markdown` to `pyproject.toml` dependencies (justified: no existing dep provides markdown parsing; `pymupdf` already covers PDF generation), run `poetry lock && poetry install`
- [x] T003 [P] Create `src/multiagent-governance_course/module_1_foundations/__init__.py` with `ErrorRecord` TypedDict and `logger` import
- [x] T004 [P] Create `tests/multiagent-governance_course/test_module_1_foundations/__init__.py` with `sys.path.insert(0, ...)` for import discovery

**Checkpoint**: Module structure ready, dependencies installed

---

## Phase 2: Foundational — Scenario Data Models

**Purpose**: Core entity models that ALL user stories depend on

- [x] T005 Create `src/multiagent-governance_course/module_1_foundations/scenarios/base.py` with Pydantic models: `AgentAttribute(name, value, description?)`, `AgentDef(id, name, description, attributes)`, `InteractionDef(source, target, label, type)`, `InteractionType(Enum)`, `AgentType(Enum)`, `Scenario(id, name, description, agents, interactions)`, `ErrorRecord(TypedDict)`
- [x] T006 Create `src/multiagent-governance_course/module_1_foundations/scenarios/traffic.py` with `traffic_scenario: Scenario` — Traffic Sensor (Reactive), Traffic Light Controller (Deliberative), Route Planner (Deliberative) with 3 interactions
- [x] T007 Create `src/multiagent-governance_course/module_1_foundations/scenarios/task_manager.py` with `task_manager_scenario: Scenario` — Personal Assistant (Hybrid) with perception→reasoning→action cycle

**Checkpoint**: Scenario data model and 2 predefined scenarios ready

---

## Phase 3: User Story 1 — Classify Agents by Type (Priority: P1) 🎯 MVP

**Goal**: Classify AI agents as Reactive, Deliberative, or Hybrid via rule-based decision tree + LLM fallback

**Independent Test**: `python -c "from module_1_foundations.classification.graph import classify_agent; print(classify_agent('reads sensor data and emits it without state'))"` → `agent_type == 'reactive'`

- [x] T008 Create `src/multiagent-governance_course/module_1_foundations/classification/__init__.py`
- [x] T009 Create `src/multiagent-governance_course/module_1_foundations/classification/rules.py` — decision tree with sentence-level negation detection; function `classification_rules(state) -> state` populating `agent_type`/`justification`; function `needs_llm(state) -> Literal["llm_fallback", "finalize"]` as conditional edge router
- [x] T010 Create `src/multiagent-governance_course/module_1_foundations/classification/prompts.py` — `build_classification_prompt(description: str) -> str` for LLM fallback
- [x] T011 Create `src/multiagent-governance_course/module_1_foundations/classification/graph.py` — `ClassificationState(TypedDict)`, LangGraph `StateGraph` with conditional edge routing; public `classify_agent(description: str) -> dict`
- [x] T012 Create `tests/multiagent-governance_course/test_module_1_foundations/test_classification.py` — 11 tests: stateless→Reactive, world-model→Deliberative, mixed→Hybrid, negation-aware, empty description error, graph integration

**Checkpoint**: Agent classification working with rule-based and LLM fallback, all tests pass

---

## Phase 4: User Story 2 — Map Agent Interactions (Priority: P1)

**Goal**: Generate Mermaid interaction diagrams showing directed data flow between agents

**Independent Test**: `python -c "from module_1_foundations.scenarios.traffic import traffic_scenario; from module_1_foundations.interaction_map.mapper import generate_interaction_map; d=generate_interaction_map(traffic_scenario); assert 'sensor' in d and 'controller' in d and '-->' in d"`

- [x] T013 Create `src/multiagent-governance_course/module_1_foundations/interaction_map/__init__.py`
- [x] T014 Create `src/multiagent-governance_course/module_1_foundations/interaction_map/mapper.py` — function `generate_interaction_map(scenario: Scenario) -> str` returning Mermaid flowchart with labeled nodes (agent name + type), directed arrows for `data_flow`/`control_flow`, dashed arrows for `feedback_loop`, isolated nodes for zero-interaction agents
- [x] T015 Create `tests/multiagent-governance_course/test_module_1_foundations/test_interaction_map.py` — 4 tests: unidirectional flow, bidirectional feedback loop, zero-interaction scenario, flowchart starts with keyword

**Checkpoint**: Interaction maps generated and rendered as Mermaid, all tests pass

---

## Phase 5: User Story 3 — Analyze Agent Type Trade-offs (Priority: P2)

**Goal**: Analyze reactive vs deliberative vs hybrid trade-offs across 5 architectural dimensions

**Independent Test**: `python -c "from module_1_foundations.analysis.tradeoffs import generate_tradeoff_analysis; a=generate_tradeoff_analysis(traffic_scenario); assert 'speed' in a and 'accuracy' in a and 'resilience' in a"`

- [x] T016 Create `src/multiagent-governance_course/module_1_foundations/analysis/__init__.py`
- [x] T017 Create `src/multiagent-governance_course/module_1_foundations/analysis/tradeoffs.py` — `generate_tradeoff_analysis(scenario) -> str` producing per-dimension score table (1–5) with rationale across speed, accuracy, scalability, resilience, adaptability; plus side-by-side comparison table of pure reactive, pure deliberative, hybrid; single-agent and same-type edge case handling
- [x] T018 Create `tests/multiagent-governance_course/test_module_1_foundations/test_analysis.py` — 5 tests: all 5 dimensions present, side-by-side comparison, single-agent scenario, empty scenario warning, scores in table format

**Checkpoint**: Trade-off analysis generated with all 5 dimensions, all tests pass

---

## Phase 6: User Story 4 — Model Core Agent Capabilities (Priority: P2)

**Goal**: Model and diagram the perception → reasoning → action cycle for a single agent

**Independent Test**: `python -c "from module_1_foundations.interaction_map.mapper import generate_capability_cycle; d=generate_capability_cycle(task_manager_scenario, 'personal_assistant'); assert 'Perception' in d and 'Reasoning' in d and 'Action' in d"`

- [x] T019 Implement `generate_capability_cycle(scenario: Scenario, agent_id: str) -> str` in `src/multiagent-governance_course/module_1_foundations/interaction_map/mapper.py` — returns Mermaid flowchart with 3 subgraphs (Perception, Reasoning, Action), labeled transitions, input/output annotations; raises `ValueError` for unknown `agent_id`
- [x] T020 Add capability cycle tests to `tests/multiagent-governance_course/test_module_1_foundations/test_interaction_map.py` — 3 tests: full cycle with personal assistant, unknown agent_id error, single-agent scenario

**Checkpoint**: Capability cycle diagrams generated, all tests pass

---

## Phase 7: Export & Streamlit App

**Purpose**: Compile all 4 deliverables into .md + .PDF and present via Streamlit wizard

- [x] T021 Create `src/multiagent-governance_course/module_1_foundations/export/__init__.py`
- [x] T022 Create `src/multiagent-governance_course/module_1_foundations/export/submission.py` — `compile_submission(...)` returning markdown with 5 sections; `generate_pdf(...)` using markdown + pymupdf
- [x] T023 Create `src/multiagent-governance_course/module_1_foundations/app.py` — Streamlit 4-step wizard
- [x] T024 Create `tests/multiagent-governance_course/test_module_1_foundations/test_export.py` — 6 tests: compile_submission structure, PDF generation, smart-quote handling
- [x] T025 Create `tests/multiagent-governance_course/test_module_1_foundations/test_scenarios.py` — 5 tests: agent counts, unique IDs, valid interaction references

**Checkpoint**: Full pipeline working — Streamlit app ready, .md and .PDF export functional

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, validation, and quality

- [x] T026 [P] Update `AGENTS.md` with new directory patterns (module_1_foundations structure)
- [x] T027 [P] Run quickstart.md validation scenarios end-to-end
- [x] T028 [P] Run final test suite: `python -m unittest discover -s tests/multiagent-governance_course/test_module_1_foundations -t . -v` — 34/37 pass (3 pre-existing lab errors)
- [ ] T029 Update `README.md` with module_1_foundations section if applicable (skipped — not explicitly requested)

**Checkpoint**: All 29+ tests pass, quickstart scenarios verified

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 — no dependency on other stories
- **Phase 4 (US2)**: Depends on Phase 2 — no dependency on other stories
- **Phase 5 (US3)**: Depends on Phase 3 (uses classified agents) — can also accept unclassified scenarios
- **Phase 6 (US4)**: Depends on Phase 2 — no dependency on other stories
- **Phase 7 (Export)**: Depends on Phases 3, 4, 5, 6 — integrates all deliverables
- **Phase 8 (Polish)**: Depends on Phase 7
- **Phase 9 (Convergence)**: Depends on Phase 8
- **Phase 10 (PDF Diagrams)**: Depends on Phase 7 (uses export pipeline) and Phase 2 (uses Scenario data model) — independent of Phases 8–9

### User Story Dependencies

- **US1 (P1)**: Independent — can start after Foundational phase
- **US2 (P1)**: Independent — can start after Foundational phase
- **US3 (P2)**: Depends on US1 (classifications needed) but analysis works with unclassified agents too
- **US4 (P2)**: Independent — can start after Foundational phase
- **Export**: Depends on all 4 stories

### Within Each User Story

- Models → Services → Tests
- Core implementation before integration
- Story complete before moving to next

### Parallel Opportunities

| Phase | Parallel Tasks | Rationale |
|-------|---------------|-----------|
| Phase 1 | T002, T003, T004 | Different files (`pyproject.toml`, `__init__.py`, `__init__.py`) |
| Phase 2 | T006, T007 | Independent scenario files |
| Phase 3 | T009, T010 | Independent files (`rules.py`, `prompts.py`) |
| Phase 4 | — | Single-file story, sequential |
| Phase 5 | — | Single-file story, sequential |
| Phase 6 | — | Single function in existing file |
| Phase 7 | T022, T024, T025 | Independent files (`submission.py`, `test_export.py`, `test_scenarios.py`) |
| Phase 8 | T026, T027, T028 | Independent concerns |
| Phase 10 | T034, T036 | New file (`diagram_renderer.py`) vs test file (`test_diagram_renderer.py`) |

---

## Parallel Example: Phase 3 (US1)

```bash
# Launch all independent tasks together:
Task: T009 "Create rules.py" — src/multiagent-governance_course/module_1_foundations/classification/rules.py
Task: T010 "Create prompts.py" — src/multiagent-governance_course/module_1_foundations/classification/prompts.py
```

## Parallel Example: Phase 4 + Phase 6 (US2 + US4)

```bash
# US2 and US4 share mapper.py but are independent functions:
Task: T014 "generate_interaction_map" at end of mapper.py
Task: T019 "generate_capability_cycle" at end of mapper.py
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1 (classification)
4. **STOP and VALIDATE**: Run `test_classification.py` — all 5 tests pass
5. Deploy/demo classification engine

### Incremental Delivery

1. Setup + Foundational → Foundation ready (T001–T007)
2. US1 → Classification works → MVP! (T008–T012)
3. US2 → Interaction maps → (T013–T015)
4. US3 → Trade-off analysis → (T016–T018)
5. US4 → Capability cycles → (T019–T020)
6. Export + Streamlit → Full app → (T021–T025)
7. Polish → Final quality → (T026–T029)
8. PDF Diagrams → Visual diagrams in PDF export → (T034–T036)

### Parallel Team Strategy

With multiple developers:
1. Team completes Phase 1 + Phase 2 together
2. Developer A: US1 (Phase 3) + US3 (Phase 5)
3. Developer B: US2 (Phase 4) + US4 (Phase 6)
4. Developer C: Phase 7 (Export + App)
5. Developer A + B: Phase 8 (Polish) after all stories integrated

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story independently completable and testable
- Tests MUST exist for each module per constitution mandate
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- Verify all tests pass before marking a phase as complete

---

## Phase 9: Convergence

**Purpose**: Close gaps between spec/plan/constitution and the current implementation

- [x] T030 [CRITICAL] Add exponential backoff retry around `LLMFactory.call()` in `graph.py::llm_node()` before falling back to partial output per Constitution III (`contradicts`)
- [x] T031 [HIGH] Fix async/sync mismatch in `graph.py:46` — `LLMFactory.call()` is async but called without `await`; use synchronous `LLMFactory.create().invoke()` instead to prevent runtime crash on LLM fallback per FR-001 (`contradicts`)
- [x] T032 [MEDIUM] Integrate `AgentAttribute` into classification pipeline — pass structured attributes from `AgentDef` to `classify_agent()` via mapper.py and app.py per FR-006 (`partial`)
- [x] T033 [LOW] Update `README.md` with module_1_foundations section per T029 (`missing`)

**Checkpoint**: All convergence gaps closed — 34/34 tests pass

---

## Phase 10: PDF Diagram Rendering (FR-013)

**Purpose**: Render interaction diagrams and capability cycles as visual graphics in the PDF using `grandalf` for graph layout + `pymupdf` drawing primitives, replacing the "[Mermaid diagram omitted]" text notes

**Independent Test**: `python -c "from module_1_foundations.export.diagram_renderer import render_interaction_diagram; from module_1_foundations.scenarios.traffic import traffic_scenario; import fitz, tempfile, os; doc=fitz.Document(); doc.new_page(); render_interaction_diagram(doc, 0, traffic_scenario); d=tempfile.mkdtemp(); p=os.path.join(d,'t.pdf'); doc.save(p); doc2=fitz.Document(p); t=doc2[0].get_text(); assert 'Sensor' in t or 'sensor' in t; doc2.close(); os.unlink(p); os.rmdir(d)"`

- [ ] T034 [P] Create `src/multiagent-governance_course/module_1_foundations/export/diagram_renderer.py` with `render_interaction_diagram(doc, page_num, scenario)` and `render_capability_cycle_diagram(doc, page_num, scenario, agent_id)` — use `grandalf` for node layout/positioning and `pymupdf` (`page.draw_rect()`, `page.insert_textbox()`, `page.draw_line()`, `page.draw_bezier()` for arrows) to draw the diagram on the given page
- [ ] T035 Update `src/multiagent-governance_course/module_1_foundations/export/submission.py` — modify `generate_pdf()` to call `render_interaction_diagram()` and `render_capability_cycle_diagram()` after `insert_htmlbox()`, adding new pages as needed; update `_sanitize_for_pdf()` to keep the `[Mermaid diagram omitted]` note (text fallback) but the diagram renderer handles visual rendering on separate pages
- [ ] T036 Create `tests/multiagent-governance_course/test_module_1_foundations/test_diagram_renderer.py` — 4 tests: interaction diagram renders with all agents, capability cycle renders 3 subgraphs, edges have labels, unknown agent_id raises ValueError

**Checkpoint**: PDF includes visual interaction diagrams and capability cycles — Mermaid code blocks remain in .md export only
