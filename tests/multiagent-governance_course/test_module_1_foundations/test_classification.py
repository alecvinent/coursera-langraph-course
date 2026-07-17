from unittest import TestCase

from module_1_foundations.classification.graph import classify_agent
from module_1_foundations.classification.rules import (
    classification_rules,
    needs_llm,
)


class TestClassificationRules(TestCase):
    def test_stateless_sensor_is_reactive(self):
        state = {"description": "A sensor that reads temperature and emits it. No internal state, no memory."}
        result = classification_rules(state)
        self.assertEqual(result["agent_type"], "reactive")

    def test_world_model_is_deliberative(self):
        state = {"description": "Models the road network and plans optimal routes using historical data."}
        result = classification_rules(state)
        self.assertEqual(result["agent_type"], "deliberative")

    def test_mixed_traits_is_hybrid(self):
        state = {"description": "Uses immediate sensor data to avoid obstacles while also maintaining a long-term world model for route planning."}
        result = classification_rules(state)
        self.assertEqual(result["agent_type"], "hybrid")

    def test_negation_detection_prevents_false_positive(self):
        state = {"description": "An agent without internal state or memory."}
        result = classification_rules(state)
        self.assertNotEqual(result["agent_type"], "deliberative")

    def test_no_description_returns_empty_type(self):
        state = {"description": ""}
        result = classification_rules(state)
        self.assertEqual(result["agent_type"], "")
        self.assertIn("errors", result)

    def test_ambiguous_routes_to_llm(self):
        state = {"description": "", "agent_type": "", "justification": ""}
        result = classification_rules(state)
        self.assertEqual(needs_llm(result), "llm_fallback")

    def test_clear_case_routes_to_finalize(self):
        state = {"description": "A stateless reactive sensor.", "agent_type": "reactive", "justification": "test"}
        self.assertEqual(needs_llm(state), "finalize")

    def test_explicit_hybrid_keyword(self):
        state = {"description": "A hybrid agent that combines reactive reflexes with deliberative planning."}
        result = classification_rules(state)
        self.assertEqual(result["agent_type"], "hybrid")


class TestClassificationGraph(TestCase):
    def test_stateless_is_reactive_via_graph(self):
        result = classify_agent("A sensor that reads temperature and emits data. No internal state or memory.")
        self.assertEqual(result["agent_type"], "reactive")
        self.assertIn("latencies", result)
        self.assertIn("paths_taken", result)

    def test_deliberative_via_graph(self):
        result = classify_agent("Models road network and plans optimal routes with historical traffic data.")
        self.assertEqual(result["agent_type"], "deliberative")

    def test_hybrid_via_graph(self):
        result = classify_agent("Combines immediate sensor reflexes with long-term world model planning.")
        self.assertEqual(result["agent_type"], "hybrid")
