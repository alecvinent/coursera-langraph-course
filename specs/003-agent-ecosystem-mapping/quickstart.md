# Quickstart: Agent Ecosystem Mapping

**Date**: 2026-07-17 | **Feature**: 003-agent-ecosystem-mapping

## Prerequisites

- Python 3.10+ via the project's Poetry environment
- Install the only new dependency: `poetry add markdown` (justified: no existing dep provides md→HTML; `pymupdf` already covers PDF generation)
- A `.env` file with `LLM_PROVIDER` and `LLM_API_KEY` (for LLM fallback; rule-based mode works without these)

## Setup

```bash
# Activate the Poetry environment
cd /path/to/langgraph-course
poetry shell

# Verify imports work
python -c "from module_1_foundations.classification.graph import classify_agent; print('OK')"
```

## Validation Scenarios

### Scenario 1: Rule-Based Classification (Happy Path)

```bash
python -c "
from module_1_foundations.classification.graph import classify_agent
result = classify_agent('A sensor that reads temperature and emits it. No internal state, no memory.')
print(result['agent_type'])     # expected: reactive
print(result['justification'])  # expected: references statelessness
print(result['method'])         # expected: rule_based
"
```

**Expected**: `agent_type == "reactive"`, `method == "rule_based"`

### Scenario 2: LLM Fallback Classification (Ambiguous)

Requires working `.env` with LLM provider.

```bash
python -c "
from module_1_foundations.classification.graph import classify_agent
result = classify_agent('An agent that uses both immediate sensor data and long-term planning. It maintains a world model but also reacts quickly to unexpected obstacles.')
print(result['agent_type'])     # expected: hybrid
print(result['method'])         # expected: llm
"
```

**Expected**: `agent_type == "hybrid"`, `method == "llm"`

### Scenario 3: Interaction Map Generation

```bash
python -c "
from module_1_foundations.scenarios.traffic import traffic_scenario
from module_1_foundations.interaction_map.mapper import generate_interaction_map
diagram = generate_interaction_map(traffic_scenario)
print(diagram)
# Expected: Mermaid flowchart with sensor → controller → planner
"
```

**Expected**: Valid Mermaid syntax, 3 agent nodes, directed arrows with labels.

### Scenario 4: Trade-off Analysis

```bash
python -c "
from module_1_foundations.scenarios.traffic import traffic_scenario
from module_1_foundations.analysis.tradeoffs import generate_tradeoff_analysis
analysis = generate_tradeoff_analysis(traffic_scenario)
print(analysis)
# Expected: 5 dimension analyses + side-by-side comparison table
"
```

**Expected**: Covers all 5 dimensions with scores and rationale.

### Scenario 5: Capability Cycle

```bash
python -c "
from module_1_foundations.scenarios.task_manager import task_manager_scenario
from module_1_foundations.interaction_map.mapper import generate_capability_cycle
diagram = generate_capability_cycle(task_manager_scenario, 'personal_assistant')
print(diagram)
# Expected: Perception → Reasoning → Action subgraphs
"
```

**Expected**: Valid Mermaid with 3 labeled subgraphs.

### Scenario 6: Full Submission Export

```bash
python -c "
from module_1_foundations.scenarios.traffic import traffic_scenario
from module_1_foundations.classification.graph import classify_agent
from module_1_foundations.interaction_map.mapper import generate_interaction_map, generate_capability_cycle
from module_1_foundations.analysis.tradeoffs import generate_tradeoff_analysis
from module_1_foundations.export.submission import compile_submission, generate_pdf
import tempfile, os

classifications = [classify_agent(a.description) for a in traffic_scenario.agents]
interaction_map = generate_interaction_map(traffic_scenario)
capability_cycle = generate_capability_cycle(traffic_scenario, traffic_scenario.agents[0].id)
analysis = generate_tradeoff_analysis(traffic_scenario)
md = compile_submission(traffic_scenario, classifications, interaction_map, analysis, capability_cycle)
print(md[:500])  # first 500 chars of markdown

with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as f:
    pass
pdf_path = generate_pdf(md, f.name)
print(f'PDF generated: {pdf_path}')
os.unlink(pdf_path)
"
```

**Expected**: Markdown output has 5 sections + PDF file generated and deleted.

## Running Tests

```bash
# All module_1 tests (use -t . for hyphenated directory support)
python -m unittest discover -s tests/multiagent-governance_course/test_module_1_foundations -t . -v

# Specific test file
python -m unittest discover -s tests/multiagent-governance_course/test_module_1_foundations -t . -p test_classification.py -v
```

**Expected**: All tests pass (rule-based, LLM fallback, mapper, analysis, export).

## Running the Streamlit App

```bash
# Requires streamlit (dev dependency)
poetry run streamlit run src/multiagent-governance_course/module_1_foundations/app.py
```

**Expected**: Browser opens with 4-step wizard: Select Scenario → Classify Agents → View Maps/Analysis → Export Submission.

## Edge Cases to Verify

| Test | How to Verify |
|------|---------------|
| Empty description | `classify_agent("")` → raises `ValueError` |
| Description with negated keywords | `classify_agent("agent without internal state")` → reactive (not deliberative) |
| Zero-interaction scenario | `generate_interaction_map(scenario_without_interactions)` → isolated nodes, no arrows |
| Single-agent scenario analysis | `generate_tradeoff_analysis(single_agent_scenario)` → still produces 5-dim analysis |
| LLM timeout | Network disconnected + ambiguous description → `ErrorRecord` in state, `processing_outcome="partial"` |
| PDF special characters | Smart quotes, em dashes in analysis → replaced with ASCII, no encoding crash |
| PDF diagram rendering | `generate_pdf(md, path)` with interaction map → page contains visual node+arrow graphics, not just code blocks |
