# Research: Agent Ecosystem Mapping

**Date**: 2026-07-17 | **Feature**: 003-agent-ecosystem-mapping

## Overview

Technical decisions and trade-offs for the Agent Ecosystem Mapping feature, a Streamlit-based educational tool that classifies AI agents, maps interactions, analyzes trade-offs, and exports submissions for Coursera.

---

## Decisions

### Decision 1: Classification Engine — Rule-Based + LLM via LangGraph

- **Decision**: Hybrid approach: rule-based decision tree for unambiguous cases, LangGraph `StateGraph` with conditional edge routing to LLM fallback for ambiguous cases
- **Rationale**: Rule-based handles ~80% of cases (stateless→Reactive, world-model→Deliberative, mixed→Hybrid) instantly without network calls; LLM fallback catches edge cases where attributes conflict or language is nuanced; LangGraph provides inspectability via state records and future extensibility (add nodes/steps without restructuring)
- **Alternatives considered**:
  - Pure rule-based (no LLM): fails on ambiguous descriptions, poor learner experience
  - Pure LLM: expensive latency, unnecessary for simple cases, violates "offline-capable rule-based" constraint
  - Single LLM call with structured output: no offline mode, harder to trace decision path

### Decision 2: Interaction Map Output Format

- **Decision**: Mermaid.js flowchart syntax (```mermaid ... ```)
- **Rationale**: Natively rendered by GitHub, Coursera, and markdown viewers; no external image hosting; text-based so easy to diff and grade programmatically; supports subgraphs, arrow labels, feedback loops
- **Alternatives considered**:
  - SVG/PNG via matplotlib: binary output, not self-contained in .md, harder for AI graders to parse
  - PlantUML: requires server or Java runtime, less portable

### Decision 3: PDF Export Library

- **Decision**: markdown (parse md → HTML) + PyMuPDF (HTML → PDF via `page.insert_htmlbox()`)
- **Rationale**: PyMuPDF (fitz) is already in the project dependencies (`pymupdf ^1.27.2.3`). Its
  `page.insert_htmlbox()` method renders HTML with inline CSS directly into a PDF page, which
  covers our formatting needs (tables, bold, lists, headers). No new PDF library needed. Only
  `markdown` is added as a new dependency for md→HTML conversion (no existing dep provides
  markdown parsing).
- **Justification for `markdown`**: Existing dependencies (langchain, pymupdf, grandalf, etc.)
  do not include a markdown-to-HTML converter. Writing a custom parser that handles tables,
  fenced code blocks, nested lists, and inline formatting would require 300–500+ lines of
  fragile regex-based code with significant edge-case bugs. The `markdown` package is the
  de facto standard — pure Python, ~50KB, no binary dependencies.
- **Alternatives considered**:
  - fpdf2: new dependency, replaces PyMuPDF's existing PDF capability unnecessarily
  - WeasyPrint: large install (Cairo, Pango), complex Windows setup
  - ReportLab: lower-level, more code needed for tables/markdown rendering
  - pandoc: external binary, not pip-installable

### Decision 4: Streamlit Architecture

- **Decision**: Single `app.py` with 4-step wizard (tab/state-machine)
- **Rationale**: Streamlit's `st.session_state` and rerun model naturally support multi-step forms; single file keeps deployment simple (one `streamlit run app.py`); no need for FastAPI backend since computation is local and stateless
- **Alternatives considered**:
  - FastAPI + React frontend: overengineered for single-user educational tool
  - Jupyter Notebook: poor UX for non-technical learners, no PDF download built-in
  - Flask + Jinja: more boilerplate for interactive wizard flow

### Decision 5: Negation-Aware Keyword Matching

- **Decision**: Sentence-level negation detection — scan for "no", "not", "without", "lacks" within ±5 tokens of agent-type keywords before matching
- **Rationale**: Prevents false positives on negated phrases like "agent without internal state" matching "state" (which would wrongly suggest Deliberative); sentence parsing keeps complexity low vs full NLP pipeline
- **Alternatives considered**:
  - spaCy dependency parsing: heavy dependency (500MB+ models) for simple rule
  - Regex negation list: fragile across sentence boundaries

### Decision 7: PDF Diagram Rendering

- **Decision**: Use `grandalf` for graph layout (node positioning) + `pymupdf` drawing primitives (shapes, text, arrows) to render interaction diagrams and capability cycles as visual graphics inside the PDF, replacing the `<pre class="codehilite">` Mermaid code blocks that PyMuPDF's `insert_htmlbox()` cannot render when combined with tables and CSS
- **Rationale**: Both `grandalf` (graph layout) and `pymupdf` (PDF generation) are already in the approved dependency stack (Constitution VI). `grandalf` provides algorithmic node positioning (Sugiyama, Layer, etc.) so nodes don't overlap. `pymupdf` can draw rectangles, text labels, and arrows natively — no new external dependencies required. The Mermaid code blocks remain in the .md export (they render correctly in GitHub/Coursera markdown viewers).
- **Approach**: A new `render_diagram()` function in the export pipeline that takes the same parameters as the Mermaid generators, computes graph layout via `grandalf`, draws nodes as rounded rectangles with agent name + type, draws directed edges as lines/arrows with labels, and inserts the resulting shapes/text into the PDF page via `page.insert_textbox()` and `page.draw_rect()`/`page.draw_line()`.
- **Alternatives considered**:
  - Render Mermaid via CLI (`mmdc`): requires Node.js runtime, breaks offline use, not pip-installable
  - Python mermaid parser library: new external dependency needing justification, bloat for simple graphs
  - Keep `<pre>` blocks only: user request explicitly asks for visual diagrams in PDF
  - Use only `pymupdf` without `grandalf`: manual positioning works for fixed 3-node traffic graph but breaks for arbitrary topologies (capability cycle subgraphs, varied interaction counts)

- **Decision**: Pydantic `BaseModel` classes in `scenarios/` with `Scenario(name, description, agents: list[AgentDef], interactions: list[InteractionDef])`
- **Rationale**: Pydantic provides validation, serialization to dict, and IDE type hints; `AgentDef` and `InteractionDef` are simple TypedDicts for readability
- **Alternatives considered**:
  - JSON files: no validation, harder to maintain references
  - YAML files: extra dependency, no type safety
  - Dataclasses: no built-in serialization, no validation

---

## Unresolved Items

None — all NEEDS CLARIFICATION markers from the spec have been resolved in this document.

| Section | Resolution |
|---------|-----------|
| Language/Version | Python 3.10+ (locked by pyproject.toml) |
| Primary Dependencies | +markdown for md→HTML (justified — no existing dep provides markdown parsing); `pymupdf` already in deps for PDF |
| Testing | unittest (stdlib), not pytest — per constitution |
| Target Platform | Streamlit web (dev), CLI (tests) |
| Performance Goals | <1s rule-based, <15s LLM fallback, <500ms diagram gen, <2s export |
| Constraints | Offline rule-based, English-only, self-contained output |
| Scale/Scope | Single-user, 4 scenarios, 1 PDF per session |
