from abc import ABC, abstractmethod
from typing import Dict

from langgraph.graph.state import CompiledStateGraph
from loguru import logger


class AgentBase(ABC):
    CONTINUE = "continue"
    END_SIGNAL = "end"

    def __init__(self) -> None:
        self.graph = self._build_graph()

    @abstractmethod
    def _build_graph(self) -> CompiledStateGraph:
        ...

    def chatbot(self, state) -> Dict:
        response = self.llm.invoke(state["messages"])
        logger.info("Chatbot responded: {}...", response.content[:60])
        return {"response": response.content, "messages": [response]}

    @classmethod
    def get_last_message(cls, state) -> str:
        if "messages" in state and state["messages"]:
            msg = state["messages"][-1]
            if isinstance(msg, tuple):
                return msg[1]
            return msg.content
        return state.get("message", "")

    @classmethod
    def should_continue(cls, state) -> str:
        last = cls.get_last_message(state).lower()
        if any(word in last for word in ("bye", "goodbye", "exit", "quit", "done", "end conversation", "that's all", "no more")):
            return cls.END_SIGNAL
        return cls.CONTINUE

    def run(self, question: str) -> Dict:
        logger.info("Processing inquiry: {!r}", question)
        result = self.graph.invoke({"messages": [("user", question)]})
        logger.info("Result: {}", result.get("response", ""))
        return result

    def print_graph(self) -> None:
        graph = self.graph.get_graph(xray=True)
        print(graph.draw_ascii())
        print("\n--- Mermaid ---\n")
        print(graph.draw_mermaid())
