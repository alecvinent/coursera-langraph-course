from __future__ import annotations

from datetime import datetime

from loguru import logger

from langgraph_course.module_3.labs.multi_agent_research.state import (
    TelemetryEvent,
    TelemetryEventType,
)


class TelemetryBuffer:
    def __init__(self, max_events: int = 1000):
        self._events: list[TelemetryEvent] = []
        self._max_events = max_events

    def record(
        self,
        event_type: TelemetryEventType,
        agent_role: str,
        value: float,
        details: dict | None = None,
    ) -> TelemetryEvent:
        event = TelemetryEvent(
            event_type=event_type,
            agent_role=agent_role,
            value=value,
            details=details or {},
        )
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events.pop(0)
        logger.debug(
            "Telemetry: type={} agent={} value={}", event_type.value, agent_role, value
        )
        return event

    def query(
        self,
        window: int = 100,
        event_type: TelemetryEventType | None = None,
        agent_role: str | None = None,
    ) -> list[TelemetryEvent]:
        events = self._events[-window:]
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if agent_role:
            events = [e for e in events if e.agent_role == agent_role]
        return events

    def query_since(self, since: datetime) -> list[TelemetryEvent]:
        return [e for e in self._events if e.timestamp >= since]

    def summary(self, window: int = 100) -> dict:
        events = self._events[-window:]
        summary: dict = {}
        for e in events:
            key = e.event_type.value
            if key not in summary:
                summary[key] = {"count": 0, "agents": set()}
            summary[key]["count"] += 1
            summary[key]["agents"].add(e.agent_role)
        for v in summary.values():
            v["agents"] = list(v["agents"])
        return summary

    def clear(self) -> None:
        self._events.clear()


_buffer: TelemetryBuffer | None = None


def get_buffer() -> TelemetryBuffer:
    global _buffer
    if _buffer is None:
        _buffer = TelemetryBuffer()
    return _buffer


def reset_buffer() -> None:
    global _buffer
    _buffer = None
