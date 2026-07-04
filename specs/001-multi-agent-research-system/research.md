# Research: Multi-Agent Research System

## Design Decisions

### Decision 1: Agent implementation strategy
- **Decision**: LangGraph StateGraph with typed state, each agent as a node function
- **Rationale**: The project already uses LangGraph; StateGraph is the idiomatic way to define stateful multi-node workflows with parallel/conditional edges. Typed state via pydantic ensures schema validation and IDE support.
- **Alternatives considered**: Custom async task queue (too much infrastructure), single LLM with tool-calling (loses agent specialization and provenance clarity)

### Decision 2: Shared state persistence
- **Decision**: LangGraph's built-in StateGraph with in-memory state for v1, with Checkpointer for optional persistence
- **Rationale**: In-memory is sufficient for the initial volume; LangGraph's Checkpoint API allows transparent addition of persistence later without restructuring.
- **Alternatives considered**: External database (over-engineered for v1), Redis (adds operational complexity)

### Decision 3: Parallel vs sequential execution model
- **Decision**: LangGraph fan-out pattern — agents that can run in parallel (web research, data analysis) fan out concurrently; sequential chaining where outputs feed into downstream agents
- **Rationale**: LangGraph's `Send` API supports dynamic parallel branching; conditional edges handle sequential dependencies.
- **Alternatives considered**: Fully sequential (too slow for SC-001), fully parallel (impossible — agents need each other's outputs)

### Decision 4: Conflict detection approach
- **Decision**: Structured comparison of Finding confidence scores and content similarity at synthesis trigger time
- **Rationale**: Contradictions are surfaced by comparing agent outputs on overlapping dimensions (e.g., same metric, different values); confidence scores help determine which finding to trust.
- **Alternatives considered**: LLM-based judgment for every finding pair (too expensive), manual analyst review only (violates FR-006)

### Decision 5: Synthesis stop criteria
- **Decision**: Three-tier trigger — (1) all required agents complete, (2) confidence threshold met across all findings, (3) max execution budget exhausted (whichever comes first)
- **Rationale**: Covers SC-007 while still allowing early synthesis when sufficient evidence is gathered. Budget enforcement prevents runaway execution per FR-014.
- **Alternatives considered**: Single "all agents done" trigger (no early synthesis), human-signaled trigger (too slow for autonomous operation)

### Decision 6: Telemetry approach
- **Decision**: Log-based telemetry events with structured logging (loguru) consumed by an event buffer for dashboard queries
- **Rationale**: loguru is already in the project stack; structured events can be consumed by a lightweight dashboard without adding a time-series database for v1.
- **Alternatives considered**: Dedicated APM tool (overkill for v1), custom metrics service (too much infrastructure)

### Decision 7: Steering instruction handling
- **Decision**: Steering instructions pause the workflow and re-trigger targeted agents; the synthesis agent receives a flag that new input arrived mid-stream
- **Rationale**: Simple interruption model that maps to LangGraph's interruptible node pattern.
- **Alternatives considered**: Full workflow restart (loses completed work), queued instructions (delayed feedback frustrates analyst)
