from __future__ import annotations

import time

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.nodes.web_research import (
    _parse_findings,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    ExecutionState,
    ResearchState,
)
from langgraph_course.module_3.labs.multi_agent_research.telemetry.events import (
    TelemetryEventType,
    get_buffer,
)
from langgraph_course.utils.llm import LLMFactory


def data_analysis_node(state: ResearchState) -> ResearchState:
    start = time.monotonic()
    logger.info("DataAnalysisAgent activated")

    web_findings = state.agent_outputs.get(AgentRole.WEB_RESEARCH.value, [])
    web_context = "\n".join(
        [f"- {f.content} (source: {f.source})" for f in web_findings]
    )

    llm = LLMFactory.create(provider="openrouter")
    prompt = (
        f"Analyze quantitative data related to: '{state.request.topic}'.\n"
        f"Web research findings for context:\n{web_context}\n\n"
        "Provide 2-4 data points, statistics, or quantitative observations. "
        "Format each as: FINDING: <content> | SOURCE: <dataset or reference> | CONFIDENCE: <0.0-1.0>"
    )
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    findings = _parse_findings(content, AgentRole.DATA_ANALYSIS.value)

    state.agent_outputs[AgentRole.DATA_ANALYSIS.value] = findings
    state.agent_states[AgentRole.DATA_ANALYSIS.value].execution_state = (
        ExecutionState.COMPLETED
    )

    elapsed = time.monotonic() - start
    get_buffer().record(
        TelemetryEventType.AGENT_LATENCY,
        AgentRole.DATA_ANALYSIS.value,
        elapsed,
    )
    logger.info(
        "DataAnalysisAgent completed: {} findings in {:.2f}s",
        len(findings),
        elapsed,
    )
    return state
