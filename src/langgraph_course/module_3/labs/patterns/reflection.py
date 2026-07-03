"""
Reflection Pattern — Generate → Critique → Refine Loop

Contrast with the other patterns in this module:
  - Coordinator (hub-and-spoke): central hub routes to specialists.
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.
  - ReAct (single-agent loop): agent calls tools, reads results, responds.

The Reflection pattern uses two roles — a generator and a critic — that
alternate to iteratively improve a response. The generator produces a draft,
the critic evaluates it and provides feedback, and the generator revises.
The loop continues until the critic approves or MAX_ROUNDS is reached.

Graph:
  entry -> human_review -> generator -> critic -> generator (or END)
                                  ↑         |
                                  +---loop--+

  1. entry: capture the user query.
  2. human_review: optional approval gate via interrupt().
  3. generator: produce an initial draft answer.
  4. critic: evaluate the draft — approve or return improvement feedback.
  5. generator (second call): revise the draft using the critic's feedback.
  6. critic (second call): approve the revised draft → END.

Key differences from the other patterns:
  - Two roles (generator + critic) instead of N agents or 1 agent + tools.
  - The loop is improvement-driven: each iteration raises quality.
  - No external tool calls — the refinement is purely internal to the LLM.

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
# State schema
# ---------------------------------------------------------------------------
# Compared to the coordinator state (next_agent) or ReAct (tool_to_call),
# Reflection introduces:
#   - draft      → the current response being refined
#   - feedback   → the critic's evaluation and suggestions
#   - approved   → whether the critic has accepted the current draft
class ReflectionState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    draft: str
    feedback: str
    approved: bool
    response: str
    rounds: int
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class ReflectionAgent(AgentBase):
    """
    Reflection pattern: a generator and critic that refine a response together.

    The generator creates/revises drafts, the critic evaluates them and
    provides feedback.  The loop runs until the critic approves or
    MAX_ROUNDS is exhausted.

    Like the other patterns, the classifier is keyword-based so tests can
    run without an API call.  Swap the hard-coded strings for LLM invocations
    to get a production-grade reflection loop.
    """

    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    # Determines the topic of the user's query so the generator can tailor
    # its initial draft and the critic can check topic-specific quality.
    @classmethod
    def _classify_topic(cls, query: str) -> str:
        topic = query.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return "billing"
        if any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return "technical"
        if any(word in topic for word in ("human", "manager", "escalate", "agent", "representative")):
            return "escalation"
        return "general"

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: ReflectionState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Reflection loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Reflection loop")],
        }

    # -- Human review gate ------------------------------------------------
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: ReflectionState) -> Dict:
        logger.info("[Human Review] Pending review for Reflection agent")
        decision = interrupt({"message": "Approve Reflection agent execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: ReflectionState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'generator'

    # -- Generator node ---------------------------------------------------
    # Produces the initial draft (first call) or revises an existing draft
    # based on the critic's feedback (subsequent calls).
    @classmethod
    @timed_node('generator')
    def generator(cls, state: ReflectionState) -> Dict:
        rounds = state.get('rounds', 0)
        query = state.get('query', '')
        feedback = state.get('feedback', '')
        logger.info("[Generator] Drafting response (round {})", rounds + 1)

        if rounds >= cls.MAX_ROUNDS:
            return {
                'response': state.get('draft', ''),
                'rounds': rounds + 1,
            }

        # First call — produce an initial draft.
        if not feedback:
            draft = cls._initial_draft(query)
            return {
                'draft': draft,
                'rounds': rounds + 1,
                'messages': [("assistant", f"Generator: Initial draft (round {rounds + 1})")],
            }

        # Subsequent calls — revise the draft using the critic's feedback.
        revised = cls._revise_draft(state.get('draft', ''), feedback)
        return {
            'draft': revised,
            'rounds': rounds + 1,
            'messages': [("assistant", f"Generator: Revised draft (round {rounds + 1})")],
        }

    @classmethod
    def _initial_draft(cls, query: str) -> str:
        topic = cls._classify_topic(query)
        if topic == "billing":
            return (
                "We have received your billing inquiry. "
                "Our team will review your account and get back to you shortly."
            )
        if topic == "technical":
            return (
                "We have received your technical support request. "
                "Our engineering team will investigate the issue."
            )
        if topic == "escalation":
            return (
                "We have received your escalation request. "
                "A senior team member will follow up with you."
            )
        return (
            "Thank you for your inquiry. "
            "We have received your message and will respond as soon as possible."
        )

    @classmethod
    def _revise_draft(cls, draft: str, feedback: str) -> str:
        # Simulate incorporating feedback by expanding the draft with the
        # critic's suggestions.  A real LLM would rewrite the draft directly.
        topic_words = draft.lower()
        if "billing" in topic_words or "payment" in topic_words or "invoice" in topic_words:
            return (
                "Thank you for reaching out about your billing concern. "
                "We have reviewed your account and identified the issue. "
                "To resolve this, please verify your payment method on file. "
                "If the problem persists, our billing team will reach out "
                "within 24 hours with a detailed resolution plan."
            )
        if "technical" in topic_words or "bug" in topic_words or "error" in topic_words or "crash" in topic_words:
            return (
                "Thank you for reporting this technical issue. "
                "Our engineering team has identified the root cause and "
                "is deploying a fix. As a workaround, please try clearing "
                "your cache or restarting the application. "
                "We will notify you once the fix is live."
            )
        if "escalation" in topic_words:
            return (
                "We have escalated your case to our senior support team. "
                "A dedicated representative has been assigned and will "
                "contact you within 2 hours. Your case reference number "
                "is #ESC-8921. Please keep this for your records."
            )
        return (
            "Thank you for your inquiry. We value your feedback and "
            "have forwarded your request to the appropriate team. "
            "We aim to respond within 24 hours. If you have additional "
            "details to share, please do not hesitate to reply."
        )

    # -- Critic node ------------------------------------------------------
    # Evaluates the current draft.  Returns feedback with improvement
    # suggestions or marks the draft as approved.
    @classmethod
    @timed_node('critic')
    def critic(cls, state: ReflectionState) -> Dict:
        rounds = state.get('rounds', 0)
        draft = state.get('draft', '')
        logger.info("[Critic] Evaluating draft (round {})", rounds)

        if rounds >= cls.MAX_ROUNDS:
            return {'approved': True, 'response': draft}

        evaluation = cls._evaluate_draft(draft, rounds)
        if evaluation['approved']:
            logger.info("[Critic] Draft approved")
            return {
                'approved': True,
                'feedback': '',
                'response': draft,
                'messages': [("assistant", "Critic: Draft approved.")],
            }

        logger.info("[Critic] Feedback: {}", evaluation['feedback'][:60])
        return {
            'approved': False,
            'feedback': evaluation['feedback'],
            'messages': [("assistant", f"Critic: {evaluation['feedback']}")],
        }

    @classmethod
    def _evaluate_draft(cls, draft: str, rounds: int) -> Dict:
        # Round 1 drafts are intentionally brief — the critic asks for more
        # detail.  Round 2+ drafts have been expanded and should pass.
        if rounds <= 1:
            # Check if the draft is too short or generic.
            if len(draft) < 100:
                return {
                    'approved': False,
                    'feedback': (
                        "The response is too brief and lacks specific details. "
                        "Please expand the draft to include: "
                        "(1) a clear description of the issue, "
                        "(2) the steps being taken to resolve it, "
                        "(3) the expected timeline, and "
                        "(4) any action the user needs to take."
                    ),
                }

        # Longer / subsequent-round drafts are considered good enough.
        return {'approved': True}

    # -- Routers ----------------------------------------------------------
    # generator_router: after the generator runs, always route to critic.
    # critic_router   : if the draft is approved → END, otherwise → generator
    #                   for another revision round.
    @classmethod
    def generator_router(cls, state: ReflectionState) -> str:
        return 'critic'

    @classmethod
    def critic_router(cls, state: ReflectionState) -> str:
        if state.get('approved', False):
            return END
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        return 'generator'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(ReflectionState)

        # Register all nodes.
        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('generator', self.generator)
        workflow.add_node('critic', self.critic)

        # Graph topology:
        #   entry → human_review → generator → critic → generator (loop) → END
        #                                 ↑              |
        #                                 +---router-----+
        workflow.set_entry_point('entry')

        # entry always proceeds to human review.
        workflow.add_edge('entry', 'human_review')

        # human_review can approve (→generator), redirect (→entry), or end.
        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'generator': 'generator'},
        )

        # generator always proceeds to critic.
        workflow.add_conditional_edges(
            'generator',
            self.generator_router,
            {'critic': 'critic'},
        )

        # critic either approves (→END) or sends back to generator.
        workflow.add_conditional_edges(
            'critic',
            self.critic_router,
            {END: END, 'generator': 'generator'},
        )

        # MemorySaver checkpointer is required for interrupt()/Command().
        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Reflection request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "draft": "",
            "feedback": "",
            "approved": False,
            "response": "",
            "rounds": 0,
            "total_processing_time": time.time(),
            "latencies": {},
            "paths_taken": [],
            "human_decision": "",
        }
        # First invoke hits the interrupt at human_review.
        result = self.graph.invoke(initial_state, config)
        # Auto-resume until the interrupt is cleared.
        while '__interrupt__' in result:
            result = self.graph.invoke(Command(resume="approve"), config)
        logger.info("Result: {}", result.get("response", ""))
        return result


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == '__main__':
    agent = ReflectionAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "What is my invoice balance?",
        "The app keeps crashing when I log in",
        "I want to speak to a manager",
        "Tell me about your services",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Drafts / rounds: {result.get('rounds')}")
        print(f"  Approved: {result.get('approved')}")
        print(f"  Response: {result.get('response')}")
