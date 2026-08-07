# Quickstart: Sequential Multi-Agent Blog Workflow

**Date**: 2026-08-03 | **Feature**: 004-sequential-agent-blog-workflow

## Prerequisites

- Python 3.10+ via the project's Poetry environment.
- The repo's existing stack: langgraph, langchain + langchain-openai, pydantic, pydantic-settings, loguru. **No new installation required.**
- `POETRY` path that includes `src/` (and `src/multiagent-governance_course/`) so `module_2_multiagents` imports resolve.
- For real LLM runs: a `.env` with `LLM_PROVIDER` and `LLM_API_KEY`. For offline tests: no `.env` needed (nodes accept a stubbed callable).

## Setup

```bash
# Activate the Poetry environment
cd /path/to/langgraph-course
poetry shell

# Sanity-check imports resolve
python -c "from module_2_multiagents import run_pipeline; print('OK')"
```

## Validation Scenarios

### Scenario 1: End-to-end run with a stubbed LLM (deterministic, offline)

```bash
python - <<'PY'
from module_2_multiagents import run_pipeline

FAKE = {
    "outline": "- Point 1\n- Point 2\n- Point 3\n- Point 4\n- Point 5\n",
    "draft": "Para1 on the topic's claim.\n\nPara2 continuing from the outline.\n\nPara3 concluding.",
    "seo": "SEO Title Options:\n1) <T1>\n2) <T2>\n3) <T3>\nRelevant Keywords: k1, k2, k3, k4, k5",
}

def fake_llm(prompt: str) -> str:
    if "SEO Title Options" in prompt or "Relevant Keywords" in prompt:
        return FAKE["seo"]
    if "5-point bulleted outline" in prompt:
        return FAKE["outline"]
    if "write a short, engaging 3-paragraph blog post" in prompt:
        return FAKE["draft"]
    raise AssertionError("unexpected prompt not bound to a known node")

state = run_pipeline("The future of AI in marketing", llm=fake_llm)
assert state.processing_outcome == "full"
assert "- Point 1" in state.outline
assert "Para3" in state.draft
assert "k1" in state.seo_feedback
print("OK: linear chain produced outline -> draft -> seo_feedback")
PY
```

**Expected**: A `BlogState` with `processing_outcome == "full"` and non-empty `outline`, `draft`, `seo_feedback`.

### Scenario 2: Empty topic is rejected

```bash
python -c "
from module_2_multiagents import run_pipeline
try:
    run_pipeline('   ')
    print('FAIL: no error')
except ValueError as e:
    print('OK: ValueError raised ->', e)
"
```

**Expected**: `ValueError` is raised before any downstream node executes.

### Scenario 3: Communication-protocol analysis is in-range and valid

```bash
python - <<'PY'
from module_2_multiagents.export import build_analysis_doc, build_prompts_doc
md, n = build_analysis_doc()
print(n)            # expected: 150 <= n <= 200
assert 150 <= n <= 200, n
assert 'advantage' in md.lower() and 'limitation' in md.lower()
print(build_prompts_doc()[:200])
PY
```

**Expected**: The analysis length is within 150–200 words; the prompts document renders the three prompts + justifications.

### Scenario 4: CLI report for a real topic

Requires working `.env`.

```bash
poetry run python -m module_2_multiagents "The Future of AI in Marketing"
```

**Expected**: A printed report with `Research Outline` → `Article Draft` → `SEO Feedback` sections.

## Running Tests

```bash
# All module_2 tests
poetry run python -m unittest discover -s tests/multiagent-governance_course/test_module_2_multiagents -t . -V

# A single file
poetry run python -m unittest discover -s tests/multiagent-governance_course/test_module_2_multiagents -t . -p test_workflow.py -V
```

**Expected**: All tests pass (state, prompts, agents, workflow, export) — offline via the injected fake LLM.

## Deliverables Mapping (Submission)

| Lab deliverable | Produced by |
|-----------------|-------------|
| 1. Final Workflow Canvas (Flowise screenshot) | Manual in Flowise — the LangGraph graph here is the repr of the same chain |
| 2. Agent Prompt Engineering document | `module_2_multiagents.export.build_prompts_doc()` |
| 3. Communication Protocol Analysis | `module_2_multiagents.export.build_analysis_doc()` |

## Edge Cases to Verify

| Test | How to Verify |
|------|---------------|
| Empty/whitespace topic | `run_pipeline("   ")` raises `ValueError` |
| Researcher returns empty outline | Writer node errors → `processing_outcome == "partial"`, `error_records` non-empty, no downstream success |
| Analysis out of word range | `build_analysis_doc()` raises `ValueError` if 150–200 violated |
| Missing `.env` + no injected LLM | Node raises `APIError` → tagged `partial`, not a silent blank |
| Prompt placeholder mismatch | Any prompt lacking its single `{...}` placeholder → test failure (guards handoff) |