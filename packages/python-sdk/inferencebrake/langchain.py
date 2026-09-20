"""Backwards-compatible re-export. Prefer ``inferencebrake.adapters.langchain``."""

from .adapters.langchain import HAS_LANGCHAIN, InferenceBrakeCallbackHandler
from .client import LoopDetectedError

__all__ = ["InferenceBrakeCallbackHandler", "LoopDetectedError", "HAS_LANGCHAIN"]