from __future__ import annotations

import time

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    ExecutionState,
    Finding,
    ResearchState,
)
from langgraph_course.module_3.labs.multi_agent_research.telemetry.events import (
    TelemetryEventType,
    get_buffer,
)
from langgraph_course.utils.llm import LLMFactory


def web_research_node(state: ResearchState) -> ResearchState:
    start = time.monotonic()
    logger.info(
        "WebResearchAgent activated for topic: {}", state.request.topic
    )

    llm = LLMFactory.create(provider="openrouter")
    topic = state.request.topic
    domain_tags = state.request.domain_tags

    prompt = (
        f"Research the following topic: '{topic}'. "
        f"Domain tags: {', '.join(domain_tags) if domain_tags else 'general'}. "
        "Provide 3-5 key findings with sources. "
        "Format each finding as: FINDING: <content> | SOURCE: <url or reference> | CONFIDENCE: <0.0-1.0>"
    )
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    findings = _parse_findings(content, AgentRole.WEB_RESEARCH.value)

    state.agent_outputs[AgentRole.WEB_RESEARCH.value] = findings
    state.agent_states[AgentRole.WEB_RESEARCH.value].execution_state = (
        ExecutionState.COMPLETED
    )

    elapsed = time.monotonic() - start
    get_buffer().record(
        TelemetryEventType.AGENT_LATENCY,
        AgentRole.WEB_RESEARCH.value,
        elapsed,
    )
    logger.info(
        "WebResearchAgent completed: {} findings in {:.2f}s",
        len(findings),
        elapsed,
    )
    return state


def _parse_findings(
    content: str, agent_role: str
) -> list[Finding]:
    findings: list[Finding] = []
    for line in content.strip().split("\n"):
        line = line.strip()
        if not line or "FINDING:" not in line:
            continue
        try:
            finding_part = line.split("FINDING:")[1].split("| SOURCE:")[0].strip()
            source_part = line.split("| SOURCE:")[1].split("| CONFIDENCE:")[0].strip()
            confidence_part = (
                line.split("| CONFIDENCE:")[1].strip() if "| CONFIDENCE:" in line else "0.7"
            )
            confidence = max(0.0, min(1.0, float(confidence_part)))
            findings.append(
                Finding(
                    agent_role=agent_role,
                    content=finding_part,
                    source=source_part,
                    confidence=confidence,
                )
            )
        except (IndexError, ValueError):
            continue
    if not findings:
        findings.append(
            Finding(
                agent_role=agent_role,
                content=content[:500],
                source="llm-response",
                confidence=0.5,
            )
        )
    return findings
