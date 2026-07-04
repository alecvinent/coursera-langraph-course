from __future__ import annotations

import time
from typing import Any, Callable, Literal

from langgraph.graph import StateGraph
from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.coordination.router import (
    activate_agents_router,
    check_execution_budget,
    should_synthesize,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    ResearchState,
)
from langgraph_course.module_3.labs.multi_agent_research.nodes.competitive_intel import (
    competitive_intel_node,
)
from langgraph_course.module_3.labs.multi_agent_research.nodes.data_analysis import (
    data_analysis_node,
)
from langgraph_course.module_3.labs.multi_agent_research.nodes.synthesis import (
    synthesis_node,
)
from langgraph_course.module_3.labs.multi_agent_research.nodes.trend_analysis import (
    trend_analysis_node,
)
from langgraph_course.module_3.labs.multi_agent_research.nodes.web_research import (
    web_research_node,
)
NodeFunction = Callable[[ResearchState], ResearchState]


class ResearchGraph:
    def __init__(self):
        self.graph = StateGraph(ResearchState)
        self._nodes: dict[str, NodeFunction] = {}
        self._routes: dict[str, list[str]] = {}
        self._conditional_routes: dict[str, Callable] = {}

    def register_node(self, name: str, node_fn: NodeFunction) -> None:
        self._nodes[name] = node_fn
        self.graph.add_node(name, node_fn)
        logger.debug("Registered node: {}", name)

    def add_edge(self, source: str, target: str) -> None:
        if source not in self._routes:
            self._routes[source] = []
        self._routes[source].append(target)
        self.graph.add_edge(source, target)
        logger.debug("Added edge: {} -> {}", source, target)

    def add_conditional_edges(
        self,
        source: str,
        router_fn: Callable[[ResearchState], str],
        destinations: dict[str, str],
    ) -> None:
        self._conditional_routes[source] = router_fn
        self.graph.add_conditional_edges(source, router_fn, destinations)
        logger.debug("Added conditional edges from: {}", source)

    def set_entry_point(self, node: str) -> None:
        self.graph.set_entry_point(node)
        logger.debug("Set entry point: {}", node)

    def set_finish_point(self, node: str) -> None:
        self.graph.set_finish_point(node)
        logger.debug("Set finish point: {}", node)

    def compile(self) -> Any:
        return self.graph.compile()

    def invoke(self, state: ResearchState) -> ResearchState:
        compiled = self.compile()
        result = compiled.invoke(state)
        if isinstance(result, dict):
            return ResearchState.model_validate(result)
        return result

    def stream(
        self, state: ResearchState
    ) -> Any:
        compiled = self.compile()
        for event in compiled.stream(state):
            for node_name, output in event.items():
                if isinstance(output, dict):
                    yield node_name, ResearchState.model_validate(output)
                else:
                    yield node_name, output


def validate_request_node(state: ResearchState) -> ResearchState:
    is_broad = activate_agents_router(state)
    if is_broad == "needs_refinement":
        logger.info("Request flagged as too broad: '{}'", state.request.topic)
    return state


def synthesis_router(state: ResearchState) -> Literal["synthesize", "continue"]:
    if check_execution_budget(state):
        logger.warning("Execution budget exhausted — forcing synthesis")
        return "synthesize"
    decision = should_synthesize(state)
    if decision in ("synthesize", "max_budget"):
        return "synthesize"
    return "continue"


def create_full_graph() -> ResearchGraph:
    rg = ResearchGraph()

    rg.register_node("validate_request", validate_request_node)
    rg.register_node("web_research", web_research_node)
    rg.register_node("data_analysis", data_analysis_node)
    rg.register_node("trend_analysis", trend_analysis_node)
    rg.register_node("competitive_intel", competitive_intel_node)
    rg.register_node("synthesize", synthesis_node)

    def refine_and_retry(state: ResearchState) -> ResearchState:
        logger.info("Request needs refinement: '{}'", state.request.topic)
        return state

    rg.register_node("needs_refinement", refine_and_retry)

    rg.set_entry_point("validate_request")

    rg.add_conditional_edges(
        "validate_request",
        activate_agents_router,
        {
            "run_research": "web_research",
            "needs_refinement": "needs_refinement",
        },
    )
    rg.add_edge("needs_refinement", "web_research")

    rg.add_edge("web_research", "data_analysis")
    rg.add_edge("data_analysis", "trend_analysis")
    rg.add_edge("trend_analysis", "competitive_intel")

    rg.add_conditional_edges(
        "competitive_intel",
        synthesis_router,
        {
            "synthesize": "synthesize",
            "continue": "web_research",
        },
    )

    rg.set_finish_point("synthesize")

    return rg


def run_research(
    topic: str,
    domain_tags: list[str] | None = None,
    max_execution_minutes: int = 30,
) -> ResearchState:
    from langgraph_course.module_3.labs.multi_agent_research.state import (
        AgentState,
        ResearchRequest,
        ResearchRequestStatus,
        ResearchState,
    )

    state = ResearchState(
        request=ResearchRequest(
            topic=topic,
            domain_tags=domain_tags or [],
            status=ResearchRequestStatus.ACTIVE,
        ),
        agent_states={
            AgentRole.WEB_RESEARCH.value: AgentState(role=AgentRole.WEB_RESEARCH),
            AgentRole.DATA_ANALYSIS.value: AgentState(role=AgentRole.DATA_ANALYSIS),
            AgentRole.TREND_ANALYSIS.value: AgentState(role=AgentRole.TREND_ANALYSIS),
            AgentRole.COMPETITIVE_INTELLIGENCE.value: AgentState(
                role=AgentRole.COMPETITIVE_INTELLIGENCE
            ),
            AgentRole.SYNTHESIS.value: AgentState(role=AgentRole.SYNTHESIS),
        },
        execution_metadata={
            "workflow_start": time.monotonic(),
            "max_execution_minutes": max_execution_minutes,
        },
    )

    graph = create_full_graph()
    result = graph.invoke(state)

    status_val = result.request.status
    if isinstance(status_val, str):
        logger.info(
            "Research complete: topic='{}' status={} agents={} findings={}",
            topic,
            status_val,
            len(result.agent_outputs),
            sum(len(v) for v in result.agent_outputs.values()),
        )
    else:
        logger.info(
            "Research complete: topic='{}' status={} agents={} findings={}",
            topic,
            status_val.value,
            len(result.agent_outputs),
            sum(len(v) for v in result.agent_outputs.values()),
        )
    return result


def stream_research(
    topic: str,
    domain_tags: list[str] | None = None,
    max_execution_minutes: int = 30,
) -> Any:
    from langgraph_course.module_3.labs.multi_agent_research.state import (
        AgentState,
        AgentRole,
        ResearchRequest,
        ResearchRequestStatus,
        ResearchState,
    )

    state = ResearchState(
        request=ResearchRequest(
            topic=topic,
            domain_tags=domain_tags or [],
            status=ResearchRequestStatus.ACTIVE,
        ),
        agent_states={
            AgentRole.WEB_RESEARCH.value: AgentState(role=AgentRole.WEB_RESEARCH),
            AgentRole.DATA_ANALYSIS.value: AgentState(role=AgentRole.DATA_ANALYSIS),
            AgentRole.TREND_ANALYSIS.value: AgentState(role=AgentRole.TREND_ANALYSIS),
            AgentRole.COMPETITIVE_INTELLIGENCE.value: AgentState(
                role=AgentRole.COMPETITIVE_INTELLIGENCE
            ),
            AgentRole.SYNTHESIS.value: AgentState(role=AgentRole.SYNTHESIS),
        },
        execution_metadata={
            "workflow_start": time.monotonic(),
            "max_execution_minutes": max_execution_minutes,
        },
    )

    graph = create_full_graph()
    for node_name, result_state in graph.stream(state):
        yield node_name, result_state
