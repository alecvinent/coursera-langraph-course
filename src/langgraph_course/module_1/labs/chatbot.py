from typing import Dict

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from langgraph_course.models import State
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.llm import LLMFactory


class ChatBot(AgentBase):
    def __init__(self) -> None:
        self.llm = None
        super().__init__()

    async def chatbot(self, state: State) -> Dict:
        prompt = state["messages"][-1].content
        content = await LLMFactory.call(prompt)
        logger.info("LLM responded: {}...", content[:60])
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=content)]}

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(State)
        workflow.add_node("chatbot", self.chatbot)
        workflow.add_edge(START, "chatbot")
        workflow.add_edge("chatbot", END)
        return workflow.compile()

    async def chat(self, message: str) -> str:
        result = await self.graph.ainvoke({"messages": [("user", message)]})
        return result["messages"][-1].content

    async def stream(self, message: str):
        async for event in self.graph.astream({"messages": [("user", message)]}):
            for value in event.values():
                yield value["messages"][-1].content


if __name__ == "__main__":
    import asyncio

    bot = ChatBot()
    bot.print_graph()

    question = "Recommend the top 10 famous restaurants in New York"

    async def main():
        print(f"\nUser: {question}")
        print("Assistant: ", end="", flush=True)
        async for chunk in bot.stream(question):
            print(chunk, end="", flush=True)
        print()

    asyncio.run(main())
