# Quickstart: Multi-Agent Research System

## Prerequisites

- Python 3.10+
- Poetry installed
- LLM API key configured (via `.env` per project convention)

## Setup

```bash
poetry install
```

## Validation Scenarios

### Scenario 1: Basic research request → synthesized report

**Goal**: Verify that a research request produces a multi-agent report.

```bash
poetry run python -c "
from langgraph_course.module_3.labs.multi_agent_research.graph import run_research

result = run_research(topic='EV battery market in Southeast Asia')
print('Report sections:', len(result.report.sections) if result.report else 0)
print('Agent contributions:', {role: len(fs) for role, fs in result.agent_outputs.items()})
"
```

**Expected**: Report has at least 1 section; at least 2 agents contributed findings.

### Scenario 2: Conflict detection via Streamlit (visual)

**Goal**: Verify the Steamlit UI shows the research system.

```bash
poetry run streamlit run streamlit_app.py
```

1. Select **"🧠 Multi-Agent Research"** from sidebar
2. Enter a research topic (e.g., "EV battery market in Southeast Asia")
3. Wait for completion (shows spinner during execution)
4. Expand **"📊 Per-Agent Contributions"**, **"⚡ Conflicts Detected"**, **"🏷️ Provenance Trace"**

**Expected**: Report renders with expandable detail sections showing individual agent findings, conflicts, and provenance.

### Scenario 3: Running tests

**Goal**: Verify all unit tests pass.

```bash
poetry run python -m unittest discover -v tests/module_3/test_multi_agent_research/
```

**Expected**: All tests pass (some may skip if no LLM API key configured).

### Scenario 4: Budget enforcement

**Goal**: Verify workflow terminates within the configured budget.

```bash
poetry run python -c "
import time
from langgraph_course.module_3.labs.multi_agent_research.graph import run_research

start = time.time()
result = run_research(topic='Broad research topic', max_execution_minutes=1)
elapsed = time.time() - start
print('Elapsed minutes:', elapsed / 60)
print('Status:', result.request.status.value)
"
```

**Expected**: Execution completes within ~1.5 minutes; status is `completed`.

## Running Tests

```bash
poetry run python -m unittest discover -v tests/module_3/test_multi_agent_research/
```

## Key Contracts

- Agent interfaces: [contracts/agent-interfaces.md](contracts/agent-interfaces.md)
- API contracts: [contracts/api-contracts.md](contracts/api-contracts.md)
- Data model: [data-model.md](data-model.md)
