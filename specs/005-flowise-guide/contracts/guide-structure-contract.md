# Guide Structure Contract: Flowise Multi-Agent Course Guide

**Contract type**: Content/structure agreement for the deliverable `docs/flowise-course-end-project/README.md`.
**Version**: 1.0 | **Date**: 2026-08-06

This contract defines the mandatory sections, the verified node vocabulary, and the route table that the guide MUST contain. Any deviation requires updating this contract and re-checking the spec's FRs.

## 1. Document layout (mandatory sections in order)

1. **Overview** — assignment scenario (Future Gadgets Inc.), tools, learning objectives, and the four grading deliverables.
2. **Prerequisites** — running `docker-flowise-1`, access `http://localhost:3000`, an LLM credential, and the optional FAQ source file.
3. **Architecture sketch** — one orchestrator + three specialists with arrows.
4. **Part 1 — Specialist agents** — subsections: Product Agent, Order Agent, Promotions Agent; each with persona prompt guidance, node placement, and save naming.
5. **Part 2 — Orchestrator** — create orchestrator, add `Multi Prompt Chain`, add three `Prompt Retriever` routes (name/description), wire each route to a `Chatflow Tool` connected to the right specialist, and create the `Chatflow API` credential.
6. **Testing checklist** — three probe queries, one per intent, with expected route/target.
7. **Part 3 — Written deliverables** — structure/prompts for Deliverables 2, 3, 4 and the screenshot (Deliverable 1).
8. **Submission steps** — report PDF, Peer Review upload.
9. **Troubleshooting** — empty responses (check model/credential), wrong routing (tighten route descriptions).

## 2. Node vocabulary (verified against local Flowise source)

| Guide term | Flowise category | Verified source path | Usage |
|-----------|------------------|----------------------|-------|
| Multi Prompt Chain | Chains | `packages/components/nodes/chains/MultiPromptChain/MultiPromptChain.ts` | Router ("brain") |
| Prompt Retriever | Retrievers | `packages/components/nodes/retrievers/PromptRetriever/PromptRetriever.ts` | Defines route name/description/message |
| Chatflow Tool | Tools | `packages/components/nodes/tools/ChatflowTool/ChatflowTool.ts` | Links orchestrator → specialist |
| Chatflow API credential | Credentials | `packages/components/credentials/ChatflowApi.credential.ts` | Auth for Chatflow Tool |
| Chat Model nodes (e.g. ChatOpenAI, Deepseek, Groq) | Chat Models | `packages/components/nodes/chatmodels/` | Model provider |

The guide MUST NOT name any other routing/connection node as required.

## 3. Route table contract

| Route name | Assignment intent | Route description guidance |
|-----------|-------------------|----------------------------|
| `product_info` | Product features, specs, availability | "Routes questions about product features, details, or specifications" |
| `order_status` | Order location, ETA, delivery | "Routes questions about order tracking, shipping, or delivery dates" |
| `promotions` | Sales, discounts, special offers | "Routes questions about current sales, discounts, and special offers" |

Each `Prompt Retriever` MUST set `name` and `description` from this table; `systemMessage` defines the delegated persona/answer.

## 4. Governance & quality gates

- **G1**: No API key, model name, or provider-specific secret appears as a literal value anywhere in the guide.
- **G2**: Every node named in the guide maps to an entry in §2 above.
- **G3**: The guide covers all four deliverables of the assignment PDF.
- **G4**: The guide's testing section must include the three probe queries from §5 of the spec.
