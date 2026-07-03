"""
ReAct Pattern — Reasoning + Acting Agent Loop

Contrast with the other multi-agent patterns in this module:
  - Coordinator (hub-and-spoke): central hub routes to specialists.
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.

The ReAct pattern uses a single agent that iteratively reasons about the
user's request and acts by calling tools. The agent can call tools, receive
results, and refine its response based on the tool output.

This is the classic LLM agent loop — think ChatGPT with plugins or an
Anthropic agent using tool calls.  The flow is:

    entry -> human_review -> agent <-> tools -> END
                                ↑         |
                                +---loop--+

  1. entry: capture and normalise the user query.
  2. human_review: optional approval gate via interrupt().
  3. agent: reason — decide which tool to call OR respond directly.
  4. tools: execute the selected tool, return structured results.
  5. agent (second call): reason with tool result, craft final answer.
  6. END: return the natural-language response.

Key differences from coordinator/specialist/event-driven:
  - Single agent (no multi-agent routing).
  - Agent uses tools as external knowledge sources.
  - Loop is agent→tools→agent (not agent→coordinator→agent).

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
# Tool registry
# ---------------------------------------------------------------------------
# Each tool represents an external capability the agent can invoke.  The agent
# selects one based on query keywords; in a real system the LLM would choose
# via structured tool calls (function-calling).
class ToolType:
    LOOKUP_INVOICE = "lookup_invoice"
    CHECK_SYSTEM = "check_system_status"
    ESCALATE = "escalate_to_human"


TOOL_DESCRIPTIONS: dict[str, str] = {
    ToolType.LOOKUP_INVOICE: "Retrieves invoice details for billing inquiries.",
    ToolType.CHECK_SYSTEM: "Checks current system status and known issues.",
    ToolType.ESCALATE: "Escalates the case to a human support agent.",
}


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
# Compared to the coordinator state (next_agent), ReAct replaces the routing
# target with tool-specific fields:
#   - tool_to_call  → which tool the agent selected
#   - tool_input    → the raw query passed to the tool
#   - tool_result   → the data returned by the tool
#   - task_complete → set to True when the agent has a final answer
class ReActState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_to_call: str
    tool_input: str
    tool_result: str
    response: str
    rounds: int
    task_complete: bool
    query: str
    total_processing_time: float
    latencies: Dict[str, float]
    paths_taken: list[str]
    human_decision: str


# ---------------------------------------------------------------------------
# Agent class
# ---------------------------------------------------------------------------
class ReActAgent(AgentBase):
    """
    ReAct pattern: a single agent that reasons, calls tools, and responds.

    The __init__ accepts an LLM (for consistency with coordinator.py) but the
    current classifier is keyword-based so tests can run without an API call.
    Swap _classify_query for an LLM invocation to get the full ReAct loop.
    """

    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    # Maps natural-language keywords to the tool the agent should invoke.
    # Returns None when no tool is needed (the agent can answer directly).
    @classmethod
    def _classify_query(cls, query: str) -> str | None:
        topic = query.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return ToolType.LOOKUP_INVOICE
        if any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return ToolType.CHECK_SYSTEM
        if any(word in topic for word in ("human", "manager", "escalate", "agent", "representative")):
            return ToolType.ESCALATE
        return None

    # -- Entry node -------------------------------------------------------
    # Captures the user query into the state (falling back to get_last_message
    # for flexibility) and logs the start of the ReAct loop.
    @classmethod
    @timed_node('entry')
    def entry(cls, state: ReActState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting ReAct loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting ReAct loop")],
        }

    # -- Human review gate ------------------------------------------------
    # Pauses the graph with interrupt() so a human can approve, redirect back
    # to entry, or end the workflow entirely.  The run() method auto-resumes
    # with "approve" via Command(resume="approve").
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: ReActState) -> Dict:
        logger.info("[Human Review] Pending review for ReAct agent")
        decision = interrupt({"message": "Approve ReAct agent execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: ReActState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'agent'

    # -- Agent node (the core "reasoning" step) ---------------------------
    # Called at least once.  On the first call the agent decides whether a
    # tool is needed; if so it sets tool_to_call and routes to tools.
    # On subsequent calls (after tool_result is populated) it formulates a
    # final response.
    @classmethod
    @timed_node('agent')
    def agent(cls, state: ReActState) -> Dict:
        rounds = state.get('rounds', 0)
        query = state.get('query', '')
        tool_result = state.get('tool_result', '')

        # Safety: never iterate more than MAX_ROUNDS.
        if rounds >= cls.MAX_ROUNDS:
            return cls._build_response(
                state,
                "I've reached the maximum number of reasoning steps. "
                "Here's what I know so far.",
            )

        # If a tool already ran, interpret its result.
        if tool_result:
            return cls._handle_tool_result(state, query, tool_result, rounds)

        # First pass — decide which tool (if any) to call.
        return cls._first_reasoning(state, query, rounds)

    @classmethod
    def _first_reasoning(cls, state: ReActState, query: str, rounds: int) -> Dict:
        tool = cls._classify_query(query)
        if tool:
            logger.info("[Agent] Reasoning: query requires tool '{}'", tool)
            # Return tool_to_call so the agent_router routes to the tools node.
            return {
                'tool_to_call': tool,
                'tool_input': query,
                'rounds': rounds + 1,
                'messages': [("assistant", f"Agent: I need to check information using {tool}.")],
            }
        # No tool needed — respond directly (task_complete=True routes to END).
        logger.info("[Agent] Reasoning: no tool needed — responding directly")
        return cls._build_response(
            state,
            "Agent: Thank you for your inquiry. Based on my knowledge, "
            "I can help you with general questions. For billing or technical "
            "issues, please provide more specific details.",
        )

    @classmethod
    def _handle_tool_result(cls, state: ReActState, query: str, tool_result: str, rounds: int) -> Dict:
        tool = state.get('tool_to_call', '')
        logger.info("[Agent] Reasoning with result from '{}': {}", tool, tool_result[:60])

        # Each tool type produces a domain-specific response that incorporates
        # the structured data returned by the tool.
        if tool == ToolType.LOOKUP_INVOICE:
            return cls._build_response(
                state,
                f"Agent (Billing): I looked up your account. {tool_result} "
                "Would you like me to help with payment or do you have another question?",
            )
        if tool == ToolType.CHECK_SYSTEM:
            return cls._build_response(
                state,
                f"Agent (Technical): I checked our systems. {tool_result} "
                "If you're still experiencing issues, please try restarting "
                "or contact us for further assistance.",
            )
        if tool == ToolType.ESCALATE:
            return cls._build_response(
                state,
                f"Agent: I've escalated your case. {tool_result} "
                "A team member will reach out to you shortly.",
            )
        return cls._build_response(state, f"Agent: I received the following information: {tool_result}")

    # Helper: sets task_complete=True so the agent_router routes to END.
    @classmethod
    def _build_response(cls, state: ReActState, response: str) -> Dict:
        rounds = state.get('rounds', 0)
        return {
            'response': response,
            'messages': [("assistant", response)],
            'rounds': rounds + 1,
            'task_complete': True,
            'total_processing_time': time.time() - state.get('total_processing_time', time.time()),
        }

    # -- Tools node (the "acting" step) -----------------------------------
    # Executes the tool selected by the agent.  In a production system this
    # would call an external API, database, or service.  Here it returns
    # canned structured data for demonstration.
    @classmethod
    @timed_node('tools')
    def tools(cls, state: ReActState) -> Dict:
        tool = state.get('tool_to_call', '')
        tool_input = state.get('tool_input', '')
        logger.info("[Tools] Executing '{}' with input: {}", tool, tool_input[:60])

        if tool == ToolType.LOOKUP_INVOICE:
            return {
                'tool_result': (
                    'Invoice #1024: $249.99, issued 2026-06-01, '
                    'due 2026-07-01. Status: Pending.'
                ),
            }
        if tool == ToolType.CHECK_SYSTEM:
            return {
                'tool_result': (
                    'System status: All core services operational. '
                    'Login service experienced a brief interruption '
                    'at 2026-06-28 14:30 UTC. Now resolved.'
                ),
            }
        if tool == ToolType.ESCALATE:
            return {
                'tool_result': (
                    'Case #ESC-8921 created. Priority: High. '
                    'Estimated response time: 2 hours.'
                ),
            }
        logger.warning("[Tools] Unknown tool: {}", tool)
        return {'tool_result': f'Error: Unknown tool "{tool}".'}

    # -- Routers ----------------------------------------------------------
    # agent_router: if the agent has a final answer (task_complete) → END,
    #               otherwise route to tools to execute the selected tool.
    # tool_router : after running a tool, always route back to agent for a
    #               second reasoning pass (unless MAX_ROUNDS is exceeded).
    @classmethod
    def agent_router(cls, state: ReActState) -> str:
        if state.get('task_complete', False):
            return END
        return 'tools'

    @classmethod
    def tool_router(cls, state: ReActState) -> str:
        if state.get('rounds', 0) >= cls.MAX_ROUNDS:
            return END
        return 'agent'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(ReActState)

        # Register all nodes.
        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('agent', self.agent)
        workflow.add_node('tools', self.tools)

        # Graph topology:
        #   entry → human_review → agent → tools → agent (loop) → END
        #                          ↑           |
        #                          +--router---+
        workflow.set_entry_point('entry')

        # entry always proceeds to human review.
        workflow.add_edge('entry', 'human_review')

        # human_review can approve (→agent), redirect (→entry), or end.
        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'agent': 'agent'},
        )

        # agent either responds (task_complete → END) or calls a tool.
        workflow.add_conditional_edges(
            'agent',
            self.agent_router,
            {END: END, 'tools': 'tools'},
        )

        # tools always route back to agent (unless MAX_ROUNDS hit).
        workflow.add_conditional_edges(
            'tools',
            self.tool_router,
            {END: END, 'agent': 'agent'},
        )

        # MemorySaver checkpointer is required for interrupt()/Command().
        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing ReAct request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "total_processing_time": time.time(),
            "tool_to_call": "",
            "tool_input": "",
            "tool_result": "",
            "response": "",
            "rounds": 0,
            "task_complete": False,
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
    agent = ReActAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "What is my invoice balance?",
        "I can't log in to my account",
        "I want to speak to a human agent",
        "What services do you offer?",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Tool called: {result.get('tool_to_call')}")
        print(f"  Response: {result.get('response')}")
