"""
Sequential Pattern — Multi-Agent System

A fixed-order linear pipeline where agents execute one after another in a
predetermined sequence.  Each agent passes its output to the next, and the
last agent produces the final response.  No routing decisions, no loops —
the simplest multi-agent topology.

Contrast with the other patterns in this module:
  - Coordinator (hub-and-spoke): central hub re-classifies every round.
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.
  - ReAct (single-agent loop): agent calls tools, reads results, responds.
  - Reflection (generate → critique): generator and critic refine a response.
  - Planning (plan → execute → review): planner decomposes into ordered steps.
  - Tool (classify → run tool → format): one-shot tool pipeline.

Graph:
  entry -> human_review -> analyzer -> specialist -> formatter -> END

  1. entry:      capture the user query.
  2. human_review: optional approval gate via interrupt().
  3. analyzer:   classify the query and extract key information.
  4. specialist: produce a domain-specific response based on the analysis.
  5. formatter:  polish the specialist's output into the final response.

Key differences from the other patterns:
  - No loops: the flow goes through exactly once, then terminates.
  - No routing decisions: each node has exactly one outgoing edge.
  - Strict ordering: agents execute in a fixed, predetermined sequence.
  - Each agent has a single responsibility in the pipeline.

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


# ---------------------------------------------------------------------------
# Topic classification constants
# ---------------------------------------------------------------------------
class Topic:
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
# Compared to coordinator (next_agent for routing) or ReAct (tool_to_call),
# Sequential introduces:
#   - query_analysis      -> the analyzer's classification and extracted info
#   - specialist_response -> the specialist's domain-specific response
# These fields capture the output of each pipeline stage so downstream
# agents can build on them without re-reading raw messages.
class SequentialState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    query_analysis: str
    specialist_response: str
    response: str
    rounds: int
    task_complete: bool
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class SequentialAgent(AgentBase):
    """
    Sequential pattern: fixed-order pipeline of agents.

    The analyzer classifies the query, the specialist handles it, and the
    formatter produces the final response.  The flow is strictly linear —
    no loops, no routing decisions.

    The classifier is keyword-based so tests run without an API call.
    Swap _classify_topic for an LLM invocation to get full analysis.
    """

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    @classmethod
    def _classify_topic(cls, query: str) -> str:
        topic = query.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return Topic.BILLING
        if any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return Topic.TECHNICAL
        return Topic.GENERAL

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: SequentialState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Sequential pipeline for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Sequential pipeline")],
        }

    # -- Human review gate ------------------------------------------------
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: SequentialState) -> Dict:
        logger.info("[Human Review] Pending review for Sequential pipeline")
        decision = interrupt({"message": "Approve Sequential pipeline execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: SequentialState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'analyzer'

    # -- Analyzer node ----------------------------------------------------
    # Classifies the query topic and extracts key information that the
    # specialist will use to produce a domain-specific response.
    @classmethod
    @timed_node('analyzer')
    def analyzer(cls, state: SequentialState) -> Dict:
        query = state.get('query', cls.get_last_message(state))
        topic = cls._classify_topic(query)
        logger.info("[Analyzer] Classified topic: {}", topic)

        if topic == Topic.BILLING:
            analysis = f"Topic: billing. The user has a billing-related inquiry about {query[:40]}... Routing to billing specialist."
        elif topic == Topic.TECHNICAL:
            analysis = f"Topic: technical. The user has a technical issue about {query[:40]}... Routing to technical specialist."
        else:
            analysis = f"Topic: general. The user has a general inquiry about {query[:40]}... Routing to general support."

        logger.info("[Analyzer] Analysis: {}", analysis[:60])
        return {
            'query_analysis': analysis,
            'rounds': 1,
            'messages': [("assistant", f"Analyzer: {analysis}")],
        }

    # -- Specialist node --------------------------------------------------
    # Reads the analyzer's classification and produces a domain-specific
    # response.  In production this would call APIs, query databases, or
    # use an LLM to generate a detailed answer.
    @classmethod
    @timed_node('specialist')
    def specialist(cls, state: SequentialState) -> Dict:
        analysis = state.get('query_analysis', '')
        topic = Topic.BILLING if "billing" in analysis.lower() else Topic.TECHNICAL if "technical" in analysis.lower() else Topic.GENERAL
        logger.info("[Specialist] Handling topic: {}", topic)

        if topic == Topic.BILLING:
            specialist_msg = "Agent (Billing): Your billing inquiry has been processed. Invoice #INV-5678 shows a balance of $249.00, due 2026-07-15. A receipt has been sent to your email."
        elif topic == Topic.TECHNICAL:
            specialist_msg = "Agent (Technical): Your technical issue has been logged. Our team identified a login service interruption at 14:30 UTC. The fix has been deployed and the service is now stable."
        else:
            specialist_msg = "Agent (General): Thank you for reaching out. Our support team has received your request and we will get back to you within 24 hours."

        logger.info("[Specialist] Response: {}", specialist_msg[:60])
        return {
            'specialist_response': specialist_msg,
            'messages': [("assistant", specialist_msg)],
        }

    # -- Formatter node ---------------------------------------------------
    # Takes the specialist's response and wraps it in a polished final
    # message.  The formatter is also responsible for setting task_complete
    # to signal the end of the pipeline.
    @classmethod
    @timed_node('formatter')
    def formatter(cls, state: SequentialState) -> Dict:
        specialist_msg = state.get('specialist_response', '')
        logger.info("[Formatter] Polishing specialist response")

        final_msg = f"{specialist_msg}\n\n---\nProcessed through Sequential pipeline. Is there anything else I can help you with?"

        return {
            'response': final_msg,
            'task_complete': True,
            'messages': [("assistant", f"Formatter: {final_msg}")],
        }

    # -- Routers ----------------------------------------------------------
    # Each node routes unconditionally to the next in the sequence.
    # The formatter terminates the pipeline by routing to END.
    @classmethod
    def analyzer_router(cls, state: SequentialState) -> str:
        return 'specialist'

    @classmethod
    def specialist_router(cls, state: SequentialState) -> str:
        return 'formatter'

    @classmethod
    def formatter_router(cls, state: SequentialState) -> str:
        return END

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(SequentialState)

        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('analyzer', self.analyzer)
        workflow.add_node('specialist', self.specialist)
        workflow.add_node('formatter', self.formatter)

        # Graph topology:
        #   entry -> human_review -> analyzer -> specialist -> formatter -> END
        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'analyzer': 'analyzer'},
        )

        workflow.add_conditional_edges(
            'analyzer',
            self.analyzer_router,
            {'specialist': 'specialist'},
        )

        workflow.add_conditional_edges(
            'specialist',
            self.specialist_router,
            {'formatter': 'formatter'},
        )

        workflow.add_conditional_edges(
            'formatter',
            self.formatter_router,
            {END: END},
        )

        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Sequential request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "query_analysis": "",
            "specialist_response": "",
            "response": "",
            "rounds": 0,
            "task_complete": False,
            "total_processing_time": time.time(),
            "latencies": {},
            "paths_taken": [],
            "human_decision": "",
        }
        result = self.graph.invoke(initial_state, config)
        while '__interrupt__' in result:
            result = self.graph.invoke(Command(resume="approve"), config)
        logger.info("Result: {}", result.get("response", ""))
        return result


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    agent = SequentialAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "I have a billing question about my invoice",
        "Need technical support, my login is broken",
        "Hello, I need some general help",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Analysis: {result.get('query_analysis', 'N/A')[:60]}...")
        print(f"  Response: {result.get('response')}")
