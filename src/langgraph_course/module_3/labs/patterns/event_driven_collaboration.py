"""
Event-Driven Collaboration Pattern — Multi-Agent System

In contrast to the coordinator pattern (central hub-and-spoke) and the specialist
pattern (fully-connected mesh), the event-driven collaboration pattern uses a
shared event queue (pub-sub bus) for agent communication. No agent routes to
another directly. Instead, each agent processes events from the bus and publishes
new events back to the bus. An event bus node dispatches events to the appropriate
subscriber based on event type.

Graph:
  entry -> human_review -> event_bus -> subscriber -> event_bus (or END)
                                         ^              |
                                          +---always-----+

Reference: https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/
"""

import time
import uuid
from typing import Annotated, Dict, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import END
from langgraph.graph import StateGraph, add_messages
from langgraph.graph.state import CompiledStateGraph
from langgraph.types import Command, interrupt

from langgraph_course.log import logger
from langgraph_course.utils.agentbase import AgentBase
from langgraph_course.utils.decorators import timed_node
from langgraph_course.utils.llm import LLMFactory


class EventType:
    BILLING_REQUEST = "billing_request"
    TECHNICAL_REQUEST = "technical_request"
    GENERAL_REQUEST = "general_request"
    RESOLUTION = "resolution"


SUBSCRIPTIONS: dict[str, str | None] = {
    EventType.BILLING_REQUEST: "agent_a",
    EventType.TECHNICAL_REQUEST: "agent_b",
    EventType.GENERAL_REQUEST: "agent_c",
    EventType.RESOLUTION: None,
}


class EventRecord(TypedDict):
    type: str
    payload: str
    source: str


class EventDrivenState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    events: List[EventRecord]
    event_index: int
    active_subscriber: str
    response: str
    rounds: int
    task_complete: bool
    query: str
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


class EventDrivenAgent(AgentBase):
    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    @classmethod
    def _classify_message(cls, message_content: str) -> str:
        topic = message_content.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return EventType.BILLING_REQUEST
        elif any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return EventType.TECHNICAL_REQUEST
        else:
            return EventType.GENERAL_REQUEST

    @classmethod
    @timed_node('entry')
    def entry(cls, state: EventDrivenState) -> Dict:
        last_msg = cls.get_last_message(state)
        event_type = cls._classify_message(last_msg)
        logger.info("[Entry] Publishing {} event", event_type)
        return {
            'events': [EventRecord(type=event_type, payload=last_msg, source='user')],
            'next_agent': event_type,
            'messages': [("assistant", f"Entry: Publishing {event_type}")],
        }

    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: EventDrivenState) -> Dict:
        proposed = state.get('next_agent', '')
        logger.info("[Human Review] Reviewing event dispatch: {}", proposed)
        decision = interrupt({"proposed_dispatch": proposed})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: EventDrivenState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'event_bus'

    @classmethod
    @timed_node('event_bus')
    def event_bus(cls, state: EventDrivenState) -> Dict:
        events: list = state.get('events', [])
        idx = state.get('event_index', 0)
        if idx >= len(events):
            logger.info("[Event Bus] No more events — terminating")
            return {'active_subscriber': '', 'task_complete': True}
        event = events[idx]
        subscriber = SUBSCRIPTIONS.get(event['type'], None)
        logger.info("[Event Bus] Dispatching {} (idx={}) to {}", event['type'], idx, subscriber)
        return {'active_subscriber': subscriber or ''}

    @classmethod
    def event_bus_router(cls, state: EventDrivenState) -> str:
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        subscriber = state.get('active_subscriber', '')
        return subscriber if subscriber else END

    @classmethod
    def _agent_response(
        cls, state: EventDrivenState, name: str, response: str,
        new_events: list[EventRecord] | None = None,
    ) -> Dict:
        idx = state.get('event_index', 0)
        rounds = state.get('rounds', 0) + 1
        existing: list = state.get('events', [])
        merged = list(existing) + (new_events or [])
        logger.info("[{}] processed event idx={}, publishing {} new event(s)", name, idx, len(new_events or []))
        return {
            'response': response,
            'messages': [("assistant", response)],
            'event_index': idx + 1,
            'events': merged,
            'rounds': rounds,
            'total_processing_time': time.time() - state.get('total_processing_time', time.time()),
            'task_complete': False,
        }

    @classmethod
    def agent_router(cls, state: EventDrivenState) -> str:
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        return 'event_bus'

    @classmethod
    @timed_node('agent_a')
    def agent_a(cls, state: EventDrivenState) -> Dict:
        logger.info("[Agent A] Processing billing event")
        query = state.get('query', '').lower()
        new_events: list[EventRecord] = []
        response = "Agent A (Billing): Your billing inquiry has been processed. Invoice details are on your account."
        if any(word in query for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            new_events.append(
                EventRecord(type=EventType.TECHNICAL_REQUEST, payload=query, source="agent_a"),
            )
            response = "Agent A (Billing): Billing handled. A technical follow-up has been queued for the support team."
        new_events.append(
            EventRecord(type=EventType.RESOLUTION, payload="Billing processed", source="agent_a"),
        )
        return cls._agent_response(state, "Agent A", response, new_events=new_events)

    @classmethod
    @timed_node('agent_b')
    def agent_b(cls, state: EventDrivenState) -> Dict:
        logger.info("[Agent B] Processing technical event")
        query = state.get('query', '').lower()
        new_events: list[EventRecord] = []
        response = "Agent B (Technical): Your technical issue has been resolved. A summary will be emailed to you."
        if any(word in query for word in ("billing", "payment", "invoice", "refund", "finance")):
            new_events.append(
                EventRecord(type=EventType.BILLING_REQUEST, payload=query, source="agent_b"),
            )
            response = "Agent B (Technical): Technical issue logged. A billing follow-up has been queued."
        new_events.append(
            EventRecord(type=EventType.RESOLUTION, payload="Technical issue resolved", source="agent_b"),
        )
        return cls._agent_response(state, "Agent B", response, new_events=new_events)

    @classmethod
    @timed_node('agent_c')
    def agent_c(cls, state: EventDrivenState) -> Dict:
        logger.info("[Agent C] Processing general event")
        return cls._agent_response(
            state, "Agent C",
            "Agent C (General): Thank you for reaching out. A general representative will assist you shortly.",
            new_events=[EventRecord(type=EventType.RESOLUTION, payload="General request completed", source="agent_c")],
        )

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(EventDrivenState)
        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('event_bus', self.event_bus)
        workflow.add_node('agent_a', self.agent_a)
        workflow.add_node('agent_b', self.agent_b)
        workflow.add_node('agent_c', self.agent_c)

        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'event_bus': 'event_bus'},
        )

        workflow.add_conditional_edges(
            'event_bus',
            self.event_bus_router,
            {
                END: END,
                'agent_a': 'agent_a',
                'agent_b': 'agent_b',
                'agent_c': 'agent_c',
            },
        )

        for agent in ('agent_a', 'agent_b', 'agent_c'):
            workflow.add_conditional_edges(
                agent,
                self.agent_router,
                {END: END, 'event_bus': 'event_bus'},
            )

        return workflow.compile(checkpointer=MemorySaver())

    def run(self, question: str) -> Dict:
        logger.info("Processing event-driven request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "total_processing_time": time.time(),
            "events": [],
            "event_index": 0,
            "active_subscriber": "",
            "next_agent": "",
            "response": "",
            "rounds": 0,
            "task_complete": False,
            "latencies": {},
            "paths_taken": [],
            "human_decision": "",
        }
        result = self.graph.invoke(initial_state, config)
        while '__interrupt__' in result:
            result = self.graph.invoke(Command(resume="approve"), config)
        logger.info("Result: {}", result.get("response", ""))
        return result


if __name__ == '__main__':
    agent = EventDrivenAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "I have a billing question about my invoice",
        "Need technical support, my login is broken",
        "Hello, I need some general help",
        "I'm having a technical bug with payment",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Events: {[e['type'] for e in result.get('events', [])]}")
        print(f"  Response: {result.get('response')}")
