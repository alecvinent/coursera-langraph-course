import os
import tempfile
from unittest import TestCase

import fitz

from module_1_foundations.export.diagram_renderer import (
    render_capability_cycle_diagram,
    render_interaction_diagram,
)
from module_1_foundations.scenarios.task_manager import task_manager_scenario
from module_1_foundations.scenarios.traffic import traffic_scenario


class TestRenderInteractionDiagram(TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _render_and_get_text(self, render_fn, *args):
        doc = fitz.Document()
        doc.new_page()
        render_fn(doc, 0, *args)
        pdf_path = os.path.join(self.tmpdir, "test.pdf")
        doc.save(pdf_path)
        doc.close()
        doc2 = fitz.Document(pdf_path)
        text = doc2[0].get_text()
        doc2.close()
        os.unlink(pdf_path)
        return text

    def test_interaction_diagram_contains_all_agents(self):
        text = self._render_and_get_text(render_interaction_diagram, traffic_scenario)
        self.assertIn("Traffic Sensor", text)
        self.assertIn("Traffic Light Controller", text)
        self.assertIn("Route Planner", text)

    def test_capability_cycle_has_three_subgraphs(self):
        text = self._render_and_get_text(
            render_capability_cycle_diagram, task_manager_scenario, "personal_assistant"
        )
        self.assertIn("Perception", text)
        self.assertIn("Reasoning", text)
        self.assertIn("Action", text)

    def test_interaction_diagram_has_edge_labels(self):
        text = self._render_and_get_text(render_interaction_diagram, traffic_scenario)
        self.assertIn("sends sensor readings", text)
        self.assertIn("transmits traffic data", text)

    def test_unknown_agent_id_raises_value_error(self):
        doc = fitz.Document()
        doc.new_page()
        with self.assertRaises(ValueError):
            render_capability_cycle_diagram(doc, 0, traffic_scenario, "nonexistent_agent")
        doc.close()
