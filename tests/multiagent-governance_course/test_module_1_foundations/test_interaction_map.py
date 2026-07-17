from unittest import TestCase

from module_1_foundations.interaction_map.mapper import (
    generate_capability_cycle,
    generate_interaction_map,
)
from module_1_foundations.scenarios.base import (
    AgentAttribute,
    AgentDef,
    InteractionDef,
    InteractionType,
    Scenario,
)

simple_scenario = Scenario(
    id="test_simple",
    name="Test",
    description="Test scenario.",
    agents=[
        AgentDef(id="a", name="Agent A", description="Stateless sensor.", attributes=[AgentAttribute(name="internal_state", value="none")]),
        AgentDef(id="b", name="Agent B", description="Stateless actuator.", attributes=[AgentAttribute(name="internal_state", value="none")]),
    ],
    interactions=[
        InteractionDef(source="a", target="b", label="triggers", type=InteractionType.data_flow),
    ],
)

bidirectional_scenario = Scenario(
    id="test_bi",
    name="Bidirectional Test",
    description="Test with feedback loop.",
    agents=[
        AgentDef(id="x", name="Agent X", description="Stateless sensor.", attributes=[AgentAttribute(name="internal_state", value="none")]),
        AgentDef(id="y", name="Agent Y", description="Stateless actuator.", attributes=[AgentAttribute(name="internal_state", value="none")]),
    ],
    interactions=[
        InteractionDef(source="x", target="y", label="sends data", type=InteractionType.data_flow),
        InteractionDef(source="y", target="x", label="feedback", type=InteractionType.feedback_loop),
    ],
)

no_interaction_scenario = Scenario(
    id="test_none",
    name="No Interactions",
    description="Isolated agents.",
    agents=[
        AgentDef(id="p", name="Agent P", description="Stateless.", attributes=[AgentAttribute(name="internal_state", value="none")]),
        AgentDef(id="q", name="Agent Q", description="Stateless.", attributes=[AgentAttribute(name="internal_state", value="none")]),
    ],
    interactions=[],
)

task_manager_scenario = Scenario(
    id="personal_task_manager",
    name="Personal Task Manager",
    description="An AI personal assistant that helps manage schedules.",
    agents=[
        AgentDef(
            id="personal_assistant",
            name="Personal Assistant",
            description="""Monitors calendar and weather APIs, detects scheduling conflicts,
evaluates alternatives, and updates appointments. Combines reactive alert handling
with deliberative planning.""",
            attributes=[
                AgentAttribute(name="internal_state", value="partial", description="Temporary working memory"),
                AgentAttribute(name="planning_horizon", value="short_term"),
                AgentAttribute(name="memory", value="short_term"),
                AgentAttribute(name="decision_logic", value="utility"),
                AgentAttribute(name="adaptability", value="medium"),
                AgentAttribute(name="sensing", value="both"),
            ],
        ),
    ],
    interactions=[],
)


class TestInteractionMap(TestCase):
    def test_unidirectional_flow(self):
        d = generate_interaction_map(simple_scenario)
        self.assertIn("a[", d)
        self.assertIn("b[", d)
        self.assertIn("-->", d)
        self.assertIn("triggers", d)

    def test_bidirectional_feedback_loop(self):
        d = generate_interaction_map(bidirectional_scenario)
        self.assertIn("-.->", d)
        self.assertIn("sends data", d)
        self.assertIn("feedback", d)

    def test_no_interactions_shows_isolated_nodes(self):
        d = generate_interaction_map(no_interaction_scenario)
        self.assertIn("p[", d)
        self.assertIn("q[", d)
        self.assertNotIn("-->", d)
        self.assertNotIn("-.->", d)

    def test_flowchart_starts_with_keyword(self):
        d = generate_interaction_map(simple_scenario)
        self.assertTrue(d.startswith("flowchart LR"))


class TestCapabilityCycle(TestCase):
    def test_full_cycle_has_three_subgraphs(self):
        d = generate_capability_cycle(task_manager_scenario, "personal_assistant")
        self.assertIn("Perception", d)
        self.assertIn("Reasoning", d)
        self.assertIn("Action", d)

    def test_cycle_has_transitions(self):
        d = generate_capability_cycle(task_manager_scenario, "personal_assistant")
        self.assertIn("P2 --> R1", d)
        self.assertIn("R2 --> A1", d)

    def test_unknown_agent_raises_error(self):
        with self.assertRaises(ValueError):
            generate_capability_cycle(task_manager_scenario, "nonexistent_agent")
