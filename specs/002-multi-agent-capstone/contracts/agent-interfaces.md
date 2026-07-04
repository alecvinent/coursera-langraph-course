# Agent Interface Contracts: Capstone Project

## Node Function Signature

Every agent node follows the LangGraph node pattern:

```
node_function(state: SharedState) -> SharedState
```

Each node receives the full shared state and returns updated state with its contributions appended.

## Agent Contract: ResearchAgent

**Role**: Raw data gathering — collects facts, figures, context from knowledge sources (web search, documents)

**Input requirements**: ResearchRequest (topic, domain_tags, constraints)

**Output**: Produces Finding entries with factual data and source attribution

**Triggered by**: First in sequence after input validation passes

**Signals to other agents**: Publishes findings under `agent_outputs["research"]`; tags findings with dimension_tags (e.g., "market_size", "regulation", "technology") that downstream agents use for routing

**Failure mode**: Returns empty findings list with FAILED state; circuit breaker tracks consecutive failures

## Agent Contract: FinancialAgent

**Role**: Quantitative analysis — revenue projections, cost structures, investment metrics, financial ratios

**Input requirements**: ResearchRequest + findings from ResearchAgent (for financial context and baseline figures)

**Output**: Produces Finding entries with financial data, projections, and quantitative insights

**Triggered by**: Completion of ResearchAgent (or circuit bypass)

**Signals to other agents**: Publishes under `agent_outputs["financial"]`; cross-references ResearchAgent findings via provenance_chain; flags financial risks for RiskAgent

## Agent Contract: MarketAgent

**Role**: Competitive and market positioning — market share, competitors, growth trends, customer segments

**Input requirements**: ResearchAgent findings + FinancialAgent findings (for market context and financial positioning)

**Output**: Produces Finding entries with market analysis, competitive landscape, segment breakdowns

**Triggered by**: Completion of FinancialAgent (or circuit bypass)

**Signals to other agents**: Publishes under `agent_outputs["market"]`; cross-references both Research and Financial findings; identifies market-level risks for RiskAgent

## Agent Contract: RiskAgent

**Role**: Threat and risk assessment — regulatory, operational, market, and technology risks derived from all upstream findings

**Input requirements**: Research + Financial + Market findings

**Output**: Produces Finding entries identifying risks, mitigations, and confidence assessments

**Triggered by**: Completion of MarketAgent (or circuit bypass)

**Signals to other agents**: Publishes under `agent_outputs["risk"]`; provides conflict-relevant assessments (contradictory claims flagged for Synthesis)

## Agent Contract: SynthesisAgent

**Role**: Integration and report generation — consolidates all findings, resolves conflicts, generates final report

**Input requirements**: All upstream agent findings + conflict records + steering instructions + degraded_agents metadata

**Output**: SynthesisReport with cross-referenced findings, conflict disclosures, and data gaps

**Triggered by**: First-to-fire among: (a) all agents complete, (b) confidence threshold ≥0.8 with ≥10 findings, (c) max execution budget reached

**Signals to**: End user (final report); operations (telemetry events)

## Coordination Contract: Router

**Decision points**:
- Validate input specificity → route to refinement or agent activation
- After each agent completion → route to next agent or check budget for loop
- Check circuit breaker → route around failed agent or allow retry
- Evaluate synthesis triggers → continue agents or terminal synthesize

## Coordination Contract: ConflictResolver

**Detection**: Compares Finding entries for overlapping dimension_tags with contradictory content, numeric mismatches, or opposing conclusions

**Resolution strategy**: Attempt LLM-based judgment for conflicting pairs; if confidence delta >0.3, higher-confidence finding wins; otherwise surface both with escalation status
