import tempfile
from pathlib import Path
from unittest import TestCase

from module_1_foundations.export.submission import compile_submission, generate_pdf
from module_1_foundations.interaction_map.mapper import (
    generate_capability_cycle,
    generate_interaction_map,
)
from module_1_foundations.scenarios.traffic import traffic_scenario


class TestCompileSubmission(TestCase):
    def setUp(self):
        self.classifications = [
            {"agent_id": "sensor", "agent_type": "reactive", "justification": "Stateless sensor."},
            {"agent_id": "controller", "agent_type": "deliberative", "justification": "World model."},
            {"agent_id": "planner", "agent_type": "deliberative", "justification": "Route planning."},
        ]
        self.interaction_map = generate_interaction_map(traffic_scenario)
        self.capability_cycle = generate_capability_cycle(traffic_scenario, "sensor")
        self.tradeoff = "## Trade-off Analysis\n\nSpeed: reactive wins."

    def test_has_all_five_sections(self):
        md = compile_submission(
            traffic_scenario, self.classifications,
            self.interaction_map, self.tradeoff, self.capability_cycle,
        )
        self.assertIn("Section 1: Agent Classification", md)
        self.assertIn("Section 2: Agent Interaction Diagram", md)
        self.assertIn("Section 3: Trade-off Analysis", md)
        self.assertIn("Section 4: Capability Cycle", md)
        self.assertIn("Section 5: Reflection", md)

    def test_classification_table_has_agents(self):
        md = compile_submission(
            traffic_scenario, self.classifications,
            self.interaction_map, self.tradeoff, self.capability_cycle,
        )
        self.assertIn("Traffic Sensor", md)
        self.assertIn("Traffic Light Controller", md)
        self.assertIn("Route Planner", md)

    def test_contains_mermaid_block(self):
        md = compile_submission(
            traffic_scenario, self.classifications,
            self.interaction_map, self.tradeoff, self.capability_cycle,
        )
        self.assertIn("```mermaid", md)

    def test_scenario_name_in_output(self):
        md = compile_submission(
            traffic_scenario, self.classifications,
            self.interaction_map, self.tradeoff, self.capability_cycle,
        )
        self.assertIn(traffic_scenario.name, md)


class TestGeneratePDF(TestCase):
    def test_pdf_file_is_created(self):
        md = "# Test\n\nHello world."
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        pdf_path = generate_pdf(md, tmp.name)
        self.assertTrue(Path(pdf_path).exists())
        self.assertGreater(Path(pdf_path).stat().st_size, 0)
        Path(pdf_path).unlink()

    def test_unicode_smart_quotes_handled(self):
        md = "# Test\n\n\u201cHello\u201d and \u2018world\u2019 \u2014 test."
        tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        tmp.close()
        pdf_path = generate_pdf(md, tmp.name)
        self.assertTrue(Path(pdf_path).exists())
        Path(pdf_path).unlink()
