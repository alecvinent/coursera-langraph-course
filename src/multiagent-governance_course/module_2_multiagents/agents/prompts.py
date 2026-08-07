from __future__ import annotations

from typing import Callable

from log import logger
from utils.llm import LLMFactory


def invoke_llm(prompt: str, llm: Callable[[str], str] | None = None) -> str:
    """Invoke either an injected callable or the production LLM factory.

    The injected callable is used by tests for deterministic offline runs;
    production calls go exclusively through ``LLMFactory`` (Constitution IV).
    """
    if llm is not None:
        result = llm(prompt)
        return result if isinstance(result, str) else str(result)
    model = LLMFactory.create()
    result = model.invoke(prompt)
    return result.content if hasattr(result, "content") else str(result)


RESEARCHER_PROMPT = """You are a world-class researcher. Given the topic '{topic}', generate a 5-point bulleted outline for a blog post on that topic. Each bullet must be a concise, distinct key point. Output ONLY the bulleted list, no preamble and no closing remarks."""

WRITER_PROMPT = """You are a skilled content writer. Using the following outline:

{outline}

write a short, engaging 3-paragraph blog post. Expand each outline point into a paragraph so the draft preserves the researcher's structure. Output ONLY the article body, with paragraphs separated by a blank line."""

SEO_PROMPT = """You are an SEO expert. Based on the article provided:

{draft}

reference the article's content so your feedback derives from the draft. Then suggest exactly 3 SEO-friendly title options and 5 relevant keywords.

Format your response exactly as:
SEO Title Options:
1) <title>
2) <title>
3) <title>
Relevant Keywords: <kw1>, <kw2>, <kw3>, <kw4>, <kw5>"""
