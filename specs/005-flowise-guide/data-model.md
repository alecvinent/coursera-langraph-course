# Data Model: Flowise Multi-Agent Course Guide

**Phase 1 output** for `/specs/005-flowise-guide/plan.md`. Generated 2026-08-06.

> **Note**: This feature is a step-by-step guide (documentation). The "data model" below is the *conceptual model of the system the guide teaches the learner to build* — the four chatflows, their roles, and the routing connections. There is no application database or code. Fields map to what the Flowise UI/node config exposes.

## Entities

### Specialist Agent (chatflow)
A self-contained Flowise chatflow that answers one category of support query. Three required per the assignment.

| Field | Type | Valid values / notes |
|-------|------|----------------------|
| displayName | string | Clean, distinctive name. **Product Agent**, **Order Agent**, **Promotions Agent** |
| persona | text | The system/prompt persona (product expert, shipping support, sales assistant) |
| model | chat-model node | Reused provider node (e.g. ChatOpenAI/Deepseek/Groq); non-hardcoded |
| queryCategory | enum | `product_info`, `order_status`, `promotions` |
| chatflowId | string (generated) | Flowise-generated ID used by the orchestrator's `Chatflow Tool` to invoke it |

Relationships:
- A Specialist is **invoked by** the Orchestrator via a `Chatflow Tool`.
- The Product Agent **may optionally read from** a Document Loader (advanced path, product FAQs text file).

### Orchestrator — chatflow
The primary chatflow, the user's single point of contact.

| Field | Type | Validated / notes |
|-------|------|--------------------|
| displayName | string | e.g. "Orchestrator Agent" |
| routerNode | node ref | `Multi Prompt Chain` node (the "brain") |
| model | chat-model reference | Shared chat model across the system |

Relationships: Orchestrator **contains** the Router; Orchestrator **connects to** each Specialist via `Chatflow Tool`.

### Route
A routing definition inside the `Multi Prompt Chain`, backed by a `Prompt Retriever`.

| Field | Type | Validated / notes |
|-------|------|--------------------|
| name | string | Short route id: `product_info`, `order_status`, `promotions` |
| description | string | Instructions telling the router when to choose this route |
| systemMessage | string | Prompt for the target agent outcome |
| target | `Chatflow Tool` | The connection to the Specialist chatflow |

Relationships: A Route **maps to** exactly one Specialist via a `Chatflow Tool`.

### Router (Multi Prompt Chain)
Analysis node that chooses among routes based on the user input.

- Inputs: `Language Model`, `Prompt Retriever[]` (three), optional `Input Moderation`.
- Behavior: knows Route `name` + `description` table and picks the best match.
- Badge note: `Multi Prompt Chain` is marked **DEPRECATING** in the verified source (`2.0`). Guide notes this and that it remains the assignment-mandated/intended node for the course prototype.

### Credential — Chatflow API
Required by each `Chatflow Tool`.

| Field | Type | Notes |
|-------|------|-------|
| chatflowApiKey | password | Generated in Flowise UI (Credentials → Chatflow API → generated key) |

## State transitions (conceptual)

```
User query
   → Orchestrator chatflow receives query
   → Router selects route (R_A/R_B/R_C) via name+description match
   → Chatflow Tool invokes chosen Specialist chatflow
   → Specialist returns answer back through orchestrator
```

## Validation rules (from spec requirements)
- Must have at least 3 specialists + 1 orchestrator (Deliverable 1).
- Each specialist produces a coherent on-topic answer for its queryCategory (SC-002).
- The orchestrator routes each query intent to the right specialist 100% of the time in testing (SC-004).
- No hardcoded API keys or model names in the guide (Constitution II).

## Configuration / state
- Not applicable, this is a Markdown guide. The Flowise data is durable in the instance's PostgreSQL on the Docker setup.