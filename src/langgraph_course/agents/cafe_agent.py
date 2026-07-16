from typing import Annotated, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from langgraph_course.agents.cafe.prompts import system_prompt as _PROMPT
from langgraph_course.agents.cafe.tools import (
    get_daily_menu,
)
from utils import LLMFactory


class CafeAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]


_TOOLS = [
    get_daily_menu,
    # get_recommendations,
    # recommend_by_preference,
    # create_order,
    # get_orders,
    # set_customer_info,
    # send_order,
]


def _build_agent(provider: str = "openrouter"):
    model = LLMFactory.create(provider=provider).bind_tools(_TOOLS)

    def agent_node(state: CafeAgentState) -> CafeAgentState:
        sys_msg = SystemMessage(content=_PROMPT.strip())
        response = model.invoke([sys_msg] + list(state["messages"]))
        return {"messages": [response]}

    def should_continue(state: CafeAgentState) -> str:
        last = state["messages"][-1]
        return "continue" if last.tool_calls else "end"

    workflow = StateGraph(CafeAgentState)
    workflow.add_node("agent", agent_node)
    workflow.add_node("tools", ToolNode(_TOOLS))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {"continue": "tools", "end": END},
    )
    workflow.add_edge("tools", "agent")
    return workflow.compile()


def run_agent(message: str, provider: str = "openrouter") -> str:
    app = _build_agent(provider=provider)
    result = app.invoke({"messages": [HumanMessage(content=message)]})

    for msg in reversed(result["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            return msg.content
    return ""


def run_agent_full(message: str, provider: str = "openrouter") -> dict:
    app = _build_agent(provider=provider)
    return app.invoke({"messages": [HumanMessage(content=message)]})


if __name__ == "__main__":
    print("Cafe Agent ready. Type your questions (or 'bye' to exit).\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if question.lower() in ("bye", "exit", "quit", "goodbye"):
            print("Assistant: Goodbye!")
            break
        reply = run_agent(question)
        print(f"Assistant: {reply}")
