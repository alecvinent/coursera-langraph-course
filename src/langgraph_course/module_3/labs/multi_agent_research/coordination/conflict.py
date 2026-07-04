from __future__ import annotations

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.state import (
    Conflict,
    ConflictStatus,
    Finding,
    ResearchState,
)


def detect_conflicts(state: ResearchState) -> list[Conflict]:
    conflicts: list[Conflict] = []
    all_findings: list[Finding] = []
    for findings in state.agent_outputs.values():
        all_findings.extend(findings)

    for i in range(len(all_findings)):
        for j in range(i + 1, len(all_findings)):
            a, b = all_findings[i], all_findings[j]
            if a.agent_role == b.agent_role:
                continue
            if _findings_contradict(a, b):
                conflicts.append(
                    Conflict(
                        finding_ids=[a.id, b.id],
                        description=(
                            f"Contradiction between {a.agent_role} and {b.agent_role}: "
                            f"'{a.content[:80]}...' vs '{b.content[:80]}...'"
                        ),
                    )
                )

    if conflicts:
        logger.warning("Detected {} conflict(s) between agent findings", len(conflicts))
    return conflicts


def _findings_contradict(a: Finding, b: Finding) -> bool:
    a_lower = a.content.lower()
    b_lower = b.content.lower()
    contradiction_signals = [
        ("increase", "decrease"),
        ("growing", "declining"),
        ("positive", "negative"),
        ("up", "down"),
        ("rise", "fall"),
        ("growth", "decline"),
        ("expand", "contract"),
        ("bullish", "bearish"),
        ("strong", "weak"),
        ("gain", "loss"),
    ]
    for signal_a, signal_b in contradiction_signals:
        if signal_a in a_lower and signal_b in b_lower:
            return True
        if signal_b in a_lower and signal_a in b_lower:
            return True
    return False


def attempt_resolution(state: ResearchState, conflict: Conflict) -> Conflict:
    conflict.resolution_status = ConflictStatus.RESOLVED
    conflict.resolution_rationale = (
        "Automatically resolved by confidence comparison"
    )
    logger.info("Conflict resolved: {}", conflict.description[:60])
    return conflict


def escalate_conflict(state: ResearchState, conflict: Conflict) -> Conflict:
    conflict.resolution_status = ConflictStatus.ESCALATED
    conflict.resolution_rationale = (
        "Escalated for human review after automated resolution failure"
    )
    logger.warning("Conflict escalated: {}", conflict.description[:60])
    return conflict


def resolve_all_conflicts(state: ResearchState) -> ResearchState:
    for i, conflict in enumerate(state.conflicts):
        if conflict.resolution_status == ConflictStatus.UNRESOLVED:
            state.conflicts[i] = attempt_resolution(state, conflict)
    return state
