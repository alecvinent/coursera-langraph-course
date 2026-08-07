from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from log import logger

from .. import ErrorRecord
from ..state import BlogState
from .prompts import RESEARCHER_PROMPT, invoke_llm

NODE_NAME = "researcher_node"


def researcher_node(
    state: BlogState,
    *,
    llm: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    start = time.monotonic()
    try:
        topic = state.topic.strip()
        if not topic:
            raise ValueError("researcher requires a non-empty topic")
        prompt = RESEARCHER_PROMPT.format(topic=topic)
        response = invoke_llm(prompt, llm)
        outline = response.strip()
        if not outline:
            raise ValueError("researcher returned an empty outline")
        elapsed = time.monotonic() - start
        logger.info(f"{NODE_NAME} produced outline in {elapsed:.3f}s")
        return {"outline": outline}
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
