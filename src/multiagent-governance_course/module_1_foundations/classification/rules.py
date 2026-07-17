from __future__ import annotations

import re
from typing import Literal

from .. import ErrorRecord

NEGATION_WORDS = {"no", "not", "without", "lacks", "doesn't", "don't", "never", "nor", "neither", "absent", "none"}

REACTIVE_KEYWORDS = [
    "stateless", "no state", "no internal state", "no memory",
    "if-then", "if then", "stimulus-response", "stimulus response",
    "reactive", "sensor", "direct sensing", "stateless emitter",
    "reads sensor", "emits data", "immediate response",
]

DELIBERATIVE_KEYWORDS = [
    "world model", "planning", "long-term", "long term",
    "utility", "reasoning", "deliberative",
    "stateful", "full state", "goal-oriented", "goal oriented",
    "maintains state", "maintains model", "optimal",
    "historical trends", "traffic patterns", "road network",
]

HYBRID_KEYWORDS = [
    "hybrid", "both reactive and deliberative", "mixed",
    "combination of", "combines", "reactive alert",
    "deliberative planning", "both immediate",
]

LLM_TRIGGER_KEYWORDS = [
    "complex", "adaptive", "context-aware", "context aware",
    "sophisticated", "multi-modal", "multimodal",
]


def _sentence_tokenize(text: str) -> list[str]:
    return [s.strip() for s in re.split(r'[.!?]+', text) if s.strip()]


def _has_negation_in_sentence(sentence: str, keyword: str) -> bool:
    lower = sentence.lower()
    words = re.findall(r"[a-z']+", lower)
    kw_lower = keyword.lower()
    for i, w in enumerate(words):
        if kw_lower in w or w in kw_lower:
            start = max(0, i - 5)
            end = min(len(words), i + 6)
            window = set(words[start:end])
            if window & NEGATION_WORDS:
                return True
    return False


def _keyword_matches(text: str, keywords: list[str]) -> list[str]:
    lower = text.lower()
    matched = []
    for kw in keywords:
        if kw.lower() in lower:
            matched.append(kw)
    return matched


def _sentence_has_any_keyword(sentence: str, keywords: list[str]) -> bool:
    lower = sentence.lower()
    for kw in keywords:
        if kw.lower() in lower:
            return True
    return False


def classification_rules(state: dict) -> dict:
    description = state.get("description", "").strip()
    if not description:
        state["agent_type"] = ""
        state["justification"] = "No description provided."
        state.setdefault("errors", [])
        state["errors"].append(ErrorRecord(
            step="classification_rules",
            error_type="ValueError",
            message="Empty description",
            timestamp="",
        ))
        return state

    sentences = _sentence_tokenize(description)

    has_deliberative = False
    has_reactive = False
    deliberative_evidence = []
    reactive_evidence = []

    for sent in sentences:
        for kw in DELIBERATIVE_KEYWORDS:
            if not _has_negation_in_sentence(sent, kw) and kw.lower() in sent.lower():
                has_deliberative = True
                deliberative_evidence.append(kw)
        for kw in REACTIVE_KEYWORDS:
            if not _has_negation_in_sentence(sent, kw) and kw.lower() in sent.lower():
                has_reactive = True
                reactive_evidence.append(kw)

    is_hybrid_explicit = _keyword_matches(description, HYBRID_KEYWORDS)

    if is_hybrid_explicit or (has_deliberative and has_reactive):
        state["agent_type"] = "hybrid"
        parts = []
        if is_hybrid_explicit:
            parts.append(f"Explicitly described as hybrid ({', '.join(is_hybrid_explicit)})")
        if has_reactive:
            parts.append(f"Exhibits reactive traits: {', '.join(set(reactive_evidence))}")
        if has_deliberative:
            parts.append(f"Exhibits deliberative traits: {', '.join(set(deliberative_evidence))}")
        state["justification"] = " | ".join(parts)
        return state

    if has_deliberative:
        state["agent_type"] = "deliberative"
        state["justification"] = f"World-modeling and planning detected: {', '.join(set(deliberative_evidence))}"
        return state

    if has_reactive:
        state["agent_type"] = "reactive"
        state["justification"] = f"Stateless stimulus-response behavior detected: {', '.join(set(reactive_evidence))}"
        return state

    state["agent_type"] = ""
    state["justification"] = "Ambiguous — no clear agent type indicators found."
    return state


def needs_llm(state: dict) -> Literal["llm_fallback", "finalize"]:
    if not state.get("agent_type"):
        return "llm_fallback"
    return "finalize"
