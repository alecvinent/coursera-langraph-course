from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from langgraph_course.module_1.labs.chatbot import ChatBot


class TestChatBot(IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.bot = ChatBot()

    def test_graph_is_compiled(self) -> None:
        self.assertIsNotNone(self.bot.graph)

    @patch("langgraph_course.module_1.labs.chatbot.LLMFactory.call", new_callable=AsyncMock)
    async def test_chatbot_calls_llm_factory_and_returns_message(self, mock_call) -> None:
        mock_call.return_value = "Hello from LLM"
        from langchain_core.messages import HumanMessage
        result = await self.bot.chatbot({"messages": [HumanMessage(content="hi")]})
        self.assertIn("messages", result)
        self.assertEqual(len(result["messages"]), 1)
        self.assertEqual(result["messages"][-1].content, "Hello from LLM")

    @patch("langgraph_course.module_1.labs.chatbot.LLMFactory.call", new_callable=AsyncMock)
    async def test_chat_returns_llm_response(self, mock_call) -> None:
        mock_call.return_value = "I am fine, thank you."
        reply = await self.bot.chat("How are you?")
        self.assertEqual(reply, "I am fine, thank you.")

    @patch("langgraph_course.module_1.labs.chatbot.LLMFactory.call", new_callable=AsyncMock)
    async def test_chat_passes_user_message_as_prompt(self, mock_call) -> None:
        mock_call.return_value = "42"
        await self.bot.chat("What is the meaning of life?")
        mock_call.assert_called_once_with("What is the meaning of life?")

    @patch("langgraph_course.module_1.labs.chatbot.LLMFactory.call", new_callable=AsyncMock)
    async def test_stream_yields_content(self, mock_call) -> None:
        mock_call.return_value = "streamed"
        results = []
        async for chunk in self.bot.stream("hello"):
            results.append(chunk)
        self.assertEqual(results, ["streamed"])
