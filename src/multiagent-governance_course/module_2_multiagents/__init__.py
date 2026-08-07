from typing import TypedDict

from log import logger


class ErrorRecord(TypedDict):
    step: str
    error_type: str
    message: str
    timestamp: str


def __getattr__(name: str):
    if name in ("run_pipeline", "build_workflow", "BlogState"):
        from .runtime import run_pipeline
        from .state import BlogState
        from .workflow import build_workflow

        return {"run_pipeline": run_pipeline, "build_workflow": build_workflow, "BlogState": BlogState}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["ErrorRecord", "logger", "run_pipeline", "build_workflow", "BlogState"]