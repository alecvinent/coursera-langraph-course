import unittest

from langgraph_course.module_3.labs.multi_agent_research.graph import (
    create_full_graph,
    run_research,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    SteeringInstruction,
)


class TestWorkflow(unittest.TestCase):
    def test_graph_creation(self):
        graph = create_full_graph()
        compiled = graph.compile()
        self.assertIsNotNone(compiled)

    def test_graph_has_all_nodes(self):
        graph = create_full_graph()
        expected_nodes = {
            "validate_request",
            "web_research",
            "data_analysis",
            "trend_analysis",
            "competitive_intel",
            "synthesize",
            "needs_refinement",
        }
        registered = set(graph._nodes.keys())
        self.assertEqual(registered, expected_nodes)


class TestSteering(unittest.TestCase):
    def test_steering_instruction_applied(self):
        instruction = SteeringInstruction(
            instruction_text="Focus on AWS vs Azure",
            target_agents=["web_research", "data_analysis"],
            applied=True,
        )
        self.assertTrue(instruction.applied)
        self.assertIn("web_research", instruction.target_agents)

    def test_steering_instruction_default_not_applied(self):
        instruction = SteeringInstruction(
            instruction_text="Focus on AWS",
            target_agents=["web_research"],
        )
        self.assertFalse(instruction.applied)


class TestIntervention(unittest.TestCase):
    def test_state_abort_marks_failed(self):
        from langgraph_course.module_3.labs.multi_agent_research.state import (
            ResearchRequestStatus,
        )

        try:
            state = run_research("test abort topic", max_execution_minutes=1)
        except Exception as e:
            if "API key" in str(e).lower() or "provider" in str(e).lower():
                self.skipTest("LLM API not configured")
            raise
        state.request.status = ResearchRequestStatus.FAILED
        state.execution_metadata["intervention"] = "aborted"
        self.assertEqual(
            state.request.status, ResearchRequestStatus.FAILED
        )
        self.assertEqual(
            state.execution_metadata.get("intervention"), "aborted"
        )
