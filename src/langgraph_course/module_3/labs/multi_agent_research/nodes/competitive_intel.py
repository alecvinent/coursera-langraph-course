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


def competitive_intel_node(state: ResearchState) -> ResearchState:
    start = time.monotonic()
    logger.info("CompetitiveIntelligenceAgent activated")

    web_findings = state.agent_outputs.get(AgentRole.WEB_RESEARCH.value, [])
    trend_findings = state.agent_outputs.get(AgentRole.TREND_ANALYSIS.value, [])

    context_parts = []
    if web_findings:
        context_parts.append(
            "MARKET CONTEXT:\n"
            + "\n".join([f"- {f.content}" for f in web_findings])
        )
    if trend_findings:
        context_parts.append(
            "TRENDS:\n"
            + "\n".join([f"- {f.content}" for f in trend_findings])
        )
    context = "\n\n".join(context_parts) if context_parts else "No preliminary findings available."

    llm = LLMFactory.create(provider="openrouter")
    prompt = (
        f"Analyze the competitive landscape for: '{state.request.topic}'.\n"
        f"Context:\n{context}\n\n"
        "Provide 2-4 competitive intelligence observations about key players, market positioning, or strategic moves. "
        "Format each as: FINDING: <intelligence insight> | SOURCE: <reference> | CONFIDENCE: <0.0-1.0>"
    )
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    findings = _parse_findings(content, AgentRole.COMPETITIVE_INTELLIGENCE.value)

    state.agent_outputs[AgentRole.COMPETITIVE_INTELLIGENCE.value] = findings
    state.agent_states[AgentRole.COMPETITIVE_INTELLIGENCE.value].execution_state = (
        ExecutionState.COMPLETED
    )

    elapsed = time.monotonic() - start
    get_buffer().record(
        TelemetryEventType.AGENT_LATENCY,
        AgentRole.COMPETITIVE_INTELLIGENCE.value,
        elapsed,
    )
    logger.info(
        "CompetitiveIntelligenceAgent completed: {} findings in {:.2f}s",
        len(findings),
        elapsed,
    )
    return state
