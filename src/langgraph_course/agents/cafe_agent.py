from enum import Enum
from typing import TypedDict, Dict, Annotated

from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph_course.log import logger

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
    my_orders: list


class CafeAgent(AgentBase):
    def __init__(self, provider: str = "auto", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        self._state = {"messages": []}
        super().__init__()

    def _build_graph(self):
        workflow = StateGraph(CafeAgentState)

        workflow.add_node('classify intent', self.classify_intent)
        workflow.add_node('get_daily_menu', self.get_daily_menu)
        workflow.add_node('get_recommendations', self.get_recommendations)
        workflow.add_node('chat', self.chatbot)
        workflow.add_node('create_order', self.add_order)
        workflow.add_node('review_orders', self.list_orders)
        workflow.add_node('send_order', self.send_order)
        workflow.add_node('respond', self.generate_response)

        workflow.set_entry_point('classify intent')

        workflow.add_conditional_edges(
            'classify intent', self._route_intent, {
                CafeAgentIntentType.REQUEST_DAILY_MENU: 'get_daily_menu',
                CafeAgentIntentType.REQUEST_RECOMMENDATION: 'get_recommendations',
                CafeAgentIntentType.CHAT: 'chat',
                CafeAgentIntentType.CREATE_ORDER: 'create_order',
                CafeAgentIntentType.REVIEW_ORDER: 'review_orders',
                CafeAgentIntentType.SEND_ORDER: 'send_order',
            }
        )
        for node in ('get_daily_menu', 'get_recommendations', 'chat', 'create_order', 'review_orders', 'send_order'):
            workflow.add_edge(node, 'respond')
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
        CafeAgentIntentType.CREATE_ORDER: "Order added:\n{items}",
        CafeAgentIntentType.REVIEW_ORDER: "Your orders:\n{items}",
        CafeAgentIntentType.SEND_ORDER: "Order sent!\n{items}\nTotal: ${total:.2f}",
    }

    @staticmethod
    def _format_items(items: list) -> str:
        lines = []
        for i in items:
            qty = i.get("quantity", 1)
            name = i['name']
            price = i['price']
            if qty > 1:
                lines.append(f"- {name} x{qty}: ${price * qty:.2f}")
            else:
                lines.append(f"- {name}: ${price:.2f}")
        return "\n".join(lines)

    DATA_KEYS = {
        CafeAgentIntentType.REQUEST_DAILY_MENU: "daily_menu",
        CafeAgentIntentType.REQUEST_RECOMMENDATION: "recommendations",
        CafeAgentIntentType.CREATE_ORDER: "my_orders",
        CafeAgentIntentType.REVIEW_ORDER: "my_orders",
        CafeAgentIntentType.SEND_ORDER: "my_orders",
    }

    @staticmethod
    def _total(items: list) -> float:
        return sum(i['price'] * i.get('quantity', 1) for i in items)

    def generate_response(self, state: CafeAgentState) -> Dict:
        intent = state["intent"]
        template = self.RESPONSE_TEMPLATES.get(intent)
        if template:
            data_key = self.DATA_KEYS[intent]
            items = state.get(data_key, [])
            formatted = self._format_items(items)
            total = self._total(items)
            response = template.format(items=formatted, total=total)
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

    def list_orders(self, state: CafeAgentState) -> Dict:
        logger.info("Listing orders")
        return {
            'my_orders': state.get('my_orders', []),
        }

    def add_order(self, state: CafeAgentState) -> Dict:
        logger.info("Adding order")
        last_message = self.get_last_message(state)
        orders = list(state.get("my_orders", []))
        orders.append({"name": last_message, "price": 0})
        return {"my_orders": orders}

    def send_order(self, state: CafeAgentState) -> Dict:
        logger.info("Sending order")
        return {"my_orders": []}

    @classmethod
    def _classify_message(cls, message: str) -> CafeAgentIntentType:
        message = message.lower()

        if 'menu' in message or 'daily menu' in message:
            return CafeAgentIntentType.REQUEST_DAILY_MENU
        elif 'recommendation' in message or 'would' in message:
            return CafeAgentIntentType.REQUEST_RECOMMENDATION
        elif 'send' in message or 'submit' in message:
            return CafeAgentIntentType.SEND_ORDER
        elif 'review' in message or 'list' in message or 'my order' in message:
            return CafeAgentIntentType.REVIEW_ORDER
        elif 'add' in message or 'order' in message or 'buy' in message or 'purchase' in message:
            return CafeAgentIntentType.CREATE_ORDER
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

    def run(self, question: str) -> Dict:
        initial = {**self._state}
        initial.setdefault("messages", [])
        initial["messages"].append(("user", question))
        result = self.graph.invoke(initial)
        self._state = result
        return result

if __name__ == "__main__":
    cafe_agent = CafeAgent(provider="openrouter")

    cafe_agent.print_graph()

    print("\nCafe Agent ready. Type your questions (or 'bye' to exit).\n")

    while True:
        question = input("You: ").strip()
        if not question:
            continue
        if cafe_agent.should_continue({"messages": [("user", question)]}) == cafe_agent.END_SIGNAL:
            print("Assistant: Goodbye!")
            break
        result = cafe_agent.run(question=question)
        print(f"Assistant: {result.get('response', '')}")
