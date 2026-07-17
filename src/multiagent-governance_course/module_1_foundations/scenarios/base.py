from __future__ import annotations

import re
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field, model_validator


class InteractionType(str, Enum):
    data_flow = "data_flow"
    control_flow = "control_flow"
    feedback_loop = "feedback_loop"


class AgentType(str, Enum):
    reactive = "reactive"
    deliberative = "deliberative"
    hybrid = "hybrid"


class AgentAttribute(BaseModel):
    name: str
    value: str
    description: str | None = None


class AgentDef(BaseModel):
    id: str
    name: str
    description: str
    attributes: list[AgentAttribute]

    @model_validator(mode="after")
    def validate_id(self) -> "AgentDef":
        if not re.match(r"^[a-z][a-z0-9_]*$", self.id):
            raise ValueError(f"AgentDef.id must match ^[a-z][a-z0-9_]*$, got {self.id!r}")
        if not self.name or len(self.name) > 80:
            raise ValueError("AgentDef.name must be non-empty and ≤ 80 chars")
        if not self.attributes:
            raise ValueError("AgentDef.attributes must contain at least one entry")
        return self


class InteractionDef(BaseModel):
    source: str
    target: str
    label: str
    type: InteractionType


class Scenario(BaseModel):
    id: str
    name: str
    description: str
    agents: list[AgentDef]
    interactions: list[InteractionDef]

    @model_validator(mode="after")
    def validate_interactions(self) -> "Scenario":
        agent_ids = {a.id for a in self.agents}
        for ix in self.interactions:
            if ix.source not in agent_ids:
                raise ValueError(f"Interaction source {ix.source!r} not found in agents")
            if ix.target not in agent_ids:
                raise ValueError(f"Interaction target {ix.target!r} not found in agents")
            if ix.source == ix.target:
                raise ValueError(f"Self-loop interaction on {ix.source!r} is not allowed")
        return self


class DimensionScore(TypedDict):
    reactive_score: int
    deliberative_score: int
    hybrid_score: int
    rationale: str


class ComparisonView(TypedDict):
    table: str
    recommendation: str
