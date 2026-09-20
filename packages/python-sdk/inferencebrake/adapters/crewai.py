"""CrewAI (and generic step-based) callback for InferenceBrake loop detection.

The callback is duck-typed: it does not import CrewAI, so it works with any
framework that calls an ``on_agent_action`` style hook (CrewAI, AutoGen step
listeners, or custom loops).
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from ..client import CheckStatus, InferenceBrake, LoopDetectedError

logger = logging.getLogger(__name__)


@dataclass
class CrewAICallback:
    """Callback that checks each agent step for a reasoning loop."""

    api_key: str
    supabase_url: Optional[str] = None
    session_id: Optional[str] = None
    threshold: Optional[float] = None
    auto_stop: bool = True
    fail_open: bool = True
    loop_key: Optional[Callable[[str], Optional[str]]] = None
    on_loop_detected: Optional[Callable[[CheckStatus], None]] = None
    _client: Any = field(default=None, repr=False)
    _step_count: int = field(default=0, repr=False)

    def __post_init__(self) -> None:
        if not self.api_key:
            raise ValueError("CrewAICallback requires an api_key")
        if not self.session_id:
            self.session_id = f"crewai-{os.urandom(8).hex()}"

    @property
    def client(self) -> InferenceBrake:
        if self._client is None:
            self._client = InferenceBrake(
                api_key=self.api_key,
                supabase_url=self.supabase_url,
                fail_open=self.fail_open,
            )
        return self._client

    def on_agent_action(self, agent: Any, action: Any) -> None:
        """Called when an agent takes an action (CrewAI signature)."""
        self.step(action)

    def step(self, reasoning: Any, action: Optional[str] = None) -> CheckStatus:
        """Check one reasoning/action string. Framework-agnostic entry point."""
        self._step_count += 1

        identity = loop_key_value(self.loop_key, action)
        status = self.client.check(
            reasoning=str(reasoning),
            session_id=self.session_id or "",
            threshold=self.threshold,
            action=identity,
        )

        if status.should_stop:
            logger.warning(
                "InferenceBrake: loop detected at step %s (confidence %.2f, detectors: %s)",
                self._step_count,
                status.confidence,
                status.detector_triggered or "none",
            )
            if self.on_loop_detected is not None:
                self.on_loop_detected(status)
            if self.auto_stop:
                raise LoopDetectedError(f"Loop detected: {status.message}")

        return status

    def reset(self, new_session_id: Optional[str] = None) -> None:
        """Start a new logical session."""
        self._step_count = 0
        if new_session_id:
            self.session_id = new_session_id


def loop_key_value(
    loop_key: Optional[Callable[[str], Optional[str]]],
    action: Optional[str],
) -> Optional[str]:
    if action is None:
        return None
    if loop_key is None:
        return action
    try:
        return loop_key(str(action))
    except Exception as e:  # never let identity computation crash the run
        logger.warning("loop_key failed (%s); falling back to raw action", e)
        return action


def create_crewai_callback(
    api_key: Optional[str] = None,
    supabase_url: Optional[str] = None,
    session_id: Optional[str] = None,
    threshold: Optional[float] = None,
    auto_stop: bool = True,
    fail_open: bool = True,
    loop_key: Optional[Callable[[str], Optional[str]]] = None,
    on_loop_detected: Optional[Callable[[CheckStatus], None]] = None,
) -> CrewAICallback:
    """Factory for a CrewAI loop-detection callback."""
    return CrewAICallback(
        api_key=api_key or os.getenv("INFERENCEBRAKE_API_KEY") or "",
        supabase_url=supabase_url,
        session_id=session_id,
        threshold=threshold,
        auto_stop=auto_stop,
        fail_open=fail_open,
        loop_key=loop_key,
        on_loop_detected=on_loop_detected,
    )