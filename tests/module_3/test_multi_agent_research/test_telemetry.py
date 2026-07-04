import unittest

from langgraph_course.module_3.labs.multi_agent_research.telemetry.events import (
    TelemetryBuffer,
    get_buffer,
    reset_buffer,
)
from langgraph_course.module_3.labs.multi_agent_research.state import (
    TelemetryEventType,
)


class TestTelemetryBuffer(unittest.TestCase):
    def setUp(self):
        reset_buffer()

    def test_record_event(self):
        buf = TelemetryBuffer()
        event = buf.record(
            TelemetryEventType.AGENT_LATENCY,
            "web_research",
            1.23,
            {"detail": "test"},
        )
        self.assertEqual(event.event_type, TelemetryEventType.AGENT_LATENCY)
        self.assertEqual(event.agent_role, "web_research")
        self.assertEqual(event.value, 1.23)

    def test_query_returns_recent_events(self):
        buf = TelemetryBuffer()
        for i in range(10):
            buf.record(TelemetryEventType.AGENT_LATENCY, "test", float(i))
        results = buf.query(window=5)
        self.assertEqual(len(results), 5)

    def test_query_filter_by_type(self):
        buf = TelemetryBuffer()
        buf.record(TelemetryEventType.AGENT_LATENCY, "a", 1.0)
        buf.record(TelemetryEventType.CONFLICT_DETECTED, "b", 2.0)
        results = buf.query(event_type=TelemetryEventType.CONFLICT_DETECTED)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].event_type, TelemetryEventType.CONFLICT_DETECTED)

    def test_query_filter_by_agent(self):
        buf = TelemetryBuffer()
        buf.record(TelemetryEventType.AGENT_LATENCY, "agent_a", 1.0)
        buf.record(TelemetryEventType.AGENT_LATENCY, "agent_b", 2.0)
        results = buf.query(agent_role="agent_a")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].agent_role, "agent_a")

    def test_summary(self):
        buf = TelemetryBuffer()
        buf.record(TelemetryEventType.AGENT_LATENCY, "web", 1.0)
        buf.record(TelemetryEventType.AGENT_LATENCY, "data", 2.0)
        buf.record(TelemetryEventType.CONFLICT_DETECTED, "synth", 1.0)
        summary = buf.summary(window=10)
        self.assertIn("agent_latency", summary)
        self.assertIn("conflict_detected", summary)

    def test_clear(self):
        buf = TelemetryBuffer()
        buf.record(TelemetryEventType.AGENT_LATENCY, "test", 1.0)
        buf.clear()
        self.assertEqual(len(buf.query(window=100)), 0)

    def test_max_events(self):
        buf = TelemetryBuffer(max_events=5)
        for i in range(10):
            buf.record(TelemetryEventType.AGENT_LATENCY, "test", float(i))
        self.assertEqual(len(buf._events), 5)

    def test_get_buffer_singleton(self):
        b1 = get_buffer()
        b2 = get_buffer()
        self.assertIs(b1, b2)
