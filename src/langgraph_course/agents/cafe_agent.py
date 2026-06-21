from enum import Enum
from typing import TypedDict, Dict, Annotated

from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from loguru import logger

from langgraph_course.module_1.labs.data import cafe_data
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.llm import LLMFactory


class CafeAgentIntentType(Enum):
    CHAT = 'CHAT'
    REQUEST_DAILY_MENU = 'REQUEST_DAILY_MENU'
    REQUEST_RECOMMENDATION = 'REQUEST_RECOMMENDATION'
    CREATE_ORDER = 'CREATE_ORDER'
    REVIEW_ORDER = 'REVIEW_ORDER'
    SEND_ORDER = 'SEND_ORDER'


class CafeAgentState(TypedDict):
    messages: Annotated[list, add_messages]
    intent: CafeAgentIntentType
    response: str
    daily_menu: list
    recommendations: list


class CafeAgent(AgentBase):
    def __init__(self, provider: str = "auto", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    def _build_graph(self):
        workflow = StateGraph(CafeAgentState)

        workflow.add_node('classify intent', self.classify_intent)
        workflow.add_node('get_daily_menu', self.get_daily_menu)
        workflow.add_node('get_recommendations', self.get_recommendations)
        workflow.add_node('chat', self.chatbot)
        workflow.add_node('respond', self.generate_response)

        workflow.set_entry_point('classify intent')

        workflow.add_conditional_edges(
            'classify intent', self._route_intent, {
                CafeAgentIntentType.REQUEST_DAILY_MENU: 'get_daily_menu',
                CafeAgentIntentType.REQUEST_RECOMMENDATION: 'get_recommendations',
                CafeAgentIntentType.CHAT: 'chat',
                CafeAgentIntentType.CREATE_ORDER: 'chat',
                CafeAgentIntentType.REVIEW_ORDER: 'chat',
                CafeAgentIntentType.SEND_ORDER: 'chat',
            }
        )
        workflow.add_edge('get_daily_menu', 'respond')
        workflow.add_edge('get_recommendations', 'respond')
        workflow.add_edge('chat', 'respond')
        workflow.add_edge('respond', END)

        return workflow.compile()

    @classmethod
    def _route_intent(cls, state: CafeAgentState) -> CafeAgentIntentType:
        return state['intent']

    def classify_intent(self, state: CafeAgentState) -> Dict:
        message = self.get_last_message(state)
        intent = self._classify_message(message)
        return {'intent': intent}

    RESPONSE_TEMPLATES = {
        CafeAgentIntentType.REQUEST_DAILY_MENU: "Today's menu:\n{items}",
        CafeAgentIntentType.REQUEST_RECOMMENDATION: "Recommendations:\n{items}",
    }

    @staticmethod
    def _format_items(items: list) -> str:
        return "\n".join(f"- {i['name']}: ${i['price']}" for i in items)

    def generate_response(self, state: CafeAgentState) -> Dict:
        intent = state["intent"]
        template = self.RESPONSE_TEMPLATES.get(intent)
        if template:
            data_key = "daily_menu" if intent == CafeAgentIntentType.REQUEST_DAILY_MENU else "recommendations"
            items = self._format_items(state.get(data_key, []))
            response = template.format(items=items)
        else:
            response = self._create_response(intent)
        logger.info("Auto respond to {}: {}", intent, response)
        return {"response": response}

    def get_daily_menu(self, state: CafeAgentState) -> Dict:
        logger.info("Getting daily menu")
        return {
            'daily_menu': cafe_data.get('daily_menu', []),
        }

    def get_recommendations(self, state: CafeAgentState) -> Dict:
        logger.info("Getting recommendations")
        return {
            'recommendations': cafe_data.get('recommendations', []),
        }

    @classmethod
    def _classify_message(cls, message: str) -> CafeAgentIntentType:
        message = message.lower()

        # todo: work with a vector db so can handle similarities

        if 'menu' in message or 'daily menu' in message:
            return CafeAgentIntentType.REQUEST_DAILY_MENU
        elif 'recommendation' in message or 'would' in message:
            return CafeAgentIntentType.REQUEST_RECOMMENDATION
        elif 'order' in message:
            return CafeAgentIntentType.CREATE_ORDER
        elif 'recommendation' in message:
            return CafeAgentIntentType.REQUEST_RECOMMENDATION
        elif 'review' in message:
            return CafeAgentIntentType.REVIEW_ORDER
        elif 'send' in message:
            return CafeAgentIntentType.SEND_ORDER
        else:
            return CafeAgentIntentType.CHAT

    @classmethod
    def _create_response(cls, intent: CafeAgentIntentType) -> str:
        if intent == CafeAgentIntentType.REQUEST_DAILY_MENU:
            return "Requesting daily menu API method"

        elif intent == CafeAgentIntentType.REQUEST_RECOMMENDATION:
            return "Requesting recommendation API method"

        elif intent == CafeAgentIntentType.CREATE_ORDER:
            return "Creating order API method"

        elif intent == CafeAgentIntentType.REVIEW_ORDER:
            return "Reviewing order API method"

        elif intent == CafeAgentIntentType.SEND_ORDER:
            return "Sending order API method"

        else:
            return "Free chat with agent"


if __name__ == "__main__":
    cafe_agent = CafeAgent(provider="openrouter")

    cafe_agent.print_graph()

    for question in cafe_data.get('questions', []):
        result = cafe_agent.run(question=question)
        print(result)
