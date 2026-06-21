from unittest import TestCase
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

from langgraph_course.module_1.labs.customer_inquiry import (
    CustomerInquiryAgent,
    CustomerInquiryState,
    CustomerInquiryIntentType,
    CustomerInquiryWorkflowAction,
)


class TestCustomerInquiry(TestCase):
    def setUp(self) -> None:
        self.mock_llm = MagicMock()
        self.system = CustomerInquiryAgent(llm=self.mock_llm)

    def test_classify_detects_pricing_query(self) -> None:
        result = self.system.classify_intent(
            {"message": "What is the price?", "messages": [("user", "What is the price?")]}
        )
        self.assertEqual(result["intent"], CustomerInquiryIntentType.PRICING_QUERY.value)

    def test_classify_detects_return_request(self) -> None:
        result = self.system.classify_intent(
            {"message": "I want to return an item", "messages": [("user", "I want to return an item")]}
        )
        self.assertEqual(result["intent"], CustomerInquiryIntentType.RETURN_REQUEST.value)

    def test_classify_detects_unknown(self) -> None:
        result = self.system.classify_intent(
            {"message": "Hello, need help", "messages": [("user", "Hello, need help")]}
        )
        self.assertEqual(result["intent"], CustomerInquiryIntentType.UNKNOWN.value)

    def test_generate_response_pricing(self) -> None:
        result = self.system.generate_response(
            {"message": "price?", "intent": CustomerInquiryIntentType.PRICING_QUERY.value, "response": "", "messages": [("user", "price?")]}
        )
        self.assertIn("$100", result["response"])

    def test_generate_response_return(self) -> None:
        result = self.system.generate_response(
            {"message": "return", "intent": CustomerInquiryIntentType.RETURN_REQUEST.value, "response": "", "messages": [("user", "return")]}
        )
        self.assertIn("30 days", result["response"])

    def test_generate_response_unknown_falls_through(self) -> None:
        result = self.system.generate_response(
            {"message": "help", "intent": CustomerInquiryIntentType.UNKNOWN.value, "response": "", "messages": [("user", "help")]}
        )
        self.assertIsNotNone(result["response"])

    def test_human_review_returns_review_message(self) -> None:
        result = self.system.human_review({"message": "test", "response": ""})
        self.assertIn("Human review", result["response"])

    def test_human_review_adds_user_message_to_history(self) -> None:
        result = self.system.human_review({"message": "test", "response": ""})
        self.assertIn("messages", result)

    def test_build_graph_returns_compiled_state_graph(self) -> None:
        self.assertIsNotNone(self.system.graph)

    def test_chatbot_calls_llm_with_messages(self) -> None:
        self.mock_llm.invoke.return_value = AIMessage(content="LLM reply")
        result = self.system.chatbot({
            "message": "hi",
            "messages": [("user", "hi")],
        })
        self.assertEqual(result["response"], "LLM reply")

    def test_run_returns_response_for_pricing(self) -> None:
        result = self.system.run("whats your price range?")
        self.assertIn("$100", result.get("response", ""))

    def test_run_returns_response_for_return(self) -> None:
        result = self.system.run("I need to return something")
        self.assertIn("30 days", result.get("response", ""))

    def test_run_unknown_routes_to_chatbot(self) -> None:
        self.mock_llm.invoke.return_value = AIMessage(content="LLM fallback")
        result = self.system.run("hello")
        self.assertEqual(result["response"], "LLM fallback")
