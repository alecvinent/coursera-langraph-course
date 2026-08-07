from __future__ import annotations

from functools import partial
from typing import Callable

from langgraph.graph import END, StateGraph

from .agents.researcher import researcher_node
from .agents.seo import seo_node
from .agents.writer import writer_node
from .state import BlogState


def build_workflow(llm: Callable[[str], str] | None = None) -> object:
    """Build the strictly linear Researcher -> Writer -> SEO Analyst chain.

    Each node is bound to the same optional injected ``llm`` callable so the
    graph is deterministic and offline-testable while production calls go
    through ``LLMFactory`` (see research.md Decision 3).
    """
    workflow = StateGraph(BlogState)

    workflow.add_node("researcher", partial(researcher_node, llm=llm))
    workflow.add_node("writer", partial(writer_node, llm=llm))
    workflow.add_node("seo", partial(seo_node, llm=llm))

    workflow.set_entry_point("researcher")
    workflow.add_edge("researcher", "writer")
    workflow.add_edge("writer", "seo")
    workflow.add_edge("seo", END)

    return workflow.compile()
