# Contract: Classification Engine

## Module
`module_1_foundations.classification.graph`

## Public Interface

### `classify_agent(description: str) -> AgentClassification`

Classifies a single agent description into Reactive / Deliberative / Hybrid.

**Input**:
- `description`: Natural-language description of the agent's behavior and attributes

**Output**: `AgentClassification`
- `agent_id`: auto-generated UUID string
- `agent_type`: `"reactive"` | `"deliberative"` | `"hybrid"`
- `justification`: Multi-sentence explanation
- `confidence`: Float 0.0–1.0 (only populated for LLM path)
- `method`: `"rule_based"` | `"llm"`

**Errors**: Raises `ClassificationError` on LLM timeout or invalid response

---

### `ClassificationState (TypedDict)`

```python
{
    "description": str,           # Input agent description
    "agent_type": NotRequired[str],       # Classification result
    "justification": NotRequired[str],    # Reasoning
    "errors": list[ErrorRecord],          # Accumulated errors
    "latencies": dict[str, float],        # Per-node timing
    "paths_taken": list[str],             # Execution path
}
```

---

## Module
`module_1_foundations.classification.rules`

### `classification_rules(state: ClassificationState) -> ClassificationState`

Applies decision-tree rules. Populates `agent_type` and `justification` for clear-cut cases; leaves them unset for ambiguous cases.

### `needs_llm(state: ClassificationState) -> Literal["llm_fallback", "finalize"]`

Conditional edge router. Returns `"llm_fallback"` if rules could not determine type, `"finalize"` otherwise.

---

## Module
`module_1_foundations.classification.prompts`

### `build_classification_prompt(description: str) -> str`

Constructs the LLM prompt for ambiguous classification cases.
