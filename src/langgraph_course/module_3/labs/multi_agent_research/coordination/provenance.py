from __future__ import annotations

from typing import Any

from langgraph_course.module_3.labs.multi_agent_research.state import Finding


def build_provenance_trace(
    agent_outputs: dict[str, list[Finding]]
) -> dict[str, Any]:
    trace: dict[str, Any] = {}
    for agent_role, findings in agent_outputs.items():
        trace[agent_role] = []
        for finding in findings:
            entry = {
                "finding_id": finding.id,
                "content": finding.content,
                "source": finding.source,
                "confidence": finding.confidence,
                "timestamp": finding.timestamp.isoformat(),
                "provenance_chain": finding.provenance_chain,
                "cross_references": finding.cross_references,
            }
            trace[agent_role].append(entry)
    return trace


def is_attributable(finding: Finding) -> bool:
    return bool(finding.source) and bool(finding.agent_role)


def attribution_ratio(agent_outputs: dict[str, list[Finding]]) -> float:
    total = 0
    attributed = 0
    for findings in agent_outputs.values():
        for f in findings:
            total += 1
            if is_attributable(f):
                attributed += 1
    return attributed / total if total > 0 else 1.0
