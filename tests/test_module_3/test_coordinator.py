from unittest import TestCase
from unittest.mock import MagicMock, patch

from langgraph.constants import END

from langgraph_course.module_3.labs.patterns.coordinator import (
    AgentType,
    CoordinatorState,
)
from langgraph_course.module_3.labs.patterns.coordinator import CoordinatorAgent


def _base_state(**overrides: object) -> CoordinatorState:
    state: CoordinatorState = {
        'messages': [],
        'next_agent': '',
        'response': '',
        'rounds': 0,
        'task_complete': False,
        'query': '',
        'total_processing_time': 0.0,
        'latencies': {},
        'paths_taken': [],
        'human_decision': '',
    }
    state.update(**overrides)
    return state


class TestCoordinatorClassification(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_classify_billing_returns_agent_a(self) -> None:
        result = self.system._classify_message('I have a billing question')
        self.assertEqual(result, AgentType.AGENT_A)

    def test_classify_payment_returns_agent_a(self) -> None:
        result = self.system._classify_message('Payment issue with my account')
        self.assertEqual(result, AgentType.AGENT_A)

    def test_classify_technical_returns_agent_b(self) -> None:
        result = self.system._classify_message('Technical bug in the system')
        self.assertEqual(result, AgentType.AGENT_B)

    def test_classify_support_returns_agent_b(self) -> None:
        result = self.system._classify_message('Need support with login')
        self.assertEqual(result, AgentType.AGENT_B)

    def test_classify_general_returns_agent_c(self) -> None:
        result = self.system._classify_message('Hello, how are you?')
        self.assertEqual(result, AgentType.AGENT_C)

    def test_classify_empty_returns_agent_c(self) -> None:
        result = self.system._classify_message('')
        self.assertEqual(result, AgentType.AGENT_C)


class TestCoordinatorNode(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_coordinator_sets_next_agent_for_billing(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "billing question")]))
        self.assertEqual(result['next_agent'], AgentType.AGENT_A)

    def test_coordinator_sets_next_agent_for_technical(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "technical error occurred")]))
        self.assertEqual(result['next_agent'], AgentType.AGENT_B)

    def test_coordinator_sets_next_agent_for_general(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "just saying hello")]))
        self.assertEqual(result['next_agent'], AgentType.AGENT_C)

    def test_coordinator_adds_routing_message(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "billing question")]))
        self.assertIn('messages', result)
        self.assertGreaterEqual(len(result['messages']), 1)

    def test_coordinator_increments_rounds(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "billing question")]))
        self.assertEqual(result['rounds'], 1)

    def test_coordinator_increments_from_existing_rounds(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "billing question")], rounds=1))
        self.assertEqual(result['rounds'], 2)


class TestCoordinatorAgentNodes(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_agent_a_returns_billing_response(self) -> None:
        result = self.system.agent_a(_base_state(total_processing_time=100.0))
        self.assertIn('Billing', result['response'])
        self.assertIn('messages', result)
        self.assertGreater(result['total_processing_time'], 0.0)
        self.assertFalse(result['task_complete'])

    def test_agent_b_returns_technical_response(self) -> None:
        result = self.system.agent_b(_base_state(total_processing_time=100.0))
        self.assertIn('Technical', result['response'])
        self.assertIn('messages', result)
        self.assertGreater(result['total_processing_time'], 0.0)
        self.assertFalse(result['task_complete'])

    def test_agent_c_returns_general_response(self) -> None:
        result = self.system.agent_c(_base_state(total_processing_time=100.0))
        self.assertIn('General', result['response'])
        self.assertIn('messages', result)
        self.assertGreater(result['total_processing_time'], 0.0)
        self.assertTrue(result['task_complete'])

    def test_agent_a_message_contains_support_keyword(self) -> None:
        result = self.system.agent_a(_base_state(total_processing_time=100.0))
        msg = result['messages'][-1]
        content = msg[1] if isinstance(msg, tuple) else msg.content
        self.assertIn('support', content.lower())

    def test_agent_c_force_completes_at_max_rounds(self) -> None:
        result = self.system.agent_c(_base_state(total_processing_time=100.0, rounds=5))
        self.assertTrue(result['task_complete'])


class TestCoordinatorRouter(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_router_returns_agent_a(self) -> None:
        result = self.system.coordinator_router(_base_state(next_agent=AgentType.AGENT_A))
        self.assertEqual(result, AgentType.AGENT_A)

    def test_router_returns_agent_b(self) -> None:
        result = self.system.coordinator_router(_base_state(next_agent=AgentType.AGENT_B))
        self.assertEqual(result, AgentType.AGENT_B)

    def test_router_returns_agent_c(self) -> None:
        result = self.system.coordinator_router(_base_state(next_agent=AgentType.AGENT_C))
        self.assertEqual(result, AgentType.AGENT_C)

    def test_router_defaults_to_agent_c(self) -> None:
        result = self.system.coordinator_router(_base_state())
        self.assertEqual(result, AgentType.AGENT_C)

    def test_router_never_returns_end(self) -> None:
        result = self.system.coordinator_router(_base_state(next_agent=AgentType.AGENT_A, rounds=10))
        self.assertEqual(result, AgentType.AGENT_A)


class TestAgentRouter(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_agent_router_returns_end_when_task_complete(self) -> None:
        result = self.system.agent_router(_base_state(task_complete=True))
        self.assertEqual(result, END)

    def test_agent_router_returns_coordinator_when_not_complete(self) -> None:
        result = self.system.agent_router(_base_state(task_complete=False))
        self.assertEqual(result, 'coordinator')

    def test_agent_router_defaults_to_coordinator(self) -> None:
        result = self.system.agent_router(_base_state())
        self.assertEqual(result, 'coordinator')


class TestHumanReviewRouter(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_human_review_logs_proposed_agent(self) -> None:
        with patch('langgraph_course.module_3.labs.patterns.coordinator.interrupt', return_value='approve') as mock_int:
            result = self.system.human_review(_base_state(next_agent=AgentType.AGENT_A))
        self.assertIn('latencies', result)
        self.assertIn('paths_taken', result)
        self.assertIn('human_review', result['paths_taken'])
        self.assertEqual(result.get('human_decision'), 'approve')
        mock_int.assert_called_once_with({'proposed_agent': AgentType.AGENT_A})

    def test_human_router_approve_routes_to_next_agent(self) -> None:
        r = self.system.human_router(_base_state(next_agent=AgentType.AGENT_A, human_decision='approve'))
        self.assertEqual(r, AgentType.AGENT_A)

    def test_human_router_redirect_routes_to_coordinator(self) -> None:
        r = self.system.human_router(_base_state(human_decision='redirect'))
        self.assertEqual(r, 'coordinator')

    def test_human_router_end_routes_to_end(self) -> None:
        r = self.system.human_router(_base_state(human_decision='end'))
        self.assertEqual(r, END)

    def test_human_router_returns_agent_a(self) -> None:
        r = self.system.human_router(_base_state(next_agent=AgentType.AGENT_A, human_decision='approve'))
        self.assertEqual(r, AgentType.AGENT_A)

    def test_human_router_returns_agent_b(self) -> None:
        r = self.system.human_router(_base_state(next_agent=AgentType.AGENT_B, human_decision='approve'))
        self.assertEqual(r, AgentType.AGENT_B)

    def test_human_router_returns_agent_c(self) -> None:
        r = self.system.human_router(_base_state(next_agent=AgentType.AGENT_C, human_decision='approve'))
        self.assertEqual(r, AgentType.AGENT_C)

    def test_human_router_defaults_to_agent_c(self) -> None:
        r = self.system.human_router(_base_state())
        self.assertEqual(r, AgentType.AGENT_C)


class TestCoordinatorRun(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorAgent(llm=self.mock_llm)

    def test_build_graph_returns_compiled_graph(self) -> None:
        self.assertIsNotNone(self.system.graph)

    def test_run_billing_crosses_all_agents(self) -> None:
        result = self.system.run('I have a billing issue')
        self.assertEqual(
            result['paths_taken'],
            ['coordinator', 'human_review', 'agent_a', 'coordinator', 'human_review', 'agent_b', 'coordinator', 'human_review', 'agent_c'],
        )
        self.assertEqual(result['rounds'], 3)

    def test_run_technical_crosses_all_agents(self) -> None:
        result = self.system.run('technical problem with login')
        self.assertEqual(
            result['paths_taken'],
            ['coordinator', 'human_review', 'agent_b', 'coordinator', 'human_review', 'agent_c'],
        )
        self.assertEqual(result['rounds'], 2)

    def test_run_general_ends_immediately(self) -> None:
        result = self.system.run('Hello, I need some help')
        self.assertEqual(result['paths_taken'], ['coordinator', 'human_review', 'agent_c'])
        self.assertEqual(result['rounds'], 1)

    def test_total_processing_time_is_recorded(self) -> None:
        result = self.system.run('billing question')
        self.assertIn('total_processing_time', result)
        self.assertGreater(result['total_processing_time'], 0.0)

    def test_latencies_recorded_in_result(self) -> None:
        result = self.system.run('billing question')
        self.assertIn('latencies', result)
        self.assertIn('coordinator', result['latencies'])
        self.assertIn('human_review', result['latencies'])
        self.assertIn('agent_a', result['latencies'])
        self.assertIn('agent_b', result['latencies'])
        self.assertIn('agent_c', result['latencies'])
