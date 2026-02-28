"""
Base detector interface.

All detection strategies implement this interface to participate
in the multi-layer pipeline voting system.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod

from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


class BaseDetector(ABC):
    """
    Abstract base class for loop detectors.

    Each detector examines a different signal (text patterns,
    embeddings, entropy, actions) and returns a DetectionSignal
    with its verdict and confidence.
    """

    name: str = "base"

    @abstractmethod
    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        """
        Analyze the current reasoning step against session history.

        Args:
            reasoning: The current reasoning text to evaluate.
            session: The full session state with history.
            config: Threshold configuration.

        Returns:
            DetectionSignal with verdict, confidence, and details.
        """
        ...

    def _safe_signal(self, detail: str = "") -> DetectionSignal:
        """Return a SAFE signal with zero confidence."""
        return DetectionSignal(
            detector_name=self.name,
            verdict=DetectorVerdict.SAFE,
            loop_type=LoopType.NONE,
            confidence=0.0,
            score=0.0,
            threshold_used=0.0,
            detail=detail,
        )

    def _timed(self, func, *args, **kwargs):
        """Run a function and return (result, latency_ms)."""
        t0 = time.perf_counter()
        result = func(*args, **kwargs)
        latency = (time.perf_counter() - t0) * 1000
        return result, latency
