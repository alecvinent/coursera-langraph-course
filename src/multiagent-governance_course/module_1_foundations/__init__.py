from typing import TypedDict

from log import logger


class ErrorRecord(TypedDict):
    step: str
    error_type: str
    message: str
    timestamp: str


__all__ = ["ErrorRecord", "logger"]
