# Data Model: Sequential Multi-Agent Blog Workflow

**Date**: 2026-08-03 | **Feature**: 004-sequential-agent-blog-workflow

## Overview

Entities for the Module 2 "Mastering Sequential Agent Workflows" lab. All structs are pydantic `BaseModel` classes defined in `src/multiagent-governance_course/module_2_multiagents/state.py`. The single carrier structure is `BlogState`, which is the LangGraph state schema passed through the linear chain. The four pipeline artifacts (`Topic` → `Outline` → `ArticleDraft` → `SeoFeedback`) are fields on `BlogState`.

---

## Entity: BlogState

**Location**: `module_2_multiagents/state.py` | **Purpose**: The LangGraph state schema and the only data container passed between nodes

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | `str` | Yes | The single user-provided topic seeding the chain (FR-001) |
| `outline` | `str \| None` | No | Researcher output — structured bulleted outline (≥ 5 points) |
| `draft` | `str \| None` | No | Writer output — multi-paragraph article built from the outline |
| `seo_feedback` | `str \| None` | No | SEO Analyst output — title options + keywords derived from draft |
| `processing_outcome` | `str` | No | `"full"` or `"partial"` (Constitution III degraded-output tag) |
| `error_records` | `list[ErrorRecord]` | No | Accumulated structured errors across nodes |

**Validation**:
- `topic` must be non-empty (raise `ValueError` on empty/whitespace).
- `outline` is set by the Researcher node only; non-empty when present.
- `draft` is set by the Writer node only; non-empty when present.
- `seo_feedback` is set by the SEO Analyst node only; non-empty when present.
- Supports `.model_dump()` for serialization; immutable values (no message reducer needed).

---

## Entity: Agenda / Pipeline artifacts

The three intermediate artifacts are simply string fields on `BlogState` whose downstream node consumes the prior node's field:

| Artifact | Field | Produced By | Consumed By | Requirement |
|----------|-------|-------------|-------------|-------------|
| Research outline | `outline` | Researcher | Writer | FR-002, FR-003 |
| Article draft | `draft` | Writer | SEO Analyst | FR-003, FR-004 |
| SEO feedback | `seo_feedback` | SEO Analyst | — (terminal) | FR-004, FR-009 |

---

## Entity: ErrorRecord (TypedDict)

**Location**: `module_2_multiagents/__init__.py` | **Purpose**: Structured error tracking (Constitution III)

| Field | Type | Description |
|-------|------|-------------|
| `step` | `str` | Node/function name where the error occurred |
| `error_type` | `str` | Error class name (e.g., `"APIError"`, `"ValueError"`) |
| `message` | `str` | Error message |
| `timestamp` | `str` | ISO-8601 timestamp |

---

## Entity: NodeResult (internal)

**Location**: `agents/*.py` | **Purpose**: Return contract of each agent node to the graph (a partial state update)

All three agent nodes return a partial dict of `BlogState` with exactly one new field set:
- `researcher_node(state) -> {"outline": [...]}`
- `writer_node(state) -> {"draft": [...]}`
- `seo_node(state) -> {"seo_feedback": [...]}`

On failure each node additionally returns `processing_outcome: "partial"` and appends an `ErrorRecord`.

---

## State Transitions

Single linear, one-way pipeline (no branching, no cycles, no feedback loop):

```
[ BlogState(topic) ]
        │  Researcher node
        ▼
 [ BlogState(topic, outline) ]
        │  Writer node (reads outline)
        ▼
 [ BlogState(topic, outline, draft) ]
        │  SEO Analyst node (reads draft)
        ▼
 [ BlogState(topic, outline, draft, seo_feedback) ]   ← terminal
```

No multi-cycle state machine. Each run is independent and stateless (no persistence).