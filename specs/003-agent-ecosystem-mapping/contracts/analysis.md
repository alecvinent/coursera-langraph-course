# Contract: Trade-off Analysis

## Module
`module_1_foundations.analysis.tradeoffs`

### `generate_tradeoff_analysis(scenario: Scenario) -> str`

Generates a formatted trade-off analysis document comparing reactive, deliberative, and hybrid architectures across 5 dimensions.

**Input**: `Scenario` with classified agents
**Output**: Markdown string with:

1. **Per-dimension analysis** (speed, accuracy, scalability, resilience, adaptability):
   - Score table (1–5) for each agent type per dimension
   - Rationale paragraph for each dimension

2. **Side-by-side comparison**:
   - Table comparing pure reactive, pure deliberative, and hybrid system designs
   - Qualitative best-fit recommendation

**Dimensions and scoring heuristics**:
- **Speed**: Reactive scores highest (direct stimulus-response); deliberative lowest (planning overhead)
- **Accuracy**: Deliberative scores highest (world model + planning); reactive lowest (no state)
- **Scalability**: Reactive scores highest (stateless, easy to replicate); deliberative lowest (state coordination)
- **Resilience**: Reactive scores highest (no single point of failure); deliberative lowest (centralized reasoner)
- **Adaptability**: Hybrid scores highest (rules + planning combined); reactive lowest (no learning/planning)

**Edge Cases**:
- Single agent in scenario → analysis still valid (compares hypothetical pure types)
- All agents same type → comparison table notes homogeneity
- Empty scenario → returns empty report with warning
