"""
Planning Pattern — Plan → Execute → Review → Repeat

Contrast with the other patterns in this module:
  - Coordinator (hub-and-spoke): central hub routes to specialists.
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.
  - ReAct (single-agent loop): agent calls tools, reads results, responds.
  - Reflection (generate → critique): generator and critic refine a response.

The Planning pattern creates an ordered step-by-step plan and executes each
step sequentially.  A planner decomposes the user's request into discrete
steps, an executor runs each one, and the planner reviews progress after
every step, moving to the next or completing the workflow.

Graph:
  entry -> human_review -> planner -> executor -> planner (or END)
                                      ↑         |
                                      +---loop--+

  1. entry: capture the user query.
  2. human_review: optional approval gate via interrupt().
  3. planner: decompose the query into ordered steps (plan).
  4. executor: execute the next pending step and return its result.
  5. planner (subsequent): review the step result, mark it complete,
     pick the next step — or respond when all steps are done.

Key differences from the other patterns:
  - Explicit plan: the workflow is pre-defined as a list of discrete steps.
  - Sequential execution: steps run one at a time in order.
  - Progress tracking: completed steps are accumulated in state.
  - Planning happens before acting — unlike ReAct (interleaved).

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

from log import logger
from utils import AgentBase
from utils import timed_node
from utils import LLMFactory


# ---------------------------------------------------------------------------
# Topic classification constants
# ---------------------------------------------------------------------------
class PlanTopic:
    BILLING = "billing"
    TECHNICAL = "technical"
    GENERAL = "general"


# ---------------------------------------------------------------------------
# Step execution results
# ---------------------------------------------------------------------------
# Pre-defined step outcomes for each topic.  In a production system the
# executor would make API calls or query a knowledge base.
STEP_RESULTS: Dict[str, List[Dict[str, str]]] = {
    PlanTopic.BILLING: [
        {"step": "Verify customer identity and account status", "result": "Customer verified — account #A1024, active since 2024."},
        {"step": "Retrieve invoice and payment history", "result": "Invoice #INV-5678: $249.00, due 2026-07-15. Last payment: 2026-05-01."},
        {"step": "Reconcile billing discrepancy", "result": "Discrepancy found: a late fee was applied in error. Fee waived."},
        {"step": "Communicate resolution to customer", "result": "Resolution: invoice adjusted to $249.00. Updated invoice sent to customer email."},
    ],
    PlanTopic.TECHNICAL: [
        {"step": "Identify affected system or service", "result": "Service affected: user authentication (login service)."},
        {"step": "Check system logs and error reports", "result": "Logs show elevated 503 errors on login endpoint since 14:30 UTC. Root cause: database connection pool exhaustion."},
        {"step": "Determine root cause and workaround", "result": "Root cause: connection pool size too low under peak load. Workaround: restart connection pool. Fix: increase pool limit."},
        {"step": "Provide fix instructions or timeline", "result": "Fix deployed at 14:45 UTC. Login service restored. Monitoring active for 1 hour."},
    ],
    PlanTopic.GENERAL: [
        {"step": "Categorise the inquiry", "result": "Inquiry categorised as general information request."},
        {"step": "Retrieve relevant information", "result": "Relevant information gathered from knowledge base."},
        {"step": "Formulate and deliver response", "result": "Response drafted with relevant details and next steps."},
    ],
}

PLANS: Dict[str, List[str]] = {
    PlanTopic.BILLING: ["Verify customer identity and account status", "Retrieve invoice and payment history", "Reconcile billing discrepancy", "Communicate resolution to customer"],
    PlanTopic.TECHNICAL: ["Identify affected system or service", "Check system logs and error reports", "Determine root cause and workaround", "Provide fix instructions or timeline"],
    PlanTopic.GENERAL: ["Categorise the inquiry", "Retrieve relevant information", "Formulate and deliver response"],
}

RESPONSES: Dict[str, str] = {
    PlanTopic.BILLING: "Your billing issue has been resolved. The late fee has been waived and your updated invoice of $249.00 has been sent to your email. Is there anything else we can help with?",
    PlanTopic.TECHNICAL: "The login issue has been resolved. Our team identified a database connection problem and deployed a fix at 14:45 UTC. The service is now stable. If you continue to experience issues, please let us know.",
    PlanTopic.GENERAL: "Thank you for your inquiry. I've gathered the relevant information and prepared a response. If you need further details, please don't hesitate to ask.",
}


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
# Compared to coordinator (next_agent) or ReAct (tool_to_call), Planning
# introduces:
#   - plan             → the ordered list of steps
#   - completed_steps  → steps already executed
#   - step_results     → outcomes of executed steps
#   - current_step     → the step being executed or about to be executed
class PlanningState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    plan: List[str]
    completed_steps: List[str]
    step_results: List[Dict[str, str]]
    current_step: str
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
class PlanningAgent(AgentBase):
    """
    Planning pattern: create a step-by-step plan, execute each step in order.

    The planner decomposes the user's query into discrete steps, the executor
    runs the next pending step, and the planner reviews progress and moves
    to the next step.  When all steps are done, the planner composes the
    final response.

    The classifier is keyword-based so tests run without an API call.
    Swap _classify_topic for an LLM invocation to get full plan generation.
    """

    MAX_ROUNDS = 6

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    @classmethod
    def _classify_topic(cls, query: str) -> str:
        topic = query.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return PlanTopic.BILLING
        if any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return PlanTopic.TECHNICAL
        return PlanTopic.GENERAL

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: PlanningState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Planning loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Planning loop")],
        }

    # -- Human review gate ------------------------------------------------
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: PlanningState) -> Dict:
        logger.info("[Human Review] Pending review for Planning agent")
        decision = interrupt({"message": "Approve Planning agent execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: PlanningState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'planner'

    # -- Planner node -----------------------------------------------------
    # First call: classify the query and generate a multi-step plan.
    # Subsequent calls: review the executor's result, mark the step as
    # completed, and either pick the next step or respond.
    @classmethod
    @timed_node('planner')
    def planner(cls, state: PlanningState) -> Dict:
        rounds = state.get('rounds', 0)
        plan = state.get('plan', [])
        completed = state.get('completed_steps', [])
        results = state.get('step_results', [])
        query = state.get('query', '')
        logger.info("[Planner] Reviewing progress (round {})", rounds + 1)

        if rounds >= cls.MAX_ROUNDS:
            return {
                'response': state.get('response', ''),
                'rounds': rounds + 1,
                'task_complete': True,
            }

        # First call — create the plan.
        if not plan:
            return cls._create_plan(query)

        # Subsequent calls — review the latest step result.
        if results:
            logger.info("[Planner] Reviewing result: {}", results[-1].get('result', '')[:60])
            return cls._review_progress(state, plan, completed, results)

        # No results yet (shouldn't normally reach here) — proceed.
        return cls._next_step(plan, completed, results, rounds)

    @classmethod
    def _create_plan(cls, query: str) -> Dict:
        topic = cls._classify_topic(query)
        steps = PLANS.get(topic, PLANS[PlanTopic.GENERAL])
        first_step = steps[0] if steps else ""
        logger.info("[Planner] Created plan with {} steps: {}", len(steps), first_step)
        return {
            'plan': steps,
            'current_step': first_step,
            'rounds': 1,
            'messages': [("assistant", f"Planner: Created {len(steps)}-step plan. Starting: {first_step}")],
        }

    @classmethod
    def _review_progress(cls, state: PlanningState, plan: List[str], completed: List[str], results: List[Dict[str, str]]) -> Dict:
        rounds = state.get('rounds', 0)

        # All steps done — compose the final response.
        if len(completed) >= len(plan):
            topic = cls._classify_topic(state.get('query', ''))
            final_msg = RESPONSES.get(topic, RESPONSES[PlanTopic.GENERAL])
            summary = "\n".join(f"  ✅ {s}" for s in completed)
            logger.info("[Planner] All {} steps complete — responding", len(plan))
            return {
                'response': final_msg,
                'rounds': rounds + 1,
                'task_complete': True,
                'messages': [("assistant", f"Planner: All steps complete.\n{summary}\n\n{final_msg}")],
            }

        # More steps remain — advance to the next one.
        return cls._next_step(plan, completed, results, rounds)

    @classmethod
    def _next_step(cls, plan: List[str], completed: List[str], results: List[Dict[str, str]], rounds: int) -> Dict:
        next_idx = len(completed)
        step = plan[next_idx] if next_idx < len(plan) else ""
        logger.info("[Planner] Advancing to step {}/{}: {}", next_idx + 1, len(plan), step)
        return {
            'current_step': step,
            'rounds': rounds + 1,
            'messages': [("assistant", f"Planner: Executing step {next_idx + 1}/{len(plan)}: {step}")],
        }

    # -- Executor node ----------------------------------------------------
    # Executes the current step and returns a simulated result based on the
    # query topic.  In production this would call an API, database, or tool.
    @classmethod
    @timed_node('executor')
    def executor(cls, state: PlanningState) -> Dict:
        step = state.get('current_step', '')
        query = state.get('query', '')
        completed = state.get('completed_steps', [])
        results = state.get('step_results', [])
        logger.info("[Executor] Running step: {}", step[:60])

        topic = cls._classify_topic(query)
        topic_results = STEP_RESULTS.get(topic, STEP_RESULTS[PlanTopic.GENERAL])

        # Find the matching step result by name.
        step_result = {"step": step, "result": "Step completed."}
        for sr in topic_results:
            if sr["step"] == step:
                step_result = sr
                break

        logger.info("[Executor] Result: {}", step_result["result"][:60])
        return {
            'completed_steps': completed + [step],
            'step_results': results + [step_result],
            'messages': [("assistant", f"Executor: Step '{step}' complete — {step_result['result']}")],
        }

    # -- Routers ----------------------------------------------------------
    # planner_router : if the task is complete → END, otherwise → executor.
    # executor_router: after running a step, always route back to planner
    #                  for progress review.
    @classmethod
    def planner_router(cls, state: PlanningState) -> str:
        if state.get('task_complete', False):
            return END
        return 'executor'

    @classmethod
    def executor_router(cls, state: PlanningState) -> str:
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        return 'planner'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(PlanningState)

        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('planner', self.planner)
        workflow.add_node('executor', self.executor)

        # Graph topology:
        #   entry → human_review → planner → executor → planner (loop) → END
        #                                 ↑              |
        #                                 +---router-----+
        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'planner': 'planner'},
        )

        workflow.add_conditional_edges(
            'planner',
            self.planner_router,
            {END: END, 'executor': 'executor'},
        )

        workflow.add_conditional_edges(
            'executor',
            self.executor_router,
            {END: END, 'planner': 'planner'},
        )

        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Planning request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "plan": [],
            "completed_steps": [],
            "step_results": [],
            "current_step": "",
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
    agent = PlanningAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "I have a billing question about my invoice",
        "Need technical support, my login is broken",
        "Hello, I need some general help",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Plan ({len(result.get('plan', []))} steps):")
        for step in result.get('plan', []):
            status = "✅" if step in result.get('completed_steps', []) else "⏳"
            print(f"    {status} {step}")
        print(f"  Response: {result.get('response')}")
