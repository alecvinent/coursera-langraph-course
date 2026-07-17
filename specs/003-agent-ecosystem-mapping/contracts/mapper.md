# Contract: Interaction Map & Capability Cycle

## Module
`module_1_foundations.interaction_map.mapper`

### `generate_interaction_map(scenario: Scenario) -> str`

Returns a Mermaid flowchart string from a `Scenario` object.

**Input**: `Scenario` with `agents` and `interactions`
**Output**: Mermaid syntax string:
```mermaid
flowchart LR
    sensor["Traffic Sensor<br><i>Reactive</i>"]
    controller["Traffic Light Controller<br><i>Deliberative</i>"]
    planner["Route Planner<br><i>Deliberative</i>"]

    sensor -->|sends sensor readings| controller
    controller -->|transmits traffic data| planner
    planner -.->|provides route recommendations| controller
```

**Edge Cases**:
- Zero interactions → returns flowchart with isolated agent nodes (no arrows)
- Unidirectional → single solid arrow (`-->`)
- Bidirectional / feedback loops → dashed arrow (`-.->`) with `feedback_loop` label

---

### `generate_capability_cycle(scenario: Scenario, agent_id: str) -> str`

Returns a Mermaid flowchart string modeling the perception → reasoning → action cycle for a specific agent.

**Input**: `Scenario`, `agent_id` (must reference an agent in the scenario)
**Output**: Mermaid flowchart with subgraphs for each phase:
```mermaid
flowchart LR
    subgraph Perception
        P1["Receive weather alert"] --> P2["Check calendar conflicts"]
    end
    subgraph Reasoning
        R1["Evaluate alternatives"] --> R2["Select best action"]
    end
    subgraph Action
        A1["Update calendar entry"] --> A2["Send notifications"]
    end
    P2 --> R1
    R2 --> A1
```

**Edge Cases**:
- Unknown `agent_id` → raises `ValueError`
- Agent with no scenario context → raises `ValueError`
