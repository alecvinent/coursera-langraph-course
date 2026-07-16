from __future__ import annotations

import time
from datetime import datetime, timezone

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.coordination.conflict import (
    detect_conflicts,
)
from langgraph_course.module_3.labs.multi_agent_research.coordination.provenance import (
    build_provenance_trace,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    ConflictStatus,
    ExecutionState,
    Finding,
    ResearchRequestStatus,
    ResearchState,
    SynthesisReport,
    TelemetryEventType,
)
from langgraph_course.module_3.labs.multi_agent_research.telemetry.events import (
    get_buffer,
)
from utils import LLMFactory


def synthesis_node(state: ResearchState) -> ResearchState:
    start = time.monotonic()
    logger.info("SynthesisAgent activated")

    _handle_empty_findings(state)
    conflicts = detect_conflicts(state)
    state.conflicts.extend(conflicts)

    provenance_trace = build_provenance_trace(state.agent_outputs)

    all_findings = []
    for role, findings in state.agent_outputs.items():
        for f in findings:
            all_findings.append(f)

    context_parts = []
    for role, findings in state.agent_outputs.items():
        if not findings:
            context_parts.append(f"[{role}]: No findings available — gap documented")
            continue
        context_parts.append(f"[{role}]:")
        for f in findings:
            context_parts.append(f"  - {f.content} (confidence: {f.confidence:.2f})")

    if conflicts:
        context_parts.append("\n[CONFLICTS DETECTED]:")
        for c in conflicts:
            status = c.resolution_status.value
            context_parts.append(f"  - {c.description} [{status}]")

    context = "\n".join(context_parts)

    llm = LLMFactory.create(provider="openrouter")
    prompt = (
        f"Synthesize a comprehensive market analysis report for: '{state.request.topic}'.\n\n"
        f"Agent findings:\n{context}\n\n"
        "Produce a structured report with sections: Executive Summary, Key Findings, "
        "Data Analysis, Trends & Projections, Competitive Landscape, and Conclusions. "
        "Cross-reference findings from different agents where they connect. "
        "Mark any conflicting information clearly."
    )
    response = llm.invoke(prompt)
    content = response.content if hasattr(response, "content") else str(response)

    report = SynthesisReport(
        sections=[{"title": "Synthesized Report", "content": content}],
        cross_references=_extract_cross_references(all_findings),
        conflict_disclosures=[c for c in state.conflicts if c.resolution_status == ConflictStatus.ESCALATED],
        provenance_trace=provenance_trace,
        generated_at=datetime.now(timezone.utc),
    )
    state.report = report
    state.request.status = ResearchRequestStatus.COMPLETED
    state.agent_states[AgentRole.SYNTHESIS.value].execution_state = (
        ExecutionState.COMPLETED
    )

    _log_steering_impact(state)

    elapsed = time.monotonic() - start
    get_buffer().record(
        TelemetryEventType.AGENT_LATENCY,
        AgentRole.SYNTHESIS.value,
        elapsed,
    )
    logger.info("SynthesisAgent completed in {:.2f}s", elapsed)
    return state


def _handle_empty_findings(state: ResearchState) -> None:
    for role_key in (
        AgentRole.WEB_RESEARCH.value,
        AgentRole.DATA_ANALYSIS.value,
        AgentRole.TREND_ANALYSIS.value,
        AgentRole.COMPETITIVE_INTELLIGENCE.value,
    ):
        if role_key not in state.agent_outputs or not state.agent_outputs[role_key]:
            state.agent_outputs[role_key] = []
            logger.warning(
                "Insufficient data from {} — documenting gap", role_key
            )


def _extract_cross_references(
    findings: list[Finding],
) -> list[dict]:
    cross_refs: list[dict] = []
    for f in findings:
        if f.cross_references:
            cross_refs.append(
                {
                    "finding_id": f.id,
                    "agent_role": f.agent_role,
                    "cross_references": f.cross_references,
                }
            )
    return cross_refs


def _log_steering_impact(state: ResearchState) -> None:
    if state.steering_instructions:
        logger.info(
            "Report includes {} steering intervention(s)",
            len(state.steering_instructions),
        )
