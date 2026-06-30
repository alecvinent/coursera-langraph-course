"""Legal document processing agent with resilient state management.

Implements a LangGraph agent that processes legal documents through a
multi-stage pipeline with error handling, fallback mechanisms, and
comprehensive audit/telemetry tracking.
"""

import re
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional, TypedDict

from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph

from langgraph_course.log import logger
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.decorators import timed_node
from langgraph_course.utils.llm import LLMFactory


# ---------------------------------------------------------------------------
# State schema (matches design doc exactly)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()




# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

COMPLEXITY_THRESHOLD_WORDS = 100

CLAUSE_INDICATORS = [
    r'\bwhereas\b', r'\bhereinafter\b', r'\bindemnif(y|ication)\b',
    r'\bconfidential\b', r'\btermination\b', r'\bgoverning\b',
    r'\barbitration\b', r'\bforce\s+majeure\b', r'\bwarrant(y|ies)\b',
    r'\bindemnification\b', r'\blimitation\s+of\s+liability\b',
    r'\bintellectual\s+property\b', r'\bdispute\s+resolution\b',
]

ENTITY_INDICATORS = [
    r'\bInc\.?\b', r'\bLLC\b', r'\bCorp\.?\b', r'\bCompany\b',
    r'\bParty\b', r'\bAgreement\b', r'\bLicensor\b', r'\bLicensee\b',
]

SIMPLE_CLAUSE_PATTERNS: list[tuple[str, str]] = [
    (r'payment\s+terms?\b', 'Payment Terms'),
    (r'\bterm\b', 'Term'),
    (r'\bconfidential\b', 'Confidentiality'),
    (r'\btermination\b', 'Termination'),
    (r'\bliability\b', 'Liability'),
    (r'\bindemnif', 'Indemnification'),
    (r'\bgoverning\s+law\b', 'Governing Law'),
    (r'\barbitration\b', 'Arbitration'),
    (r'\bwarrant', 'Warranty'),
    (r'\bforce\s+majeure\b', 'Force Majeure'),
]

COMPLEX_CLAUSE_PATTERNS: list[tuple[str, str]] = [
    (r'\bdispute\s+resolution\b', 'Dispute Resolution'),
    (r'\bseverability\b', 'Severability'),
    (r'\bentire\s+agreement\b', 'Entire Agreement'),
    (r'\bassignment\b', 'Assignment'),
    (r'\bwaiver\b', 'Waiver'),
    (r'\bnotice\b', 'Notice'),
    (r'\bsurvival\b', 'Survival'),
    (r'\bamendments?\b', 'Amendment'),
    (r'\bno\s+oral\s+modification\b', 'No Oral Modification'),
]


# ---------------------------------------------------------------------------
# Agent
# ---------------------------------------------------------------------------


class LegalDocumentAgent(AgentBase):
    """LangGraph agent for resilient legal document processing.

    Simulation flags (class-level, settable by tests):
        SIMULATE_API_FAILURE  — extract_document raises ConnectionError on every try
        SIMULATE_SYSTEM_DEGRADED — complex_path falls back to simple regex logic
        SIMULATE_REPAIR_FAILURE  — repair_attempt always fails
    """

    SIMULATE_API_FAILURE: bool = False
    SIMULATE_SYSTEM_DEGRADED: bool = False
    SIMULATE_REPAIR_FAILURE: bool = False

    def __init__(self, provider: str = 'openrouter', llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # ------------------------------------------------------------------
    # Nodes
    # ------------------------------------------------------------------

    @classmethod
    @timed_node('extract_document')
    def extract_document(cls, state: LegalDocumentState) -> Dict:
        """Simulate OCR extraction with retry + exponential backoff + regex fallback."""
        raw_text = state.get('raw_text', '')
        error_handling = dict(state.get('error_handling', {}))
        error_logs = list(error_handling.get('error_logs', []))
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        datasources_used = list(compliance.get('datasources_used', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('extract_document')

        max_retries = error_handling.get('max_retries', 3)
        retry_count = 0
        delay = 1.0
        last_error: Optional[Exception] = None

        while retry_count <= max_retries:
            try:
                if cls.SIMULATE_API_FAILURE:
                    raise ConnectionError(
                        'Simulated OCR API failure (attempt {})'.format(retry_count + 1)
                    )

                cleaned_text = raw_text.strip()
                if not cleaned_text:
                    raise ValueError('Empty document content')

                datasources_used.append('ocr_api')
                audit_trail.append(AuditRecord(
                    step='extract_document', action='ocr_extraction',
                    datasource='ocr_api', timestamp=_now(),
                ))

                return {
                    'extracted_clauses': cleaned_text,
                    'error_handling': {
                        **error_handling,
                        'retry_count': retry_count,
                        'error_logs': error_logs,
                    },
                    'compliance': {
                        'audit_trail': audit_trail,
                        'datasources_used': datasources_used,
                        'processing_outcome': 'success',
                    },
                    'execution_tracking': {
                        'processing_step': 'extract_document',
                        'timestamp': _now(),
                        'failed': False,
                        'processing_history': processing_history,
                    },
                }

            except (ConnectionError, TimeoutError) as e:
                retry_count += 1
                last_error = e
                error_logs.append(ErrorRecord(
                    step='extract_document', error_type=type(e).__name__,
                    message=str(e), timestamp=_now(),
                ))
                if retry_count <= max_retries:
                    logger.warning(
                        'Retry {}/{} for extract_document after {:.1f}s delay: {}',
                        retry_count, max_retries, delay, e,
                    )
                    time.sleep(delay)
                    delay *= 2.0
                else:
                    logger.error('All retries exhausted for extract_document: {}', e)

            except Exception as e:
                last_error = e
                error_logs.append(ErrorRecord(
                    step='extract_document', error_type=type(e).__name__,
                    message=str(e), timestamp=_now(),
                ))
                break

        # --- Fallback: regex extraction ---
        logger.warning('Falling back to regex extraction for document {}',
                       state.get('document_id', '?'))
        fallback_clauses = _regex_fallback_extract(raw_text)

        datasources_used.append('regex_fallback')
        audit_trail.append(AuditRecord(
            step='extract_document', action='regex_fallback_extraction',
            datasource='regex_fallback', timestamp=_now(),
        ))

        return {
            'extracted_clauses': fallback_clauses,
            'error_handling': {
                **error_handling,
                'fallback_used': True,
                'fallback_reason': 'OCR API unavailable: {}'.format(last_error) if last_error
                else 'Unknown error',
                'retry_count': retry_count,
                'error_logs': error_logs,
            },
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': datasources_used,
                'processing_outcome': 'partial' if raw_text.strip() else 'failed',
            },
            'execution_tracking': {
                'processing_step': 'extract_document',
                'timestamp': _now(),
                'failed': not bool(raw_text.strip()),
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('validate_quality')
    def validate_quality(cls, state: LegalDocumentState) -> Dict:
        """Check document quality: length, encoding, readability."""
        raw_text = state.get('raw_text', '')
        error_handling = dict(state.get('error_handling', {}))
        error_logs = list(error_handling.get('error_logs', []))
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('validate_quality')

        validation_errors: list[str] = []

        # 1 — Length check
        if not raw_text or not raw_text.strip():
            validation_errors.append('Empty document content')
            error_logs.append(ErrorRecord(
                step='validate_quality', error_type='corrupted_content',
                message='Document is empty', timestamp=_now(),
            ))

        # 2 — UTF-8 decodability
        try:
            raw_text.encode('utf-8').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            validation_errors.append('Content is not valid UTF-8')
            error_logs.append(ErrorRecord(
                step='validate_quality', error_type='encoding_error',
                message='Content is not valid UTF-8', timestamp=_now(),
            ))

        # 3 — Readability (printable-character ratio)
        if raw_text:
            printable = sum(1 for c in raw_text if c.isprintable() or c in '\n\r\t')
            ratio = printable / len(raw_text)
            if ratio < 0.5:
                validation_errors.append(
                    'Poor readability ratio: {:.1f}%'.format(ratio * 100)
                )
                error_logs.append(ErrorRecord(
                    step='validate_quality', error_type='corrupted_content',
                    message='Readability ratio {:.1f}% below 50%'.format(ratio * 100),
                    timestamp=_now(),
                ))

        failed = len(validation_errors) > 0

        audit_trail.append(AuditRecord(
            step='validate_quality', action='quality_validation',
            datasource='quality_check', timestamp=_now(),
        ))

        return {
            'validation_results': '; '.join(validation_errors) if validation_errors else 'pass',
            'error_handling': {
                **error_handling,
                'error_logs': error_logs,
            },
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': 'failed' if failed else 'success',
            },
            'execution_tracking': {
                'processing_step': 'validate_quality',
                'timestamp': _now(),
                'failed': failed,
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('repair_attempt')
    def repair_attempt(cls, state: LegalDocumentState) -> Dict:
        """Attempt to repair corrupted document content."""
        raw_text = state.get('raw_text', '')
        error_handling = dict(state.get('error_handling', {}))
        error_logs = list(error_handling.get('error_logs', []))
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('repair_attempt')

        if cls.SIMULATE_REPAIR_FAILURE:
            return {
                'validation_results': 'Repair failed: could not recover content',
                'error_handling': {
                    **error_handling,
                    'error_logs': error_logs,
                },
                'compliance': {
                    'audit_trail': audit_trail,
                    'datasources_used': compliance.get('datasources_used', []),
                    'processing_outcome': 'failed',
                },
                'execution_tracking': {
                    'processing_step': 'repair_attempt',
                    'timestamp': _now(),
                    'failed': True,
                    'processing_history': processing_history,
                },
            }

        # Replace non-printable chars with spaces, then normalize whitespace
        repaired = ''.join(
            c if c.isprintable() or c in '\n\r\t' else ' ' for c in raw_text
        )
        repaired = re.sub(r'\s+', ' ', repaired).strip()

        original_len = len(raw_text) if raw_text else 0
        repaired_len = len(repaired) if repaired else 0
        ratio = repaired_len / original_len if original_len > 0 else 0

        if ratio < 0.5:
            audit_trail.append(AuditRecord(
                step='repair_attempt', action='repair_failed',
                datasource='repair_attempt', timestamp=_now(),
            ))
            return {
                'validation_results': (
                    'Repair failed: recovered {:.1f}% of content'.format(
                        ratio * 100,
                    )
                ),
                'error_handling': {
                    **error_handling,
                    'error_logs': error_logs,
                },
                'compliance': {
                    'audit_trail': audit_trail,
                    'datasources_used': compliance.get('datasources_used', []),
                    'processing_outcome': 'failed',
                },
                'execution_tracking': {
                    'processing_step': 'repair_attempt',
                    'timestamp': _now(),
                    'failed': True,
                    'processing_history': processing_history,
                },
            }

        audit_trail.append(AuditRecord(
            step='repair_attempt', action='repair_successful',
            datasource='repair_attempt', timestamp=_now(),
        ))
        return {
            'raw_text': repaired,
            'validation_results': 'Repair successful: recovered {}/{} chars'.format(
                repaired_len, original_len,
            ),
            'error_handling': {
                **error_handling,
                'error_logs': error_logs,
            },
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': 'success',
            },
            'execution_tracking': {
                'processing_step': 'repair_attempt',
                'timestamp': _now(),
                'failed': False,
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('assess_complexity')
    def assess_complexity(cls, state: LegalDocumentState) -> Dict:
        """Determine simple vs complex based on word count and pattern heuristics."""
        raw_text = state.get('raw_text', '')
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('assess_complexity')

        words = raw_text.split()
        word_count = len(words)

        clause_count = sum(
            1 for p in CLAUSE_INDICATORS if re.search(p, raw_text, re.IGNORECASE)
        )
        entity_count = sum(
            1 for p in ENTITY_INDICATORS if re.search(p, raw_text, re.IGNORECASE)
        )

        complexity = 'complex' if (
            word_count >= COMPLEXITY_THRESHOLD_WORDS
            or clause_count >= 3
            or entity_count >= 3
        ) else 'simple'

        logger.info(
            'Complexity assessment: words={} clauses={} entities={} -> {}',
            word_count, clause_count, entity_count, complexity,
        )

        audit_trail.append(AuditRecord(
            step='assess_complexity', action='complexity_assessment',
            datasource='complexity_analysis', timestamp=_now(),
        ))

        return {
            'complexity': complexity,
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': compliance.get('processing_outcome', 'success'),
            },
            'execution_tracking': {
                'processing_step': 'assess_complexity',
                'timestamp': _now(),
                'failed': tracking.get('failed', False),
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('simple_path')
    def simple_path(cls, state: LegalDocumentState) -> Dict:
        """Fast regex-based clause extraction."""
        raw_text = state.get('raw_text', '')
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('simple_path')

        clauses_found: list[str] = []
        for pattern, clause_name in SIMPLE_CLAUSE_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                clauses_found.append(clause_name)

        extracted = '; '.join(clauses_found) if clauses_found else 'No standard clauses identified'
        validation = 'Extracted {} clauses via regex'.format(len(clauses_found))

        audit_trail.append(AuditRecord(
            step='simple_path', action='regex_extraction',
            datasource='regex_parser', timestamp=_now(),
        ))

        return {
            'extracted_clauses': extracted,
            'validation_results': validation,
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': compliance.get('processing_outcome', 'success'),
            },
            'execution_tracking': {
                'processing_step': 'simple_path',
                'timestamp': _now(),
                'failed': not bool(clauses_found),
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('complex_path')
    def complex_path(cls, state: LegalDocumentState) -> Dict:
        """Slower LLM-enhanced extraction with degraded-mode fallback."""
        raw_text = state.get('raw_text', '')
        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        error_handling = dict(state.get('error_handling', {}))
        error_logs = list(error_handling.get('error_logs', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('complex_path')

        # --- Degraded-mode fallback check ---
        if cls.SIMULATE_SYSTEM_DEGRADED:
            logger.warning(
                'System degraded — complex_path falling back to simple regex extraction'
            )
            error_logs.append(ErrorRecord(
                step='complex_path', error_type='system_degraded',
                message='System health flag is degraded, using regex fallback',
                timestamp=_now(),
            ))

            clauses_found: list[str] = []
            for pattern, clause_name in SIMPLE_CLAUSE_PATTERNS:
                if re.search(pattern, raw_text, re.IGNORECASE):
                    clauses_found.append(clause_name)

            extracted = (
                '; '.join(clauses_found)
                if clauses_found
                else 'No standard clauses identified (degraded mode)'
            )
            validation = 'Extracted {} clauses via regex fallback (degraded)'.format(
                len(clauses_found),
            )

            audit_trail.append(AuditRecord(
                step='complex_path', action='regex_fallback_extraction',
                datasource='regex_fallback_degraded', timestamp=_now(),
            ))

            return {
                'extracted_clauses': extracted,
                'validation_results': validation,
                'error_handling': {
                    **error_handling,
                    'fallback_used': True,
                    'fallback_reason': 'System degraded, regex fallback used',
                    'error_logs': error_logs,
                },
                'compliance': {
                    'audit_trail': audit_trail,
                    'datasources_used': compliance.get('datasources_used', []),
                    'processing_outcome': 'partial',
                },
                'execution_tracking': {
                    'processing_step': 'complex_path',
                    'timestamp': _now(),
                    'failed': not bool(clauses_found),
                    'processing_history': processing_history,
                },
            }

        # --- LLM-enhanced extraction (simulated) ---
        time.sleep(0.5)  # simulate slower LLM processing

        clauses_found = []
        for pattern, clause_name in SIMPLE_CLAUSE_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                clauses_found.append(clause_name)

        for pattern, clause_name in COMPLEX_CLAUSE_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                if clause_name not in clauses_found:
                    clauses_found.append(clause_name)

        extracted = (
            '; '.join(clauses_found)
            if clauses_found
            else 'No clauses identified via LLM extraction'
        )
        validation = 'LLM-enhanced extraction identified {} clauses'.format(len(clauses_found))

        audit_trail.append(AuditRecord(
            step='complex_path', action='llm_enhanced_extraction',
            datasource='llm_parser', timestamp=_now(),
        ))

        return {
            'extracted_clauses': extracted,
            'validation_results': validation,
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': compliance.get('processing_outcome', 'success'),
            },
            'execution_tracking': {
                'processing_step': 'complex_path',
                'timestamp': _now(),
                'failed': not bool(clauses_found),
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('generate_summary')
    def generate_summary(cls, state: LegalDocumentState) -> Dict:
        """Produce a summary factoring in degradation/outcome status."""
        extracted = state.get('extracted_clauses', '')
        validation = state.get('validation_results', '')
        compliance = state.get('compliance', {})
        outcome = compliance.get('processing_outcome', 'success')
        error_handling = state.get('error_handling', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('generate_summary')

        parts: list[str] = []

        if outcome == 'success':
            parts.append('Document processed successfully.')
        elif outcome == 'partial':
            parts.append('Document processed with degraded quality.')
            if error_handling.get('fallback_used'):
                parts.append('Fallback was used: {}'.format(
                    error_handling.get('fallback_reason', 'unknown'),
                ))
        else:
            parts.append('Document processing failed. Human review required.')

        if extracted:
            parts.append('Extracted clauses: {}'.format(extracted))
        if validation:
            parts.append('Validation: {}'.format(validation))

        summary = ' | '.join(parts)

        audit_trail.append(AuditRecord(
            step='generate_summary', action='summary_generation',
            datasource='summary_engine', timestamp=_now(),
        ))

        return {
            'summary': summary,
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': outcome,
            },
            'execution_tracking': {
                'processing_step': 'generate_summary',
                'timestamp': _now(),
                'failed': outcome == 'failed',
                'processing_history': processing_history,
            },
        }

    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: LegalDocumentState) -> Dict:
        """Log warning and return human-intervention response."""
        outcome = state.get('compliance', {}).get('processing_outcome', 'failed')
        error_handling = state.get('error_handling', {})
        retry_count = error_handling.get('retry_count', 0)
        fallback_used = error_handling.get('fallback_used', False)

        logger.warning(
            'Human review triggered for document {}: outcome={} retries={} fallback={}',
            state.get('document_id', '?'), outcome, retry_count, fallback_used,
        )

        compliance = state.get('compliance', {})
        audit_trail = list(compliance.get('audit_trail', []))
        tracking = dict(state.get('execution_tracking', {}))
        processing_history = list(tracking.get('processing_history', []))
        processing_history.append('human_review')

        audit_trail.append(AuditRecord(
            step='human_review', action='human_review_triggered',
            datasource='human_review', timestamp=_now(),
        ))

        return {
            'summary': (
                'This document requires human review. '
                'Processing outcome: {}. '
                'Retries: {}. '
                'Fallback used: {}. '
                'Document ID: {}'
            ).format(outcome, retry_count, fallback_used, state.get('document_id', '?')),
            'compliance': {
                'audit_trail': audit_trail,
                'datasources_used': compliance.get('datasources_used', []),
                'processing_outcome': outcome,
            },
            'execution_tracking': {
                'processing_step': 'human_review',
                'timestamp': _now(),
                'failed': True,
                'processing_history': processing_history,
            },
        }

    # ------------------------------------------------------------------
    # Routing conditions
    # ------------------------------------------------------------------

    @classmethod
    def _quality_routing(cls, state: LegalDocumentState) -> str:
        """After validate_quality: failed -> repair_attempt, else -> assess_complexity."""
        if state.get('execution_tracking', {}).get('failed', False):
            return 'repair_attempt'
        return 'assess_complexity'

    @classmethod
    def _repair_routing(cls, state: LegalDocumentState) -> str:
        """After repair_attempt: still failed -> human_review, else -> assess_complexity."""
        if state.get('execution_tracking', {}).get('failed', False):
            return 'human_review'
        return 'assess_complexity'

    @classmethod
    def _complexity_routing(cls, state: LegalDocumentState) -> str:
        """Route based on complexity, urgency, system health, and retry history."""
        urgency = state.get('urgency', 'standard')
        error_handling = state.get('error_handling', {})
        retry_count = error_handling.get('retry_count', 0)
        max_retries = error_handling.get('max_retries', 3)

        # Rush -> simple path (skip expensive LLM processing)
        if urgency == 'rush':
            return 'simple_path'

        # System degraded -> prefer simpler fallback
        if cls.SIMULATE_SYSTEM_DEGRADED:
            return 'simple_path'

        # High retry count -> skip to simple path
        if retry_count > max_retries // 2:
            return 'simple_path'

        complexity = state.get('complexity', 'simple')
        return 'simple_path' if complexity == 'simple' else 'complex_path'

    @classmethod
    def _summary_routing(cls, state: LegalDocumentState) -> str:
        """After generate_summary: success -> END, otherwise -> human_review."""
        outcome = state.get('compliance', {}).get('processing_outcome', 'success')
        if outcome == 'success':
            return 'end'
        return 'human_review'

    # ------------------------------------------------------------------
    # Build graph & run
    # ------------------------------------------------------------------

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(LegalDocumentState)

        workflow.add_node('extract_document', self.extract_document)
        workflow.add_node('validate_quality', self.validate_quality)
        workflow.add_node('repair_attempt', self.repair_attempt)
        workflow.add_node('assess_complexity', self.assess_complexity)
        workflow.add_node('simple_path', self.simple_path)
        workflow.add_node('complex_path', self.complex_path)
        workflow.add_node('generate_summary', self.generate_summary)
        workflow.add_node('human_review', self.human_review)

        workflow.set_entry_point('extract_document')

        workflow.add_edge('extract_document', 'validate_quality')

        workflow.add_conditional_edges(
            'validate_quality',
            self._quality_routing,
            {
                'repair_attempt': 'repair_attempt',
                'assess_complexity': 'assess_complexity',
            },
        )

        workflow.add_conditional_edges(
            'repair_attempt',
            self._repair_routing,
            {
                'human_review': 'human_review',
                'assess_complexity': 'assess_complexity',
            },
        )

        workflow.add_conditional_edges(
            'assess_complexity',
            self._complexity_routing,
            {
                'simple_path': 'simple_path',
                'complex_path': 'complex_path',
            },
        )

        workflow.add_edge('simple_path', 'generate_summary')
        workflow.add_edge('complex_path', 'generate_summary')

        workflow.add_conditional_edges(
            'generate_summary',
            self._summary_routing,
            {
                'end': END,
                'human_review': 'human_review',
            },
        )

        workflow.add_edge('human_review', END)

        return workflow.compile()

    def run(self, document: Dict) -> Dict:
        """Validate input, invoke the graph, and return the final state.

        *document* keys: ``document_id``, ``raw_text``, ``urgency`` (optional).
        """
        if document is None:
            logger.error('No document provided')
            return {'summary': 'Error: No document provided', 'total_processing_time': 0.0}

        doc_id = document.get('document_id', '')
        raw_text = document.get('raw_text', '')

        if not doc_id:
            logger.error('Invalid document: missing document_id')
            return {'summary': 'Error: Missing document ID', 'total_processing_time': 0.0}

        if not isinstance(raw_text, str):
            logger.error('Invalid document: raw_text must be a string')
            return {'summary': 'Error: Invalid document content', 'total_processing_time': 0.0}

        logger.info(
            'Processing document: id={} urgency={} length={}',
            doc_id, document.get('urgency', 'standard'), len(raw_text),
        )
        start = time.monotonic()

        initial_state: LegalDocumentState = {
            'document_id': doc_id,
            'raw_text': raw_text,
            'extracted_clauses': '',
            'validation_results': '',
            'summary': '',
            'urgency': document.get('urgency', 'standard'),
            'complexity': 'simple',
            'paths_taken': [],
            'latencies': {},
            'total_processing_time': 0.0,
            'execution_tracking': {
                'processing_step': 'init',
                'timestamp': _now(),
                'failed': False,
                'processing_history': [],
            },
            'error_handling': {
                'fallback_used': False,
                'fallback_reason': '',
                'retry_count': 0,
                'max_retries': 3,
                'error_logs': [],
            },
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'success',
            },
        }

        try:
            invoke_result = self.graph.invoke(initial_state)
        except Exception:
            logger.exception('Graph invocation failed for document {}', doc_id)
            elapsed = time.monotonic() - start
            return {
                'summary': 'Error: Internal processing failure',
                'total_processing_time': elapsed,
            }

        elapsed = time.monotonic() - start
        invoke_result['total_processing_time'] = elapsed
        logger.info(
            'Completed in {:.1f}ms: {}',
            elapsed * 1000, invoke_result.get('summary', '')[:80],
        )
        return invoke_result


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _regex_fallback_extract(text: str) -> str:
    """Basic regex-based extraction used when OCR/API is unavailable."""
    if not text or not text.strip():
        return 'No content to extract'
    clauses: list[str] = []
    for pattern, clause_name in SIMPLE_CLAUSE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            clauses.append(clause_name)
    return '; '.join(clauses) if clauses else 'No clauses identified'


# ---------------------------------------------------------------------------
# Sample documents
# ---------------------------------------------------------------------------

sample_documents: list[Dict[str, str]] = [
    {
        'document_id': 'DOC-001',
        'raw_text': (
            'This is a simple legal document. '
            'Payment terms are 30 days net. '
            'The term of this agreement is one year. '
            'Either party may terminate with 30 days notice.'
        ),
        'urgency': 'standard',
    },
    {
        'document_id': 'DOC-002',
        'raw_text': (
            'This Master Services Agreement (the "Agreement") is entered into by and between '
            'TechCorp Inc., a Delaware corporation ("Company"), and Client LLC ("Client"). '
            'WHEREAS, Company provides certain software services; and WHEREAS, Client desires '
            'to engage Company for such services. NOW, THEREFORE, the parties agree as follows: '
            '1. SERVICES. Company shall provide the services described in Exhibit A. '
            '2. PAYMENT. Client shall pay fees as set forth in Exhibit B. '
            '3. CONFIDENTIALITY. Each party shall maintain the confidentiality of the other\'s '
            'proprietary information. 4. INDEMNIFICATION. Company shall indemnify Client against '
            'any third-party claims. 5. LIMITATION OF LIABILITY. Neither party shall be liable '
            'for indirect or consequential damages. 6. TERMINATION. Either party may terminate '
            'this Agreement upon 30 days written notice. 7. GOVERNING LAW. This Agreement shall '
            'be governed by the laws of the State of Delaware. 8. DISPUTE RESOLUTION. Any disputes '
            'arising under this Agreement shall be resolved through binding arbitration. '
            '9. FORCE MAJEURE. Neither party shall be liable for delays caused by events beyond '
            'its reasonable control. 10. ENTIRE AGREEMENT. This Agreement constitutes the entire '
            'agreement between the parties. IN WITNESS WHEREOF, the parties have executed this '
            'Agreement as of the date first written above.'
        ),
        'urgency': 'standard',
    },
    {
        'document_id': 'DOC-003',
        'raw_text': 'Short',
        'urgency': 'standard',
    },
    {
        'document_id': 'DOC-004',
        'raw_text': 'This is an urgent legal document requiring immediate processing and review.',
        'urgency': 'rush',
    },
    {
        'document_id': 'DOC-005',
        'raw_text': '\x00\x01\x02\x03\x04\x05\x00\x01\x02\x03',
        'urgency': 'standard',
        'description': 'Corrupted binary content — triggers validate_quality failure, routes to repair_attempt, then human_review',
    },
    {
        'document_id': 'DOC-006',
        'raw_text': '',
        'urgency': 'standard',
        'description': 'Empty document — triggers extract_document fallback, validate_quality failure, routes to human_review',
    },
    {
        'document_id': 'DOC-007',
        'raw_text': '\x00\x01\x02' * 50 + 'confidential clause here',
        'urgency': 'standard',
        'description': 'Mostly binary with small readable fragment — repair recovers <50%, routes to human_review',
    },
]


if __name__ == '__main__':
    agent = LegalDocumentAgent(provider='openrouter')
    agent.print_graph()

    for doc in sample_documents:
        result = agent.run(doc)
        logger.info('  -> {}', result.get('summary', '')[:120])
