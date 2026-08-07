from __future__ import annotations

from .agents.prompts import RESEARCHER_PROMPT, SEO_PROMPT, WRITER_PROMPT


def build_prompts_doc() -> str:
    """Render the lab's Agent Prompt Engineering deliverable (Deliverable 2).

    Each prompt is shown verbatim followed by exactly one sentence explaining
    how it converts its incoming artifact into the structured output the next
    agent consumes. Reuses the prompt templates so the document never drifts
    from the live prompts.
    """
    sections = [
        (
            "Researcher",
            RESEARCHER_PROMPT,
            "This prompt converts the raw {topic} into a structured five-point "
            "outline that the Writer can consume bullet-by-bullet next in the chain.",
        ),
        (
            "Writer",
            WRITER_PROMPT,
            "This prompt converts the Researcher's {outline} into a three-paragraph "
            "draft by instructing the model to expand each outline point, so the "
            "article preserves the outline's structure for the SEO Agent next.",
        ),
        (
            "SEO Analyst",
            SEO_PROMPT,
            "This prompt converts the Writer's {draft} into formatted SEO feedback "
            "(title options plus keywords) by instructing the model to derive the "
            "suggestions from the article's content for the final stage.",
        ),
    ]

    lines = [
        "# Agent Prompt Engineering — Sequential Multi-Agent Blog Workflow",
        "",
        "Exact text of the three engineered prompts and how each transforms its "
        "input into structured output for the next agent in the chain.",
        "",
    ]
    for title, prompt, justification in sections:
        lines.append(f"## {title}")
        lines.append(f"**Prompt:** `{prompt.strip()}`")
        lines.append("")
        lines.append("**How it transforms input for the next agent:**")
        lines.append(justification)
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines).rstrip()


def _count_words(text: str) -> int:
    return len(text.split())


ANALYSIS = (
    "The Simple Sequential Chain implements a linear, one-way communication "
    "protocol: information flows strictly forward from the Researcher to the "
    "Writer to the SEO Analyst, and each agent consumes the exact artifact the "
    "previous one produced. Its major advantage is predictability. Because every "
    "stage has exactly one source of input and one consumer of its output, the "
    "pipeline is trivial to trace and debug, and responsibilities stay clearly "
    "bounded, which made the task easy to decompose into research, writing, and "
    "SEO stages. Its significant limitation is the absence of feedback. The "
    "Writer cannot ask the Researcher to expand a thin outline, and the SEO "
    "Analyst cannot suggest reordering the draft, so errors and gaps propagate "
    "forward with no correction loop; a single weak early stage degrades "
    "everything downstream. The most critical consideration in prompt design was "
    "the handoff: defining a stable, explicit output format for each agent and "
    "instructing each consumer to reference exactly what it receives. That "
    "guarantees the draft preserves the outline and the SEO feedback derives "
    "from the draft, keeping the linear channel lossless."
)


def build_analysis_doc(word_count: int | None = None) -> tuple[str, int]:
    """Return the communication-protocol analysis and its word count.

    The write-up must be within 150-200 words (Deliverable 3). ``word_count``
    is an optional override used to validate the range check in isolation;
    when provided it is reported as-is after being range-validated.
    """
    if word_count is not None:
        if not 150 <= word_count <= 200:
            raise ValueError(
                f"analysis word count must be within 150-200, got {word_count}"
            )
        return ANALYSIS, word_count

    count = _count_words(ANALYSIS)
    if not 150 <= count <= 200:
        raise ValueError(f"analysis is {count} words; must be within 150-200")
    return ANALYSIS, count