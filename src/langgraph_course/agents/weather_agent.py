from typing import Literal, TypedDict, Annotated, Sequence, Any

import requests
from langchain_core.messages import BaseMessage
from langchain_core.tools import tool
from langgraph.graph import END, START, StateGraph, add_messages
from langgraph.prebuilt import ToolNode

from langgraph_course.log import logger
from langgraph_course.utils.llm import LLMFactory
from langgraph_course.utils.request import get_json


@tool
def get_weather(location: str) -> str:
    """Get the weather for a given location."""
    logger.info(f"Getting weather for {location}")
    url = f'http://localhost:8000/weather/{location}'

    logger.info(f"Fetching weather data from {url}")

    try:
        return get_json(url)
    except requests.RequestException as e:
        return f"Error fetching weather data: {e}"


@tool
def get_weather_forecast_icon(location: str):
    """Get the weather forecast icon URL for a given location."""
    logger.info(f"Fetching weather forecast icon for {location}")
    url = f'http://localhost:8000/weather/{location}'

    try:
        data = get_json(url)
        daily = data.get("daily", [])
        if daily:
            return {
                'weather_image': daily[0].get('weather_image') or 'https://via.placeholder.com/150'
            }
        return "No forecast data available"
    except (requests.RequestException, ValueError, KeyError) as e:
        return f"Error fetching weather icon: {e}"


@tool
def get_cafe_daily_menu():
    """Get the daily menu for a cafe."""
    logger.info("Fetching cafe menu...")

    url = 'http://localhost:3000/api/v1/daily-menu'
    try:
        return get_json(url)
    except requests.RequestException as e:
        return f"Error fetching cafe menu: {e}"


ENABLED_TOOLS = [
    get_weather,
    get_weather_forecast_icon,
    get_cafe_daily_menu
]


class WeatherAgentState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    weather_image: str


class WeatherAgent:
    def __init__(self, provider: str = "openrouter"):
        self.llm = LLMFactory.create(
            provider=provider,
        ).bind_tools(ENABLED_TOOLS)
        self.graph = self._configure_workflow().compile()

    def call_model(self, state: WeatherAgentState):
        logger.info("Calling model...")

        invoker_response = self.llm.invoke(state["messages"])
        return {"messages": [invoker_response]}

    def should_continue(self, state: WeatherAgentState) -> Literal["tools", END]:
        logger.info("Checking if agent should continue...")

        last_message = state["messages"][-1]
        if last_message.tool_calls:
            return "tools"
        return END

    def _configure_workflow(self):
        workflow = StateGraph(WeatherAgentState)

        tool_node = ToolNode(ENABLED_TOOLS)

        workflow.add_node('agent', self.call_model)
        workflow.add_node('tools', tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges(
            "agent",
            self.should_continue,
            # {"continue": "tools", "end": END}
        )
        workflow.add_edge("tools", "agent")

        return workflow

    def run_agent(self, message: str):
        return self.graph.invoke({"messages": [message]})

    def print_graph(self) -> None:
        graph = self.graph.get_graph(xray=True)
        logger.info(graph.draw_ascii())
        logger.info("\n--- Mermaid ---\n")
        logger.info(graph.draw_mermaid())


if __name__ == "__main__":
    agent = WeatherAgent()

    questions = ["What's the weather in London?", "What's the weather in Paris?"]
    for question in questions:
        response = agent.run_agent(question)
        content = response.get("messages")[-1].content
        logger.info(content)
