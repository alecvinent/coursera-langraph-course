import unittest

from langgraph_course.module_3.labs.multi_agent_research.coordination.provenance import (
    attribution_ratio,
    build_provenance_trace,
    is_attributable,
)
from langgraph_course.module_3.labs.multi_agent_research.state import Finding


class TestProvenance(unittest.TestCase):
    def test_is_attributable_with_source(self):
        f = Finding(
            agent_role="web_research",
            content="test",
            source="https://example.com",
            confidence=0.9,
        )
        self.assertTrue(is_attributable(f))

    def test_is_attributable_without_source(self):
        f = Finding(
            agent_role="web_research",
            content="test",
            source="",
            confidence=0.9,
        )
        self.assertFalse(is_attributable(f))

    def test_build_provenance_trace(self):
        findings = [
            Finding(
                agent_role="web_research",
                content="Finding A",
                source="source-a",
                confidence=0.9,
            )
        ]
        trace = build_provenance_trace({"web_research": findings})
        self.assertIn("web_research", trace)
        self.assertEqual(len(trace["web_research"]), 1)
        self.assertEqual(
            trace["web_research"][0]["finding_id"], findings[0].id
        )

    def test_attribution_ratio_perfect(self):
        findings = [
            Finding(
                agent_role="web_research",
                content="A",
                source="s1",
                confidence=0.8,
            ),
            Finding(
                agent_role="data_analysis",
                content="B",
                source="s2",
                confidence=0.9,
            ),
        ]
        ratio = attribution_ratio({"test": findings})
        self.assertEqual(ratio, 1.0)

    def test_attribution_ratio_partial(self):
        findings = [
            Finding(
                agent_role="web_research",
                content="A",
                source="s1",
                confidence=0.8,
            ),
            Finding(
                agent_role="data_analysis",
                content="B",
                source="",
                confidence=0.9,
            ),
        ]
        ratio = attribution_ratio({"test": findings})
        self.assertEqual(ratio, 0.5)
