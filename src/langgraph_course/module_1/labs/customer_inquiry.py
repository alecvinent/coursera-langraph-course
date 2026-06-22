from enum import Enum
from typing import Annotated, Dict, TypedDict

from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from loguru import logger

from langgraph_course.module_1.labs.data import customer_inquiry_questions
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.llm import LLMFactory


class CustomerInquiryIntentType(Enum):
    PRICING_QUERY = "pricing_query"
    RETURN_REQUEST = "return_request"
    UNKNOWN = "unknown"


class CustomerInquiryWorkflowAction(Enum):
    HUMAN_REVIEW = "human_review"
    RESPOND = "respond"


class CustomerInquiryState(TypedDict):
    message: str
    messages: Annotated[list, add_messages]
    intent: str
    confidence: float
    response: str


class CustomerInquiryAgent(AgentBase):
    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    @staticmethod
    def _classify_message(message: str) -> tuple:
        message = message.lower()
        if "price" in message or "cost" in message:
            return CustomerInquiryIntentType.PRICING_QUERY.value, 0.9
        elif "return" in message:
            return CustomerInquiryIntentType.RETURN_REQUEST.value, 0.85
        return CustomerInquiryIntentType.UNKNOWN.value, 0.6

    @staticmethod
    def _create_response(intent: str, message: str) -> str:
        if intent == CustomerInquiryIntentType.PRICING_QUERY.value:
            return "Our products price range from $100 to $200"
        elif intent == CustomerInquiryIntentType.RETURN_REQUEST.value:
            return "You can initiate a return within 30 days"
        return "Forwarding to human review"

    def classify_intent(self, state: CustomerInquiryState) -> Dict:
        intent, confidence = self._classify_message(self.get_last_message(state))
        logger.info("Classified message={!r} as intent={} confidence={:.2f}",
                    state["message"], intent, confidence)
        return {"intent": intent, "confidence": confidence}

    def generate_response(self, state: CustomerInquiryState) -> Dict:
        response = self._create_response(state["intent"], self.get_last_message(state))
        logger.info("Auto respond to {}: {}", state["intent"], response)
        return {"response": response}

    @classmethod
    def human_review(cls, state: CustomerInquiryState) -> Dict:
        logger.warning("Routing to human review: intent={} confidence={}",
                       state.get("intent"), state.get("confidence"))
        return {"response": "Human review due to low confidence",
                "messages": [("user", state["message"])]}

    @classmethod
    def _should_review(cls, state: CustomerInquiryState) -> str:
        action = (
            CustomerInquiryWorkflowAction.HUMAN_REVIEW.value
            if state["confidence"] < 0.75
            else CustomerInquiryWorkflowAction.RESPOND.value
        )
        logger.info("Routing decision: confidence={:.2f} → {}",
                    state.get("confidence"), action)
        return action

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(CustomerInquiryState)

        workflow.add_node("classify", self.classify_intent)
        workflow.add_node("respond", self.generate_response)
        workflow.add_node("human_review", self.human_review)
        workflow.add_node("chatbot", self.chatbot)

        workflow.set_entry_point("classify")

        workflow.add_conditional_edges(
            "classify", self._should_review, {
                CustomerInquiryWorkflowAction.RESPOND.value: "respond",
                CustomerInquiryWorkflowAction.HUMAN_REVIEW.value: "human_review",
            }
        )
        workflow.add_edge("respond", END)
        workflow.add_edge("human_review", "chatbot")
        workflow.add_edge("chatbot", END)

        return workflow.compile()

    def run(self, question: str) -> CustomerInquiryState:
        logger.info("Processing inquiry: {!r}", question)
        invoker_result = self.graph.invoke({
            "message": question,
            "messages": [("user", question)],
        })
        logger.info("Result: {}", invoker_result.get("response"))
        return invoker_result


if __name__ == "__main__":
    agent = CustomerInquiryAgent(
        provider="openrouter"
    )
    agent.print_graph()

    for question in customer_inquiry_questions:
        result = agent.run(question)
        print(result)
