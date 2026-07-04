# API Contracts: Capstone Project

## User-Facing Interface

### Submit Business Problem

```
Submit: topic, domain_tags?, constraints?, max_execution_minutes?
Return: ResearchState (after execution completes or refinement halts)
```

**Usage** (sync):
```python
from langgraph_course.module_4.labs.capstone.graph import run_capstone

state = run_capstone(
    topic="What is the market opportunity for fintech in Southeast Asia?",
    domain_tags=["fintech", "Southeast Asia"],
    max_execution_minutes=15,
)
```

**Usage** (streaming — for live UI):
```python
from langgraph_course.module_4.labs.capstone.graph import stream_capstone

for node_name, state in stream_capstone(
    topic="What is the market opportunity for fintech in Southeast Asia?",
    domain_tags=["fintech", "Southeast Asia"],
    max_execution_minutes=15,
):
    print(node_name, len(state.agent_outputs))  # progressive state
```

### Interpret Results

```python
# Final report
report = state.report
report.sections          # list[dict] with attributed findings
report.conflict_disclosures  # unresolved conflicts
report.data_gaps         # agents that were bypassed or produced no findings
report.provenance_trace  # claim → source → agent mapping

# Per-agent contributions
state.agent_outputs      # { agent_role: [Finding, ...] }
state.agent_states       # { agent_role: Agent } — includes failure_count, execution_state

# Telemetry
state.telemetry_events   # [TelemetryEvent, ...] — latency, confidence, failures, circuit breaks
```

### Refinement Handling

If the system determines the input is too broad:

```python
state = run_capstone(topic="AI")       # too short, no tags
state.request.status                   # "needs_refinement"
# Caller should prompt user to add detail or domain_tags, then resubmit
```

## Operations-Facing Interface (Internal)

### Telemetry Access

```python
for event in state.telemetry_events:
    print(f"{event.agent_role}: {event.event_type.value} = {event.value}")
```

### Inspect Workflow Status

```python
state.execution_metadata
# {
#     "workflow_start": monotonic_seconds,
#     "max_execution_minutes": 15,
#     "degraded_agents": [],        # roles that were circuit-broken
#     "stop_reason": "all_complete",
#     "round": 2,
# }
```

### Inspect Agent Health

```python
for role, agent_state in state.agent_states.items():
    print(f"{role}: {agent_state.execution_state.value}, failures={agent_state.failure_count}")
```
