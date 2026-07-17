from __future__ import annotations

from module_1_foundations.scenarios.base import Scenario

DIMENSIONS = ["speed", "accuracy", "scalability", "resilience", "adaptability"]

DIMENSION_DESCRIPTIONS = {
    "speed": "Response time and throughput",
    "accuracy": "Decision quality and precision",
    "scalability": "Ability to handle increased load",
    "resilience": "Fault tolerance and recovery",
    "adaptability": "Ability to adjust to new conditions",
}

DEFAULT_SCORES: dict[str, dict[str, int]] = {
    "speed": {"reactive": 5, "deliberative": 2, "hybrid": 3},
    "accuracy": {"reactive": 2, "deliberative": 5, "hybrid": 4},
    "scalability": {"reactive": 5, "deliberative": 2, "hybrid": 3},
    "resilience": {"reactive": 5, "deliberative": 2, "hybrid": 3},
    "adaptability": {"reactive": 1, "deliberative": 4, "hybrid": 5},
}

DIMENSION_RATIONALES: dict[str, str] = {
    "speed": "Reactive agents excel at speed due to direct stimulus-response with no planning overhead. Deliberative agents are slowest because they build and query world models. Hybrid agents balance immediate reactions with occasional planning.",
    "accuracy": "Deliberative agents achieve highest accuracy through world modeling and long-term planning. Reactive agents lack state, leading to lower precision. Hybrid agents leverage both immediate data and models for good accuracy.",
    "scalability": "Reactive agents are stateless and easy to replicate horizontally. Deliberative agents require synchronized state, limiting scalability. Hybrid agents carry some state overhead but can scale reasonably.",
    "resilience": "Reactive agents have no single point of failure and degrade gracefully. Deliberative agents with centralized planners are vulnerable. Hybrid agents can fall back to reactive mode if planning fails.",
    "adaptability": "Reactive agents follow fixed rules and cannot adapt. Deliberative agents can replan when conditions change. Hybrid agents combine rule reflexes with planning, making them the most adaptable.",
}


def _score_table(scenario: Scenario) -> str:
    lines = [
        "| Dimension | Reactive | Deliberative | Hybrid |",
        "|-----------|----------|-------------|--------|",
    ]
    for dim in DIMENSIONS:
        scores = DEFAULT_SCORES[dim]
        lines.append(
            f"| {dim.capitalize()} | {scores['reactive']}/5 | "
            f"{scores['deliberative']}/5 | {scores['hybrid']}/5 |"
        )
    return "\n".join(lines)


def _dimension_analyses() -> str:
    parts: list[str] = []
    for dim in DIMENSIONS:
        parts.append(f"### {dim.capitalize()}")
        parts.append(f"_{DIMENSION_DESCRIPTIONS[dim]}_")
        parts.append("")
        parts.append(DIMENSION_RATIONALES[dim])
        parts.append("")
        parts.append(_score_row(dim))
        parts.append("")
    return "\n".join(parts)


def _score_row(dim: str) -> str:
    scores = DEFAULT_SCORES[dim]
    return (
        f"- **Reactive**: {scores['reactive']}/5 — "
        f"{'Fast' if scores['reactive'] >= 4 else 'Moderate' if scores['reactive'] >= 3 else 'Slow'} "
        f"({_score_tag(scores['reactive'], dim, 'reactive')})"
    )


def _score_tag(score: int, dim: str, agent_type: str) -> str:
    if score >= 4:
        return "strong suit"
    if score >= 3:
        return "adequate"
    return "weakness"


def _side_by_side_comparison() -> str:
    return """## Side-by-Side Comparison

| Criteria | Pure Reactive | Pure Deliberative | Hybrid |
|----------|--------------|-------------------|--------|
| Best for | Real-time systems, simple automation | Complex planning, high-stakes decisions | Balanced systems needing both speed and accuracy |
| Weakness | No learning, poor accuracy | Slow, fragile central planner | Added complexity, coordination overhead |
| Example | Traffic sensor | Route planner | Personal assistant |
| Architecture | Stateless, if-then | Stateful, world model | Layered (reactive + deliberative) |

**Recommendation**: Hybrid architectures offer the best balance for most systems. Use pure reactive for time-critical subsystems and pure deliberative when decision quality is paramount and latency is acceptable."""


def generate_tradeoff_analysis(scenario: Scenario) -> str:
    agent_count = len(scenario.agents)
    lines: list[str] = []

    lines.append(f"# Trade-off Analysis: {scenario.name}")
    lines.append("")
    lines.append(f"**Scenario**: {scenario.description}")
    lines.append(f"**Agents analyzed**: {agent_count}")
    lines.append("")

    if agent_count == 0:
        lines.append("*Warning: No agents in scenario — analysis is empty.*")
        return "\n".join(lines)

    same_type = len({a.description for a in scenario.agents}) == 1

    if same_type:
        lines.append("*Note: All agents share the same type description — comparison shows hypothetical pure-type baselines.*")
        lines.append("")

    lines.append("## Dimensional Analysis")
    lines.append("")
    lines.append(_dimension_analyses())

    lines.append("")
    lines.append("## Score Summary")
    lines.append("")
    lines.append(_score_table(scenario))

    lines.append("")
    lines.append(_side_by_side_comparison())

    return "\n".join(lines)
