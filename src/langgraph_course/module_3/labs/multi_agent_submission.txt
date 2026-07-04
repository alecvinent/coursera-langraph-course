1. Collaborative State Architecture

The ResearchState is a pydantic BaseModel that enables true collaboration through a shared, typed state accessible to all agents. The state is divided into three conceptual layers:

Business layer: ResearchRequest (topic, domain_tags, constraints, status) holds the analyst's original query and its lifecycle. agent_outputs maps each AgentRole (web_research, data_analysis, trend_analysis, competitive_intelligence, synthesis) to a list of Finding records, each containing content, source, confidence, timestamp, provenance_chain, and cross_references. The report field holds the final SynthesisReport with sections, cross_references, conflict_disclosures, and provenance_trace.

Coordination layer: conflicts tracks detected contradictions between agents' findings with resolution_status (unresolved/resolved/escalated). steering_instructions captures analyst mid-workflow interventions with instruction_text, target_agents, and applied flag. cross_agent_insights records emergent connections discovered between agents' domains.

Telemetry layer: agent_states tracks each agent's ExecutionState (idle/running/completed/failed/paused). telemetry_events records structured TelemetryEvent entries (event_type, agent_role, value, details, timestamp) for operational observability. execution_metadata stores workflow timing, retry counts, and the synthesis stop trigger reason.

The key design choice was using pydantic BaseModel with typed fields rather than a plain TypedDict — this provides schema validation at every state mutation, IDE autocompletion for all agent developers, and serialization for LangGraph checkpointing without custom marshalling. The Annotated[list, add_messages] reducer on the messages field ensures LangGraph's built-in message accumulation works alongside custom agent state.

2. Agent Coordination Patterns

Five specialized agents coordinate through shared state with clear handoff protocols:

WebResearchAgent (round 1): Activated first. Receives the ResearchRequest (topic, domain_tags). Uses LLMFactory to research the topic and produces 3-5 Finding entries with source attribution. Its findings populate agent_outputs["web_research"], which downstream agents read for context.

DataAnalysisAgent (round 2): Activated after WebResearchAgent completes. Consumes web research findings for context on what data to analyze. Produces quantitative findings (statistics, figures, data points). Populates agent_outputs["data_analysis"] for TrendAnalysisAgent and CompetitiveIntelligenceAgent.

TrendAnalysisAgent (round 3): Activated after both WebResearchAgent and DataAnalysisAgent have findings available. Identifies patterns, projections, and temporal insights by synthesizing across web research and data analysis outputs. Populates agent_outputs["trend_analysis"].

CompetitiveIntelligenceAgent (round 3/4): Activated after TrendAnalysisAgent or independently if the request is competition-focused. Analyzes competitor positioning, market share, and strategic moves. Cross-references trend and data analysis findings.

SynthesisAgent (final): Triggered by the first-to-fire among three stop criteria: all required agents complete, aggregate confidence threshold met (>=0.8 with >=10 findings), or max execution budget exhausted. Reads all agent findings, conflict records, and steering instructions. Produces a SynthesisReport with narrative sections, cross-references between agent domains, conflict disclosures, and full provenance_trace mapping every claim to its source agent.

Each agent signals readiness by setting its execution_state to completed and publishing findings to shared state. The Router in coordination/router.py determines activation order and parallelism. The should_synthesize conditional edge in the graph checks all three stop criteria every cycle.

3. Dynamic Workflow Logic

The coordination logic in coordination/router.py adapts collaboration patterns dynamically:

Agent activation decision (activate_agents_router): Before any research begins, the router checks whether the request is too broad using keyword indicators ("everything about", "all about", "general", "technology"). If broad, it returns "needs_refinement" and sets the request status accordingly, preventing wasted agent execution on underspecified topics.

Parallel vs sequential execution (determine_agent_parallelism): The router builds execution groups based on available findings. In the first round, WebResearchAgent runs alone (sequential — it needs to establish context). Once web findings exist, DataAnalysisAgent runs. TrendAnalysisAgent and CompetitiveIntelligenceAgent run after their input agents complete. The design deliberately starts sequential to establish context, then fans out where dependencies allow — this is the trade-off between parallel speed (faster wall-clock time) and sequential depth (richer cross-referencing).

Synthesis trigger (should_synthesize): Three-tier stop criteria evaluated every cycle: (1) all four research agents complete — immediate synthesis, (2) at least 10 total findings with average confidence >= 0.8 — early synthesis when evidence is strong, (3) execution budget exhausted (configurable, default 30 minutes) — forced synthesis with available data. The router also checks for pending steering instructions on each cycle, injecting them before evaluating stop criteria.

Conflict detection: During synthesis, the synthesis node compares findings across agent roles for contradictory signals (increase vs decrease, growing vs declining, strong vs weak, etc.). Detected contradictions are recorded as Conflict entries with finding_ids, description, and resolution_status. This happens at synthesis time rather than continuously to avoid premature conflict escalation during data gathering.

4. Collaboration Rationale — Emergent Intelligence

The design creates emergent intelligence through three mechanisms:

Cross-agent awareness via shared state: Every agent reads the full ResearchState, not just its input slice. WebResearchAgent's findings on "EV battery market in Southeast Asia" become context for DataAnalysisAgent, which then produces targeted quantitative findings. TrendAnalysisAgent synthesizes both to identify patterns. CompetitiveIntelligenceAgent adds market positioning context. The synthesis agent sees all of these as an interconnected whole, enabling it to write a report where "WebResearchAgent found growing demand in Thailand, DataAnalysisAgent identified a 23% CAGR, TrendAnalysisAgent projects this accelerating, and CompetitiveIntelligenceAgent notes Tesla's recent entry" — each finding builds on the previous ones.

Provenance tracking ensures every claim is attributable: Each Finding carries a provenance_chain (IDs of findings it derived from) and cross_references (IDs of related findings from other agents). The build_provenance_trace function in coordination/provenance.py assembles a complete trace mapping every report claim to its source agent, source document, and confidence score. This turns individual outputs into emergent insights by making the connections between agents' work explicit and traceable.

Conflict surfacing prevents false consensus: When agents contradict each other (e.g., WebResearchAgent finds "declining growth" while DataAnalysisAgent shows "increasing revenue"), the synthesis agent does not silently pick a winner. It surfaces both perspectives with supporting evidence, confidence scores, and a flagged uncertainty marker. This transforms contradictions from bugs into features — the report demonstrates that the system recognized the tension and presented it transparently.

The trade-off between parallel speed and sequential depth is managed by the round-based activation. Web research is always first (sequential) because all other agents need its context. Data analysis runs second. Trend and competitive intelligence can run in parallel after their prerequisites complete because they work on different analytical dimensions. Synthesis waits until enough evidence is gathered or budget is reached. This means a narrow question with obvious answers triggers early synthesis (fast), while a complex multi-domain question waits for all agents (deep).

5. Reflection — Multi-Agent Coordination

The most impactful design decision was making shared state the single coordination mechanism rather than implementing direct agent-to-agent messaging. With shared state, any agent can see any other agent's findings at any time without explicit handoff protocols. A new agent can be added by simply writing to agent_outputs — no routing table changes needed. The downside is that agents must scan the full state to find relevant context, which an explicit message-passing system would avoid. For this scale (5 agents), shared state is simpler and more extensible.

The three-tier synthesis stop criteria solved the "when to stop" problem more effectively than a single trigger would. In testing, the confidence threshold often fires early for obvious questions (fast turnaround), while complex questions benefit from all-agent completion. The budget enforcement is a safety net that prevents runaway execution, which is critical for production deployment where an agent might enter an infinite loop.

Three telemetry signals would drive production adaptation: per-agent latency trends (if WebResearchAgent consistently takes 3x longer than peers, its LLM prompt or model may need tuning), conflict detection rate (a spike from 10% to 40% suggests contradictory source data that may need pre-filtering), and early synthesis rate (if >50% of requests hit early synthesis via confidence threshold, the all-agents-complete path may be too conservative — the system could optimize for speed by defaulting to early synthesis).

Human-in-the-loop checkpoints would be added at two points: steering instructions (already designed — analyst can inject mid-workflow) and conflict escalation (if automated conflict resolution fails after max retries, the system should route to a human analyst with both perspectives and supporting evidence). At scale, adding a human review gate before synthesis finalization on "partial" processing_outcome would prevent degraded reports from reaching clients.
