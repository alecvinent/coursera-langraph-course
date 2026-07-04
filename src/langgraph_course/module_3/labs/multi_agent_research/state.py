from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AgentRole(str, Enum):
    WEB_RESEARCH = "web_research"
    DATA_ANALYSIS = "data_analysis"
    TREND_ANALYSIS = "trend_analysis"
    COMPETITIVE_INTELLIGENCE = "competitive_intelligence"
    SYNTHESIS = "synthesis"


class ResearchRequestStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REFINEMENT = "needs_refinement"


class ExecutionState(str, Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"


class ConflictStatus(str, Enum):
    UNRESOLVED = "unresolved"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


class TelemetryEventType(str, Enum):
    AGENT_LATENCY = "agent_latency"
    OUTPUT_CONFIDENCE = "output_confidence"
    CONFLICT_DETECTED = "conflict_detected"
    FAILURE = "failure"
    STOP_TRIGGERED = "stop_triggered"


class ResearchRequest(BaseModel):
    topic: str = Field(default="default research topic", min_length=1, max_length=500)
    domain_tags: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    status: ResearchRequestStatus = ResearchRequestStatus.PENDING


class Finding(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    agent_role: str
    content: str
    source: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_chain: list[str] = Field(default_factory=list)
    cross_references: list[str] = Field(default_factory=list)


class Conflict(BaseModel):
    finding_ids: list[str] = Field(..., min_length=2)
    description: str
    detected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolution_status: ConflictStatus = ConflictStatus.UNRESOLVED
    resolution_rationale: str = ""


class SteeringInstruction(BaseModel):
    instruction_text: str
    target_agents: list[str]
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    applied: bool = False


class TelemetryEvent(BaseModel):
    event_type: TelemetryEventType
    agent_role: str
    value: float
    details: dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AgentState(BaseModel):
    role: AgentRole
    execution_state: ExecutionState = ExecutionState.IDLE
    input_requirements: list[str] = Field(default_factory=list)
    findings: list[Finding] = Field(default_factory=list)
    confidence: float = 0.0


class SynthesisReport(BaseModel):
    sections: list[dict[str, Any]] = Field(default_factory=list)
    cross_references: list[dict[str, Any]] = Field(default_factory=list)
    conflict_disclosures: list[Conflict] = Field(default_factory=list)
    provenance_trace: dict[str, Any] = Field(default_factory=dict)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchState(BaseModel):
    request: ResearchRequest = Field(default_factory=ResearchRequest)
    agent_outputs: dict[str, list[Finding]] = Field(default_factory=dict)
    agent_states: dict[str, AgentState] = Field(default_factory=dict)
    conflicts: list[Conflict] = Field(default_factory=list)
    cross_agent_insights: list[str] = Field(default_factory=list)
    execution_metadata: dict[str, Any] = Field(default_factory=dict)
    steering_instructions: list[SteeringInstruction] = Field(default_factory=list)
    report: SynthesisReport | None = None
    messages: list = Field(default_factory=list)
    telemetry_events: list[TelemetryEvent] = Field(default_factory=list)
