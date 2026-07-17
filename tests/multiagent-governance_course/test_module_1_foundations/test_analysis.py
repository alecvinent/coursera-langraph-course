from unittest import TestCase

from module_1_foundations.analysis.tradeoffs import generate_tradeoff_analysis
from module_1_foundations.scenarios.base import (
    AgentAttribute,
    AgentDef,
    InteractionDef,
    InteractionType,
    Scenario,
)

traffic_scenario = Scenario(
    id="traffic_control",
    name="Traffic Control",
    description="A traffic management system.",
    agents=[
        AgentDef(id="s", name="Sensor", description="Stateless sensor.", attributes=[AgentAttribute(name="internal_state", value="none")]),
        AgentDef(id="c", name="Controller", description="Models traffic patterns.", attributes=[AgentAttribute(name="internal_state", value="full")]),
    ],
    interactions=[
        InteractionDef(source="s", target="c", label="data", type=InteractionType.data_flow),
    ],
)

single_scenario = Scenario(
    id="single",
    name="Single Agent",
    description="A lone agent.",
    agents=[
        AgentDef(id="a", name="Agent", description="Stateless sensor.", attributes=[AgentAttribute(name="internal_state", value="none")]),
    ],
    interactions=[],
)

empty_scenario = Scenario(
    id="empty",
    name="Empty",
    description="No agents.",
    agents=[],
    interactions=[],
)


class TestTradeoffAnalysis(TestCase):
    def test_all_five_dimensions_present(self):
        a = generate_tradeoff_analysis(traffic_scenario)
        for dim in ["speed", "accuracy", "scalability", "resilience", "adaptability"]:
            self.assertIn(dim.capitalize(), a)

    def test_side_by_side_table_present(self):
        a = generate_tradeoff_analysis(traffic_scenario)
        self.assertIn("Side-by-Side Comparison", a)
        self.assertIn("Pure Reactive", a)
        self.assertIn("Pure Deliberative", a)
        self.assertIn("Hybrid", a)

    def test_single_agent_still_produces_analysis(self):
        a = generate_tradeoff_analysis(single_scenario)
        self.assertIn("speed", a.lower())
        self.assertIn("adaptability", a.lower())

    def test_empty_scenario_returns_warning(self):
        a = generate_tradeoff_analysis(empty_scenario)
        self.assertIn("Warning", a)

    def test_scores_in_table_format(self):
        a = generate_tradeoff_analysis(traffic_scenario)
        self.assertIn("| Dimension |", a)
        self.assertIn("| Speed |", a)
        self.assertIn("5/5", a)
