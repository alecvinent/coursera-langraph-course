from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

from . import ErrorRecord


class BlogState(BaseModel):
    topic: str = Field(..., description="Single user-provided topic seeding the chain")
    outline: str | None = Field(default=None, description="Researcher output: structured bulleted outline")
    draft: str | None = Field(default=None, description="Writer output: multi-paragraph article draft")
    seo_feedback: str | None = Field(default=None, description="SEO Analyst output: titles + keywords")
    processing_outcome: str = Field(default="full", description="'full' or 'partial'")
    error_records: list[ErrorRecord] = Field(default_factory=list)

    @field_validator("topic")
    @classmethod
    def topic_must_be_non_empty(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("topic must be non-empty")
        return stripped
