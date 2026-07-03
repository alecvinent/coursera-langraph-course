from unittest import TestCase
from unittest.mock import MagicMock, patch

from langgraph.constants import END

from langgraph_course.module_3.labs.patterns.coordinator_cafe import (
    CafeAgentType,
    CoordinatorCafeState,
)
from langgraph_course.module_3.labs.patterns.coordinator_cafe import CoordinatorCafeAgent


def _base_state(**overrides: object) -> CoordinatorCafeState:
    state: CoordinatorCafeState = {
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


class TestCafeClassification(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_menu_keyword_routes_to_menu(self) -> None:
        self.assertEqual(self.system._classify_message("What's on the menu?"), CafeAgentType.MENU)

    def test_specials_routes_to_menu(self) -> None:
        self.assertEqual(self.system._classify_message("Any specials today?"), CafeAgentType.MENU)

    def test_coffee_routes_to_menu(self) -> None:
        self.assertEqual(self.system._classify_message("What coffee options do you have?"), CafeAgentType.MENU)

    def test_order_routes_to_order(self) -> None:
        self.assertEqual(self.system._classify_message("I want to order a latte"), CafeAgentType.ORDER)

    def test_buy_routes_to_order(self) -> None:
        self.assertEqual(self.system._classify_message("I'd like to buy a croissant"), CafeAgentType.ORDER)

    def test_price_routes_to_order(self) -> None:
        self.assertEqual(self.system._classify_message("How much does it cost?"), CafeAgentType.ORDER)

    def test_greeting_routes_to_customer(self) -> None:
        self.assertEqual(self.system._classify_message("Hello, I need help"), CafeAgentType.CUSTOMER)

    def test_delivery_routes_to_customer(self) -> None:
        self.assertEqual(self.system._classify_message("Set up delivery please"), CafeAgentType.CUSTOMER)


class TestCafeCoordinatorNode(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_coordinator_sets_menu_agent(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "what's on the menu?")]))
        self.assertEqual(result['next_agent'], CafeAgentType.MENU)

    def test_coordinator_sets_order_agent(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "i want to order")]))
        self.assertEqual(result['next_agent'], CafeAgentType.ORDER)

    def test_coordinator_sets_customer_agent(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "hello")]))
        self.assertEqual(result['next_agent'], CafeAgentType.CUSTOMER)

    def test_coordinator_increments_rounds(self) -> None:
        result = self.system.coordinator(_base_state(messages=[("user", "menu please")]))
        self.assertEqual(result['rounds'], 1)


class TestCafeAgentNodes(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_menu_agent_response(self) -> None:
        result = self.system.menu_agent(_base_state(total_processing_time=100.0))
        self.assertIn('Menu', result['response'])
        self.assertFalse(result['task_complete'])

    def test_order_agent_response(self) -> None:
        result = self.system.order_agent(_base_state(total_processing_time=100.0))
        self.assertIn('Order', result['response'])
        self.assertFalse(result['task_complete'])

    def test_customer_agent_response(self) -> None:
        result = self.system.customer_agent(_base_state(total_processing_time=100.0))
        self.assertIn('Customer', result['response'])
        self.assertTrue(result['task_complete'])

    def test_menu_message_triggers_order_keyword(self) -> None:
        result = self.system.menu_agent(_base_state(total_processing_time=100.0))
        msg = result['messages'][-1]
        content = msg[1] if isinstance(msg, tuple) else msg.content
        self.assertIn('order', content.lower())


class TestCafeHumanReview(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_human_review_logs_proposed_agent(self) -> None:
        with patch('langgraph_course.module_3.labs.patterns.coordinator_cafe.interrupt', return_value='approve') as mock_int:
            result = self.system.human_review(_base_state(next_agent=CafeAgentType.ORDER))
        self.assertIn('latencies', result)
        self.assertIn('paths_taken', result)
        self.assertIn('human_review', result['paths_taken'])
        self.assertEqual(result.get('human_decision'), 'approve')
        mock_int.assert_called_once_with({'proposed_agent': CafeAgentType.ORDER})

    def test_human_router_approve_routes_to_next_agent(self) -> None:
        r = self.system.human_router(_base_state(next_agent=CafeAgentType.ORDER, human_decision='approve'))
        self.assertEqual(r, CafeAgentType.ORDER)

    def test_human_router_redirect_routes_to_coordinator(self) -> None:
        r = self.system.human_router(_base_state(human_decision='redirect'))
        self.assertEqual(r, 'coordinator')

    def test_human_router_end_routes_to_end(self) -> None:
        r = self.system.human_router(_base_state(human_decision='end'))
        self.assertEqual(r, END)

    def test_human_router_returns_next_agent(self) -> None:
        r = self.system.human_router(_base_state(next_agent=CafeAgentType.ORDER, human_decision='approve'))
        self.assertEqual(r, CafeAgentType.ORDER)

    def test_human_router_defaults_to_customer(self) -> None:
        r = self.system.human_router(_base_state())
        self.assertEqual(r, CafeAgentType.CUSTOMER)


class TestCafeRouters(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_coordinator_router_returns_next_agent(self) -> None:
        r = self.system.coordinator_router(_base_state(next_agent=CafeAgentType.ORDER))
        self.assertEqual(r, CafeAgentType.ORDER)

    def test_coordinator_router_defaults_to_customer(self) -> None:
        r = self.system.coordinator_router(_base_state())
        self.assertEqual(r, CafeAgentType.CUSTOMER)

    def test_agent_router_ends_when_complete(self) -> None:
        r = self.system.agent_router(_base_state(task_complete=True))
        self.assertEqual(r, END)

    def test_agent_router_loops_to_coordinator(self) -> None:
        r = self.system.agent_router(_base_state(task_complete=False))
        self.assertEqual(r, 'coordinator')


class TestCafeRun(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CoordinatorCafeAgent(llm=self.mock_llm)

    def test_build_graph_returns_compiled(self) -> None:
        self.assertIsNotNone(self.system.graph)

    def test_menu_crosses_to_order_then_customer(self) -> None:
        result = self.system.run("What's on the menu?")
        self.assertEqual(
            result['paths_taken'],
            ['coordinator', 'human_review', 'menu_agent', 'coordinator', 'human_review', 'order_agent', 'coordinator', 'human_review', 'customer_agent'],
        )

    def test_order_crosses_to_customer(self) -> None:
        result = self.system.run("I want to order a latte")
        self.assertEqual(
            result['paths_taken'],
            ['coordinator', 'human_review', 'order_agent', 'coordinator', 'human_review', 'customer_agent'],
        )

    def test_customer_ends_immediately(self) -> None:
        result = self.system.run("Hello, I need help")
        self.assertEqual(result['paths_taken'], ['coordinator', 'human_review', 'customer_agent'])

    def test_latencies_recorded(self) -> None:
        result = self.system.run("menu please")
        self.assertIn('latencies', result)
        self.assertIn('coordinator', result['latencies'])
        self.assertIn('human_review', result['latencies'])
        self.assertIn('menu_agent', result['latencies'])
