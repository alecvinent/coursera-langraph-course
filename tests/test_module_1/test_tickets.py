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


def _base_state(**overrides: object) -> TicketState:
    state: TicketState = {
        'ticket': Ticket(topic='test'),
        'classification_results': None,
        'urgency_level': None,
        'routing_decision': '',
        'additional_metadata': '',
        'response': '',
        'total_processing_time': 0.0,
        'latencies': {},
        'paths_taken': [],
        'retry_count': 0,
    }
    state.update(**overrides)
    return state


class TestTicketClassifier(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_classify_billing_ticket(self) -> None:
        result = self.system.classify_ticket(_base_state(ticket=Ticket(topic='Billing issue with invoice')))
        self.assertEqual(result['classification_results'].category, TicketCategory.BILLING_ISSUE)
        self.assertGreaterEqual(result['classification_results'].confidence, 0.8)

    def test_classify_technical_ticket(self) -> None:
        result = self.system.classify_ticket(_base_state(ticket=Ticket(topic='Technical bug in dashboard')))
        self.assertEqual(result['classification_results'].category, TicketCategory.TECHNICAL_ISSUE)

    def test_classify_feature_request(self) -> None:
        result = self.system.classify_ticket(_base_state(ticket=Ticket(topic='Feature request for dark mode')))
        self.assertEqual(result['classification_results'].category, TicketCategory.FEATURE_REQUEST)

    def test_classify_account_management(self) -> None:
        result = self.system.classify_ticket(_base_state(ticket=Ticket(topic='Help reset my password')))
        self.assertEqual(result['classification_results'].category, TicketCategory.ACCOUNT_MANAGEMENT)

    def test_classify_unknown(self) -> None:
        result = self.system.classify_ticket(_base_state(ticket=Ticket(topic='Random gibberish text here')))
        self.assertEqual(result['classification_results'].category, TicketCategory.UNKNOWN)
        self.assertLess(result['classification_results'].confidence, 0.5)


class TestTicketUrgency(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_urgent_flag_sets_high(self) -> None:
        result = self.system.urgent_assessment(
            _base_state(ticket=Ticket(topic='Password reset', is_urgent=True))
        )
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.HIGH)

    def test_urgent_keyword_sets_high(self) -> None:
        result = self.system.urgent_assessment(
            _base_state(ticket=Ticket(topic='URGENT: server is down'))
        )
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.HIGH)

    def test_medium_keywords_set_medium(self) -> None:
        result = self.system.urgent_assessment(
            _base_state(ticket=Ticket(topic='I need help with my account'))
        )
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.MEDIUM)

    def test_low_urgency(self) -> None:
        result = self.system.urgent_assessment(
            _base_state(ticket=Ticket(topic='Feature suggestion for future'))
        )
        self.assertEqual(result['urgency_level'], TicketUrgencyLevel.LOW)


class TestTicketRouting(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_urgent_technical_to_senior_engineer(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.TECHNICAL_ISSUE, confidence=0.8),
            urgency_level=TicketUrgencyLevel.HIGH,
        ))
        self.assertIn('Senior Engineer', result['routing_decision'])

    def test_billing_to_billing_team(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.BILLING_ISSUE, confidence=0.8),
            urgency_level=TicketUrgencyLevel.LOW,
        ))
        self.assertIn('Billing Team', result['routing_decision'])

    def test_feature_to_product_team(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.FEATURE_REQUEST, confidence=0.8),
            urgency_level=TicketUrgencyLevel.LOW,
        ))
        self.assertIn('Product Team', result['routing_decision'])

    def test_account_to_account_manager(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.ACCOUNT_MANAGEMENT, confidence=0.8),
            urgency_level=TicketUrgencyLevel.LOW,
        ))
        self.assertIn('Account Manager', result['routing_decision'])

    def test_technical_to_technical_support(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.TECHNICAL_ISSUE, confidence=0.8),
            urgency_level=TicketUrgencyLevel.MEDIUM,
        ))
        self.assertIn('Technical Support Team', result['routing_decision'])

    def test_low_confidence_does_not_set_response(self) -> None:
        result = self.system.routing_decision(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.BILLING_ISSUE, confidence=0.4),
            urgency_level=TicketUrgencyLevel.LOW,
        ))
        self.assertNotIn('response', result)

    def test_none_classification_returns_fallback(self) -> None:
        result = self.system.routing_decision(_base_state(
            urgency_level=TicketUrgencyLevel.LOW,
        ))
        self.assertIn('general queue', result['routing_decision'])


class TestTicketRoutingCondition(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_high_confidence_known_category_routes_to_respond(self) -> None:
        result = self.system._routing_condition(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.TECHNICAL_ISSUE, confidence=0.85),
        ))
        self.assertEqual(result, 'respond')

    def test_low_confidence_within_retry_budget_routes_to_retry(self) -> None:
        result = self.system._routing_condition(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.TECHNICAL_ISSUE, confidence=0.40),
            retry_count=0,
        ))
        self.assertEqual(result, 'retry_classifier')

    def test_unknown_within_retry_budget_routes_to_retry(self) -> None:
        result = self.system._routing_condition(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.UNKNOWN, confidence=0.20),
            retry_count=0,
        ))
        self.assertEqual(result, 'retry_classifier')

    def test_low_confidence_after_max_retries_routes_to_human(self) -> None:
        result = self.system._routing_condition(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.TECHNICAL_ISSUE, confidence=0.40),
            retry_count=2,
        ))
        self.assertEqual(result, 'human_review')

    def test_none_classification_routes_to_human(self) -> None:
        result = self.system._routing_condition(_base_state())
        self.assertEqual(result, 'human_review')


class TestTicketRetryClassifier(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_retry_billing_match(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='need a receipt for my purchase'),
            retry_count=0,
        ))
        self.assertEqual(result['classification_results'].category, TicketCategory.BILLING_ISSUE)
        self.assertGreater(result['retry_count'], 0)

    def test_retry_technical_match(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='server crashed again'),
            retry_count=0,
        ))
        self.assertEqual(result['classification_results'].category, TicketCategory.TECHNICAL_ISSUE)

    def test_retry_feature_match(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='new feature idea'),
            retry_count=0,
        ))
        self.assertEqual(result['classification_results'].category, TicketCategory.FEATURE_REQUEST)

    def test_retry_account_match(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='login access problem'),
            retry_count=0,
        ))
        self.assertEqual(result['classification_results'].category, TicketCategory.ACCOUNT_MANAGEMENT)

    def test_retry_no_match_returns_unknown(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='completely unrelated topic here'),
            retry_count=1,
        ))
        self.assertEqual(result['classification_results'].category, TicketCategory.UNKNOWN)
        self.assertLess(result['classification_results'].confidence, 0.5)

    def test_retry_increments_counter(self) -> None:
        result = self.system.retry_classifier(_base_state(
            ticket=Ticket(topic='billing question'),
            retry_count=1,
        ))
        self.assertEqual(result['retry_count'], 2)


class TestTicketHumanReview(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = SupportTicketAgent(llm=self.mock_llm)

    def test_human_review_response_contains_confidence(self) -> None:
        result = self.system.human_review(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.UNKNOWN, confidence=0.15),
            urgency_level=TicketUrgencyLevel.LOW,
            retry_count=2,
        ))
        self.assertIn('human review', result['response'].lower())

    def test_human_review_reports_retry_count(self) -> None:
        result = self.system.human_review(_base_state(
            classification_results=TicketClassificationResult(category=TicketCategory.UNKNOWN, confidence=0.15),
            urgency_level=TicketUrgencyLevel.LOW,
            retry_count=2,
        ))
        self.assertIn('2 retries', result['response'])


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

    def test_run_unknown_ticket_requires_human_review(self) -> None:
        result = self.system.run(Ticket(topic='random text here'))
        self.assertIn('human review', result.get('response', '').lower())

    def test_run_urgent_technical_ticket(self) -> None:
        result = self.system.run(Ticket(topic='technical problem', is_urgent=True))
        self.assertIn('Senior Engineer', result.get('response', ''))

    def test_run_feature_request(self) -> None:
        result = self.system.run(Ticket(topic='feature suggestion'))
        self.assertIn('Product Team', result.get('response', ''))

    def test_run_account_management(self) -> None:
        result = self.system.run(Ticket(topic='account password reset'))
        self.assertIn('Account Manager', result.get('response', ''))

    def test_run_empty_topic_returns_error(self) -> None:
        result = self.system.run(Ticket(topic=''))
        self.assertIn('Error', result.get('response', ''))

    def test_run_none_ticket_returns_error(self) -> None:
        result = self.system.run(None)
        self.assertIn('Error', result.get('response', ''))

    def test_build_graph_returns_compiled_graph(self) -> None:
        self.assertIsNotNone(self.system.graph)

    def test_total_processing_time_is_recorded(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('total_processing_time', result)
        self.assertGreater(result['total_processing_time'], 0.0)

    def test_additional_metadata_is_set(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('additional_metadata', result)
        self.assertIn('category=', result['additional_metadata'])

    def test_latencies_recorded_in_result(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('latencies', result)
        self.assertIn('classifier', result['latencies'])
        self.assertIn('router', result['latencies'])

    def test_paths_taken_recorded_in_result(self) -> None:
        result = self.system.run(Ticket(topic='billing'))
        self.assertIn('paths_taken', result)
        self.assertIn('classifier', result['paths_taken'])
        self.assertIn('router', result['paths_taken'])

    def test_unknown_ticket_shows_retry_in_path(self) -> None:
        result = self.system.run(Ticket(topic='random text here'))
        self.assertIn('retry_classifier', result.get('paths_taken', []))
