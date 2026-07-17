from unittest import TestCase

from module_1_foundations.scenarios.base import Scenario
from module_1_foundations.scenarios.task_manager import task_manager_scenario
from module_1_foundations.scenarios.traffic import traffic_scenario


class TestScenarios(TestCase):
    def test_traffic_has_three_agents(self):
        self.assertEqual(len(traffic_scenario.agents), 3)

    def test_task_manager_has_one_agent(self):
        self.assertEqual(len(task_manager_scenario.agents), 1)

    def test_all_agent_ids_unique(self):
        ids = [a.id for a in traffic_scenario.agents]
        self.assertEqual(len(ids), len(set(ids)))

    def test_interactions_reference_valid_agent_ids(self):
        agent_ids = {a.id for a in traffic_scenario.agents}
        for ix in traffic_scenario.interactions:
            self.assertIn(ix.source, agent_ids)
            self.assertIn(ix.target, agent_ids)

    def test_both_are_scenario_instances(self):
        self.assertIsInstance(traffic_scenario, Scenario)
        self.assertIsInstance(task_manager_scenario, Scenario)
