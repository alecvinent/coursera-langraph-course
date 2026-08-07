---

description: "Task list for implementing the Flowise Multi-Agent Course Guide"
---

# Tasks: Flowise Multi-Agent Course Guide

**Input**: Design documents from `/specs/005-flowise-guide/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/guide-structure-contract.md, quickstart.md

**Tests**: The specification does not request automated tests and this feature is a documentation artifact. Manual verification tasks are included per section in place of automated tests.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single deliverable**: `docs/flowise-course-end-project/README.md` (the guide itself)
- **Reference source of truth** (read-only): `C:\working\projects\ai-projects\Flowise\packages\components\nodes\...` (local Flowise checkout)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare the destination directory and validate the environment assumptions the guide depends on.

- [X] T001 Create the guide directory `docs/flowise-course-end-project/` and an empty `README.md` in the repository
- [X] T002 Verify the Flowise container is running and healthy (expect `docker ps --filter "name=flowise"` → `docker-flowise-1`, image `flowiseai/flowise:3.1.3`, UI at `http://localhost:3000`)
- [X] T003 [P] Confirm node availability in the Flowise source checkout: `Multi Prompt Chain` exists at `C:\working\projects\ai-projects\Flowise\packages\components\nodes\chains\MultiPromptChain\MultiPromptChain.ts`
- [X] T004 [P] Confirm `Prompt Retriever` exists at `C:\working\projects\ai-projects\Flowise\packages\components\nodes\retrievers\PromptRetriever\PromptRetriever.ts` and note its three input fields (Prompt Name, Prompt Description, Prompt System Message)
- [X] T005 [P] Confirm `Chatflow Tool` exists at `C:\working\projects\ai-projects\Flowise\packages\components\nodes\tools\ChatflowTool\ChatflowTool.ts` and that it requires the `Chatflow API` credential (`C:\working\projects\ai-projects\Flowise\packages\components\credentials\ChatflowApi.credential.ts`)

**Checkpoint**: Directory created and all environment assumptions verified against the running container and local source.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the document skeleton, scope framing, and verified node vocabulary that every user story section reuses.

**⚠️ CRITICAL**: No user story section may be drafted until the skeleton and vocabulary are fixed.

- [X] T006 Write the guide front matter in `docs/flowise-course-end-project/README.md`: title, overview of the "Designing an Autonomous E-commerce Support Crew" assignment (Future Gadgets Inc.), tools (Flowise, text editor), and the four learning objectives
- [X] T007 Write the **Prerequisites** section in `docs/flowise-course-end-project/README.md`: running `docker-flowise-1`, access at `http://localhost:3000`, an LLM provider credential (created in the Flowise UI, provider-agnostic), optional product FAQ text file
- [X] T008 Write the **Architecture sketch** section in `docs/flowise-course-end-project/README.md`: one orchestrator + three specialists (Product, Order Status, Promotions) with routing arrows
- [X] T009 Add the **Node vocabulary table** in `docs/flowise-course-end-project/README.md` mapping guide terms to Flowise categories and sections (Multi Prompt Chain → Chains, Prompt Retriever → Retrievers, Chatflow Tool → Tools, Chatflow API credential → Credentials), with a compatibility note that the assignment PDF calls the connection node "Chatflow"

**Checkpoint**: Foundation ready — document skeleton, prerequisites, and node vocabulary are fixed; user story sections can now be drafted.

---

## Phase 3: User Story 1 - Build the Three Specialist Agent Chatflows (Priority: P1) 🎯 MVP

**Goal**: The guide's Part 1 teaches the learner to create, configure, and save the Product Agent, Order Agent, and Promotions Agent chatflows.

**Independent Test**: A reader following only this section can create three named chatflows, each returning a coherent on-topic answer to its matching probe question in its own chat canvas.

### Implementation for User Story 1

- [X] T010 [US1] Write the **Product Agent** subsection in `docs/flowise-course-end-project/README.md`: LLM Chain + chat model with a product-expert persona prompt, optional advanced path (Document Loader with product FAQ text file), save as "Product Agent"
- [X] T011 [US1] Write the **Order Agent** subsection in `docs/flowise-course-end-project/README.md`: prompt explaining the function, asking for an order number, simulated static delivery estimate (e.g., 3-5 business days), save as "Order Agent"
- [X] T012 [US1] Write the **Promotions Agent** subsection in `docs/flowise-course-end-project/README.md`: sales-assistant persona prompt stating a fictional sale (e.g., 20% off smartwatches), save as "Promotions Agent"
- [X] T013 [US1] Add a per-agent quick test note in `docs/flowise-course-end-project/README.md`: opening each chatflow's chat canvas and sending one matching probe to confirm on-topic responses

**Checkpoint**: At this point, User Story 1 is complete — the guide teaches all three specialist chatflows, each independently testable.

---

## Phase 4: User Story 2 - Building the Central Orchestrator (Priority: P1)

**Goal**: The guide's Part 2 teaches the learner to assemble the orchestrator with a routing node connected to the three specialist chatflows — the artifact required by Deliverable 1.

**Independent Test**: A reader following this section can build an orchestrator whose canvas shows the central routing node connected to the three specialist chatflows, and whose chat dispatches three probe intents to the correct specialists.

### Implementation for User Story 2

- [X] T014 [US2] Write the **Create the orchestrator** subsection in `docs/flowise-course-end-project/README.md`: new primary chatflow as the user's single point of contact
- [X] T015 [US2] Write the **Add the router node** subsection in `docs/flowise-course-end-project/README.md`: add `Multi Prompt Chain` (Chains) as the orchestrator's "brain", noting the DEPRECATING badge in 3.x and that it remains the assignment-intended node
- [X] T016 [US2] Write the **Define routing logic** subsection in `docs/flowise-course-end-project/README.md`: add three `Prompt Retriever` rows with route table from contracts (name `product_info`/`order_status`/`promotions` + route descriptions + target system messages)
- [X] T017 [US2] Write the **Create the Chatflow API credential** subsection in `docs/flowise-course-end-project/README.md`: Credentials → Chatflow API → generate key, then attach to each `Chatflow Tool`
- [X] T018 [US2] Write the **Connect the specialist agents** subsection in `docs/flowise-course-end-project/README.md`: add three `Chatflow Tool` nodes, each configured with the selected specialist chatflow, wired to the router so the canvas shows orchestrator → three specialists
- [X] T019 [US2] Write the **Testing checklist** in `docs/flowise-course-end-project/README.md`: the three probe queries (product specs/availability, order # + ETA, promotions) with expected route and target specialist (spec SC-004)

**Checkpoint**: At this point, User Stories 1 AND 2 both work independently — the guide covers the full buildable system and the Deliverable 1 screenshot.

---

## Phase 5: User Story 3 - Draft the Four Written Deliverables (Priority: P3)

**Goal**: The guide's Part 3 gives the learner chapter structures and prompts to author the four deliverables and produce the submission report PDF.

**Independent Test**: A reader following this section can produce a single PDF report containing the architecture screenshot and the three written deliverables with the required word counts.

### Implementation for User Story 3

- [X] T020 [US3] Write the **Deliverable 1** guidance in `docs/flowise-course-end-project/README.md`: full-screen PNG/JPG/JPEG screenshot of the orchestrator canvas showing the central routing node and its ≥3 specialist connections
- [X] T021 [US3] Write the **Deliverable 2** structure in `docs/flowise-course-end-project/README.md`: 150-200 word design methodology (purpose of each specialist + justification of the three routing descriptions)
- [X] T022 [US3] Write the **Deliverable 3** structure in `docs/flowise-course-end-project/README.md`: 200-300 word risk & governance analysis with ≥2 risks (e.g., incorrect info, sensitive data, hallucinations) each with one mitigation
- [X] T023 [US3] Write the **Deliverable 4** structure in `docs/flowise-course-end-project/README.md`: 250-word reflection on approach and insights
- [X] T024 [US3] Write the **Report compilation & sharing** section in `docs/flowise-course-end-project/README.md`: compile the four deliverables into a single PDF, upload to the course "Peer Review" area with a brief description

**Checkpoint**: All user stories complete — the guide covers building the system and authoring/submitting all four deliverables.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cross-cutting quality gates that affect the whole guide.

- [X] T025 Add a **Troubleshooting** section in `docs/flowise-course-end-project/README.md`: empty responses (check model/credential), wrong routing (tighten route descriptions), "node not found" (version-specific naming)
- [X] T026 Scan `docs/flowise-course-end-project/README.md` to confirm no literal API keys, model names, or provider secrets appear (contract gate G1)
- [X] T027 Cross-check every node named in `docs/flowise-course-end-project/README.md` against the vocabulary table and section 2 of `specs/005-flowise-guide/contracts/guide-structure-contract.md` (gate G2)
- [X] T028 Confirm `docs/flowise-course-end-project/README.md` covers all four assignment deliverables (gate G3) and includes the three probe queries (gate G4)
- [ ] T029 [P] Run the `specs/005-flowise-guide/quickstart.md` acceptance steps manually against the running instance and record the outcome
- [X] T030 Update the repository `README.md` to reference the new guide under `docs/flowise-course-end-project/` (per AGENTS.md documentation-sync convention)

**Checkpoint**: Guide is complete, validated against the contracts, and linked from the repository README.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Sequential order required here: US1 → US2 → US3, because the guide is a single document and Part 2 references the chatflows built in Part 1
- **Polish (Final Phase)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — no dependencies on other stories
- **User Story 2 (P1)**: Depends on US1 sections existing (references "Product Agent", "Order Agent", "Promotions Agent" created in Part 1)
- **User Story 3 (P3)**: Depends on US2 sections existing (references the built orchestrator for the screenshot)

### Within Each User Story

- Skeleton and vocabulary (Phase 2) before section drafting
- Each story section drafted completely before moving to the next priority

### Parallel Opportunities

- All Setup verification tasks (T003, T004, T005) are marked [P] and can run in parallel — they inspect different read-only source files
- Tasks within a story that touch different subsections can be authored in any order, but edit the same file `docs/flowise-course-end-project/README.md`, so sequential commits are recommended to avoid conflicts
- The reference-source verification tasks (T003–T005) can run while the document skeleton (T006–T009) is being written

---

## Parallel Example: Phase 1 verification

```bash
# Launch all node-verification tasks together (read-only, different files):
Task: "Confirm Multi Prompt Chain at .../chains/MultiPromptChain/MultiPromptChain.ts"
Task: "Confirm Prompt Retriever at .../retrievers/PromptRetriever/PromptRetriever.ts"
Task: "Confirm Chatflow Tool at .../tools/ChatflowTool/ChatflowTool.ts and ChatflowApi credential"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (directory + environment verification)
2. Complete Phase 2: Foundational (skeleton + prerequisites + vocabulary) — CRITICAL
3. Complete Phase 3: User Story 1 (specialist agent sections)
4. **STOP and VALIDATE**: A reader can build and test the three specialist chatflows
5. Demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → guide skeleton with verified vocabulary
2. Add User Story 1 → validate specialist sections → deliver (MVP)
3. Add User Story 2 → validate orchestrator sections → deliver
4. Add User Story 3 → validate deliverables sections → deliver
5. Each story adds a complete, independently testable part of the guide

### Parallel Team Strategy

With multiple writers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Writer A: User Story 1 (specialist sections)
   - Writer B: waits for US1 (or drafts Deliverable structures independently in a scratch file, then merges)
   - Writer C: runs contract gate checks (T026–T028) against the fixed vocabulary
3. Sections integrate into the single document sequentially

---

## Notes

- [P] tasks = different files, no dependencies (applies to the read-only verification tasks)
- [Story] label maps task to specific user story for traceability
- The guide is a single Markdown file; prefer sequential edits within a story to avoid same-file conflicts
- Verify environment assumptions (T002–T005) before drafting any section
- Commit after each task or logical group
- Stop at any checkpoint to validate the story independently
- Avoid: vague tasks, same-file concurrent edits, cross-story content that breaks the narrative order
