import re
import time
from enum import Enum
from typing import Any, Dict, Optional, TypedDict

from langgraph.constants import END
from langgraph.graph.state import CompiledStateGraph, StateGraph
from pydantic import BaseModel, Field

from langgraph_course.log import logger
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.decorators import timed_node
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
    classification_results: Optional[TicketClassificationResult]
    urgency_level: Optional[TicketUrgencyLevel]
    routing_decision: str
    additional_metadata: str
    response: str
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    retry_count: int


class SupportTicketAgent(AgentBase):
    CONFIDENCE_THRESHOLD = 0.6
    MAX_RETRIES = 2

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    @classmethod
    def _get_ticket_category(cls, ticket: Ticket) -> tuple[TicketCategory, float]:
        topic = ticket.topic.lower()

        if 'billing' in topic or 'bill' in topic or 'payment' in topic or 'invoice' in topic:
            return TicketCategory.BILLING_ISSUE, 0.85
        elif 'technical' in topic or 'bug' in topic or 'error' in topic or 'crash' in topic:
            return TicketCategory.TECHNICAL_ISSUE, 0.80
        elif 'feature' in topic or 'suggestion' in topic or 'upgrade' in topic:
            return TicketCategory.FEATURE_REQUEST, 0.75
        elif 'account' in topic or 'login' in topic or 'password' in topic:
            return TicketCategory.ACCOUNT_MANAGEMENT, 0.75

        return TicketCategory.UNKNOWN, 0.20

    @classmethod
    @timed_node('classifier')
    def classify_ticket(cls, state: TicketState) -> Dict:
        ticket = state.get('ticket')
        category, confidence = cls._get_ticket_category(ticket)

        logger.info("Classified topic={!r} -> category={} confidence={:.2f}",
                    ticket.topic, category.value, confidence)

        return {
            'classification_results': TicketClassificationResult(
                category=category,
                confidence=confidence,
            ),
        }

    @classmethod
    @timed_node('urgency_assessor')
    def urgent_assessment(cls, state: TicketState) -> Dict:
        current_ticket = state.get('ticket')
        topic = current_ticket.topic.lower()

        if current_ticket.is_urgent:
            urgency = TicketUrgencyLevel.HIGH
        elif any(kw in topic for kw in ('urgent', 'critical', 'down', 'emergency', 'outage')):
            urgency = TicketUrgencyLevel.HIGH
        elif any(kw in topic for kw in ('issue', 'problem', 'help', 'broken', 'error')):
            urgency = TicketUrgencyLevel.MEDIUM
        else:
            urgency = TicketUrgencyLevel.LOW

        logger.info("Urgency assessment for topic={!r} -> {}",
                    current_ticket.topic, urgency.value)

        return {'urgency_level': urgency}

    @classmethod
    @timed_node('router')
    def routing_decision(cls, state: TicketState) -> Dict:
        urgency_level = state.get('urgency_level')
        classification = state.get('classification_results')

        if classification is None:
            return {
                'routing_decision': 'Fallback: general queue',
                'additional_metadata': 'No classification available',
            }

        ticket_type = classification.category
        confidence = classification.confidence

        if urgency_level == TicketUrgencyLevel.HIGH and ticket_type == TicketCategory.TECHNICAL_ISSUE:
            decision = 'This is urgent and must be attended by a Senior Engineer'
        elif ticket_type == TicketCategory.BILLING_ISSUE:
            decision = 'This must be attended by the Billing Team'
        elif ticket_type == TicketCategory.FEATURE_REQUEST:
            decision = 'This must be attended by the Product Team'
        elif ticket_type == TicketCategory.ACCOUNT_MANAGEMENT:
            decision = 'This must be attended by the Account Manager'
        elif ticket_type == TicketCategory.TECHNICAL_ISSUE:
            decision = 'This must be attended by the Technical Support Team'
        else:
            decision = 'Unknown ticket type, so will be attended by the Sales Team'

        logger.info("Routing topic={!r} urgency={} category={} confidence={:.2f} -> {!r}",
                    state['ticket'].topic, urgency_level.value if urgency_level else '?',
                    ticket_type.value, confidence, decision)

        return {
            'routing_decision': decision,
            'additional_metadata': f'category={ticket_type.value}, confidence={confidence:.2f}',
        }

    @classmethod
    def _routing_condition(cls, state: TicketState) -> str:
        classification = state.get('classification_results')
        if classification is None:
            return 'human_review'

        if classification.category == TicketCategory.UNKNOWN or classification.confidence < cls.CONFIDENCE_THRESHOLD:
            retry_count = state.get('retry_count', 0)
            if retry_count < cls.MAX_RETRIES:
                return 'retry_classifier'
            return 'human_review'

        return 'respond'

    @classmethod
    @timed_node('respond')
    def respond(cls, state: TicketState) -> Dict:
        routing_decision = state.get('routing_decision')
        urgency_level = state.get('urgency_level')
        classification = state.get('classification_results')
        confidence = classification.confidence if classification else 0.0

        return {
            'response': (
                f'{routing_decision}. '
                f'Urgency level: {urgency_level.value}, '
                f'confidence: {confidence:.0%}'
            ),
        }

    @classmethod
    @timed_node('retry_classifier')
    def retry_classifier(cls, state: TicketState) -> Dict:
        ticket = state.get('ticket')
        topic = ticket.topic.lower()
        retry_count = state.get('retry_count', 0) + 1

        BILLING_PATTERNS = [
            r'\bbill(ing|ed|s)?\b', r'\bpayment(s)?\b', r'\binvoice(s)?\b',
            r'\bcharge(d|s)?\b', r'\breceipt(s)?\b',
        ]
        TECHNICAL_PATTERNS = [
            r'\btechni(c|que)s?\b', r'\bbug(s)?\b', r'\berror(s)?\b',
            r'\bcrash(es|ed)?\b', r'\bserver(s)?\b', r'\bnetwork(s)?\b',
        ]
        FEATURE_PATTERNS = [
            r'\bfeature(s)?\b', r'\brequest(s)?\b', r'\bsuggestion(s)?\b',
            r'\bidea(s)?\b', r'\bupgrade(s)?\b',
        ]
        ACCOUNT_PATTERNS = [
            r'\baccount(s)?\b', r'\blogin(s)?\b', r'\bpassword(s)?\b',
            r'\baccess\b', r'\bprofile(s)?\b',
        ]

        for patterns, category in [
            (BILLING_PATTERNS, TicketCategory.BILLING_ISSUE),
            (TECHNICAL_PATTERNS, TicketCategory.TECHNICAL_ISSUE),
            (FEATURE_PATTERNS, TicketCategory.FEATURE_REQUEST),
            (ACCOUNT_PATTERNS, TicketCategory.ACCOUNT_MANAGEMENT),
        ]:
            for pattern in patterns:
                if re.search(pattern, topic):
                    logger.info("Retry #{} matched {} via /{}/ for topic={!r}",
                                retry_count, category.value, pattern, ticket.topic)
                    return {
                        'classification_results': TicketClassificationResult(
                            category=category, confidence=0.65,
                        ),
                        'retry_count': retry_count,
                    }

        logger.info("Retry #{} no match for topic={!r} -> UNKNOWN", retry_count, ticket.topic)
        return {
            'classification_results': TicketClassificationResult(
                category=TicketCategory.UNKNOWN, confidence=0.15,
            ),
            'retry_count': retry_count,
        }

    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: TicketState) -> Dict:
        classification = state.get('classification_results')
        urgency_level = state.get('urgency_level')
        retry_count = state.get('retry_count', 0)
        confidence = classification.confidence if classification else 0.0

        logger.warning("Human review triggered: topic={!r} confidence={:.2f} retries={} urgency={}",
                       state['ticket'].topic, confidence, retry_count,
                       urgency_level.value if urgency_level else '?')

        return {
            'response': (
                'This ticket requires human review. '
                f'Confidence was {confidence:.0%} after {retry_count} retries. '
                f'Urgency: {urgency_level.value if urgency_level else "unknown"}'
            ),
        }

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(TicketState)

        workflow.add_node('classifier', self.classify_ticket)
        workflow.add_node('urgency_assessor', self.urgent_assessment)
        workflow.add_node('router', self.routing_decision)
        workflow.add_node('respond', self.respond)
        workflow.add_node('retry_classifier', self.retry_classifier)
        workflow.add_node('human_review', self.human_review)

        workflow.set_entry_point('classifier')

        workflow.add_edge('classifier', 'urgency_assessor')
        workflow.add_edge('urgency_assessor', 'router')

        workflow.add_conditional_edges(
            'router',
            self._routing_condition,
            {
                'respond': 'respond',
                'retry_classifier': 'retry_classifier',
                'human_review': 'human_review',
            },
        )

        workflow.add_edge('respond', END)
        workflow.add_edge('human_review', END)
        workflow.add_edge('retry_classifier', 'router')

        return workflow.compile()

    def run(self, item: Ticket) -> Dict:
        if item is None:
            logger.error("No ticket provided")
            return {'response': 'Error: No ticket provided', 'total_processing_time': 0.0}

        if not item.topic or not isinstance(item.topic, str):
            logger.error("Invalid ticket topic: {!r}", item.topic)
            return {'response': 'Error: Invalid ticket topic', 'total_processing_time': 0.0}

        logger.info("Processing ticket: topic={!r} is_urgent={}", item.topic, item.is_urgent)
        start = time.monotonic()

        try:
            invoke_result = self.graph.invoke({
                'ticket': item,
                'classification_results': None,
                'urgency_level': None,
                'routing_decision': '',
                'additional_metadata': '',
                'response': '',
                'total_processing_time': 0.0,
                'latencies': {},
                'paths_taken': [],
                'retry_count': 0,
            })
        except Exception:
            logger.exception("Graph invocation failed for topic={!r}", item.topic)
            elapsed = time.monotonic() - start
            return {
                'response': 'Error: Internal processing failure',
                'total_processing_time': elapsed,
            }

        elapsed = time.monotonic() - start
        invoke_result['total_processing_time'] = elapsed
        logger.info("Completed in {:.1f}ms: {}", elapsed * 1000, invoke_result.get('response', ''))
        return invoke_result


ticket_examples = [
    Ticket(topic='Billing issue with my invoice', is_urgent=False),
    Ticket(topic='URGENT: server is down', is_urgent=False),
    Ticket(topic='Feature request: dark mode', is_urgent=False),
    Ticket(topic='Reset my account password'),
    Ticket(topic='Technical bug in the dashboard'),
    Ticket(topic='Payment not going through', is_urgent=True),
    Ticket(topic='Need help with login'),
    Ticket(topic='Unknown random gibberish text'),
]

if __name__ == '__main__':
    agent = SupportTicketAgent(provider='openrouter')
    agent.print_graph()

    for ticket in ticket_examples:
        result = agent.run(ticket)
        logger.info(f"  -> {result.get('response', '')}")
