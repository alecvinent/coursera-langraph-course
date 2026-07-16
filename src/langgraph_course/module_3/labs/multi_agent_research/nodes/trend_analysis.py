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
from utils import LLMFactory


def trend_analysis_node(state: ResearchState) -> ResearchState:
    start = time.monotonic()
    logger.info("TrendAnalysisAgent activated")

    web_findings = state.agent_outputs.get(AgentRole.WEB_RESEARCH.value, [])
    data_findings = state.agent_outputs.get(AgentRole.DATA_ANALYSIS.value, [])

    context_parts = []
    if web_findings:
        context_parts.append(
            "WEB RESEARCH:\n"
            + "\n".join([f"- {f.content}" for f in web_findings])
        )
    if data_findings:
        context_parts.append(
            "DATA ANALYSIS:\n"
            + "\n".join([f"- {f.content}" for f in data_findings])
        )
    context = "\n\n".join(context_parts) if context_parts else "No preliminary findings available."

    llm = LLMFactory.create(provider="openrouter")
    prompt = (
        f"Identify trends and future projections for: '{state.request.topic}'.\n"
        f"Context:\n{context}\n\n"
        "Provide 2-3 trend observations or projections. "
        "Format each as: FINDING: <trend description> | SOURCE: <basis> | CONFIDENCE: <0.0-1.0>"
    )
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    findings = _parse_findings(content, AgentRole.TREND_ANALYSIS.value)

    state.agent_outputs[AgentRole.TREND_ANALYSIS.value] = findings
    state.agent_states[AgentRole.TREND_ANALYSIS.value].execution_state = (
        ExecutionState.COMPLETED
    )

    elapsed = time.monotonic() - start
    get_buffer().record(
        TelemetryEventType.AGENT_LATENCY,
        AgentRole.TREND_ANALYSIS.value,
        elapsed,
    )
    logger.info(
        "TrendAnalysisAgent completed: {} findings in {:.2f}s",
        len(findings),
        elapsed,
    )
    return state
