from __future__ import annotations

import time
from typing import Literal

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    ResearchRequestStatus,
    ResearchState,
)


def _is_request_too_broad(state: ResearchState) -> bool:
    broad_indicators = [
        "everything",
        "all about",
        "general",
        "overview of everything",
        "technology",
        "everything about",
    ]
    topic_lower = state.request.topic.lower()
    return any(indicator in topic_lower for indicator in broad_indicators)


def _has_steering_pending(state: ResearchState) -> bool:
    return any(not s.applied for s in state.steering_instructions)


def activate_agents_router(state: ResearchState) -> Literal["needs_refinement", "run_research"]:
    if _is_request_too_broad(state):
        state.request.status = ResearchRequestStatus.NEEDS_REFINEMENT
        logger.warning(
            "Research request too broad: '{}' — requesting refinement",
            state.request.topic,
        )
        return "needs_refinement"
    return "run_research"


def determine_agent_parallelism(state: ResearchState) -> dict[str, list[str]]:
    parallel_groups: dict[str, list[str]] = {}
    sequential: list[str] = []

    has_web = len(state.agent_outputs.get(AgentRole.WEB_RESEARCH.value, [])) > 0
    has_data = len(state.agent_outputs.get(AgentRole.DATA_ANALYSIS.value, [])) > 0

    if not has_web:
        parallel_groups["round_1"] = [AgentRole.WEB_RESEARCH.value]
        sequential.append(AgentRole.DATA_ANALYSIS.value)
        sequential.append(AgentRole.TREND_ANALYSIS.value)
        sequential.append(AgentRole.COMPETITIVE_INTELLIGENCE.value)
    elif not has_data:
        parallel_groups["web_enriched"] = [AgentRole.WEB_RESEARCH.value]
        sequential.append(AgentRole.DATA_ANALYSIS.value)
        sequential.append(AgentRole.TREND_ANALYSIS.value)
        sequential.append(AgentRole.COMPETITIVE_INTELLIGENCE.value)
    else:
        parallel_groups["all"] = [
            AgentRole.WEB_RESEARCH.value,
            AgentRole.DATA_ANALYSIS.value,
            AgentRole.TREND_ANALYSIS.value,
            AgentRole.COMPETITIVE_INTELLIGENCE.value,
        ]

    return parallel_groups


def should_synthesize(state: ResearchState) -> Literal["synthesize", "continue", "max_budget"]:
    _apply_pending_steering(state)

    required_roles = [
        AgentRole.WEB_RESEARCH.value,
        AgentRole.DATA_ANALYSIS.value,
        AgentRole.TREND_ANALYSIS.value,
        AgentRole.COMPETITIVE_INTELLIGENCE.value,
    ]
    all_complete = all(
        state.agent_states.get(r) and state.agent_states[r].execution_state.value == "completed"
        for r in required_roles
    )
    if all_complete:
        return "synthesize"

    total_findings = sum(len(v) for v in state.agent_outputs.values())
    if total_findings >= 10:
        confidences = [
            f.confidence
            for fs in state.agent_outputs.values()
            for f in fs
        ]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        if avg_confidence >= 0.8:
            return "synthesize"

    budget = state.execution_metadata.get("max_execution_minutes", 30) * 60
    elapsed = time.monotonic() - state.execution_metadata.get("workflow_start", time.monotonic())
    if elapsed >= budget:
        state.execution_metadata["stop_trigger"] = "max_budget_exhausted"
        logger.warning("Max execution budget reached ({:.1f}s)", elapsed)
        return "max_budget"

    return "continue"


def _apply_pending_steering(state: ResearchState) -> None:
    pending = [s for s in state.steering_instructions if not s.applied]
    for instruction in pending:
        for agent_role in instruction.target_agents:
            if agent_role in state.agent_states:
                state.agent_states[agent_role].execution_state = "idle"
        instruction.applied = True
        logger.info(
            "Applied steering: '{}' for agents {}",
            instruction.instruction_text,
            instruction.target_agents,
        )


def check_execution_budget(state: ResearchState) -> bool:
    max_minutes = state.execution_metadata.get("max_execution_minutes", 30)
    start = state.execution_metadata.get("workflow_start", time.monotonic())
    elapsed_minutes = (time.monotonic() - start) / 60
    if elapsed_minutes >= max_minutes:
        state.execution_metadata["stop_trigger"] = "budget_exhausted"
        logger.warning(
            "Execution budget exhausted: {:.1f}min >= {}min",
            elapsed_minutes,
            max_minutes,
        )
        return True
    return False
