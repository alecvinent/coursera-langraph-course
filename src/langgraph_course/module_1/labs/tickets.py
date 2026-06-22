from enum import Enum
from typing import TypedDict

from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import BaseModel, Field

from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.llm import LLMFactory


class TicketUrgencyLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TicketCategory(Enum):
    BILLING_ISSUE = "BILLING_ISSUE"
    TECHNICAL_ISSUE = "TECHNICAL_ISSUE"
    FEATURE_REQUEST = "FEATURE_REQUEST"
    ACCOUNT_MANAGEMENT = "ACCOUNT_MANAGEMENT"
    UNKNOWN = "UNKNOWN"


class Ticket(BaseModel):
    topic: str
    is_urgent: bool = Field(default=False)


class TicketClassificationResult(BaseModel):
    category: TicketCategory
    confidence: float


class TicketState(TypedDict):
    ticket: Ticket
    classification_results: TicketClassificationResult
    urgency_level: TicketUrgencyLevel
    routing_decision: str
    additional_metadata: str
    response: str


class SupportTicketAgent(AgentBase):
    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    def classify_ticket(self, ticket: Ticket) -> TicketCategory:
        if 'billing' in ticket.topic:
            return TicketCategory.BILLING_ISSUE
        elif 'technical' in ticket.topic:
            return TicketCategory.TECHNICAL_ISSUE
        elif 'feature-request' in ticket.topic:
            return TicketCategory.FEATURE_REQUEST
        elif 'account-management' in ticket.topic:
            return TicketCategory.ACCOUNT_MANAGEMENT
        else:
            return TicketCategory.UNKNOWN

    def urgent_assessment(self, state: TicketState) -> TicketState:
        ...

    def routing_decision(self, state: TicketState) -> TicketState:
        ...

    def generate_response(self, state: TicketState) -> str:
        ...

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(TicketState)

        workflow.add_node('classifier', self.classify_ticket)
        workflow.add_node('urgency_assessor', self.urgent_assessment)
        workflow.add_node('router', self.routing_decision)

        workflow.set_entry_point('classifier')

        workflow.add_edge('classifier', 'urgency_assessor')

        workflow.set_finish_point('router')

        return workflow.compile()
