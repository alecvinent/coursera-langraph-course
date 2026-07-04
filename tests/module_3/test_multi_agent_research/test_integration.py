import unittest

from langgraph_course.module_3.labs.multi_agent_research.graph import (
    create_full_graph,
    run_research,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
)


class TestIntegration(unittest.TestCase):
    def test_graph_structure(self):
        graph = create_full_graph()
        compiled = graph.compile()
        self.assertIsNotNone(compiled)
        self.assertIn("web_research", graph._nodes)
        self.assertIn("synthesize", graph._nodes)

    def test_run_research_creates_state(self):
        try:
            result = run_research(
                "EV battery market",
                domain_tags=["EV", "market"],
                max_execution_minutes=30,
            )
        except Exception as e:
            if "API key" in str(e).lower() or "provider" in str(e).lower():
                self.skipTest("LLM API not configured")
            raise
        self.assertIsNotNone(result)
        self.assertIn(AgentRole.WEB_RESEARCH.value, result.agent_outputs)
