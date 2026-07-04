# Data Model: Multi-Agent Research System

## Entity: ResearchRequest

The initial question or topic submitted by an analyst.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| topic | str | The research question or topic | Required, non-empty; max 500 chars |
| domain_tags | list[str] | Tags indicating relevant domains (e.g., "EV", "battery", "Southeast Asia") | Optional; if provided, at least 1 tag |
| constraints | dict | Optional filters: language, date_range, sources | Optional |
| status | enum | pending, active, completed, failed, needs_refinement | Default: pending |

**State transitions**: pending → active (when agents activated), active → completed/failed/needs_refinement

## Entity: Agent

A specialized research capability with a defined role.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| role | enum | web_research, data_analysis, trend_analysis, competitive_intelligence, synthesis | Required, one of five roles |
| execution_state | enum | idle, running, completed, failed, paused | Default: idle |
| input_requirements | list[str] | What this agent needs from other agents | Optional |
| findings | list[Finding] | Outputs produced by this agent | Starts empty |
| confidence | float | Aggregate confidence score for this agent's outputs | 0.0–1.0 |

## Entity: Finding

An atomic piece of information produced by an agent.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| id | str | Unique finding identifier | Auto-generated UUID |
| agent_role | str | Which agent produced this | Required |
| content | str | The finding text | Required, non-empty |
| source | str | Attribution (URL, dataset name, etc.) | Required |
| confidence | float | Confidence score (0.0–1.0) | Required, 0.0–1.0 |
| timestamp | datetime | When the finding was created | Auto-generated |
| provenance_chain | list[str] | IDs of findings this is derived from | Optional |
| cross_references | list[str] | IDs of related findings from other agents | Optional |

## Entity: Conflict

A detected contradiction between two or more findings.

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| finding_ids | list[str] | The conflicting findings | At least 2 |
| description | str | Description of the contradiction | Required |
| detected_at | datetime | When detected | Auto-generated |
| resolution_status | enum | unresolved, resolved, escalated | Default: unresolved |
| resolution_rationale | str | How the conflict was resolved | Optional |

## Entity: SharedState

The collaborative context accessible to all agents.

| Field | Type | Description |
|-------|------|-------------|
| request | ResearchRequest | The original research request |
| agent_outputs | dict[str, list[Finding]] | Per-agent findings, keyed by role |
| conflicts | list[Conflict] | Detected and resolved conflicts |
| cross_agent_insights | list[str] | Emergent connections found between agents |
| execution_metadata | dict | Workflow timing, retry counts, stop trigger reason |
| steering_instructions | list[SteeringInstruction] | Analyst mid-workflow interventions |

## Entity: SynthesisReport

The final output produced by the synthesis agent.

| Field | Type | Description |
|-------|------|-------------|
| sections | list[Section] | Narrative sections with attributed findings |
| cross_references | list[dict] | Explicit connections between different agent domains |
| conflict_disclosures | list[Conflict] | Conflicts that were unresolved and surfaced |
| provenance_trace | dict | Full mapping from every claim to source finding and agent |
| generated_at | datetime | When the report was finalized |

## Entity: SteeringInstruction

A refinement or redirection submitted by an analyst mid-workflow.

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
| event_type | enum | agent_latency, output_confidence, conflict_detected, failure, stop_triggered |
| agent_role | str | Which agent triggered this |
| value | float | Numeric value (latency ms, confidence score, etc.) |
| details | dict | Additional context |
| timestamp | datetime | When recorded |

## State Transitions

```
ResearchRequest:
  pending → active (on agent activation)
  active → completed (on synthesis finish)
  active → failed (on unrecoverable error)
  active → needs_refinement (on overly broad request)

Agent.execution_state:
  idle → running (on activation)
  running → completed (on finding production)
  running → failed (on error/timeout)
  running → paused (on steering instruction)
  paused → running (on resumed)

Conflict.resolution_status:
  unresolved → resolved (on re-investigation success)
  unresolved → escalated (on re-investigation failure)
```
