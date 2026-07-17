# Data Model: Agent Ecosystem Mapping

**Date**: 2026-07-17 | **Feature**: 003-agent-ecosystem-mapping

## Overview

Core entities for the Agent Ecosystem Mapping feature. All entities are Pydantic `BaseModel` classes defined in `src/multiagent-governance_course/module_1_foundations/scenarios/base.py` (and inline in classifier/mapper modules where they are used solely within that module).

---

## Entity: AgentDef

**Location**: `scenarios/base.py` | **Purpose**: Describes a single agent in a scenario

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique identifier (e.g., `"sensor_01"`) |
| `name` | `str` | Yes | Human-readable name (e.g., `"Traffic Sensor"`) |
| `description` | `str` | Yes | Natural-language description of role and behavior |
| `attributes` | `list[AgentAttribute]` | Yes | Traits used for classification |

**Validation**:
- `id` must be non-empty and match `^[a-z][a-z0-9_]*$`
- `name` must be non-empty and ≤ 80 chars
- `attributes` must contain at least one entry

---

## Entity: AgentAttribute

**Location**: `scenarios/base.py` | **Purpose**: Measurable characteristic used for agent type classification

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | `str` | Yes | Attribute name (e.g., `"internal_state"`, `"planning_horizon"`) |
| `value` | `str` | Yes | Attribute value (e.g., `"none"`, `"long_term"`) |
| `description` | `str` | No | Optional clarification of the attribute |

**Valid attribute names** (canonical set):
- `internal_state` — presence/absence of state persistence
- `planning_horizon` — `none`, `short_term`, `long_term`
- `memory` — `none`, `short_term`, `long_term`
- `decision_logic` — `if_then`, `utility`, `rule_based`, `learned`
- `adaptability` — `none`, `low`, `medium`, `high`
- `sensing` — `direct`, `indirect`, `both`

---

## Entity: InteractionDef

**Location**: `scenarios/base.py` | **Purpose**: Directed relationship between two agents

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source` | `str` | Yes | Agent ID of the source |
| `target` | `str` | Yes | Agent ID of the target |
| `label` | `str` | Yes | Data/control flow description (e.g., `"sends sensor readings"`) |
| `type` | `InteractionType` | Yes | Enum: `data_flow`, `control_flow`, `feedback_loop` |

**Validation**:
- `source` and `target` must reference existing AgentDef IDs
- `source` != `target` (no self-loops)
- `type` must be a member of `InteractionType` enum

---

## Entity: InteractionType (Enum)

**Location**: `scenarios/base.py` | **Values**: `data_flow`, `control_flow`, `feedback_loop`

---

## Entity: AgentType (Enum)

**Location**: `classification/` | **Values**: `reactive`, `deliberative`, `hybrid`

---

## Entity: AgentClassification

**Location**: `classification/` | **Purpose**: Output of the classification engine

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `agent_id` | `str` | Yes | Reference to classified AgentDef |
| `agent_type` | `AgentType` | Yes | Classified type |
| `justification` | `str` | Yes | Natural-language explanation referencing agent attributes |
| `confidence` | `float` | No | Optional confidence score (0.0–1.0) |
| `processing_outcome` | `str` | No | `"full"` or `"partial"` |
| `method` | `str` | No | `"rule_based"` or `"llm"` |

---

## Entity: Scenario

**Location**: `scenarios/base.py` | **Purpose**: Contextual container for a group of agents

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | `str` | Yes | Unique scenario ID |
| `name` | `str` | Yes | Display name |
| `description` | `str` | Yes | Narrative context |
| `agents` | `list[AgentDef]` | Yes | Agents in the scenario |
| `interactions` | `list[InteractionDef]` | Yes | Relations between agents |

**Predefined instances**: `traffic_control` (Activity 1), `personal_task_manager` (Activity 2)

---

## Entity: TradeoffAnalysis

**Location**: `analysis/tradeoffs.py` | **Purpose**: Output of trade-off analysis

| Field | Type | Description |
|-------|------|-------------|
| `dimensions` | `dict[str, DimensionScore]` | Scores per dimension (speed, accuracy, scalability, resilience, adaptability) |
| `comparison` | `ComparisonView` | Side-by-side table of pure reactive, pure deliberative, hybrid |

---

## Entity: DimensionScore (TypedDict)

**Location**: `analysis/tradeoffs.py` | **Fields**: `reactive_score`, `deliberative_score`, `hybrid_score` (all `int` 0–5), `rationale` (`str`)

---

## Entity: ErrorRecord (TypedDict)

**Location**: `module_1_foundations/__init__.py` | **Purpose**: Structured error tracking

| Field | Type | Description |
|-------|------|-------------|
| `step` | `str` | Node or function name where error occurred |
| `error_type` | `str` | Error class name |
| `message` | `str` | Error message |
| `timestamp` | `str` | ISO-8601 timestamp |

---

## State Transitions

The classification workflow follows a linear pipeline:

```
[Input Description] → [Attribute Extraction] → [Rule-Based Classification]
                                                        ↓
                                             (ambiguous? → LLM Fallback)
                                                        ↓
                                              [ Final Classification ]
```

No branching or multi-cycle state machine — each classification is stateless and independent.
