from __future__ import annotations

from module_1_foundations.scenarios.base import InteractionType, Scenario


def _agent_label(agent_id: str, name: str, agent_type: str) -> str:
    escaped_name = name.replace('"', "'")
    return f'{agent_id}["{escaped_name}<br><i>{agent_type}</i>"]'


def generate_interaction_map(scenario: Scenario) -> str:
    agent_types = {}
    if scenario.interactions:
        for agent in scenario.agents:
            try:
                from module_1_foundations.classification.graph import classify_agent

                attrs = [a.model_dump() for a in agent.attributes]
                result = classify_agent(agent.description, attrs)
                agent_types[agent.id] = result.get("agent_type", "reactive")
            except Exception:
                agent_types[agent.id] = "reactive"
    else:
        for agent in scenario.agents:
            agent_types[agent.id] = "reactive"

    lines = ["flowchart LR"]
    for agent in scenario.agents:
        at = agent_types.get(agent.id, "reactive")
        lines.append(f"    {_agent_label(agent.id, agent.name, at)}")

    for ix in scenario.interactions:
        arrow = "-.->" if ix.type == InteractionType.feedback_loop else "-->"
        lines.append(f'    {ix.source} {arrow}|{ix.label}| {ix.target}')

    return "\n".join(lines)


def generate_capability_cycle(scenario: Scenario, agent_id: str) -> str:
    agent = None
    for a in scenario.agents:
        if a.id == agent_id:
            agent = a
            break
    if agent is None:
        raise ValueError(f"Agent '{agent_id}' not found in scenario '{scenario.id}'")
    if not scenario.description:
        raise ValueError(f"Scenario '{scenario.id}' has no description context")

    return f"""flowchart LR
    subgraph Perception
        P1["Receive environmental input"] --> P2["Detect relevant changes"]
    end
    subgraph Reasoning
        R1["Evaluate alternatives"] --> R2["Select best action"]
    end
    subgraph Action
        A1["Execute via tools"] --> A2["Monitor outcome"]
    end
    P2 --> R1
    R2 --> A1"""
