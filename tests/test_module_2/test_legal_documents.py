"""Tests for the legal document processing agent.

Mirrors the patterns in tests/test_module_1/test_tickets.py.
"""

from unittest import TestCase
from unittest.mock import MagicMock, patch

from langgraph_course.module_2.labs.legal_documents import (
    AuditRecord,
    Compliance,
    ErrorHandling,
    ErrorRecord,
    ExecutionTracking,
    LegalDocumentAgent,
    LegalDocumentState,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _base_state(**overrides: object) -> LegalDocumentState:
    state: LegalDocumentState = {
        'document_id': 'TEST-001',
        'raw_text': 'This is a test legal document with payment terms and conditions.',
        'extracted_clauses': '',
        'validation_results': '',
        'summary': '',
        'urgency': 'standard',
        'complexity': 'simple',
        'paths_taken': [],
        'latencies': {},
        'total_processing_time': 0.0,
        'execution_tracking': {
            'processing_step': 'init',
            'timestamp': '2024-01-01T00:00:00',
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
    state.update(**overrides)
    return state


# ===================================================================
# extract_document
# ===================================================================


class TestExtractDocument(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_extract_simple_document(self) -> None:
        """Normal extraction passes through cleaned text."""
        result = self.agent.extract_document(_base_state())
        self.assertIn('latencies', result)
        self.assertIn('paths_taken', result)
        self.assertIn('extract_document', result['paths_taken'])
        self.assertEqual(
            result['compliance']['processing_outcome'], 'success',
        )
        self.assertFalse(result['execution_tracking']['failed'])

    def test_extract_sets_extracted_clauses(self) -> None:
        result = self.agent.extract_document(_base_state())
        self.assertIn('extracted_clauses', result)
        self.assertGreater(len(result['extracted_clauses']), 0)

    def test_extract_records_audit_trail(self) -> None:
        result = self.agent.extract_document(_base_state())
        audit = result['compliance']['audit_trail']
        self.assertGreater(len(audit), 0)
        self.assertEqual(audit[0]['step'], 'extract_document')
        self.assertEqual(audit[0]['action'], 'ocr_extraction')

    def test_extract_records_datasource(self) -> None:
        result = self.agent.extract_document(_base_state())
        self.assertIn('ocr_api', result['compliance']['datasources_used'])

    def test_extract_empty_document_marks_failed(self) -> None:
        result = self.agent.extract_document(_base_state(raw_text=''))
        self.assertTrue(result['execution_tracking']['failed'])
        self.assertEqual(result['compliance']['processing_outcome'], 'failed')

    def test_extract_api_failure_uses_fallback(self) -> None:
        """Simulate API failure: should retry then use regex fallback."""
        LegalDocumentAgent.SIMULATE_API_FAILURE = True
        try:
            with patch('time.sleep'):
                result = self.agent.extract_document(_base_state())
        finally:
            LegalDocumentAgent.SIMULATE_API_FAILURE = False

        # Should have fallen back to regex
        self.assertTrue(result['error_handling']['fallback_used'])
        self.assertIn('regex_fallback', result['compliance']['datasources_used'])
        # Should have retried
        self.assertGreater(result['error_handling']['retry_count'], 0)
        # Should have error logs
        self.assertGreater(len(result['error_handling']['error_logs']), 0)
        first_error = result['error_handling']['error_logs'][0]
        self.assertEqual(first_error['step'], 'extract_document')
        self.assertEqual(first_error['error_type'], 'ConnectionError')

    def test_extract_api_failure_increments_retry_count(self) -> None:
        LegalDocumentAgent.SIMULATE_API_FAILURE = True
        try:
            with patch('time.sleep'):
                result = self.agent.extract_document(_base_state())
        finally:
            LegalDocumentAgent.SIMULATE_API_FAILURE = False

        self.assertGreater(result['error_handling']['retry_count'], 1)
        self.assertLessEqual(
            result['error_handling']['retry_count'],
            result['error_handling']['max_retries'] + 1,  # +1 for final attempt
        )


# ===================================================================
# validate_quality
# ===================================================================


class TestValidateQuality(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_valid_document_passes(self) -> None:
        result = self.agent.validate_quality(_base_state())
        self.assertEqual(result['validation_results'], 'pass')
        self.assertFalse(result['execution_tracking']['failed'])

    def test_empty_document_fails(self) -> None:
        result = self.agent.validate_quality(_base_state(raw_text=''))
        self.assertTrue(result['execution_tracking']['failed'])
        self.assertIn('Empty', result['validation_results'])
        self.assertEqual(result['compliance']['processing_outcome'], 'failed')

    def test_whitespace_only_document_fails(self) -> None:
        result = self.agent.validate_quality(_base_state(raw_text='   \n\n  '))
        self.assertTrue(result['execution_tracking']['failed'])
        self.assertIn('Empty', result['validation_results'])

    def test_binary_content_fails_readability(self) -> None:
        result = self.agent.validate_quality(_base_state(
            raw_text='\x00\x01\x02\x03\x04\x05',
        ))
        self.assertTrue(result['execution_tracking']['failed'])
        self.assertIn('readability', result['validation_results'].lower())

    def test_validation_adds_error_logs(self) -> None:
        result = self.agent.validate_quality(_base_state(raw_text=''))
        self.assertGreater(len(result['error_handling']['error_logs']), 0)
        log = result['error_handling']['error_logs'][0]
        self.assertEqual(log['step'], 'validate_quality')
        self.assertEqual(log['error_type'], 'corrupted_content')

    def test_validation_records_audit_trail(self) -> None:
        result = self.agent.validate_quality(_base_state())
        self.assertEqual(result['compliance']['audit_trail'][0]['step'], 'validate_quality')
        self.assertEqual(result['compliance']['audit_trail'][0]['action'], 'quality_validation')


# ===================================================================
# repair_attempt
# ===================================================================


class TestRepairAttempt(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_repair_succeeds_on_printable_content(self) -> None:
        result = self.agent.repair_attempt(_base_state(
            raw_text='  Hello\n\nWorld  ',
        ))
        self.assertFalse(result['execution_tracking']['failed'])
        self.assertEqual(result['compliance']['processing_outcome'], 'success')
        # Whitespace should be normalized
        self.assertIn('Hello World', result['raw_text'])

    def test_repair_strips_non_printable(self) -> None:
        result = self.agent.repair_attempt(_base_state(
            raw_text='Hello\x00World\x01Test',
        ))
        self.assertFalse(result['execution_tracking']['failed'])
        self.assertEqual(result['raw_text'], 'Hello World Test')

    def test_repair_fails_on_mostly_binary(self) -> None:
        result = self.agent.repair_attempt(_base_state(
            raw_text='\x00\x01\x02\x03' * 100 + 'short',
        ))
        self.assertTrue(result['execution_tracking']['failed'])
        self.assertEqual(result['compliance']['processing_outcome'], 'failed')

    def test_repair_empty_document_fails(self) -> None:
        result = self.agent.repair_attempt(_base_state(raw_text=''))
        self.assertTrue(result['execution_tracking']['failed'])

    def test_repair_simulated_failure(self) -> None:
        LegalDocumentAgent.SIMULATE_REPAIR_FAILURE = True
        try:
            result = self.agent.repair_attempt(_base_state())
        finally:
            LegalDocumentAgent.SIMULATE_REPAIR_FAILURE = False

        self.assertTrue(result['execution_tracking']['failed'])
        self.assertIn('could not recover', result['validation_results'])

    def test_repair_records_audit_trail(self) -> None:
        result = self.agent.repair_attempt(_base_state())
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('repair_successful', actions)

    def test_repair_failure_records_audit_trail(self) -> None:
        result = self.agent.repair_attempt(_base_state(raw_text=''))
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('repair_failed', actions)


# ===================================================================
# assess_complexity
# ===================================================================


class TestAssessComplexity(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_simple_document(self) -> None:
        result = self.agent.assess_complexity(_base_state(
            raw_text='Short document.',
        ))
        self.assertEqual(result['complexity'], 'simple')

    def test_complex_document_long_text(self) -> None:
        long_text = 'word ' * 200  # 200 words
        result = self.agent.assess_complexity(_base_state(raw_text=long_text))
        self.assertEqual(result['complexity'], 'complex')

    def test_complex_document_many_clauses(self) -> None:
        text = ('This agreement contains indemnification, confidentiality, '
                'termination clauses, governing law provisions, limitation of liability, '
                'and intellectual property rights.')
        result = self.agent.assess_complexity(_base_state(raw_text=text))
        self.assertEqual(result['complexity'], 'complex')

    def test_complex_document_many_entities(self) -> None:
        text = ('Acme Inc. and Beta LLC are parties. Corp X and Company Y '
                'are also involved in this Agreement.')
        result = self.agent.assess_complexity(_base_state(raw_text=text))
        self.assertEqual(result['complexity'], 'complex')

    def test_assess_complexity_records_audit_trail(self) -> None:
        result = self.agent.assess_complexity(_base_state())
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('complexity_assessment', actions)

    def test_assess_complexity_keeps_existing_outcome(self) -> None:
        result = self.agent.assess_complexity(_base_state(**{
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'partial',
            },
        }))
        self.assertEqual(result['compliance']['processing_outcome'], 'partial')


# ===================================================================
# simple_path
# ===================================================================


class TestSimplePath(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_extracts_clauses_from_document(self) -> None:
        result = self.agent.simple_path(_base_state(
            raw_text='Payment terms are net 30. Termination requires 30 days notice.',
        ))
        self.assertIn('Payment Terms', result['extracted_clauses'])
        self.assertIn('Termination', result['extracted_clauses'])

    def test_no_clauses_found(self) -> None:
        result = self.agent.simple_path(_base_state(
            raw_text='Hello world this is a test.',
        ))
        self.assertIn('No standard clauses', result['extracted_clauses'])

    def test_validation_result_mentions_regex(self) -> None:
        result = self.agent.simple_path(_base_state(
            raw_text='Payment terms are net 30.',
        ))
        self.assertIn('regex', result['validation_results'].lower())

    def test_simple_path_records_audit_trail(self) -> None:
        result = self.agent.simple_path(_base_state())
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('regex_extraction', actions)


# ===================================================================
# complex_path
# ===================================================================


class TestComplexPath(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_extracts_simple_and_complex_clauses(self) -> None:
        text = ('Payment terms are net 30. '
                'This agreement contains a dispute resolution clause. '
                'No oral modification shall be effective.')
        result = self.agent.complex_path(_base_state(raw_text=text))
        self.assertIn('Payment Terms', result['extracted_clauses'])
        self.assertIn('Dispute Resolution', result['extracted_clauses'])
        self.assertIn('No Oral Modification', result['extracted_clauses'])

    def test_no_clauses_found(self) -> None:
        result = self.agent.complex_path(_base_state(
            raw_text='Hello world this is a test.',
        ))
        self.assertIn('No clauses', result['extracted_clauses'])

    def test_validation_mentions_llm(self) -> None:
        result = self.agent.complex_path(_base_state(
            raw_text='Payment terms are net 30.',
        ))
        self.assertIn('LLM-enhanced', result['validation_results'])

    def test_degraded_mode_falls_back_to_regex(self) -> None:
        LegalDocumentAgent.SIMULATE_SYSTEM_DEGRADED = True
        try:
            with patch('time.sleep'):
                result = self.agent.complex_path(_base_state(
                    raw_text='Payment terms are net 30.',
                ))
        finally:
            LegalDocumentAgent.SIMULATE_SYSTEM_DEGRADED = False

        self.assertTrue(result['error_handling']['fallback_used'])
        self.assertIn('regex fallback', result['validation_results'].lower())
        self.assertEqual(result['compliance']['processing_outcome'], 'partial')

    def test_complex_path_records_audit_trail(self) -> None:
        with patch('time.sleep'):
            result = self.agent.complex_path(_base_state(
                raw_text='Payment terms.',
            ))
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('llm_enhanced_extraction', actions)


# ===================================================================
# generate_summary
# ===================================================================


class TestGenerateSummary(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_success_outcome(self) -> None:
        result = self.agent.generate_summary(_base_state(**{
            'extracted_clauses': 'Payment Terms',
            'validation_results': 'pass',
            'compliance': {
                'audit_trail': [],
                'datasources_used': ['ocr_api'],
                'processing_outcome': 'success',
            },
        }))
        self.assertIn('processed successfully', result['summary'].lower())
        self.assertIn('Payment Terms', result['summary'])

    def test_partial_outcome_includes_degradation_notes(self) -> None:
        result = self.agent.generate_summary(_base_state(**{
            'extracted_clauses': 'Payment Terms',
            'compliance': {
                'audit_trail': [],
                'datasources_used': ['regex_fallback'],
                'processing_outcome': 'partial',
            },
            'error_handling': {
                'fallback_used': True,
                'fallback_reason': 'OCR API unavailable',
                'retry_count': 3,
                'max_retries': 3,
                'error_logs': [],
            },
        }))
        self.assertIn('degraded', result['summary'].lower())
        self.assertIn('OCR API unavailable', result['summary'])

    def test_failed_outcome_mentions_human_review(self) -> None:
        result = self.agent.generate_summary(_base_state(**{
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'failed',
            },
        }))
        self.assertIn('human review', result['summary'].lower())

    def test_summary_records_audit_trail(self) -> None:
        result = self.agent.generate_summary(_base_state())
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('summary_generation', actions)


# ===================================================================
# human_review
# ===================================================================


class TestHumanReview(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_human_review_reports_outcome_and_retries(self) -> None:
        result = self.agent.human_review(_base_state(**{
            'document_id': 'DOC-X',
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'failed',
            },
            'error_handling': {
                'fallback_used': True,
                'fallback_reason': 'API unavailable',
                'retry_count': 3,
                'max_retries': 3,
                'error_logs': [],
            },
        }))
        summary = result['summary']
        self.assertIn('human review', summary.lower())
        self.assertIn('failed', summary)
        self.assertIn('3', summary)
        self.assertIn('True', summary)

    def test_human_review_records_audit_trail(self) -> None:
        result = self.agent.human_review(_base_state())
        actions = [r['action'] for r in result['compliance']['audit_trail']]
        self.assertIn('human_review_triggered', actions)

    def test_human_review_marks_failed(self) -> None:
        result = self.agent.human_review(_base_state())
        self.assertTrue(result['execution_tracking']['failed'])


# ===================================================================
# Routing conditions
# ===================================================================


class TestQualityRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_failed_validation_routes_to_repair(self) -> None:
        route = self.agent._quality_routing(_base_state(**{
            'execution_tracking': {
                'processing_step': 'validate_quality',
                'timestamp': 'now',
                'failed': True,
                'processing_history': ['validate_quality'],
            },
        }))
        self.assertEqual(route, 'repair_attempt')

    def test_passed_validation_routes_to_assess(self) -> None:
        route = self.agent._quality_routing(_base_state())
        self.assertEqual(route, 'assess_complexity')


class TestRepairRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_failed_repair_routes_to_human(self) -> None:
        route = self.agent._repair_routing(_base_state(**{
            'execution_tracking': {
                'processing_step': 'repair_attempt',
                'timestamp': 'now',
                'failed': True,
                'processing_history': ['repair_attempt'],
            },
        }))
        self.assertEqual(route, 'human_review')

    def test_successful_repair_routes_to_assess(self) -> None:
        route = self.agent._repair_routing(_base_state())
        self.assertEqual(route, 'assess_complexity')


class TestComplexityRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_simple_document_routes_to_simple_path(self) -> None:
        route = self.agent._complexity_routing(_base_state(complexity='simple'))
        self.assertEqual(route, 'simple_path')

    def test_complex_document_routes_to_complex_path(self) -> None:
        route = self.agent._complexity_routing(_base_state(complexity='complex'))
        self.assertEqual(route, 'complex_path')

    def test_rush_document_uses_simple_path(self) -> None:
        route = self.agent._complexity_routing(_base_state(
            complexity='complex', urgency='rush',
        ))
        self.assertEqual(route, 'simple_path')

    def test_degraded_system_uses_simple_path(self) -> None:
        LegalDocumentAgent.SIMULATE_SYSTEM_DEGRADED = True
        try:
            route = self.agent._complexity_routing(_base_state(complexity='complex'))
        finally:
            LegalDocumentAgent.SIMULATE_SYSTEM_DEGRADED = False
        self.assertEqual(route, 'simple_path')

    def test_high_retry_count_uses_simple_path(self) -> None:
        route = self.agent._complexity_routing(_base_state(**{
            'complexity': 'complex',
            'error_handling': {
                'fallback_used': False,
                'fallback_reason': '',
                'retry_count': 3,
                'max_retries': 3,
                'error_logs': [],
            },
        }))
        self.assertEqual(route, 'simple_path')


class TestSummaryRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_success_routes_to_end(self) -> None:
        route = self.agent._summary_routing(_base_state())
        self.assertEqual(route, 'end')

    def test_partial_routes_to_human_review(self) -> None:
        route = self.agent._summary_routing(_base_state(**{
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'partial',
            },
        }))
        self.assertEqual(route, 'human_review')

    def test_failed_routes_to_human_review(self) -> None:
        route = self.agent._summary_routing(_base_state(**{
            'compliance': {
                'audit_trail': [],
                'datasources_used': [],
                'processing_outcome': 'failed',
            },
        }))
        self.assertEqual(route, 'human_review')


# ===================================================================
# Full graph / run
# ===================================================================


class TestLegalDocumentBuildGraph(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_build_graph_returns_compiled_graph(self) -> None:
        self.assertIsNotNone(self.agent.graph)

    def test_graph_includes_all_nodes(self) -> None:
        """The compiled graph should reference all registered nodes."""
        # Check that nodes exist by running a simple document — it should not crash
        result = self.agent.run({
            'document_id': 'BUILD-TEST',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertIn('summary', result)
        self.assertIn('latencies', result)
        self.assertIn('paths_taken', result)


class TestLegalDocumentRun(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.agent = LegalDocumentAgent(llm=self.mock_llm)

    def test_run_simple_document(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30. Termination with 30 days notice.',
            'urgency': 'standard',
        })
        self.assertIn('summary', result)
        # Simple documents should succeed without human review
        self.assertNotIn('human review', result.get('summary', '').lower())

    def test_run_complex_document(self) -> None:
        text = 'word ' * 150  # 150 words
        result = self.agent.run({
            'document_id': 'DOC-002',
            'raw_text': text,
            'urgency': 'standard',
        })
        self.assertIn('summary', result)
        self.assertIn('paths_taken', result)

    def test_run_rush_document_uses_simple_path(self) -> None:
        text = 'word ' * 150  # complex by word count, but rush skips complex
        result = self.agent.run({
            'document_id': 'DOC-RUSH',
            'raw_text': text,
            'urgency': 'rush',
        })
        # Rush documents should not go through complex_path
        self.assertNotIn('complex_path', result.get('paths_taken', []))

    def test_run_corrupted_document_reaches_human_review(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-CORRUPT',
            'raw_text': '\x00\x01\x02',
            'urgency': 'standard',
        })
        # Corrupted content should eventually reach human review
        self.assertIn('human review', result.get('summary', '').lower())

    def test_run_empty_document_reaches_human_review(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-EMPTY',
            'raw_text': '',
            'urgency': 'standard',
        })
        self.assertIn('human review', result.get('summary', '').lower())

    def test_run_none_document_returns_error(self) -> None:
        result = self.agent.run(None)
        self.assertIn('Error', result.get('summary', ''))

    def test_run_missing_document_id_returns_error(self) -> None:
        result = self.agent.run({
            'raw_text': 'Some text',
            'urgency': 'standard',
        })
        self.assertIn('Error', result.get('summary', ''))

    def test_run_invalid_raw_text_type_returns_error(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 12345,
            'urgency': 'standard',
        })
        self.assertIn('Error', result.get('summary', ''))

    def test_total_processing_time_is_recorded(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms.',
            'urgency': 'standard',
        })
        self.assertIn('total_processing_time', result)
        self.assertGreater(result['total_processing_time'], 0.0)

    def test_latencies_recorded_in_result(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertIn('latencies', result)
        self.assertIn('extract_document', result['latencies'])
        self.assertIn('validate_quality', result['latencies'])
        self.assertIn('assess_complexity', result['latencies'])

    def test_paths_taken_recorded_in_result(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertIn('paths_taken', result)
        self.assertIn('extract_document', result['paths_taken'])
        self.assertIn('validate_quality', result['paths_taken'])

    def test_audit_trail_populated(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertGreater(len(result['compliance']['audit_trail']), 0)

    def test_compliance_datasources_used(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertIn('ocr_api', result['compliance']['datasources_used'])

    def test_execution_tracking_has_processing_history(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Hello world.',
            'urgency': 'standard',
        })
        self.assertIn('processing_history', result['execution_tracking'])
        self.assertGreater(len(result['execution_tracking']['processing_history']), 0)

    def test_successful_document_has_success_outcome(self) -> None:
        result = self.agent.run({
            'document_id': 'DOC-001',
            'raw_text': 'Payment terms are net 30.',
            'urgency': 'standard',
        })
        self.assertEqual(result['compliance']['processing_outcome'], 'success')
