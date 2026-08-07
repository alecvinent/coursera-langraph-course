---

description: "Task list for Sequential Multi-Agent Blog Workflow implementation"
---

# Tasks: Sequential Multi-Agent Blog Workflow

**Input**: Design documents from `/specs/004-sequential-agent-blog-workflow/`

**Prerequisites**: plan.md (required), spec.md (user stories), research.md, data-model.md, contracts/workflow.md, quickstart.md

**Tests**: Included — the repo constitution mandates `unittest` coverage for every module under `src/` (Constitution V). The pipeline is offline-testable by injecting a fake LLM per research Decision 3.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- Source root: `src/multiagent-governance_course/module_2_multiagents/`
- Test root: `tests/multiagent-governance_course/test_module_2_multiagents/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Package scaffolding and project initialization

- [X] T001 Create package directory `src/multiagent-governance_course/module_2_multiagents/agents/`
- [X] T002 Create empty `__init__.py` for `src/multiagent-governance_course/module_2_multiagents/__init__.py` and `.../agents/__init__.py`
- [X] T003 Create test package `tests/multiagent-governance_course/test_module_2_multiagents/__init__.py`
- [X] T004 [P] Verify the developer source path resolves by running `poetry run python -c "import module_2_multiagents"`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core state + logging infrastructure that EVERY user story depends on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Define `BlogState` (pydantic `BaseModel`) and `ErrorRecord` (TypedDict) in `src/multiagent-governance_course/module_2_multiagents/state.py` per data-model.md — fields `topic`, `outline`, `draft`, `seo_feedback`, `processing_outcome`, `error_records`; empty `topic` raises `ValueError`
- [X] T006 Wire `loguru` logger configuration in `src/multiagent-governance_course/module_2_multiagents/__init__.py` following the repo's existing `langgraph_course.log` pattern so loggers are configured exactly once
- [X] T007 [P] Confirm `LLMFactory` is importable from `utils.llm` and `Settings` from the repo's `config.py`

**Checkpoint**: Foundation ready — user story implementation can now begin

---

## Phase 3: User Story 1 - Build and Run the Agent Chain (Priority: P1) 🎯 MVP

**Goal**: A strictly linear Researcher → Writer → SEO Analyst LangGraph pipeline that turns one topic into outline → draft → SEO feedback.

**Independent Test**: Run with a stubbed LLM and confirm `processing_outcome == "full"` with non-empty `outline`, `draft`, `seo_feedback`, and that draft reflects the outline and SEO references the draft (SC-002).

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [X] T008 [P] [US1] Unit test for `BlogState` validation in `tests/multiagent-governance_course/test_module_2_multiagents/test_state.py` (empty topic → ValueError; fields default to None)
- [X] T009 [P] [US1] Unit test for prompt templates in `tests/multiagent-governance_course/test_module_2_multiagents/test_prompts.py` (each prompt has exactly one `{placeholder}`: topic/outline/draft; writer & SEO prompts contain the handoff sentences)

### Implementation for User Story 1

- [X] T010 [P] [US1] Implement the three prompt constants `RESEARCHER_PROMPT` `{topic}`, `WRITER_PROMPT` `{outline}`, `SEO_PROMPT` `{draft}` in `src/multiagent-governance_course/module_2_multiagents/agents/prompts.py` per contracts/workflow.md §3 (writer expands each point; SEO references the draft; SEO returns "SEO Title Options:" + "Relevant Keywords:")
- [X] T011 [P] [US1] Implement `researcher_node(state) -> {"outline": ...}` in `src/multiagent-governance_course/module_2_multiagents/agents/researcher.py` using `state.topic`, calling `LLMFactory.create()` (or injected callable), capturing latency with `time.monotonic()` via `loguru`, and appending `ErrorRecord` + `processing_outcome="partial"` on failure
- [X] T012 [P] [US1] Implement `writer_node(state) -> {"draft": ...}` in `src/multiagent-governance_course/module_2_multiagents/agents/writer.py` reading `state.outline` with the same observability/error contract
- [X] T013 [P] [US1] Implement `seo_node(state) -> {"seo_feedback": ...}` in `src/multiagent-governance_course/module_2_multiagents/agents/seo.py` reading `state.draft` with the same observability/error contract
- [X] T014 [US1] Implement `build_workflow()` wiring `StateGraph(BlogState)` with nodes researcher → writer → seo → END (all unconditional `add_edge`, strictly linear) in `src/multiagent-governance_course/module_2_multiagents/workflow.py` (depends on T010–T013)
- [X] T015 [US1] Implement `run_pipeline(topic, *, llm=None) -> BlogState` in `src/multiagent-governance_course/module_2_multiagents/runtime.py` that raises `ValueError` on empty topic then `graph.invoke(BlogState(topic=topic))` (depends on T014)
- [X] T016 [US1] Wire public exports (`run_pipeline`, `build_workflow`) in `src/multiagent-governance_course/module_2_multiagents/__init__.py` and add a CLI entry `python -m module_2_multiagents "<topic>"` in `__main__.py`

**Checkpoint**: User Story 1 delivers a working linear pipeline — the core assignment (FR-001…FR-006, FR-009)

---

## Phase 4: User Story 2 - Capture and Submit Deliverables (Priority: P2)

**Goal**: Provide the lab's documentation deliverables: the exact prompt text + justification sentences (Deliverable 2) and a report combining the pipeline run.

**Independent Test**: `export.build_prompts_doc()` returns markdown containing all three prompts verbatim and exactly one justification sentence each referencing the consumed → produced artifact (FR-008, SC-004).

### Tests for User Story 2

- [X] T017 [P] [US2] Unit test `build_prompts_doc` in `tests/multiagent-governance_course/test_module_2_multiagents/test_export.py` — assert all three prompt texts present, each followed by one justification sentence naming its input→output conversion

### Implementation for User Story 2

- [X] T018 [US2] Implement `build_prompts_doc() -> str` in `src/multiagent-governance_course/module_2_multiagents/export.py` — renders the three prompts from `agents/prompts.py` each followed by one input→output justification sentence (depends on T010; reuses prompt templates so they never drift)

**Checkpoint**: US1 + US2 both independently functional

---

## Phase 5: User Story 3 - Reflect on Task Decomposition and Communication (Priority: P3)

**Goal**: Provide a 150–200 word written analysis of the Simple Sequential Chain as a communication protocol (one advantage + one limitation, plus the single most critical prompt-handoff consideration) — Deliverable 3.

**Independent Test**: `export.build_analysis_doc()` returns (markdown, word_count) with `150 <= word_count <= 200` and mentions one advantage and one limitation (FR-005 analysis, SC-005).

### Tests for User Story 3

- [X] T019 [P] [US3] Unit test `build_analysis_doc` in `tests/multiagent-governance_course/test_module_2_multiagents/test_export.py` — assert exported word count within 150–200 and that text contains an "advantage" and a "limitation" term

### Implementation for User Story 3

- [X] T020 [US3] Implement `build_analysis_doc(word_count=None) -> tuple[str, int]` in `src/multiagent-governance_course/module_2_multiagents/export.py` — 150–200 word reflection naming one advantage (e.g., predictability/no branching), one limitation (e.g., no feedback loop or single point of failure), and the most critical handoff decision (explicit, schema-stable output format); raise `ValueError` if the drafted text falls outside 150–200 words

**Checkpoint**: All user stories independently functional

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Repo-conformance and shared-quality improvements

- [ ] T021 [P] Add integration test `tests/multiagent-governance_course/test_module_2_multiagents/test_agents.py` covering researcher/writer/seo failure paths (empty upstream output → `processing_outcome=="partial"` + non-empty `error_records`)
- [ ] T022 Update the source tree diagram + deliverables mapping in the project `README.md` to include `module_2_multiagents/`
- [ ] T023 Run the full validation flow: `poetry run python -m unittest discover -s tests/multiagent-governance_course/test_module_2_multiagents -t . -v`
- [ ] T024 Run `poetry run ruff check src/multiagent-governance_course/module_2_multiagents tests/multiagent-governance_course/test_module_2_multiagents` and fix all findings (88-char Black-compatible line width)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **User Stories (Phase 3+)**: Depend on Foundational; then proceed in priority order (P1 → P2 → P3)
- **Polish (Phase N)**: Depends on all user stories

### User Story Dependencies

- **US1 (P1)**: After Foundational — no other story dependency; the MVP
- **US2 (P2)**: After Foundational; reuses US1's prompt templates (T018 depends on T010) but is independently testable
- **US3 (P3)**: After Foundational; independent reflection, test-only change to `test_export.py`

### Within Each User Story

- Tests written and FAIL first, then implementation
- State/prompts before nodes, nodes before graph wiring, graph before runtime façade
- Story complete before moving to next priority

### Parallel Opportunities

- T004, T007 (both check-only) run in parallel with scaffolding
- T008, T009 (US1 tests) run in parallel
- T010, T011, T012, T013 (prompts + 3 agent nodes) run in parallel
- T017 (US2 test), T019 (US3 test) run in parallel when those stories start

---

## Parallel Example: User Story 1

```bash
# First, launch pre-implementation tests together:
Task: "T008 [US1] BlogState validation test in test_state.py"
Task: "T009 [US1] Prompt template tests in test_prompts.py"

# Then, launch the four independent implementations together:
Task: "T010 [US1] prompts.py with the 3 templates"
Task: "T011 [US1] researcher.py node"
Task: "T012 [US1] writer.py node"
Task: "T013 [US1] seo.py node"

# Finally wire them into the graph:
Task: "T014 [US1] workflow.py linear StateGraph"
Task: "T015 [US1] runtime.py run_pipeline()"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1: Setup
2. Phase 2: Foundational (state.py + logging) — blocks everything
3. Phase 3: User Story 1 — linear pipeline with fake-LLM tests offline
4. **STOP and VALIDATE**: run US1 fake-LLM scenario from quickstart (Scenario 1) + `unittest` before adding documentation stories

### Incremental Delivery

1. Foundation ready (T001–T007)
2. US1 → linear pipeline → validate offline → MVP
3. US2 → `build_prompts_doc` → validate word/structure tests
4. US3 → `build_analysis_doc` → validate 150–200 word analysis
5. Polish → README + ruff + full suite

### Parallel Team Strategy

1. Team completes Setup + Foundational together
2. Once done: Dev A on US1 nodes, Dev B on US1 wiring/runtime, then Dev A on US2 (needs prompts), Dev C on US3
3. Stories integrate independently before the final single-suite run

---

## Notes

- [P] tasks = different files, no dependencies
- [US#] label maps each task to a user story for traceability
- Each user story is independently completable and testable
- Verify tests fail before implementing
- Manual Flowise canvas screenshot (lab deliverable 1) is NOT a code task — it is done by the learner in Flowise; the LangGraph graph here mirrors the same Simple Sequential Chain (see quickstart.md deliverables mapping)
- Avoid cross-story file conflicts: `export.py` is shared only by US2 (adds build_prompts_doc) then US3 (adds build_analysis_doc), applied sequentially, not in parallel