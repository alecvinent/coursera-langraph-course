from unittest import TestCase
from unittest.mock import MagicMock

from langgraph_course.module_1.labs.tickets import (
    Ticket,
    TicketCategory,
    TicketClassificationResult,
    TicketState,
    TicketUrgencyLevel,
)
from langgraph_course.module_1.labs.tickets import SupportTicketAgent


class TestTicketClassifier(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_classify_billing_ticket(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Billing issue with invoice'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.classify_ticket(state)
        self.assertEqual(result['classification_results'].category, TicketCategory.BILLING_ISSUE)
        self.assertGreaterEqual(result['classification_results'].confidence, 0.8)

    def test_classify_technical_ticket(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Technical bug in dashboard'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.classify_ticket(state)
        self.assertEqual(result['classification_results'].category, TicketCategory.TECHNICAL_ISSUE)

    def test_classify_feature_request(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Feature request for dark mode'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.classify_ticket(state)
        self.assertEqual(result['classification_results'].category, TicketCategory.FEATURE_REQUEST)

    def test_classify_account_management(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Help reset my password'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.classify_ticket(state)
        self.assertEqual(result['classification_results'].category, TicketCategory.ACCOUNT_MANAGEMENT)

    def test_classify_unknown(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Random gibberish text here'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.classify_ticket(state)
        self.assertEqual(result['classification_results'].category, TicketCategory.UNKNOWN)
        self.assertLess(result['classification_results'].confidence, 0.5)


class TestTicketUrgency(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_urgent_flag_sets_high(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Password reset', is_urgent=True),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.urgent_assessment(state)
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.HIGH)

    def test_urgent_keyword_sets_high(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='URGENT: server is down'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.urgent_assessment(state)
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.HIGH)

    def test_medium_keywords_set_medium(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='I need help with my account'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.urgent_assessment(state)
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.MEDIUM)

    def test_low_urgency(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Feature suggestion for future'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.urgent_assessment(state)
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.LOW)


class TestTicketRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def _make_state(self, category: TicketCategory, urgency: TicketUrgencyLevel, confidence: float = 0.8) -> TicketState:
        return {
            'ticket': Ticket(topic='test'),
            'classification_results': TicketClassificationResult(category=category, confidence=confidence),
            'urgency_level': urgency,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }

    def test_urgent_technical_to_senior_engineer(self) -> None:
        result = self.system.routing_decision(
            self._make_state(TicketCategory.TECHNICAL_ISSUE, TicketUrgencyLevel.HIGH)
        )
        self.assertIn('Senior Engineer', result['routing_decision'])

    def test_billing_to_billing_team(self) -> None:
        result = self.system.routing_decision(
            self._make_state(TicketCategory.BILLING_ISSUE, TicketUrgencyLevel.LOW)
        )
        self.assertIn('Billing Team', result['routing_decision'])

    def test_feature_to_product_team(self) -> None:
        result = self.system.routing_decision(
            self._make_state(TicketCategory.FEATURE_REQUEST, TicketUrgencyLevel.LOW)
        )
        self.assertIn('Product Team', result['routing_decision'])

    def test_account_to_account_manager(self) -> None:
        result = self.system.routing_decision(
            self._make_state(TicketCategory.ACCOUNT_MANAGEMENT, TicketUrgencyLevel.LOW)
        )
        self.assertIn('Account Manager', result['routing_decision'])

    def test_technical_to_technical_support(self) -> None:
        result = self.system.routing_decision(
            self._make_state(TicketCategory.TECHNICAL_ISSUE, TicketUrgencyLevel.MEDIUM)
        )
        self.assertIn('Technical Support Team', result['routing_decision'])


class TestTicketAnalysisDecision(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def _make_state(self, category: TicketCategory, confidence: float, retry_count: int = 0) -> TicketState:
        return {
            'ticket': Ticket(topic='test'),
            'classification_results': TicketClassificationResult(category=category, confidence=confidence),
            'urgency_level': TicketUrgencyLevel.LOW,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': retry_count,
            'processing_time': 0.0,
        }

    def test_high_confidence_known_category_responds(self) -> None:
        result = self.system._analysis_decision(
            self._make_state(TicketCategory.TECHNICAL_ISSUE, 0.85)
        )
        self.assertEqual(result, 'respond')

    def test_low_confidence_triggers_retry(self) -> None:
        result = self.system._analysis_decision(
            self._make_state(TicketCategory.TECHNICAL_ISSUE, 0.40)
        )
        self.assertEqual(result, 'retry_classifier')

    def test_unknown_triggers_retry_first(self) -> None:
        result = self.system._analysis_decision(
            self._make_state(TicketCategory.UNKNOWN, 0.20)
        )
        self.assertEqual(result, 'retry_classifier')

    def test_unknown_after_max_retries_goes_human(self) -> None:
        result = self.system._analysis_decision(
            self._make_state(TicketCategory.UNKNOWN, 0.20, retry_count=2)
        )
        self.assertEqual(result, 'human_review')

    def test_low_confidence_after_max_retries_goes_human(self) -> None:
        result = self.system._analysis_decision(
            self._make_state(TicketCategory.TECHNICAL_ISSUE, 0.30, retry_count=2)
        )
        self.assertEqual(result, 'human_review')


class TestTicketValidation(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_valid_input_passes(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='Billing issue'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.validate_input(state)
        self.assertEqual(result, {})

    def test_none_ticket_adds_error(self) -> None:
        state: TicketState = {
            'ticket': None,
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.validate_input(state)
        self.assertIn('errors', result)
        self.assertIn('missing_ticket', result['errors'])

    def test_empty_topic_adds_error(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic=''),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system.validate_input(state)
        self.assertIn('invalid_topic', result['errors'])

    def test_validate_decision_returns_end_on_errors(self) -> None:
        state: TicketState = {
            'ticket': None,
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': ['missing_ticket'],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system._validate_decision(state)
        self.assertEqual(result, 'end')

    def test_validate_decision_returns_classifier_on_success(self) -> None:
        state: TicketState = {
            'ticket': Ticket(topic='test'),
            'classification_results': None,
            'urgency_level': None,
            'routing_decision': '',
            'additional_metadata': '',
            'response': '',
            'errors': [],
            'retry_count': 0,
            'processing_time': 0.0,
        }
        result = self.system._validate_decision(state)
        self.assertEqual(result, 'classifier')


class TestTicketRun(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_run_billing_ticket(self) -> None:
        result = self.system.run(Ticket(topic='billing issue'))
        self.assertIn('Billing Team', result.get('response', ''))

    def test_run_technical_ticket(self) -> None:
        result = self.system.run(Ticket(topic='technical bug'))
        self.assertIn('Technical Support Team', result.get('response', ''))

    def test_run_unknown_ticket_goes_to_human(self) -> None:
        result = self.system.run(Ticket(topic='random text here'))
        self.assertIn('human', result.get('response', '').lower())

    def test_run_urgent_technical_ticket(self) -> None:
        result = self.system.run(Ticket(topic='technical problem', is_urgent=True))
        self.assertIn('Senior Engineer', result.get('response', ''))

    def test_run_empty_topic_returns_error(self) -> None:
        result = self.system.run(Ticket(topic=''))
        self.assertIn('Error', result.get('response', ''))

    def test_run_feature_request(self) -> None:
        result = self.system.run(Ticket(topic='feature suggestion'))
        self.assertIn('Product Team', result.get('response', ''))

    def test_run_account_management(self) -> None:
        result = self.system.run(Ticket(topic='account password reset'))
        self.assertIn('Account Manager', result.get('response', ''))

    def test_build_graph_returns_compiled_graph(self) -> None:
        self.assertIsNotNone(self.system.graph)

    def test_processing_time_is_recorded(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('processing_time', result)

    def test_additional_metadata_is_set(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('additional_metadata', result)
        self.assertIn('category=', result['additional_metadata'])
