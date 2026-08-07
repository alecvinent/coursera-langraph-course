# Implementation Plan: Flowise Multi-Agent Course Guide

**Branch**: `005-flowise-guide` | **Date**: 2026-08-06 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/005-flowise-guide/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Create a step-by-step guide (Markdown document) that walks a learner through building the Course-end Project "Designing an Autonomous E-commerce Support Crew" (Future Gadgets Inc.) on a local Flowise instance. The instance runs in Docker as container `docker-flowise-1` (image `flowiseai/flowise:3.1.3`, reachable at `http://localhost:3000`), with the Flowise source checkout at `C:\working\projects\ai-projects\Flowise` used as the source of truth for node names, categories, and configuration.

The guide covers: (1) Part 1 — creating three specialist chatflows (Product Agent, Order Agent, Promotions Agent); (2) Part 2 — building the central orchestrator with a `Multi Prompt Chain` router node fed by three `Prompt Retriever` nodes, each route delegated via a `Chatflow Tool` that calls the corresponding specialist chatflow; (3) Part 3 — the four written deliverables for submission, plus how to capture the grading screenshot and produce the report PDF.

## Technical Context

**Language/Version**: Markdown (guide artifact). No application code is produced. Flowise instance version `3.1.3` (confirmed from running container `docker-flowise-1`).

**Primary Dependencies**: None new — guide documents existing Flowise nodes present in the local checkout: `Multi Prompt Chain` (`packages/components/nodes/chains/MultiPromptChain/MultiPromptChain.ts`), `Prompt Retriever` (`packages/components/nodes/retrievers/PromptRetriever/PromptRetriever.ts`), `Chatflow Tool` (`packages/components/nodes/tools/ChatflowTool/ChatflowTool.ts`), credential `Chatflow API` (`packages/components/credentials/ChatflowApi.credential.ts`), and chat model nodes (ChatOpenAI, Deepseek, Groq, etc.).

**Storage**: N/A for the guide itself. The Flowise instance persists chatflows in PostgreSQL (`docker-flowise-1` env: `DATABASE_HOST=host.docker.internal`, `DATABASE_TYPE=postgres`, `DATABASE_NAME=flowise`). The guide references this only as context, not as a build target.

**Testing**: Manual validation checklist inside the guide (three probe queries, one per intent) plus a quickstart acceptance run. No automated tests apply to a documentation artifact; the checklist items in `checklists/requirements.md` validate spec quality.

**Target Platform**: Web UI of local Flowise (`http://localhost:3000`); guide rendered as Markdown (GitHub-style).

**Project Type**: Documentation / step-by-step tutorial.

**Performance Goals**: N/A (documentation). Learner success metric: a learner can create the three specialist chatflows in under 40 minutes and route three probe intents correctly.

**Constraints**: Guide MUST use real node labels/categories verified against the local Flowise source checkout (no invented node names). MUST NOT hardcode API keys or model names; instructs creating a credential in the Flowise UI instead. MUST map exactly to the assignment PDF's four deliverables.

**Scale/Scope**: One guide document. Scope boundary: chatflows only — no production backend, DB integration, or chat widget embedding unless the assignment requires it (it does not).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. LangGraph Architecture Patterns | N/A | Feature is a documentation guide for the Flowise platform; no LangGraph code is produced. No graph code to constrain. |
| II. Configuration-Driven Design | PASS | Guide instructs creating an LLM credential in the Flowise UI; no keys are committed. No `.env`/`config.py` changes needed. |
| III. Observability By Default | N/A | No runtime code; observability requirements do not apply to a Markdown artifact. |
| IV. LLM Abstraction Layer | N/A | No Python LLM code. The guide references Flowise chat-model nodes, not `LLMFactory`. |
| V. Test Discipline | PASS | No new source modules under `src/`; no unit tests required. Manual validation checklist documents expected outcomes. |
| VI. Dependency Discipline | PASS | Zero new dependencies. Documented artifacts only. |

**Gate evaluation**: No violations. All constitution principles either PASS or are N/A for a documentation feature. No Complexity Tracking entries required.

**Post-design re-check** (after Phase 1): Confirmed the design introduces no `src/` code (no LangGraph, no LLMFactory, no logging, no tests needed), requires zero new dependencies, and hardcodes no credentials (guide instructs UI-based credential creation). Constitution status unchanged — still no violations.

## Project Structure

### Documentation (this feature)

```text
specs/005-flowise-guide/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

This feature produces **no application source code**. The only artifact is the guide document, delivered in this repo. The guide is written at:

```text
docs/flowise-course-end-project/
└── README.md            # The step-by-step guide (single Markdown document)
```

**Structure Decision**: The guide is a single Markdown document under `docs/` in this repository. It references the Flowise source checkout at `C:\working\projects\ai-projects\Flowise` as the source of truth for node names and configuration, but the guide itself lives with the course repo so it remains under the repo's documentation convention and version control. No `src/` modules, no `tests/` modules, no dependency changes.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations. Section intentionally empty.
