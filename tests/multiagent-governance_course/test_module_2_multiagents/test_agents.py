from unittest import TestCase

from module_2_multiagents.runtime import run_pipeline
from module_2_multiagents.state import BlogState


class TestAgentFailurePaths(TestCase):
    def test_empty_upstream_produces_partial_and_errors(self):
        # Write node with an empty upstream (missing outline) must degrade.
        from module_2_multiagents.agents.writer import writer_node

        state = BlogState(topic="t", outline="   ")
        result = writer_node(state, llm=lambda p: "draft")
        self.assertEqual(result["processing_outcome"], "partial")
        self.assertTrue(result["error_records"])
        self.assertEqual(result["error_records"][0]["step"], "writer_node")

    def test_seo_requires_draft(self):
        from module_2_multiagents.agents.seo import seo_node

        state = BlogState(topic="t", outline="o", draft=None)
        result = seo_node(state, llm=lambda p: "feedback")
        self.assertEqual(result["processing_outcome"], "partial")
        self.assertTrue(result["error_records"])

    def test_researcher_requires_topic(self):
        from module_2_multiagents.agents.researcher import researcher_node

        state = BlogState(topic="t")
        result = researcher_node(state, llm=lambda p: "  ")
        self.assertEqual(result["processing_outcome"], "partial")
        self.assertTrue(result["error_records"])
        self.assertEqual(result["error_records"][0]["step"], "researcher_node")

    def test_pipeline_with_empty_researcher_output_degrades(self):
        def fake_llm(prompt: str) -> str:
            return "   "

        state = run_pipeline("The Future of AI", llm=fake_llm)
        self.assertEqual(state.processing_outcome, "partial")
        self.assertTrue(state.error_records)

    def test_pipeline_full_outcome_records_no_errors(self):
        def fake_llm(prompt: str) -> str:
            if "SEO Title Options" in prompt or "Relevant Keywords" in prompt:
                return "SEO Title Options:\n1) A\n2) B\n3) C\nRelevant Keywords: k1, k2, k3, k4, k5"
            if "5-point bulleted outline" in prompt:
                return "- A\n- B\n- C\n- D\n- E"
            return "Para 1.\n\nPara 2.\n\nPara 3."

        state = run_pipeline("The Future of AI", llm=fake_llm)
        self.assertEqual(state.processing_outcome, "full")
        self.assertEqual(state.error_records, [])
        self.assertTrue(state.outline)
        self.assertTrue(state.draft)
        self.assertTrue(state.seo_feedback)