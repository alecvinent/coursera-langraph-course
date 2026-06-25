from unittest import TestCase
from unittest.mock import MagicMock, patch

from langchain_core.messages import AIMessage

from langgraph_course.agents import tools as T
from langgraph_course.agents.models import Customer, OrderDetail


class TestTools(TestCase):
    def setUp(self):
        T._clear()

    def tearDown(self):
        T._clear()

    def test_get_daily_menu_returns_items_with_categories(self):
        result = T.get_daily_menu.invoke({})
        self.assertIn("Espresso", result)
        self.assertIn("$3.50", result)
        self.assertIn("[coffee]", result)
        self.assertIn("Tags:", result)
        self.assertIn("Variations:", result)

    def test_get_recommendations_returns_all_menu_items(self):
        result = T.get_recommendations.invoke({})
        self.assertIn("Today's Recommendations", result)
        self.assertIn("Espresso", result)
        self.assertIn("Avocado Toast", result)
        self.assertIn("$7.50", result)

    def test_recommend_by_preference_vegetarian(self):
        result = T.recommend_by_preference.invoke({"preference": "vegetarian"})
        self.assertIn("Latte", result)
        self.assertIn("Croissant", result)
        self.assertIn("Avocado Toast", result)
        self.assertNotIn("Espresso", result)
        self.assertNotIn("Cold Brew", result)

    def test_recommend_by_preference_vegan(self):
        result = T.recommend_by_preference.invoke({"preference": "vegan"})
        self.assertIn("Espresso", result)
        self.assertIn("Avocado Toast", result)
        self.assertIn("Cold Brew", result)
        self.assertNotIn("Latte", result)
        self.assertNotIn("Croissant", result)

    def test_recommend_by_preference_category(self):
        result = T.recommend_by_preference.invoke({"preference": "coffee"})
        self.assertIn("Espresso", result)
        self.assertIn("Latte", result)
        self.assertIn("Cold Brew", result)
        self.assertNotIn("Croissant", result)
        self.assertNotIn("Avocado Toast", result)

    def test_recommend_by_preference_no_match(self):
        result = T.recommend_by_preference.invoke({"preference": "gluten"})
        self.assertIn("No items found", result)

    def test_create_order_appends_order_detail(self):
        T.create_order.invoke({"item_name": "Latte", "quantity": 2})
        self.assertEqual(len(T._orders), 1)
        item = T._orders[0]
        self.assertIsInstance(item, OrderDetail)
        self.assertEqual(item.product, "Latte")
        self.assertEqual(item.quantity, 2)

    def test_create_order_default_quantity(self):
        T.create_order.invoke({"item_name": "Espresso"})
        self.assertEqual(T._orders[0].quantity, 1)

    def test_create_order_looks_up_price_from_menu(self):
        T.create_order.invoke({"item_name": "latte", "quantity": 1})
        self.assertEqual(T._orders[0].price, 4.50)

    def test_create_order_looks_up_price_avocado_toast(self):
        T.create_order.invoke({"item_name": "avocado toast", "quantity": 1})
        self.assertEqual(T._orders[0].price, 7.50)

    def test_create_order_rejects_and_suggests_from_category(self):
        result = T.create_order.invoke({"item_name": "hamburger", "quantity": 1})
        self.assertIn("not on the menu", result)
        self.assertIn("breakfast", result)
        self.assertIn("Avocado Toast", result)
        self.assertEqual(len(T._orders), 0)

    def test_create_order_rejects_unknown_fallback(self):
        result = T.create_order.invoke({"item_name": "pizza", "quantity": 1})
        self.assertIn("not on the menu", result)
        self.assertIn("full menu", result)
        self.assertEqual(len(T._orders), 0)

    def test_get_orders_empty(self):
        result = T.get_orders.invoke({})
        self.assertIn("no orders", result.lower())

    def test_get_orders_after_create(self):
        T.create_order.invoke({"item_name": "Croissant", "quantity": 1})
        result = T.get_orders.invoke({})
        self.assertIn("Croissant", result)
        self.assertIn("Total", result)

    def test_set_customer_info_stores_customer(self):
        T.set_customer_info.invoke({
            "name": "Alice",
            "address": "123 Main St",
            "phone": "555-0100",
            "email": "alice@test.com",
        })
        self.assertIsNotNone(T._customer)
        self.assertIsInstance(T._customer, Customer)
        self.assertEqual(T._customer.name, "Alice")

    def test_send_order_fails_without_customer(self):
        result = T.send_order.invoke({})
        self.assertIn("name", result.lower())

    def test_send_order_fails_without_items(self):
        T.set_customer_info.invoke({
            "name": "Bob",
            "address": "456 Oak St",
            "phone": "555-0200",
            "email": "bob@test.com",
        })
        result = T.send_order.invoke({})
        self.assertIn("no items", result.lower())

    def test_send_order_clears_and_returns_receipt(self):
        T.set_customer_info.invoke({
            "name": "Carol",
            "address": "789 Pine St",
            "phone": "555-0300",
            "email": "carol@test.com",
        })
        T.create_order.invoke({"item_name": "Latte", "quantity": 2})
        result = T.send_order.invoke({})
        self.assertIn("Order confirmed", result)
        self.assertIn("Thank you", result)
        self.assertIn("Carol", result)
        self.assertIn("$9.00", result)
        self.assertEqual(T._orders, [])
        self.assertIsNone(T._customer)


class TestCafeAgentGraph(TestCase):
    def setUp(self):
        T._clear()

    def tearDown(self):
        T._clear()

    @patch("langgraph_course.agents.cafe_agent.LLMFactory.create")
    def test_plain_text_reply(self, mock_factory):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = AIMessage(content="Hello! How can I help?")
        mock_factory.return_value = mock_llm

        from langgraph_course.agents.cafe_agent import run_agent

        result = run_agent("Hi")
        self.assertEqual(result, "Hello! How can I help?")

    @patch("langgraph_course.agents.cafe_agent.LLMFactory.create")
    def test_tool_call_then_reply(self, mock_factory):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "get_daily_menu",
                    "args": {},
                    "id": "call_1",
                    "type": "tool_call",
                }],
            ),
            AIMessage(content="Here is today's menu!"),
        ]
        mock_factory.return_value = mock_llm

        from langgraph_course.agents.cafe_agent import run_agent

        result = run_agent("What's on the menu?")
        self.assertEqual(result, "Here is today's menu!")

    @patch("langgraph_course.agents.cafe_agent.LLMFactory.create")
    def test_out_of_scope_question(self, mock_factory):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.return_value = AIMessage(
            content="No tengo informacion sobre eso."
        )
        mock_factory.return_value = mock_llm

        from langgraph_course.agents.cafe_agent import run_agent

        result = run_agent("What is the weather?")
        self.assertEqual(result, "No tengo informacion sobre eso.")

    @patch("langgraph_course.agents.cafe_agent.LLMFactory.create")
    def test_multiple_tool_calls_chain(self, mock_factory):
        mock_llm = MagicMock()
        mock_llm.bind_tools.return_value = mock_llm
        mock_llm.invoke.side_effect = [
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "create_order",
                    "args": {"item_name": "Latte", "quantity": 2},
                    "id": "call_1",
                    "type": "tool_call",
                }],
            ),
            AIMessage(
                content="",
                tool_calls=[{
                    "name": "get_orders",
                    "args": {},
                    "id": "call_2",
                    "type": "tool_call",
                }],
            ),
            AIMessage(content="You have 2 Lattes in your order."),
        ]
        mock_factory.return_value = mock_llm

        from langgraph_course.agents.cafe_agent import run_agent

        result = run_agent("I want 2 lattes")
        self.assertEqual(result, "You have 2 Lattes in your order.")
        self.assertEqual(len(T._orders), 1)
        self.assertEqual(T._orders[0].product, "Latte")
        self.assertEqual(T._orders[0].quantity, 2)
