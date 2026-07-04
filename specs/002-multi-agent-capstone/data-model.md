# Data Model: Multi-Agent Capstone Project

## Entity: ResearchRequest

The business problem or question submitted as input.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| topic | str | The business problem or question | Required, 10-500 chars |
| domain_tags | list[str] | Industry/context tags (e.g., "fintech", "Southeast Asia") | Required, at least 1 for refinement to pass |
| constraints | dict | Optional: budget, time horizon, geographic focus | Optional |
| status | enum | pending, active, completed, failed, needs_refinement | Default: pending |

**State transitions**: pending → active (on validation pass), pending → needs_refinement (on validation fail), active → completed (on synthesis finish), active → failed (on unrecoverable error)

## Entity: Agent

A specialized analytical capability.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| role | enum | research, financial, market, risk, synthesis | Required, one of five |
| execution_state | enum | idle, running, completed, failed, bypassed | Default: idle |
| input_requirements | list[str] | Dependencies in terms of upstream roles | Optional |
| findings | list[Finding] | Outputs produced | Starts empty |
| confidence | float | Aggregate confidence for this agent's findings | 0.0–1.0 |
| failure_count | int | Consecutive failures (for circuit breaker) | Starts 0 |

## Entity: Finding

An atomic piece of analysis produced by an agent.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str | Unique identifier | Auto-generated UUID |
| agent_role | str | Which agent produced this | Required |
| content | str | The analysis text | Required, non-empty |
| source | str | Attribution (URL, dataset, model reasoning) | Required |
| confidence | float | Confidence score | Required, 0.0–1.0 |
| timestamp | datetime | When created | Auto-generated |
| provenance_chain | list[str] | IDs of findings this is derived from | Optional |
| cross_references | list[str] | IDs of related findings from other agents | Optional, populated post-coordination |
| dimension_tags | list[str] | Semantic dimensions this finding speaks to (e.g., "revenue", "risk", "growth") | Optional, used by conflict detection |

## Entity: Conflict

A detected contradiction between two or more findings.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| finding_ids | list[str] | Conflicting findings | At least 2 |
| dimension | str | The semantic dimension where conflict exists | Required |
| description | str | Nature of the contradiction | Required |
| detected_at | datetime | When detected | Auto-generated |
| resolution_status | enum | unresolved, resolved, escalated | Default: unresolved |
| resolution_rationale | str | How resolved or why escalated | Optional |
| resolution_method | str | rule-based, llm-judgment | Optional |

## Entity: SharedState

The collaborative context (top-level state schema).

| Field | Type | Description |
|-------|------|-------------|
| request | ResearchRequest | The original request |
| agent_outputs | dict[str, list[Finding]] | Per-agent findings, keyed by role |
| agent_states | dict[str, Agent] | Per-agent state including failure counts |
| conflicts | list[Conflict] | Detected and resolved conflicts |
| cross_agent_insights | list[str] | Emergent connections found between agents |
| execution_metadata | dict | Workflow timing, budget, stop reason, degraded_agents list |
| steering_instructions | list[SteeringInstruction] | Mid-workflow analyst inputs |
| report | SynthesisReport | Final output (null until synthesis completes) |
| messages | list | LangGraph message accumulator |
| telemetry_events | list[TelemetryEvent] | All recorded operational events |

## Entity: SynthesisReport

The final deliverable.

| Field | Type | Description |
|-------|------|-------------|
| sections | list[Section] | Narrative sections with attributed findings |
| cross_references | list[dict] | Connections between different agent domains |
| conflict_disclosures | list[Conflict] | Conflicts that remained unresolved |
| data_gaps | list[str] | Areas where agents were bypassed or produced no findings |
| provenance_trace | dict | Full mapping from claim → source finding → agent |
| generated_at | datetime | When finalized |

## Entity: SteeringInstruction

Mid-workflow analyst refinement.

| Field | Type | Description |
|-------|------|-------------|
| instruction_text | str | The steering input |
| target_agents | list[str] | Which agents should incorporate this |
| timestamp | datetime | When submitted |
| applied | bool | Whether the instruction was incorporated |

## Entity: TelemetryEvent

A recorded operational event.

| Field | Type | Description |
|-------|------|-------------|
| event_type | enum | agent_latency, output_confidence, conflict_detected, failure, stop_triggered, circuit_broken |
| agent_role | str | Which agent triggered this |
| value | float | Numeric value (latency ms, confidence, etc.) |
| details | dict | Additional context (error message, retry count) |
| timestamp | datetime | When recorded |

## State Transitions

```
ResearchRequest.status:
  pending → active (input validated)
  pending → needs_refinement (input too vague)
  active → completed (synthesis produced)
  active → failed (unrecoverable error)

Agent.execution_state:
  idle → running (activated by orchestrator)
  running → completed (findings produced)
  running → failed (error or empty output)
  failed → running (retry attempt via circuit breaker allowance)
  running → bypassed (circuit breaker trips after 3 consecutive failures)

Conflict.resolution_status:
  unresolved → resolved (LLM judgment or re-investigation)
  unresolved → escalated (cannot be resolved, surfaced transparently)
```
