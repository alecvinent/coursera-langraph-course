# Contract: Sequential Blog Workflow

**Date**: 2026-08-03 | **Feature**: 004-sequential-agent-blog-workflow

This document defines the interface contracts for the `module_2_multiagents` package. It covers (1) the graph/CLI entry contract, (2) the per-node contract, (3) the prompt-handoff contract, and (4) the export contract. Consumers are: the `runtime.py` façade, the three agent node functions, and `export.py`.

---

## 1. Pipeline Entry Contract

**Public API**: `run_pipeline(topic: str, *, llm: Callable[..., str] | None = None) -> BlogState`

| Aspect | Contract |
|--------|----------|
| Input | A single non-empty topic string |
| Behavior | Builds the graph (or reuses a compiled instance), invokes `graph.invoke(BlogState(topic=topic))` |
| Output | A fully populated `BlogState` (outline, draft, seo_feedback) or one tagged `processing_outcome="partial"` with `error_records` on failure |
| Error | Raises `ValueError` on empty/whitespace topic (no downstream execution) |
| `llm` param | Optional injectable callable; when omitted, production `LLMFactory` is used for each node |

**CLI**: `python -m module_2_multiagents "<topic>"` prints the three-stage artifacts as a readable report.

---

## 2. Node Contract

Each agent node is a plain function `fn(state: BlogState) -> dict[str, object]` registered as a LangGraph node.

| Node | Reads | Writes | Returns on success | Returns on failure |
|------|-------|--------|--------------------|--------------------|
| `researcher_node` | `state.topic` | `state.outline` | `{"outline": "..."}` | `{"processing_outcome": "partial", "error_records": [ErrorRecord]}` |
| `writer_node` | `state.outline` | `state.draft` | `{"draft": "..."}` | same partial shape |
| `seo_node` | `state.draft` | `state.seo_feedback` | `{"seo_feedback": "..."}` | same partial shape |

**Invariant**: A node must never return the field it did not produce; downstream reads must always be non-empty. Node latency MUST be captured with `time.monotonic()` and logged via `loguru` (plain functions, not classmethods).

**Graph wiring**: `StateGraph(BlogState)` → `add_node` ×3 → `add_edge(start, researcher)` → `researcher → writer` → `writer → seo` → `seo → END`. Strictly linear; no conditional edges.

---

## 3. Prompt-Handoff Contract

Prompt templates live in `agents/prompts.py` and are plain f-strings with **exactly one** `{placeholder}` each, matching the consuming node's input field:

| Prompt | Placeholder | Binds to | Output contract |
|--------|-------------|----------|-----------------|
| `RESEARCHER_PROMPT` | `{topic}` | `state.topic` | A 5-point bulleted outline, markdown `-` bullets |
| `WRITER_PROMPT` | `{outline}` | `state.outline` | A 3-paragraph article draft; each paragraph expands an outline point |
| `SEO_PROMPT` | `{draft}` | `state.draft` | "SEO Title Options:" (3 numbered) + "Relevant Keywords:" (5 comma-separated) |

**Handoff rule**: The writer prompt MUST explicitly instruct the model to "expand each outline point into a paragraph so the draft preserves the researcher's structure"; the SEO prompt MUST instruct the model to "reference the article's content" so SEO feedback demonstrably derives from the draft. These sentences are what guarantee the SC-002 information-flow property and are quoted verbatim in the export document.

---

## 4. Export Contract

`export.py` exposes two pure functions:

| Function | Signature | Output |
|----------|-----------|--------|
| `build_prompts_doc() -> str` | () → markdown | Exact text of the 3 prompts + one justification sentence per prompt ("it converts `<input>` into `<output>` for the next agent") |
| `build_analysis_doc(word_count: int | None = None) -> tuple[str, int]` | () → (markdown, word count) | 150–200 word communication-protocol analysis; returns count for validation |

**Word-count rule**: The analysis body must be within **150–200 words**. If the generated text falls outside that range, `build_analysis_doc` must raise `ValueError` (fail fast) so tests catch drift.

---

## 5. Configuration Contract

- All model/provider/api-key values come from the repo's `Settings` (pydantic-settings) via `.env`; never hardcoded.
- LLM instances are created exclusively through `LLMFactory.create(provider=settings.llm_provider)` — direct model instantiation is forbidden.
- The package `__init__.py` imports the repo's `loguru` configuration (existing `langgraph_course.log` wiring) so loggers are configured exactly once.