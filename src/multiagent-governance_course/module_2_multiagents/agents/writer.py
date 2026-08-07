from __future__ import annotations

import time
from datetime import datetime, timezone
from typing import Any, Callable

from log import logger

from .. import ErrorRecord
from ..state import BlogState
from .prompts import WRITER_PROMPT, invoke_llm

NODE_NAME = "writer_node"


def writer_node(
    state: BlogState,
    *,
    llm: Callable[[str], str] | None = None,
) -> dict[str, Any]:
    start = time.monotonic()
    try:
        outline = (state.outline or "").strip()
        if not outline:
            raise ValueError("writer requires a non-empty outline from the researcher")
        prompt = WRITER_PROMPT.format(outline=outline)
        response = invoke_llm(prompt, llm)
        draft = response.strip()
        if not draft:
            raise ValueError("writer returned an empty draft")
        elapsed = time.monotonic() - start
        logger.info(f"{NODE_NAME} produced draft in {elapsed:.3f}s")
        return {"draft": draft}
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
