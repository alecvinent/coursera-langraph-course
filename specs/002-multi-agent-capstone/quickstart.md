# Quickstart: Multi-Agent Capstone Project

## Prerequisites

- Python 3.10+
- Poetry installed
- LLM API key configured (`.env` — project standard)
- This project's dependencies installed (`poetry install`)

## Validation Scenarios

### Scenario 1: Full workflow — business problem → synthesized report

**Goal**: Verify all 5 agents execute and produce a cross-referenced report.

```bash
poetry run python -c "
from langgraph_course.module_4.labs.capstone.graph import run_capstone

state = run_capstone(
    topic='Market opportunity for fintech in Southeast Asia',
    domain_tags=['fintech', 'Southeast Asia'],
    max_execution_minutes=5,
)
report = state.report
print('Sections:', len(report.sections) if report else 0)
print('Agent outputs:', {r: len(fs) for r, fs in state.agent_outputs.items()})
print('Conflicts:', len(state.conflicts))
print('Data gaps:', report.data_gaps if report else [])
"
```

**Expected**: All 5 roles in agent_outputs; at least 1 section; report has cross_references and provenance_trace.

### Scenario 2: Input refinement — vague topic rejected

**Goal**: Verify FR-012 — overly broad inputs are rejected with refinement request.

```bash
poetry run python -c "
from langgraph_course.module_4.labs.capstone.graph import run_capstone

state = run_capstone(topic='AI', domain_tags=[])
print('Status:', state.request.status.value)
print('Expected: needs_refinement')
"
```

**Expected**: Status is `needs_refinement`; no agents executed.

### Scenario 3: Graceful degradation — circuit breaker on agent failure

**Goal**: Verify FR-014 / FR-008 — a failing agent is bypassed and the rest continue.

```bash
poetry run python -c "
from langgraph_course.module_4.labs.capstone.graph import run_capstone

# Force failure via a constraint recognized by the graph (implementation-specific test hook)
state = run_capstone(
    topic='Test circuit breaker behavior',
    domain_tags=['test'],
    constraints={'simulate_failure_roles': ['financial']},
    max_execution_minutes=2,
)
print('Degraded agents:', state.execution_metadata.get('degraded_agents', []))
print('Report data gaps:', state.report.data_gaps if state.report else [])
print('Other agents produced output:', len(state.agent_outputs) > 0)
"
```

**Expected**: `financial` appears in degraded_agents; other agents still produced findings; report includes data gaps section.

### Scenario 4: Conflict detection between agents

**Goal**: Verify FR-009 — contradictory findings are detected and surfaced.

```bash
poetry run python -c "
from langgraph_course.module_4.labs.capstone.graph import run_capstone

# Use constraints to seed findings that create a known contradiction (implementation-specific test hook)
state = run_capstone(
    topic='Growth projections for EVs in 2025',
    domain_tags=['EV', 'automotive'],
    constraints={'seed_conflicts': True},
    max_execution_minutes=3,
)
if state.conflicts:
    print('Conflicts detected:', len(state.conflicts))
    for c in state.conflicts:
        print(f'  - {c.description} | status={c.resolution_status.value}')
else:
    print('No conflicts detected (acceptable if agents agreed)')
"
```

**Expected**: Either conflicts are detected and resolved/escalated, or agents produced consistent findings (both valid outcomes).

### Scenario 5: Execution budget enforcement

**Goal**: Verify FR-011 — workflow terminates within configured budget.

```bash
poetry run python -c "
import time
from langgraph_course.module_4.labs.capstone.graph import run_capstone

start = time.time()
state = run_capstone(
    topic='Broad topic that requires iteration',
    domain_tags=['general'],
    max_execution_minutes=1,   # very tight budget
)
elapsed = time.time() - start
print(f'Elapsed: {elapsed:.1f}s  Expected < 90s')
print(f'Stop reason: {state.execution_metadata.get(\"stop_reason\", \"unknown\")}')
print(f'Status: {state.request.status.value}')
"
```

**Expected**: Completion within ~90 seconds; stop_reason is "max_budget".

## Running Tests

```bash
poetry run python -m unittest discover -v tests/module_4/test_capstone/
```

**Expected**: All tests pass. Tests requiring LLM API may skip gracefully.

## Key Contracts

- Agent interfaces: [contracts/agent-interfaces.md](contracts/agent-interfaces.md)
- API contracts: [contracts/api-contracts.md](contracts/api-contracts.md)
- Data model: [data-model.md](data-model.md)
