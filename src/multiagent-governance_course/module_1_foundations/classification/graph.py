from __future__ import annotations

import json
import time
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph
from log import logger

from .. import ErrorRecord
from utils.llm import LLMFactory

from .prompts import build_classification_prompt
from .rules import classification_rules, needs_llm


class ClassificationState(TypedDict, total=False):
    description: str
    agent_type: str
    justification: str
    confidence: float
    processing_outcome: str
    method: str
    errors: list[ErrorRecord]
    latencies: dict[str, float]
    paths_taken: list[str]


def rules_node(state: ClassificationState) -> dict[str, Any]:
    start = time.monotonic()
    result = classification_rules(dict(state))
    elapsed = time.monotonic() - start
    return {
        "agent_type": result.get("agent_type", ""),
        "justification": result.get("justification", ""),
        "errors": result.get("errors", []),
        "latencies": {"classify_rules": elapsed},
        "paths_taken": ["classify_rules"],
    }


def _call_llm_with_retry(messages: str, max_retries: int = 3) -> str:
    base_delay = 1.0
    for attempt in range(max_retries):
        try:
            llm = LLMFactory.create()
            result = llm.invoke(messages)
            return result.content if hasattr(result, "content") else str(result)
        except (ConnectionError, TimeoutError, OSError) as exc:
            if attempt < max_retries - 1:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
            else:
                raise
        except Exception:
            raise


def llm_node(state: ClassificationState) -> dict[str, Any]:
    start = time.monotonic()
    description = state.get("description", "")
    try:
        messages = build_classification_prompt(description)
        response = _call_llm_with_retry(str(messages))
        parsed = json.loads(response.strip().removeprefix("```json").removesuffix("```").strip())
        agent_type = parsed.get("agent_type", "").lower()
        justification = parsed.get("justification", "")
        elapsed = time.monotonic() - start
        return {
            "agent_type": agent_type if agent_type in ("reactive", "deliberative", "hybrid") else "",
            "justification": justification,
            "confidence": 0.85,
            "method": "llm",
            "processing_outcome": "full",
            "latencies": {"classify_llm": elapsed},
            "paths_taken": ["classify_llm"],
        }
    except Exception as exc:
        elapsed = time.monotonic() - start
        logger.error(f"LLM classification failed: {exc}")
        return {
            "agent_type": "",
            "justification": f"LLM classification failed: {exc}",
            "confidence": 0.0,
            "method": "llm",
            "processing_outcome": "partial",
            "latencies": {"classify_llm": elapsed},
            "paths_taken": ["classify_llm"],
            "errors": [ErrorRecord(
                step="classify_llm",
                error_type=type(exc).__name__,
                message=str(exc),
                timestamp="",
            )],
        }


def build_classifier() -> StateGraph:
    workflow = StateGraph(ClassificationState)

    workflow.add_node("classification_rules", rules_node)
    workflow.add_node("llm_fallback", llm_node)

    workflow.set_entry_point("classification_rules")

    workflow.add_conditional_edges(
        "classification_rules",
        needs_llm,
        {"llm_fallback": "llm_fallback", "finalize": END},
    )

    workflow.add_edge("llm_fallback", END)

    return workflow.compile()


classifier_app = build_classifier()


def classify_agent(description: str, attributes: list[dict] | None = None) -> dict[str, Any]:
    enriched = description.strip()
    if attributes:
        attr_lines = "; ".join(f"{a.get('name', '')}={a.get('value', '')}" for a in attributes)
        enriched = f"{enriched}\nAttributes: {attr_lines}"
    initial: ClassificationState = {
        "description": enriched,
        "errors": [],
        "latencies": {},
        "paths_taken": [],
    }
    result = classifier_app.invoke(initial)
    return {
        "agent_type": result.get("agent_type", ""),
        "justification": result.get("justification", ""),
        "confidence": result.get("confidence", 0.0),
        "method": result.get("method", "rule_based"),
        "processing_outcome": result.get("processing_outcome", "full"),
        "latencies": result.get("latencies", {}),
        "paths_taken": result.get("paths_taken", []),
    }
