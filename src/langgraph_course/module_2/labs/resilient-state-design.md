# Module 2 — Resilient State Management Design

## 1. State Schema

```python
from typing import Annotated, Optional, TypedDict
from datetime import datetime


class ErrorRecord(TypedDict):
    step: str
    error_type: str
    message: str
    timestamp: str


class AuditRecord(TypedDict):
    step: str
    action: str
    datasource: str
    timestamp: str


class ExecutionTracking(TypedDict):
    processing_step: str
    timestamp: str
    failed: bool
    processing_history: list[str]


class ErrorHandling(TypedDict):
    fallback_used: bool
    fallback_reason: str
    retry_count: int
    max_retries: int
    error_logs: list[ErrorRecord]


class Compliance(TypedDict):
    audit_trail: list[AuditRecord]
    datasources_used: list[str]
    processing_outcome: str  # "success" | "partial" | "failed"


class LegalDocumentState(TypedDict):
    document_id: str
    raw_text: str
    extracted_clauses: str
    validation_results: str
    summary: str
    urgency: str  # "rush" | "standard"
    complexity: str  # "simple" | "complex"
    paths_taken: list[str]
    latencies: dict[str, float]
    total_processing_time: float
    execution_tracking: ExecutionTracking
    error_handling: ErrorHandling
    compliance: Compliance
```

**Field descriptions:**
- `document_id` — unique identifier for audit traceability
- `raw_text` — original document content from OCR
- `extracted_clauses` — key legal clauses identified
- `validation_results` — pass/fail/warning per clause
- `summary` — generated document summary
- `urgency` — dictates whether fast path is used
- `complexity` — set by `assess_complexity` node
- `paths_taken` — ordered list of nodes executed (debugging + audit)
- `latencies` — per-node timing for performance monitoring
- `execution_tracking` — real-time step information
- `error_handling` — captures every failure and fallback decision
- `compliance` — immutable log for regulatory review

---

## 2. Error Handling Plan

### Scenario A: OCR / Legal Database API Failure

| Aspect | Detail |
|---|---|
| **Detection** | `try/except` on API call; catch `ConnectionError`, `TimeoutError`, `HTTPStatusError` |
| **Fallback** | Retry with exponential backoff (1s, 2s, 4s, max 3 retries). If all retries fail, switch to local regex-based extraction. Tag output as degraded. |
| **State updates** | `fallback_used=true`, `fallback_reason="OCR API unavailable"`, `error_logs.append({step, error_type, message, timestamp})`, `datasources_used.append("regex_fallback")` |

### Scenario B: Corrupted / Unreadable Document Content

| Aspect | Detail |
|---|---|
| **Detection** | Check text length (>0), encoding (UTF-8 decodable), readability score (char-to-word ratio within bounds) |
| **Fallback** | Attempt text cleanup (strip non-printable chars, re-decode with error ignoring). If cleanup yields <50% expected content, mark document as unrecoverable and route to human review. |
| **State updates** | `failed=true`, `error_logs.append({step: "validate_quality", error_type: "corrupted_content", ...})`, `retry_count+=1`. If retries exhausted → `processing_outcome="failed"` |

### Scenario C: Processing Timeout

| Aspect | Detail |
|---|---|
| **Detection** | `time.monotonic()` delta checked per node. If execution exceeds `max_node_duration`, raise a timeout. |
| **Fallback** | Interrupt current node, return whatever partial results exist, mark the step as `degraded`. Skip remaining dependent nodes and route to `generate_summary` with available data. |
| **State updates** | `processing_outcome="partial"`, `error_logs.append({step, error_type: "timeout", message: "exceeded N seconds"})`, `processing_history` recorded up to failed step |

---

## 3. Conditional Routing Logic

```
entry: extract_document
    │
    ▼
validate_quality
    ├── [failed] ──► repair_attempt
    │                   ├── [success] ──► assess_complexity
    │                   └── [failed] ──► human_review ──► END
    └── [passed] ──► assess_complexity
                        │
                        ▼
            ┌── word count threshold
            ├── clause count
            └── entity count
            │
        ┌───┴───┐
    simple     complex
        │         │
        ▼         ▼
  regex_path   llm_path
   (fast,      (LLM-enhanced,
    cheap)      thorough)
        │         │
        └───┬─────┘
            ▼
       generate_summary
            │
        ┌───┴───┐
    success  partial/fail
        │         │
        ▼         ▼
       END    human_review ──► END
```

**Decision factors:**

| Factor | Values | Impact on routing |
|---|---|---|
| **Document complexity** | `simple` / `complex` | Simple → regex path (low cost, fast). Complex → LLM path (accurate, expensive) |
| **System health** | `healthy` / `degraded` | If degraded, prefer simpler fallback paths regardless of complexity |
| **Processing history** | `retry_count` per doc type | If same doc type has failed >2 times today, skip to fallback directly |
| **Urgency** | `rush` / `standard` | Rush → skip non-essential validation, route to fastest available path |

---

## 4. Resilience Rationale

The design ensures reliability through three layered defenses:

**1. Retry with backoff** handles transient failures (network hiccups, rate limits, temporary service unavailability). This is the cheapest defense and covers ~80% of real-world API failures with minimal latency cost. Retries are bounded (`max_retries`) to prevent infinite loops.

**2. Graceful degradation** keeps the pipeline moving when a service is genuinely down. Regex fallback for OCR, cleanup attempts for corrupted text, and partial results on timeout all allow the system to produce *something* useful. Every degraded output is explicitly tagged (`processing_outcome="partial"`, `fallback_used=true`) so downstream consumers and auditors know the quality level.

**3. Human escalation** is reserved for cases the automated system cannot resolve: retries exhausted, unrecoverable corruption, or low-confidence fallback outputs. This prevents humans from becoming the bottleneck while ensuring no document silently produces bad results.

**Compliance is built into every state mutation.** The `Compliance` sub-state captures each step's action and data source. The `ErrorHandling` sub-state preserves the full failure trail. Together they produce an auditable record that satisfies the legal firm's regulatory requirements.
