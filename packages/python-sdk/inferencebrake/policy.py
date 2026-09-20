"""Loop-handling policy: escalate, steer, or stop when a loop is detected.

Mirrors the escalation idea from OpenRouter's doom-loop ladder, but framework
agnostic: the SDK does not control model selection, so ``escalate`` is a hook
you provide (switch to a stronger model, inject a steering message, call an
advisor, and so on).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Optional

from .client import CheckStatus, LoopDetectedError

logger = logging.getLogger(__name__)

STEERING_MESSAGE = (
    "You are repeating yourself without making progress. Stop retrying the same "
    "action. Reassess what is blocking you, try a different approach, or ask for "
    "help. Do not repeat the previous action verbatim."
)


def steering_message(status: CheckStatus) -> str:
    """A ready-to-inject nudge to send the agent after a detected loop."""
    return f"{STEERING_MESSAGE}\n\nDetected: {status.message}"


@dataclass
class LoopPolicy:
    """Decides what happens when a loop is detected.

    Precedence on detection:

    1. ``escalate`` while under ``max_escalations`` (the agent keeps running)
    2. ``on_loop`` callback
    3. raise ``LoopDetectedError`` when ``auto_stop``

    Example:
        policy = LoopPolicy(
            max_escalations=2,
            escalate=lambda status, attempt: switch_to("claude-opus"),
        )
    """

    auto_stop: bool = True
    max_escalations: int = 2
    escalate: Optional[Callable[[CheckStatus, int], None]] = None
    on_loop: Optional[Callable[[CheckStatus], None]] = None
    _escalations: int = field(default=0, repr=False)

    def handle(self, status: CheckStatus) -> str:
        """Apply the policy. Returns ``escalate``, ``stop``, or ``continue``."""
        if not status.should_stop:
            return "continue"

        if self.escalate is not None and self._escalations < self.max_escalations:
            self._escalations += 1
            logger.warning(
                "InferenceBrake: loop detected, escalating (%s/%s)",
                self._escalations,
                self.max_escalations,
            )
            self.escalate(status, self._escalations)
            return "escalate"

        if self.on_loop is not None:
            self.on_loop(status)

        if self.auto_stop:
            raise LoopDetectedError(status.message)
        return "stop"

    @property
    def escalations_used(self) -> int:
        return self._escalations

    def reset(self) -> None:
        """Reset the escalation budget (for example, on a new agent run)."""
        self._escalations = 0