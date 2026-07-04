import unittest

from langgraph_course.module_3.labs.multi_agent_research.state import (
    AgentRole,
    Conflict,
    ConflictStatus,
    Finding,
    ResearchRequest,
    ResearchRequestStatus,
    ResearchState,
)


class TestResearchState(unittest.TestCase):
    def test_research_request_default_status(self):
        req = ResearchRequest(topic="Test topic")
        self.assertEqual(req.status, ResearchRequestStatus.PENDING)

    def test_research_request_validation(self):
        with self.assertRaises(ValueError):
            ResearchRequest(topic="")

    def test_finding_auto_id_and_timestamp(self):
        finding = Finding(
            agent_role="web_research",
            content="Test finding",
            source="test-source",
            confidence=0.8,
        )
        self.assertIsNotNone(finding.id)
        self.assertIsNotNone(finding.timestamp)
        self.assertEqual(finding.agent_role, "web_research")

    def test_finding_confidence_bounds(self):
        with self.assertRaises(ValueError):
            Finding(
                agent_role="test",
                content="test",
                source="test",
                confidence=1.5,
            )
        with self.assertRaises(ValueError):
            Finding(
                agent_role="test",
                content="test",
                source="test",
                confidence=-0.1,
            )

    def test_conflict_min_finding_ids(self):
        with self.assertRaises(ValueError):
            Conflict(finding_ids=["single_id"], description="test")

    def test_conflict_default_status(self):
        c = Conflict(finding_ids=["a", "b"], description="test conflict")
        self.assertEqual(c.resolution_status, ConflictStatus.UNRESOLVED)

    def test_research_state_defaults(self):
        state = ResearchState()
        self.assertEqual(len(state.agent_outputs), 0)
        self.assertEqual(len(state.conflicts), 0)
        self.assertIsNone(state.report)

    def test_agent_role_enum_values(self):
        self.assertEqual(AgentRole.WEB_RESEARCH.value, "web_research")
        self.assertEqual(AgentRole.SYNTHESIS.value, "synthesis")
        self.assertEqual(len(AgentRole), 5)
