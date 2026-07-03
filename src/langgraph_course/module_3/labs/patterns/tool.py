"""
Tool Pattern — Tool Orchestrator (classify → run tool → format response)

Contrast with the other patterns in this module:
  - Coordinator (hub-and-spoke): central hub routes to specialists (loop).
  - Specialist (mesh): peers route directly to each other.
  - Event-driven (pub-sub): agents communicate through a shared event queue.
  - ReAct (single-agent loop): agent iterates between reasoning and tool calls.
  - Reflection (generate → critique): generator and critic refine a response.
  - Planning (plan → execute): ordered steps executed sequentially.

The Tool pattern is a linear pipeline: classify the query, select a single
tool, execute it, and format the result into a final response.  Unlike ReAct
(which loops between agent and tools) or Coordinator (which loops between
hub and agents), this pattern is one-shot — no iteration.

Graph:
  entry -> human_review -> tool_orchestrator -> [tool_*] -> output_formatter -> END

  1. entry: capture the user query.
  2. human_review: optional approval gate via interrupt().
  3. tool_orchestrator: classify the query and select the appropriate tool.
  4. tool_invoice / tool_status / tool_escalate: execute the selected tool.
  5. output_formatter: read the tool result and format a natural-language response.

Key differences from ReAct:
  - ReAct: agent → tools → agent → tools → ... → END (loop).
  - Tool:  orchestrator → tool → formatter → END (linear).

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
# Tool type constants
# ---------------------------------------------------------------------------
class ToolDispatch:
    INVOICE = "tool_invoice"
    STATUS = "tool_status"
    ESCALATE = "tool_escalate"


# ---------------------------------------------------------------------------
# State schema
# ---------------------------------------------------------------------------
# Compared to coordinator (next_agent) or ReAct (tool_to_call), the Tool
# pattern uses:
#   - selected_tool → which tool the orchestrator picked
#   - tool_input    → the raw query passed to the tool
#   - tool_result   → the data returned by the tool
#   - task_complete → set by output_formatter after formatting
class ToolState(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    query: str
    selected_tool: str
    tool_input: str
    tool_result: str
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
class ToolAgent(AgentBase):
    """
    Tool Orchestrator pattern: classify → run tool → format response.

    A single orchestrator node classifies the user's query and selects one
    of three tools.  The tool runs exactly once, and an output formatter
    converts the structured result into a natural-language response.

    The classifier is keyword-based so tests run without an API call.
    Swap _classify_query for an LLM invocation for production tool selection.
    """

    MAX_ROUNDS = 4

    def __init__(self, provider: str = "openrouter", llm=None) -> None:
        self.llm = llm or LLMFactory.create(provider=provider)
        super().__init__()

    # -- Classification ---------------------------------------------------
    @classmethod
    def _classify_query(cls, query: str) -> str:
        topic = query.lower()
        if any(word in topic for word in ("billing", "payment", "invoice", "refund", "finance")):
            return ToolDispatch.INVOICE
        if any(word in topic for word in ("technical", "bug", "error", "crash", "support", "login", "password")):
            return ToolDispatch.STATUS
        if any(word in topic for word in ("human", "manager", "escalate", "agent", "representative")):
            return ToolDispatch.ESCALATE
        return ""

    # -- Entry node -------------------------------------------------------
    @classmethod
    @timed_node('entry')
    def entry(cls, state: ToolState) -> Dict:
        query = state.get('query') or cls.get_last_message(state)
        logger.info("[Entry] Starting Tool Orchestrator loop for: {}", query[:60])
        return {
            'query': query,
            'messages': [("assistant", "Entry: Starting Tool Orchestrator loop")],
        }

    # -- Human review gate ------------------------------------------------
    @classmethod
    @timed_node('human_review')
    def human_review(cls, state: ToolState) -> Dict:
        logger.info("[Human Review] Pending review for Tool Orchestrator")
        decision = interrupt({"message": "Approve Tool Orchestrator execution?"})
        logger.info("[Human Review] Decision: {}", decision)
        return {'human_decision': decision or 'approve'}

    @classmethod
    def human_router(cls, state: ToolState) -> str:
        decision = state.get('human_decision', 'approve')
        if decision == 'end':
            return END
        if decision == 'redirect':
            return 'entry'
        return 'tool_orchestrator'

    # -- Tool orchestrator node -------------------------------------------
    # Classifies the query and picks the appropriate tool.  If no tool
    # matches, responds directly (task_complete=True → END).
    @classmethod
    @timed_node('tool_orchestrator')
    def tool_orchestrator(cls, state: ToolState) -> Dict:
        query = state.get('query', '')
        tool = cls._classify_query(query)
        logger.info("[Orchestrator] Classified query -> tool: {}", tool or "direct response")

        if not tool:
            return {
                'response': "Agent: Thank you for your inquiry. For billing, technical, or escalation requests, please provide more specific details. How can I help you today?",
                'task_complete': True,
            }

        return {
            'selected_tool': tool,
            'tool_input': query,
            'messages': [("assistant", f"Orchestrator: Routing to {tool}")],
        }

    # -- Tool nodes -------------------------------------------------------
    # Each tool performs a specific operation and returns structured data.
    # Tools are one-shot — they run once and route to output_formatter.
    @classmethod
    @timed_node(ToolDispatch.INVOICE)
    def tool_invoice(cls, state: ToolState) -> Dict:
        logger.info("[Tool Invoice] Looking up invoice information")
        return {
            'tool_result': (
                'Invoice #1024: $249.99, issued 2026-06-01, '
                'due 2026-07-01. Status: Pending. '
                'Customer: Account #A1024 (active since 2024).'
            ),
        }

    @classmethod
    @timed_node(ToolDispatch.STATUS)
    def tool_status(cls, state: ToolState) -> Dict:
        logger.info("[Tool Status] Checking system status")
        return {
            'tool_result': (
                'System status: All core services operational. '
                'Login service experienced a brief interruption '
                'at 2026-06-28 14:30 UTC. Root cause: database '
                'connection pool exhaustion. Fix deployed at 14:45 UTC. '
                'Service now stable.'
            ),
        }

    @classmethod
    @timed_node(ToolDispatch.ESCALATE)
    def tool_escalate(cls, state: ToolState) -> Dict:
        logger.info("[Tool Escalate] Escalating to human agent")
        return {
            'tool_result': (
                'Case #ESC-8921 created. Priority: High. '
                'Assigned to senior support agent. '
                'Estimated response time: 2 hours. '
                'Customer notified via WhatsApp at 59896379476.'
            ),
        }

    # -- Output formatter node --------------------------------------------
    # Reads the tool result and formats it into a natural-language response.
    # This is the final node — it always sets task_complete=True → END.
    @classmethod
    @timed_node('output_formatter')
    def output_formatter(cls, state: ToolState) -> Dict:
        tool = state.get('selected_tool', '')
        result = state.get('tool_result', '')
        rounds = state.get('rounds', 0)
        logger.info("[Formatter] Formatting result from {}", tool)

        if tool == ToolDispatch.INVOICE:
            response = (
                f"Agent (Billing): I looked up your account. {result} "
                "Would you like me to help with payment or do you have "
                "another question?"
            )
        elif tool == ToolDispatch.STATUS:
            response = (
                f"Agent (Technical): I checked our systems. {result} "
                "If you're still experiencing issues, please try "
                "restarting or contact us for further assistance."
            )
        elif tool == ToolDispatch.ESCALATE:
            response = (
                f"Agent: I've escalated your case. {result} "
                "A team member will reach out to you shortly."
            )
        else:
            response = f"Agent: Here is the information I found: {result}"

        return {
            'response': response,
            'messages': [("assistant", response)],
            'rounds': rounds + 1,
            'task_complete': True,
            'total_processing_time': time.time() - state.get('total_processing_time', time.time()),
        }

    # -- Routers ----------------------------------------------------------
    # orchestrator_router: if task_complete (direct response) → END,
    #                      otherwise → the selected tool node.
    # tool_router        : always → output_formatter.
    @classmethod
    def orchestrator_router(cls, state: ToolState) -> str:
        if state.get('task_complete', False):
            return END
        tool = state.get('selected_tool', '')
        return tool if tool else ToolDispatch.INVOICE

    @classmethod
    def tool_router(cls, state: ToolState) -> str:
        return 'output_formatter'

    # -- Graph construction -----------------------------------------------
    def _build_graph(self) -> CompiledStateGraph:
        workflow = StateGraph(ToolState)

        workflow.add_node('entry', self.entry)
        workflow.add_node('human_review', self.human_review)
        workflow.add_node('tool_orchestrator', self.tool_orchestrator)
        workflow.add_node(ToolDispatch.INVOICE, self.tool_invoice)
        workflow.add_node(ToolDispatch.STATUS, self.tool_status)
        workflow.add_node(ToolDispatch.ESCALATE, self.tool_escalate)
        workflow.add_node('output_formatter', self.output_formatter)

        # Graph topology:
        #   entry → human_review → tool_orchestrator → tool_* → output_formatter → END
        workflow.set_entry_point('entry')

        workflow.add_edge('entry', 'human_review')

        workflow.add_conditional_edges(
            'human_review',
            self.human_router,
            {END: END, 'entry': 'entry', 'tool_orchestrator': 'tool_orchestrator'},
        )

        workflow.add_conditional_edges(
            'tool_orchestrator',
            self.orchestrator_router,
            {
                END: END,
                ToolDispatch.INVOICE: ToolDispatch.INVOICE,
                ToolDispatch.STATUS: ToolDispatch.STATUS,
                ToolDispatch.ESCALATE: ToolDispatch.ESCALATE,
            },
        )

        for tool_node in (ToolDispatch.INVOICE, ToolDispatch.STATUS, ToolDispatch.ESCALATE):
            workflow.add_conditional_edges(
                tool_node,
                self.tool_router,
                {'output_formatter': 'output_formatter'},
            )

        workflow.add_edge('output_formatter', END)

        return workflow.compile(checkpointer=MemorySaver())

    # -- Entry point ------------------------------------------------------
    def run(self, question: str) -> Dict:
        logger.info("Processing Tool Orchestrator request: {!r}", question)
        thread_id = str(uuid.uuid4())
        config = {"configurable": {"thread_id": thread_id}}
        initial_state: Dict = {
            "messages": [("user", question)],
            "query": question,
            "selected_tool": "",
            "tool_input": "",
            "tool_result": "",
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
    agent = ToolAgent()
    print(agent.graph.get_graph().draw_mermaid())
    samples = [
        "What is my invoice balance?",
        "The app keeps crashing when I log in",
        "I want to speak to a human agent",
        "What services do you offer?",
    ]
    for q in samples:
        result = agent.run(q)
        print(f"\nQ: {q}")
        print(f"  Paths: {' → '.join(result.get('paths_taken'))}")
        print(f"  Tool selected: {result.get('selected_tool')}")
        print(f"  Response: {result.get('response')}")
