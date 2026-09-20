"""Backwards-compatible re-export. Prefer ``inferencebrake.adapters.crewai``."""

from .adapters.crewai import CrewAICallback, create_crewai_callback
from .client import LoopDetectedError

__all__ = ["CrewAICallback", "create_crewai_callback", "LoopDetectedError"]