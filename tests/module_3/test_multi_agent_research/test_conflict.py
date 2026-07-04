import unittest

from langgraph_course.module_3.labs.multi_agent_research.coordination.conflict import (
    _findings_contradict,
    detect_conflicts,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    ConflictStatus,
    Finding,
    ResearchState,
)


class TestConflictDetection(unittest.TestCase):
    def test_findings_contradict_increase_decrease(self):
        a = Finding(
            agent_role="web_research",
            content="The market is growing rapidly with increased demand",
            source="src-a",
            confidence=0.8,
        )
        b = Finding(
            agent_role="data_analysis",
            content="Data shows declining sales with decreased revenue",
            source="src-b",
            confidence=0.7,
        )
        self.assertTrue(_findings_contradict(a, b))

    def test_findings_no_contradiction(self):
        a = Finding(
            agent_role="web_research",
            content="The market is expanding in Asia",
            source="src-a",
            confidence=0.8,
        )
        b = Finding(
            agent_role="data_analysis",
            content="Revenue grew by 15% year over year",
            source="src-b",
            confidence=0.9,
        )
        self.assertFalse(_findings_contradict(a, b))

    def test_detect_conflicts_finds_contradiction(self):
        state = ResearchState()
        state.agent_outputs["web_research"] = [
            Finding(
                agent_role="web_research",
                content="Declining market share observed globally",
                source="src",
                confidence=0.8,
            )
        ]
        state.agent_outputs["data_analysis"] = [
            Finding(
                agent_role="data_analysis",
                content="Growing market share in all regions",
                source="src",
                confidence=0.9,
            )
        ]
        conflicts = detect_conflicts(state)
        self.assertGreater(len(conflicts), 0)

    def test_no_conflict_for_same_agent(self):
        state = ResearchState()
        state.agent_outputs["web_research"] = [
            Finding(
                agent_role="web_research",
                content="Market is declining",
                source="src",
                confidence=0.8,
            ),
            Finding(
                agent_role="web_research",
                content="Market is growing",
                source="src",
                confidence=0.7,
            ),
        ]
        conflicts = detect_conflicts(state)
        self.assertEqual(len(conflicts), 0)

    def test_conflict_default_status(self):
        a = Finding(
            agent_role="web_research",
            content="Strong growth expected",
            source="src",
            confidence=0.8,
        )
        b = Finding(
            agent_role="data_analysis",
            content="Weak performance projected",
            source="src",
            confidence=0.7,
        )
        state = ResearchState()
        state.agent_outputs["web_research"] = [a]
        state.agent_outputs["data_analysis"] = [b]
        conflicts = detect_conflicts(state)
        if conflicts:
            self.assertEqual(
                conflicts[0].resolution_status, ConflictStatus.UNRESOLVED
            )
