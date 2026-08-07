from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from log import logger

from .. import ErrorRecord
from ..state import BlogState
from .prompts import SEO_PROMPT, invoke_llm

NODE_NAME = "seo_node"


def seo_node(
    state: BlogState,
    *,
    llm: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    start = time.monotonic()
    try:
        draft = (state.draft or "").strip()
        if not draft:
            raise ValueError("seo requires a non-empty draft from the writer")
        prompt = SEO_PROMPT.format(draft=draft)
        response = invoke_llm(prompt, llm)
        seo_feedback = response.strip()
        if not seo_feedback:
            raise ValueError("seo returned empty feedback")
        elapsed = time.monotonic() - start
        logger.info(f"{NODE_NAME} produced seo feedback in {elapsed:.3f}s")
        return {"seo_feedback": seo_feedback}
    except Exception as exc:
        elapsed = time.monotonic() - start
        logger.error(f"{NODE_NAME} failed: {exc}")
        return {
            "processing_outcome": "partial",
            "error_records": [
                ErrorRecord(
                    step=NODE_NAME,
                    error_type=type(exc).__name__,
                    message=str(exc),
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            ],
        }