# Research: Multi-Agent Capstone Project

## Design Decisions

### Decision 1: Agent role specialization
- **Decision**: 5 agents — Research, Financial, Market, Risk, Synthesis — covering business intelligence end-to-end
- **Rationale**: The capstone requires "at least 4 specialized agents" that demonstrate emergent intelligence through cross-agent awareness. The 5-role split maps to distinct business analysis dimensions: raw data gathering (Research), quantitative context (Financial), competitive/market positioning (Market), risk/threat assessment (Risk), and cross-cutting integration (Synthesis).
- **Alternatives considered**: Reusing module_3 roles (web_research, data_analysis, trend_analysis, competitive_intelligence) — too domain-specific; 6 agents — no additional coverage benefit for evaluation constraints.

### Decision 2: Agent activation topology
- **Decision**: Sequential round-based activation — Research → Financial → Market → Risk → Synthesis, with cyclic re-entry from Risk back to Research when budget permits; Synthesis as single terminal
- **Rationale**: Sequential activation with a conditional loop satisfies FR-002 (shared state building) and FR-015 (cross-referenced output). Downstream agents always see upstream findings. Cyclic re-entry enables iterative refinement (emergent intelligence) without needing full parallel execution. Synthesis is terminal because it consolidates all prior work.
- **Alternatives considered**: DAG/parallel fan-out (agents need each other's outputs — ordering is inherent), market-style bidding (over-engineered for capstone scale)

### Decision 3: Circuit breaker implementation
- **Decision**: Per-agent failure counter tracked in `agent_states[key].execution_state` transitions. After 3 consecutive FAILED states for the same agent, a conditional edge routes around it to the next agent. Counter resets on successful execution.
- **Rationale**: Satisfies FR-014 without adding external infrastructure. LangGraph's conditional edges can inspect `agent_states` at the routing decision point. The counter approach is simpler than a timeout-based breaker and maps naturally to the state schema.
- **Alternatives considered**: External circuit breaker library (adds dependency), timeout-only approach (doesn't handle repeated failures), throwing exception and catching at graph level (loses agent-specific tracking)

### Decision 4: Conflict detection and resolution
- **Decision**: Two-phase — (1) rule-based overlap detection at synthesis trigger time comparing finding content for contradictory claims on shared dimensions, (2) LLM-based resolution attempt with confidence-weighted tie-breaking; unresolvable conflicts surfaced transparently in output
- **Rationale**: Rule-based phase is cheap and catches obvious contradictions (same entity, different numbers). LLM phase resolves ambiguous cases. Surfacings unresolvable conflicts meets FR-009's "transparently surfacing them" clause.
- **Alternatives considered**: Pure LLM-based detection (expensive for every finding pair), skip detection (violates FR-009)

### Decision 5: Input refinement mechanism
- **Decision**: Initial validation node that checks topic length (< 10 words with no domain tags → too broad), presence of domain_tags, and constraint specificity. Returns status=needs_refinement with guidance text. Graph halts and returns refinement request to caller.
- **Rationale**: Satisfies FR-012. The existing module_3 pattern activated agents regardless of input quality; the capstone must explicitly halt and request refinement before spending budget on vague queries.
- **Alternatives considered**: LLM-based specificity scoring (adds unnecessary LLM call for validation), required structured template (reduces usability)

### Decision 6: Execution budget enforcement
- **Decision**: `time.monotonic()` comparison against `execution_metadata["max_execution_minutes"]` checked at every routing decision point. When budget is 80% consumed and synthesis has not fired, force-synthesize with available data.
- **Rationale**: Satisfies FR-011. Tie to routing rather than inline in every node keeps budget checks centralized. 80% trigger threshold gives synthesis enough time to produce output before hard timeout.
- **Alternatives considered**: Hard interrupt via signal (platform-dependent, can't cleanly capture state), node-level timeout per agent (more complex, adds per-agent configuration)

### Decision 7: Telemetry and observability
- **Decision**: `@timed_node` decorator on every agent node for latency + loguru for structured logging + TelemetryEvent records in shared state for programmatic inspection
- **Rationale**: Satisfies FR-010 and aligns with constitution Article III. Three-layer approach covers real-time (loguru), per-node (timed_node), and post-hoc (TelemetryEvent records).
- **Alternatives considered**: OpenTelemetry SDK (adds dependency, overkill for single-module capstone), LangSmith-only (not always available in eval environments)

### Decision 8: Graceful degradation strategy
- **Decision**: When an agent fails and circuit breaker fires, the graph logs the gap and proceeds. The Synthesis agent receives a flag in `execution_metadata["degraded_agents"]` with a list of roles that were bypassed. Synthesis includes a "Data Gaps" section documenting what was missed.
- **Rationale**: Satisfies FR-008. Explicit documentation of gaps prevents fabricated data (FR-013) while still producing a useful output.
- **Alternatives considered**: Retry indefinitely (can exhaust budget), skip silently (produces misleading complete-looking output)
