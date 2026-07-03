"""
Specialist Pattern — Multi-Agent System

In contrast to the coordinator pattern (central hub-and-spoke), the specialist
pattern uses a fully-connected mesh where each specialist routes directly to
other specialists. There is no central routing authority — each specialist
decides independently whether to handle the request or delegate to another.

Graph:
  entry -> human_review -> agent_a <-> agent_b <-> agent_c -> END

Each specialist has a conditional edge to every other specialist and to END.

Reference: https://machinelearningmastery.com/7-must-know-agentic-ai-design-patterns/
"""

import time
import uuid
from typing import Annotated, Dict, Sequence, TypedDict

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


class AgentType:
    AGENT_A = "agent_a"
    AGENT_B = "agent_b"
    AGENT_C = "agent_c"


class SpecialistState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    route_to: str
    response: str
    rounds: int
    task_complete: bool
    query: str
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


class SpecialistAgent(AgentBase):
    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    @classmethod
    def _classify_message(cls, message_content: str) -> str:
        topic = message_content.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return AgentType.AGENT_A
        elif any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return AgentType.AGENT_B
        else:
            return AgentType.AGENT_C

    @classmethod
    @timed_node('entry')
    def entry(cls, state: SpecialistState) -> Dict:
        last_msg = cls.get_last_message(state)
        agent = cls._classify_message(last_msg)
        logger.info("[Entry] Routing to: {}", agent)
        return {
            'next_agent': agent,
            'messages': [("assistant", f"Entry: Routing to {agent}")],
        }

    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: SpecialistState) -> Dict:
        proposed = state.get('next_agent', '')
        logger.info("[Human Review] Proposed routing to: {}", proposed)
        decision = interrupt({"proposed_agent": proposed})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: SpecialistState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        next_agent = state.get('next_agent', '')
        return next_agent if next_agent else AgentType.AGENT_C

    @classmethod
    def _agent_response(
        cls, state: SpecialistState, name: str, response: str,
        message: str | None = None, task_complete: bool = False,
        route_to: str = '',
    ) -> Dict:
        rounds = state.get('rounds', 0)
        if rounds >= cls.MAX_ROUNDS:
            task_complete = True
            route_to = ''
        logger.info("[{}] task_complete={}, route_to={}", name, task_complete, route_to)
        return {
            'response': response,
            'messages': [("assistant", message or response)],
            'route_to': route_to,
            'rounds': rounds + 1,
            'total_processing_time': time.time() - state.get('total_processing_time', time.time()),
            'task_complete': task_complete,
        }

    @classmethod
    @timed_node('agent_a')
    def agent_a(cls, state: SpecialistState) -> Dict:
        logger.info("[Agent A] Processing billing/finance request")
        query = state.get('query', cls.get_last_message(state)).lower()
        if any(word in query for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return cls._agent_response(
                state, "Agent A",
                response="Agent A (Billing): This appears to be a technical issue — forwarding to technical support.",
                message="This issue requires technical support. Please check login credentials and system logs.",
                route_to=AgentType.AGENT_B,
                task_complete=False,
            )
        return cls._agent_response(
            state, "Agent A",
            response="Agent A (Billing): Your billing inquiry has been processed. Invoice details are on your account.",
            message="Billing inquiry resolved. Payment has been processed successfully.",
            task_complete=True,
        )

    @classmethod
    @timed_node('agent_b')
    def agent_b(cls, state: SpecialistState) -> Dict:
        logger.info("[Agent B] Processing technical request")
        query = state.get('query', cls.get_last_message(state)).lower()
        if any(word in query for word in ("billing", "payment", "invoice", "refund", "finance")):
            return cls._agent_response(
                state, "Agent B",
                response="Agent B (Technical): This involves billing — redirecting to billing specialist.",
                message="This is a billing-related issue that needs the billing team's attention.",
                route_to=AgentType.AGENT_A,
                task_complete=False,
            )
        if any(word in query for word in ("general", "other", "help", "question")):
            return cls._agent_response(
                state, "Agent B",
                response="Agent B (Technical): Escalating to a general representative for follow-up.",
                message="Your case has been forwarded to our general support team for further assistance.",
                route_to=AgentType.AGENT_C,
                task_complete=False,
            )
        return cls._agent_response(
            state, "Agent B",
            response="Agent B (Technical): Your technical issue has been resolved. A summary will be emailed to you.",
            message="Technical issue resolved. Root cause analysis has been completed.",
            task_complete=True,
        )

    @classmethod
    @timed_node('agent_c')
    def agent_c(cls, state: SpecialistState) -> Dict:
        logger.info("[Agent C] Processing general request")
        return cls._agent_response(
            state, "Agent C",
            response="Agent C (General): Thank you for reaching out. A general representative will assist you shortly.",
            message="Your request is complete. Thank you for your patience.",
            task_complete=True,
        )

    @classmethod
    def specialist_router(cls, state: SpecialistState) -> str:
        if state.get('task_complete', False):
            return END
        route = state.get('route_to', '')
        return route if route else END

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(SpecialistState)
        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('agent_a', self.agent_a)
        workflow.add_node('agent_b', self.agent_b)
        workflow.add_node('agent_c', self.agent_c)

        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {
                END: END,
                AgentType.AGENT_A: 'agent_a',
                AgentType.AGENT_B: 'agent_b',
                AgentType.AGENT_C: 'agent_c',
            },
        )

        for agent in ('agent_a', 'agent_b', 'agent_c'):
            workflow.add_conditional_edges(
                agent,
                self.specialist_router,
                {
                    END: END,
                    AgentType.AGENT_A: 'agent_a',
                    AgentType.AGENT_B: 'agent_b',
                    AgentType.AGENT_C: 'agent_c',
                },
            )

        return workflow.compile(checkpointer=MemorySaver())

    def run(self, question: str) -> Dict:
        logger.info("Processing specialist request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "total_processing_time": time.time(),
            "next_agent": "",
            "route_to": "",
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
    agent = SpecialistAgent()
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
        print(f"  Response: {result.get('response')}")
