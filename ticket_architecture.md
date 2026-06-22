# Ticket Routing LangGraph — Architecture Analysis

## 1. Architecture Overview

### 1.1 Graph Structure

The ticket routing workflow is a **sequential pipeline with a single retry loopback**, built using LangGraph's `StateGraph`. The graph has 7 nodes:

```
[validate] ──(conditional)──→ [classifier] → [urgency_assessor] → [router] ──(conditional)──→ [respond] → END
     │                                                                                            │
     └──→ END                                                                                     ├──→ [human_review] → END
                                                                                                  └──→ [retry_classifier] → [urgency_assessor] → [router] (loop)
```

**File:** `src/langgraph_course/module_1/labs/tickets.py`

**Node registry** (lines 258–264):
```python
workflow.add_node('validate', self.validate_input)
workflow.add_node('classifier', self.classify_ticket)
workflow.add_node('urgency_assessor', self.urgent_assessment)
workflow.add_node('router', self.routing_decision)
workflow.add_node('respond', self.generate_response)
workflow.add_node('human_review', self.human_review)
workflow.add_node('retry_classifier', self.retry_classifier)
```

**Edges** (lines 266–292):
- `validate → {classifier | END}` — conditional on `_validate_decision`
- `classifier → urgency_assessor` — unconditional
- `urgency_assessor → router` — unconditional
- `router → {respond | human_review | retry_classifier}` — conditional on `_analysis_decision`
- `retry_classifier → urgency_assessor` — re-enters the pipeline

### 1.2 State Schema

**File:** `tickets.py`, lines 38–47

```python
class TicketState(TypedDict):
    ticket: Ticket
    classification_results: Optional[TicketClassificationResult]
    urgency_level: Optional[TicketUrgencyLevel]
    routing_decision: str
    additional_metadata: str
    response: str
    errors: list[str]
    retry_count: int
    processing_time: float
```

Supporting models:
- **`Ticket`**: `topic: str`, `is_urgent: bool`
- **`TicketClassificationResult`**: `category: TicketCategory`, `confidence: float`
- **`TicketCategory`** enum: `BILLING_ISSUE`, `TECHNICAL_ISSUE`, `FEATURE_REQUEST`, `ACCOUNT_MANAGEMENT`, `UNKNOWN`
- **`TicketUrgencyLevel`** enum: `LOW`, `MEDIUM`, `HIGH`

### 1.3 Data Flow

1. **Entry**: `run()` initialises state with the input `Ticket`, zeros/null for all fields.
2. **Validation**: `validate_input` checks `ticket is None`, empty/type-invalid `topic`. On error, returns `errors` and the graph short-circuits to END.
3. **Classification**: `classify_ticket` calls `_get_ticket_category` which does keyword matching and assigns deterministic confidence scores (0.20–0.85).
4. **Urgency Assessment**: `urgent_assessment` checks `is_urgent` flag first, then keyword heuristics for HIGH/MEDIUM/LOW.
5. **Routing**: `routing_decision` maps `(category, urgency)` — HIGH + TECHNICAL → Senior Engineer, then per-category rules.
6. **Analysis Decision**: `_analysis_decision` uses `CONFIDENCE_THRESHOLD = 0.6` and `MAX_RETRIES = 2`:
   - `confidence < 0.6` OR `category == UNKNOWN` → retry or human-review
   - `retry_count < 2` → route to `retry_classifier`
   - `retry_count >= 2` → route to `human_review`
7. **Retry**: `retry_classifier` uses broader keyword lists and lower confidence scores, increments `retry_count`, loops back to `urgency_assessor`.
8. **Human Review**: `human_review` creates a response with confidence, retry count, and urgency.
9. **Response**: `generate_response` formats the routing decision with urgency and confidence.

---

## 2. Per-Dimension Analysis

### 2.1 Trade-offs between Simplicity and Adaptability

The graph uses a **sequential backbone** (`classifier → urgency_assessor → router`) with a single **conditional fork** at `router` that can go to `respond`, `human_review`, or loop back via `retry_classifier`. This design makes explicit trade-offs:

| Trade-off | Current Implementation | What It Sacrifices |
|-----------|----------------------|-------------------|
| **Linear pipeline vs parallel branches** | classification and urgency run sequentially | Latency: urgent tickets wait for classification even though urgency is independent |
| **Keyword heuristics vs ML model** | `_get_ticket_category` uses simple substring matching | Accuracy: no synonym handling, no out-of-vocabulary topics |
| **Deterministic confidence vs probabilistic** | Confidence is a hardcoded float per keyword branch | Calibration: no evidence that 0.85 matches real accuracy |
| **Single retry strategy vs multiple strategies** | `retry_classifier` just uses broader keywords | Adaptability: if keyword matching is the failure mode, broader keywords won't help |
| **Hardcoded threshold vs configurable** | `CONFIDENCE_THRESHOLD = 0.6` is a class constant | Runtime adaptability: cannot adjust per ticket type without code change |
| **Reusing nodes in retry loop vs isolated subgraph** | Retry re-runs `urgency_assessor` and `router` | Latency: urgency reassessment is wasteful when the topic hasn't changed |

#### Key Line References

- **Line 51**: `CONFIDENCE_THRESHOLD = 0.6` — trade-off between false positives and false negatives.
- **Lines 106–114**: Hardcoded confidence values — simple to maintain, impossible to calibrate.
- **Lines 189–222 vs 102–114**: Retry classifier duplicates keyword approach — trade-off between code reuse and independent tuning.
- **Lines 280–288**: Single conditional edge concentrates branching logic — easy to reason about vs centralised complexity.

---

### 2.2 Node Design and Workflow Impact

| Node | Lines | Responsibility | Returns |
|------|-------|----------------|---------|
| `validate_input` | 59–74 | Guard clause: rejects `None` ticket, non-string/non-empty topic | `errors`, `response` on failure; `{}` on success |
| `classify_ticket` | 84–99 | Delegates to `_get_ticket_category` for keyword matching | `classification_results`, `processing_time` |
| `urgent_assessment` | 117–135 | Three-level urgency via `is_urgent` flag + topic keywords | `urgency_level` |
| `routing_decision` | 138–162 | Maps `(category, urgency)` → routing string + metadata | `routing_decision`, `additional_metadata` |
| `retry_classifier` | 189–222 | Second-attempt classification with broader keywords, lower confidence | `classification_results`, `retry_count`, `processing_time` |
| `_analysis_decision` | 165–186 | Conditional edge: confidence threshold + retry budget → next node | String routing key |
| `human_review` | 225–241 | Context-rich handoff message for human operators | `response` |
| `generate_response` | 244–256 | Formats final routing decision + urgency + confidence | `response` |

#### Design Weaknesses

**1. Duplicate classification logic (lines 102–114 vs 189–222)**

`_get_ticket_category` and `retry_classifier` share ~80% similarity — both do `ticket.topic.lower()` then `any(kw in topic for kw in (...))`. Keyword lists overlap significantly.

- **Maintainability cost**: Adding a keyword requires editing two methods.
- **Correctness risk**: If the two methods drift, first-pass and retry results become inconsistent.
- **Example**: "charge" is retry-only (line 198). A ticket saying "my charge is wrong" gets UNKNOWN on first pass and BILLING on retry — guaranteed retry for a ticket the first classifier should have caught.

**2. Missing null safety in `routing_decision` (line 141)**

```python
ticket_type = state.get('classification_results').category
```

If `classification_results` is `None`, this raises `AttributeError`.

**3. No timing telemetry in all nodes**

`validate_input` computes `start` but never returns `processing_time`. `human_review` and `generate_response` have no timing at all. The `processing_time` field only reflects classification time.

**4. Cross-cutting concerns**

- `classify_ticket` returns `processing_time` — telemetry leaking into a domain node.
- `routing_decision` sets `additional_metadata` as a formatted string — presentation logic inside a decision node.

---

### 2.3 Confidence/Uncertainty Handling and Failure Paths

**Confidence scores** (lines 106–114): Each keyword set returns a hardcoded float (0.75–0.85 for known, 0.20 for UNKNOWN).

**Threshold check** (line 176): `_analysis_decision` checks `confidence < 0.6`.

**Retry budget** (lines 177–183): Up to 2 retries via `retry_count` in state.

**Fallback to human** (line 182–183): After max retries, routes to `human_review`.

**Error state**: `validate_input` populates `errors` list (lines 65, 69); `_validate_decision` checks it (line 78).

#### Gaps

**1. Confidence is not calibrated**

Billing keywords (line 106) always return 0.85, but there is no data showing that 85% of tickets containing "billing" are actually billing issues. True confidence requires measurement against ground truth.

**2. The retry strategy is homogeneous**

`retry_classifier` uses the **same algorithm** (keyword matching) with slightly broader keywords. If the first pass failed because keyword matching is fundamentally insufficient, broader keywords will likely fail too. Strategy diversity (LLM-based fallback, regex patterns, customer metadata) would be qualitatively different.

**3. No exception handling**

No node uses `try/except`. If any node raises an exception, the entire `graph.invoke()` call (line 298) fails.

**4. The `errors` field is write-once**

No node clears errors after resolution; no node reads errors after `_validate_decision`. Accumulated errors are never surfaced in the final response.

**5. Single threshold, no confidence bands**

A single 0.6 threshold creates binary pass/fail. A more nuanced approach:
- **Green** (≥0.8): Auto-respond
- **Amber** (0.4–0.8): Human review with context
- **Red** (<0.4): Immediate human review, no retries wasted

---

### 2.4 Telemetry and Human-in-the-Loop Checkpoints

**Per-node timing telemetry** is implemented in 5 of 7 nodes:

| Node | Timing Computed | Timing Returned | Logging |
|------|----------------|-----------------|---------|
| `validate_input` (line 59) | Yes | **No** | Yes |
| `classify_ticket` (line 84) | Yes | Yes | Yes |
| `urgent_assessment` (line 117) | Yes | **No** | Yes |
| `routing_decision` (line 138) | Yes | **No** | Yes |
| `retry_classifier` (line 189) | Yes | Yes | Yes |
| `human_review` (line 225) | **No** | **No** | Yes |
| `generate_response` (line 244) | **No** | **No** | **No** |

**Structured logging** uses `loguru`:
- `logger.info` for normal operations
- `logger.warning` for human-review triggers and max-retries
- `logger.error` for validation failures

**Human-in-the-loop checkpoint** at `human_review` (lines 225–241):
- Logs topic, confidence, retry count, urgency level
- Response includes context for the human operator

#### Gaps

**1. Incomplete timing coverage**

Only `classify_ticket` and `retry_classifier` return `processing_time` to state. The field under-reports end-to-end latency by up to 3×.

**2. No cumulative or aggregate telemetry**

- No total elapsed time tracking
- No per-node latency breakdown in a single place
- No counters for how often each path is taken
- No LangSmith tracing (though `langsmith` is in the stack)

**3. Human-in-the-loop is a stub**

`human_review` returns a string response. In production it should:
- Persist the ticket to a database or queue
- Send a notification (email, Slack, PagerDuty)
- Return a reference/ticket ID for the human to pick up
- Use LangGraph's `interrupt` mechanism to pause execution

#### Proposed Additions

| Addition | Implementation | Purpose |
|----------|---------------|---------|
| `@timed_node` decorator | Auto-injects `processing_time` | Consistent timing across all nodes |
| `latencies: Dict[str, float]` | `classifier: 0.003, urgency_assessor: 0.001` | Per-node breakdown in state |
| `paths_taken: list[str]` | `['validate', 'classifier', ..., 'respond']` | Verifiable path per ticket |
| LangSmith tracing | Auto-captured via SDK | Trace ID, error rates, path distributions |
| Persistence + notification | DB table + Slack/PagerDuty | Real human-in-the-loop |
| Feedback loop | Record human corrections | Tune keyword weights offline |

---

## 3. Summary: Current Code vs 3/3 Requirements

| Dimension | Current State | What's Needed for 3/3 |
|-----------|--------------|----------------------|
| **1. Simplicity vs Adaptability** | Sequential with one loopback | Discussion of design alternatives, explicit trade-off analysis |
| **2. Node Design & Workflow** | Clear separation but duplication, missing null guards | Eliminate duplicate logic, add null checks, decorator pattern for telemetry |
| **3. Confidence & Failure Paths** | Deterministic confidence, single retry, no exception handling | Calibrated confidence, multi-strategy retry, error boundaries, confidence bands |
| **4. Telemetry & HITL** | Timing in 5/7 nodes, checkpoint log | Full timing coverage, cumulative metrics, real HITL with interrupt |

---

## 4. Key File Paths

| File | Purpose | Lines |
|------|---------|-------|
| `src/langgraph_course/module_1/labs/tickets.py` | Main implementation (graph, nodes, state) | 330 |
| `src/langgraph_course/module_1/labs/data.py` | Sample ticket data | 40 |
| `tests/test_module_1/test_tickets.py` | 34 unit tests | 386 |
| `src/langgraph_course/utils/agentbase.py` | Abstract base class (`AgentBase`) | 50 |
| `src/langgraph_course/log.py` | Loguru configuration | 11 |

## 5. Key Lines Reference

| Lines | Element | Significance |
|-------|---------|--------------|
| 38–47 | `TicketState` | The entire data contract of the graph |
| 50–52 | `CONFIDENCE_THRESHOLD`, `MAX_RETRIES` | Key tuning parameters |
| 102–114 | `_get_ticket_category` | Primary classification logic (first pass) |
| 106, 108, 110, 112, 114 | `return` statements | Hardcoded confidence values |
| 165–186 | `_analysis_decision` | Conditional edge logic — threshold + retry budget |
| 189–222 | `retry_classifier` | Second-pass classification (broader keywords) |
| 225–241 | `human_review` | Human-in-the-loop checkpoint |
| 258–294 | `_build_graph` | Complete graph topology |
| 296–310 | `run()` | Entry point with state initialisation |
| 298 | `self.graph.invoke({...})` | The single invocation point (no error handling) |
