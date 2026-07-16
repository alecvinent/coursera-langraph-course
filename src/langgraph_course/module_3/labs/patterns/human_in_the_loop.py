"""
Human-in-the-Loop Pattern — Multi-Agent System

A workflow where humans are active collaborators at key decision points, not
just approval gates.  The pattern demonstrates multiple human touchpoints:
topic classification, quality review, and revision guidance.

Contrast with the other patterns in this module:
  - Coordinator (hub-and-spoke): central hub re-classifies every round.
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.
  - ReAct (single-agent loop): agent calls tools, reads results, responds.
  - Reflection (generate -> critique): generator and critic refine a response.
  - Planning (plan -> execute -> review): planner decomposes into ordered steps.
  - Tool (classify -> run tool -> format): one-shot tool pipeline.
  - Sequential (fixed-order pipeline): agents execute in predetermined order.

Graph:
  entry -> human_classify -> agent -> human_approve -> END
                                     ^              |
                                     +--- loop -----+

  1. entry:            capture the user query.
  2. human_classify:   human classifies the topic and provides instructions.
  3. agent:            generates a response based on the human's input.
  4. human_approve:    human reviews and approves or requests revision.
  5. human_approve_router: approved/end -> END, revise -> agent (with feedback).

Key differences from the other patterns:
  - Human is the primary decision-maker: classifies, reviews, and approves.
  - Agent is a tool in the human's workflow, not an autonomous actor.
  - Two interrupt() points demonstrate multi-step human interaction.
  - Revision feedback is carried in state for the agent to incorporate.

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

from log import logger
from utils import AgentBase
from utils import timed_node
from utils import LLMFactory


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
# Compared to coordinator (next_agent for routing), Human-in-the-Loop adds:
#   - human_classification  -> the topic chosen by the human
#   - human_instructions    -> guidance provided by the human to the agent
#   - human_feedback        -> revision feedback from human_approve
# These fields capture the human's input at each stage so the agent can
# incorporate it without guessing.
class HumanInTheLoopState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    human_classification: str
    human_instructions: str
    human_feedback: str
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
class HumanInTheLoopAgent(AgentBase):
    """
    Human-in-the-Loop pattern: human collaborates with an agent at every
    decision point.

    The human classifies the query, the agent generates a response, and the
    human reviews and approves or requests revision.  The agent is a tool in
    the human's workflow, not an autonomous actor.
    """

    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: HumanInTheLoopState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Human-in-the-Loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Human-in-the-Loop pipeline")],
        }

    # -- Human classify gate ----------------------------------------------
    # First human touchpoint: the human classifies the query topic and can
    # provide optional instructions for the agent.  The interrupt() pauses
    # graph execution until the human responds via Command(resume=...).
    @classmethod
    @timed_node('human_classify')
    def human_classify(cls, state: HumanInTheLoopState) -> Dict:
        query = state.get('query', cls.get_last_message(state))
        logger.info("[Human Classify] Asking human to classify: {}", query[:60])
        result = interrupt({
            "type": "classification",
            "query": query,
            "message": (
                "How would you classify this request? "
                "Respond with 'billing', 'technical', or 'general'. "
                "Optionally add | instructions (e.g. 'billing|check for discounts')."
            ),
        })
        logger.info("[Human Classify] Human response: {}", result)

        raw = result if isinstance(result, str) else "general"
        parts = raw.split("|", 1)
        classification = parts[0].strip().lower()
        instructions = parts[1].strip() if len(parts) > 1 else ""

        if classification not in ("billing", "technical", "general"):
            classification = "general"

        return {
            'human_classification': classification,
            'human_instructions': instructions,
            'rounds': 1,
            'messages': [("assistant", f"Human Classify: Classified as '{classification}'")],
        }

    # -- Agent node -------------------------------------------------------
    # Reads the human's classification and instructions (plus any revision
    # feedback) to generate or revise a response.
    @classmethod
    @timed_node('agent')
    def agent(cls, state: HumanInTheLoopState) -> Dict:
        query = state.get('query', '')
        classification = state.get('human_classification', 'general')
        instructions = state.get('human_instructions', '')
        feedback = state.get('human_feedback', '')
        rounds = state.get('rounds', 0)
        logger.info(
            "[Agent] Round {}, classification={}, has_feedback={}",
            rounds + 1, classification, bool(feedback),
        )

        if rounds >= cls.MAX_ROUNDS:
            return {'rounds': rounds + 1, 'task_complete': True}

        if classification == "billing":
            response = (
                "Agent (Billing): Your billing inquiry has been processed. "
                "Invoice #INV-5678 shows a balance of $249.00, due 2026-07-15. "
                "A receipt has been sent to your email."
            )
        elif classification == "technical":
            response = (
                "Agent (Technical): Your technical issue has been logged. "
                "Our team identified a login service interruption at 14:30 UTC. "
                "The fix has been deployed and the service is now stable."
            )
        else:
            response = (
                "Agent (General): Thank you for reaching out. "
                "Our support team has received your request "
                "and will get back to you within 24 hours."
            )

        if instructions:
            response = f"{response}\n\nHuman instructions applied: {instructions}"

        if feedback:
            response = f"{response}\n\n[Revised based on human feedback: {feedback}]"

        return {
            'response': response,
            'rounds': rounds + 1,
            'messages': [("assistant", response)],
        }

    # -- Human approve gate -----------------------------------------------
    # Second human touchpoint: the human reviews the agent's response and
    # either approves it (-> END) or provides revision feedback (-> agent).
    @classmethod
    @timed_node('human_approve')
    def human_approve(cls, state: HumanInTheLoopState) -> Dict:
        response = state.get('response', '')
        logger.info("[Human Approve] Asking human to approve: {}", response[:60])
        result = interrupt({
            "type": "approval",
            "response": response,
            "message": (
                "Does this response look good? "
                "Reply 'approve' to send, or provide revision feedback."
            ),
        })
        logger.info("[Human Approve] Human decision: {}", result)

        decision_raw = result if isinstance(result, str) else "approve"
        if decision_raw.lower() == "approve":
            return {'human_decision': 'approve', 'human_feedback': ''}
        elif decision_raw.lower() == "end":
            return {'human_decision': 'end', 'human_feedback': ''}
        else:
            return {'human_decision': 'revise', 'human_feedback': decision_raw}

    # -- Routers ----------------------------------------------------------
    # agent -> human_approve unconditionally (simple edge in _build_graph).
    # human_approve_router: approve/end -> END, revise -> agent.
    @classmethod
    def human_approve_router(cls, state: HumanInTheLoopState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision in ('approve', 'end'):
            return END
        return 'agent'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(HumanInTheLoopState)

        workflow.add_node('entry', self.entry)
        workflow.add_node('human_classify', self.human_classify)
        workflow.add_node('agent', self.agent)
        workflow.add_node('human_approve', self.human_approve)

        # Graph topology:
        #   entry -> human_classify -> agent -> human_approve (loop to agent) -> END
        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_classify')
        workflow.add_edge('human_classify', 'agent')
        workflow.add_edge('agent', 'human_approve')

        workflow.add_conditional_edges(
            'human_approve',
            self.human_approve_router,
            {END: END, 'agent': 'agent'},
        )

        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Human-in-the-Loop request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "human_classification": "",
            "human_instructions": "",
            "human_feedback": "",
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
    agent = HumanInTheLoopAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "I have a billing question about my invoice",
        "Need technical support, my login is broken",
        "Hello, I need some general help",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Classification: {result.get('human_classification', 'N/A')}")
        print(f"  Instructions: {result.get('human_instructions', 'N/A')}")
        print(f"  Response: {result.get('response')}")
