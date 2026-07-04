# Agent Interface Contracts

## Node Function Signature

Every agent node follows the LangGraph node pattern:

```
node_function(state: AgentState) -> AgentState
```

Each node receives the full shared state and returns updated state with its contributions appended.

## Agent Contract: WebResearchAgent

**Input requirements**: ResearchRequest (topic, domain_tags, constraints)

**Output**: Produces Finding entries from web sources

**Triggered by**: ResearchRequest activation; re-triggered on steering instructions targeting it

**Signals to other agents**: Publishes findings to shared state under `agent_outputs["web_research"]`; can flag specific findings as inputs for DataAnalysisAgent

## Agent Contract: DataAnalysisAgent

**Input requirements**: ResearchRequest + findings from WebResearchAgent (for context on what data to analyze)

**Output**: Produces Finding entries with quantitative data, statistics, figures

**Triggered by**: Completion of WebResearchAgent (minimum threshold of findings received); or independently if the request is quantitative-only

**Signals to other agents**: Publishes numeric findings and structured data that TrendAnalysisAgent and CompetitiveIntelligenceAgent consume

## Agent Contract: TrendAnalysisAgent

**Input requirements**: Findings from WebResearchAgent + DataAnalysisAgent

**Output**: Produces Finding entries identifying patterns, projections, and temporal insights

**Triggered by**: Sufficient findings from both WebResearchAgent and DataAnalysisAgent (configurable threshold)

**Signals to other agents**: Publishes trend findings; may request additional data from DataAnalysisAgent if gaps are found

## Agent Contract: CompetitiveIntelligenceAgent

**Input requirements**: Findings from WebResearchAgent + TrendAnalysisAgent

**Output**: Produces Finding entries about competitor positioning, market share, strategic moves

**Triggered by**: Completion of TrendAnalysisAgent or independently if the request is competition-focused

**Signals to other agents**: Publishes competitive findings with cross-references to trend and data analysis outputs

## Agent Contract: SynthesisAgent

**Input requirements**: All other agents' findings + conflict records + steering instructions

**Output**: SynthesisReport

**Triggered by**: First-to-fire among: (a) all expected agents complete, (b) confidence threshold met, (c) max execution budget reached

**Signals to**: End user (final report); operations (telemetry)

## Coordination Contract: Router

**Decision points**:
- Which agents to activate based on domain_tags and request complexity
- Whether agents run in parallel or sequence based on dependency graph
- When to inject steering instructions mid-workflow

## Coordination Contract: ConflictResolver

**Detection**: Compares Finding fields for overlapping dimensions with contradictory values

**Resolution strategy**: Triggers re-investigation from affected agents with conflict context; if unresolved after max retries, escalates with both perspectives
