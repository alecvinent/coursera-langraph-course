# Quickstart: Flowise Multi-Agent Course Guide

**Phase 1 output** for `/specs/005-flowise-guide/plan.md`. Generated 2026-08-06.

This is the validation/run guide for the deliverable `docs/flowise-course-end-project/README.md` (the step-by-step tutorial). It documents how to verify the guide is complete and how a learner proves the built system works end-to-end. It is NOT the tutorial itself.

## Prerequisites to validate the guide

- Local Flowise running: container `docker-flowise-1` (image `flowiseai/flowise:3.1.3`).
- UI reachable: `http://localhost:3000` (verify container: `docker ps --filter "name=flowise"` shows `healthy`).
- An LLM provider credential available in the instance (created via Flowise UI — provider-agnostic).
- (Optional) a `FAQ` text file for the advanced Product Agent path.

## Validating the guide document

1. Open `docs/flowise-course-end-project/README.md`.
2. Confirm all sections in the [guide structure contract](./contracts/guide-structure-contract.md) §1 are present and in order.
3. Confirm every node named matches the contract §2 vocabulary (no invented node names).
4. Confirm no literal API keys / model names / provider secrets appear (contract §4 G1).
5. Confirm all four assignment deliverables are represented.

## End-to-end run the guide teaches (acceptance)

Follow the guide through the Flowise UI:

1. **Part 1 — Specialists**: create **Product Agent**, **Order Agent**, **Promotions Agent**; each with an LLM Chain and a chat model. Save each under its clean name.
2. **Part 2 — Orchestrator**: create **Orchestrator** chatflow; add `Multi Prompt Chain`; add three `Prompt Retriever` rows with the route table (`product_info`, `order_status`, `promotions`); create the `Chatflow API` credential; add three `Chatflow Tool` nodes, each wired to the correct specialist chatflow.
3. **Probe** from the orchestrator's chat canvas (three intents): `/quickstart` below.

## Probe queries and expected outcomes (SC-002 / SC-004)

| # | Probe query | Expected route | Expected target & signal |
|---|-------------|----------------|--------------------------|
| 1 | "Does the X2000 drone have a 4K camera and is it in stock?" | `product_info` | Product Agent; on-topic specs/availability (or acknowledgement if it only has persona) |
| 2 | "Where is my order #58291 and when will it arrive?" | `order_status` | Order Agent; asks for/acknowledges order number, simulated delivery estimate (3-5 business days) |
| 3 | "Are there any promotions or discounts right now?" | `promotions` | Promotions Agent; states the fictional sale (e.g., 20% off smartwatches) |

**Pass criteria**: Each probe returns an on-topic response **from the correct specialist** (visible via router/LLM output or by the persona of the answer), 100% of the time — spec SC-004.

## Deliverables produced after following the guide

1. **Deliverable 1**: full-screen `PNG/JPG/JPEG` screenshot of the Orchestrator canvas showing the central router node (`Multi Prompt Chain`) and its connections to the three `Chatflow Tool`/specialist chatflows (spec SC-003).
2. **Deliverable 2**: 150–200 word methodology (purpose of each specialist + justification of the three route descriptions).
3. **Deliverable 3**: 200–300 word risk & governance analysis, ≥2 risks each with one mitigation.
4. **Deliverable 4**: 250-word reflection.

## Metrics to confirm

- Learner can create the three specialist chatflows in **under 40 minutes** (SC-001).
- Orchard‑: orchestrator canvas shows one central routing node connected to ≥3 specialists (SC-003).
- Three probes route correctly 100% of the time (SC-004).
- Guide covers all four deliverables; report compiles as a single PDF (SC-005).
- Guide is self-contained — no external how-to material needed beyond the assignment (SC-006).

## Links

- Guide structure contract: [`contracts/guide-structure-contract.md`](./contracts/guide-structure-contract.md)
- System concepts/entities: [`data-model.md`](./data-model.md)
- Design decisions: [`research.md`](./research.md)