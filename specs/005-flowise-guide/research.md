# Research: Flowise Multi-Agent Course Guide

**Phase 0 output** for `/specs/005-flowise-guide/plan.md`. Generated 2026-08-06.

## Unknowns resolved

### Decision 1 — Which Flowise node performs the routing

- **Decision**: Use the `Multi Prompt Chain` node (category **Chains**) as the orchestrator's "brain", fed by three `Prompt Retriever` nodes (category **Retrievers**) that define the route name, route description, and routing prompt.
- **Rationale**: The assignment PDF explicitly names "Multi Prompt Chain or a similar routing tool" from the Chains menu. Verified in the local Flowise source checkout: `packages/components/nodes/chains/MultiPromptChain/MultiPromptChain.ts` implements `Multi Prompt Chain` with a `Prompt Retriever` list input. Each `Prompt Retriever` (`packages/components/nodes/retrievers/PromptRetriever/PromptRetriever.ts`) holds `name`, `description`, and `systemMessage` — exactly matching the assignment's requested route names (`product_info`, `order_status`) and route descriptions.
- **Alternatives considered**: (a) `Conversational Agent` with tools for routing — capable but over-engineered for a course prototype and not what the assignment names; (b) a plain `LLM Chain` with a manual classification step — adds an extra manual hop and no explicit route table. Rejected both in favor of the assignment-mandated Multi Prompt Chain.

### Decision 2 — How the orchestrator calls the specialist agents

- **Decision**: Each orchestrator route delegates to the corresponding specialist chatflow through a `Chatflow Tool` node (category **Tools**), which invokes another saved chatflow by its selected chatflow ID. The `Chatflow Tool` requires a `Chatflow API` credential (a chatflow API key created in the Flowise UI) — see `packages/components/nodes/tools/ChatflowTool/ChatflowTool.ts` and `packages/components/credentials/ChatflowApi.credential.ts`.
- **Rationale**: The assignment's Part 2 step 4 says: "Use the Chatflow node in Flowise to link each route in your orchestrator to the corresponding specialist agent chatflow." The `Chatflow Tool` is the actual node that executes another chatflow and is the closest match to that instruction in Flowise 3.x. It lets the orchestrator stay visually simple: one router node, three tool nodes, each connected to a specialist chatflow.
- **Alternatives considered**: (a) The assignment's older "Chatflow" node — not present as such in the verified 3.1.3 source; (b) pasting each specialist's prompt directly into `Prompt Retriever` `systemMessage` — avoids extra chatflows but violates the assignment's explicit requirement to build and link separate chatflows. The `Chatflow Tool` keeps the three specialist chatflows as first-class, separately testable artifacts (required for Deliverable 1's screenshot).
- **Note**: The guide must document how to create the `Chatflow API` credential in the Flowise UI (Credentials → Add → Chatflow API → Generate Key), and where the key is scoped.

### Decision 3 — Which chat model the guide recommends

- **Decision**: The guide is provider-agnostic. It instructs the learner to create one chat-model node (e.g., `ChatOpenAI`, `Deepseek`, `Groq` — all confirmed present in `packages/components/nodes/chatmodels/`) and reuse it across the three specialist chatflows and the orchestrator, selecting a model name already available in their account.
- **Rationale**: The running container has no provider configured (`.env` exposes only PORT and DATABASE_*); credentials are created per-node in the Flowise UI. Hardcoding a model name would violate AGENTS.md ("No hardcoded values") and would break for learners without that provider.
- **Alternatives considered**: (a) Configuring an API key via the instance `.env` — requires editing container env and is outside the assignment's UI-driven workflow; (b) recommending a single provider (e.g., OpenAI) — reduces flexibility. Rejected both.

### Decision 4 — Where the guide lives and in what language

- **Decision**: The guide is delivered as `docs/flowise-course-end-project/README.md` in this repository, written in English (matching the assignment materials, which are in English), with Flowise UI labels kept verbatim.
- **Rationale**: The spec's FR-015 requires a single step-by-step Markdown document; the course repo's documentation convention places guides under `docs/`. The assignment PDF and all course content are in English.
- **Alternatives considered**: (a) Placing the guide inside the Flowise source checkout (`C:\working\projects\ai-projects\Flowise\docker`) — out of this repo's control and would mix course deliverables with the upstream repo; (b) writing in Spanish — consistent with user conversation but inconsistent with the English course materials. Rejected both.

### Decision 5 — How the assignment's "Chatflow" connection is named in the guide

- **Decision**: The guide names the connection node explicitly as **Chatflow Tool** (Flowise 3.x) and includes a compatibility note: older Flowise versions / the assignment PDF call this the "Chatflow" node; the underlying behavior (one chatflow invoking another) is the same.
- **Rationale**: FR-011 requires the final canvas to show the orchestrator connected to the three specialists. Verifying the real node name avoids the guide instructing the learner to search for a node that does not exist in the installed version.
- **Alternatives considered**: (a) Referring to it only as "Chatflow" per the PDF — risks the learner not finding it in 3.1.3; (b) omitting the node-level detail — would make the guide untestable. Rejected both.

## Dependencies / best practices

- **Node labels verified against local source checkout** (source of truth): `Multi Prompt Chain` (Chains), `Prompt Retriever` (Retrievers), `Chatflow Tool` (Tools), `Chatflow API` credential (Credentials), chat models under `Chat Models` category.
- **Running instance**: container `docker-flowise-1`, image `flowiseai/flowise:3.1.3`, healthcheck `GET /api/v1/ping`, UI at `http://localhost:3000` (port from `.env`/container env `PORT=3000`).
- **Assignment mapping**: four grading deliverables — (1) full-screen PNG/JPG/JPEG screenshot of orchestrator canvas showing router + ≥3 specialist connections; (2) 150–200 word design methodology (purpose of each specialist + justification of routing descriptions); (3) 200–300 word risk & governance analysis (≥2 risks, each with one mitigation); (4) 250-word reflection on approach and insights. Report compiled as a single PDF, shared in the course "Peer Review" area.

## Consolidation

- The guide's Part 1 builds three specialist chatflows (LLM Chain persona approach; optional advanced path: Document Loader with product FAQ text file for the Product Agent).
- Part 2 builds the orchestrator: `Multi Prompt Chain` + three `Prompt Retriever` routes + three `Chatflow Tool` connections to the specialist chatflows; test via the orchestrator's chat canvas.
- Part 3 produces the four deliverables and the report PDF.
- No code, no new dependencies, no config changes to the container. Manual validation only.
