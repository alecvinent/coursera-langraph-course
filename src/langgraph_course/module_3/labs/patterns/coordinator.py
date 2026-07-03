"""
Coordinator Pattern — Hub-and-Spoke Multi-Agent System

A central coordinator classifies messages and routes them to specialist
agents.  Specialists process the request, then return to the coordinator
for re-classification — creating a hub-and-spoke topology.

This is a form of the Multi-Agent Collaboration pattern: a coordinator
agent manages work distribution, routing tasks to appropriate specialists
and synthesizing their outputs.

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


class CoordinatorState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    next_agent: str
    response: str
    rounds: int
    task_complete: bool
    query: str
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


class CoordinatorAgent(AgentBase):
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
    @timed_node('coordinator')
    def coordinator(cls, state: CoordinatorState) -> Dict:
        last_msg = cls.get_last_message(state)
        agent = cls._classify_message(last_msg)
        rounds = state.get('rounds', 0) + 1
        logger.info("[Coordinator] Round {}: Routing to {}", rounds, agent)
        return {
            'next_agent': agent,
            'rounds': rounds,
            'messages': [("assistant", f"Coordinator: Routing to {agent}")],
        }

    @classmethod
    def _agent_response(
        cls, state: CoordinatorState, name: str, response: str,
        message: str | None = None, task_complete: bool = False,
    ) -> Dict:
        rounds = state.get('rounds', 0)
        if rounds >= cls.MAX_ROUNDS:
            task_complete = True
        logger.info("[{}] task_complete={}", name, task_complete)
        return {
            'response': response,
            'messages': [("assistant", message or response)],
            'total_processing_time': time.time() - state.get('total_processing_time', time.time()),
            'task_complete': task_complete,
        }

    @classmethod
    @timed_node('agent_a')
    def agent_a(cls, state: CoordinatorState) -> Dict:
        logger.info("[Agent A] Processing billing/finance request")
        return cls._agent_response(
            state, "Agent A",
            response="Agent A (Billing): Your billing inquiry has been processed.",
            message="Your inquiry has been reviewed. A support ticket has been opened for follow-up.",
        )

    @classmethod
    @timed_node('agent_b')
    def agent_b(cls, state: CoordinatorState) -> Dict:
        logger.info("[Agent B] Processing technical request")
        return cls._agent_response(
            state, "Agent B",
            response="Agent B (Technical): Your technical issue has been logged. Our team will follow up.",
            message="Your issue has been forwarded. A customer service agent will contact you shortly.",
        )

    @classmethod
    @timed_node('agent_c')
    def agent_c(cls, state: CoordinatorState) -> Dict:
        logger.info("[Agent C] Processing general request")
        return cls._agent_response(
            state, "Agent C",
            response="Agent C (General): Thank you for your inquiry. A general representative will assist you.",
            message="Your request is complete. Thank you for your patience.",
            task_complete=True,
        )

    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: CoordinatorState) -> Dict:
        proposed = state.get('next_agent', '')
        logger.info("[Human Review] Proposed routing to: {}", proposed)
        decision = interrupt({"proposed_agent": proposed})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: CoordinatorState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'coordinator'
        next_agent = state.get('next_agent', '')
        return next_agent if next_agent else AgentType.AGENT_C

    @classmethod
    def coordinator_router(cls, state: CoordinatorState) -> str:
        next_agent = state.get('next_agent', '')
        return next_agent if next_agent else AgentType.AGENT_C

    @classmethod
    def agent_router(cls, state: CoordinatorState) -> str:
        if state.get('task_complete', False):
            return END
        return 'coordinator'

    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(CoordinatorState)
        workflow.add_node('coordinator', self.coordinator)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('agent_a', self.agent_a)
        workflow.add_node('agent_b', self.agent_b)
        workflow.add_node('agent_c', self.agent_c)

        workflow.set_entry_point('coordinator')

        workflow.add_edge('coordinator', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {
                END: END,
                'coordinator': 'coordinator',
                AgentType.AGENT_A: 'agent_a',
                AgentType.AGENT_B: 'agent_b',
                AgentType.AGENT_C: 'agent_c',
            },
        )

        for agent in ('agent_a', 'agent_b', 'agent_c'):
            workflow.add_conditional_edges(
                agent,
                self.agent_router,
                {END: END, 'coordinator': 'coordinator'},
            )

        return workflow.compile(checkpointer=MemorySaver())

    def run(self, question: str) -> Dict:
        logger.info("Processing coordinator request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "total_processing_time": time.time(),
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
    agent = CoordinatorAgent()
    print(agent.graph.get_graph(xray=True).draw_ascii())
    samples = [
        "I have a billing question about my invoice",
        "Need technical support, my login is broken",
        "Hello, I need some general help",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"Paths: {result.get('paths_taken')}")
        print(f"Response: {result.get('response')}")
