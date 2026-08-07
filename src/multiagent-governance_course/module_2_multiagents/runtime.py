from __future__ import annotations

from typing import Callable

from .state import BlogState
from .workflow import build_workflow


def run_pipeline(
    topic: str,
    *,
    llm: Callable[[str], str] | None = None,
) -> BlogState:
    """Run the full Researcher -> Writer -> SEO Analyst chain for a topic.

    Raises ``ValueError`` for an empty/whitespace topic before any node runs.
    """
    stripped = topic.strip()
    if not stripped:
        raise ValueError("topic must be non-empty")

    graph = build_workflow(llm=llm)
    result = graph.invoke(BlogState(topic=stripped))
    return BlogState.model_validate(result)
