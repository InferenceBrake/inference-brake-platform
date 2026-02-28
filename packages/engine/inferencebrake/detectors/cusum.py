"""
CUSUM (Cumulative Sum) Drift Detector.

Tracks the cumulative drift in embedding space over time.
When embeddings stop changing (drift approaches zero), the
agent is stagnating - a precursor to or indicator of looping.

Based on CUSUM change-point detection (Page, 1954), adapted for
embedding trajectory analysis. This approach can detect loops
BEFORE semantic similarity crosses its threshold, providing
advance warning.

Related work:
    - Duan et al. (2026, arXiv:2601.05693): "Circular Reasoning" --
      the most direct precedent for this detector. Uses CUSUM to
      detect reasoning loops in LRMs by monitoring hidden state
      shifts that precede textual repetition. Introduces LoopBench
      (two typologies: numerical loops and statement loops).
      Key finding: semantic repetition precedes textual repetition,
      so trajectory-based detection catches loops earlier than
      similarity thresholds alone.
    - TAAR (Chen et al., 2026, arXiv:2601.11940): Trap-aware detection
      where 89% of Long-CoT failures exhibit prefix-dominant deadlocks.
      Motivates trajectory-based detection over point-in-time similarity.

The CUSUM detector tracks two signals:
    1. Drift magnitude: cosine distance between consecutive embeddings
    2. Drift direction consistency: whether the agent explores or circles
"""


from __future__ import annotations

import numpy as np

from inferencebrake.detectors import BaseDetector
from inferencebrake.detectors.semantic import cosine_similarity
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


class CUSUMDetector(BaseDetector):
    """
    Cumulative sum drift detector for embedding trajectories.

    Monitors how much the embedding space is changing step-to-step.
    Low drift = agent is stuck in a semantic neighborhood = loop.

    The CUSUM statistic accumulates deviations below the expected
    drift rate. When it exceeds the stagnation limit, we flag
    a potential loop.

    This detector provides earlier warning than pure similarity
    because it catches the TRAJECTORY toward repetition, not just
    the final similarity score.
    """

    name = "cusum"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        embedding: list[float] | None = None,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection + 1:
            return self._safe_signal("Need at least 3 steps for drift analysis")

        if embedding is None:
            return self._safe_signal("No embedding available")

        # Get recent embeddings including the new one
        recent_embeddings = session.get_recent_embeddings(config.cusum_window)
        if len(recent_embeddings) < 2:
            return self._safe_signal("Not enough embeddings for drift")

        # Compute step-to-step drift values
        drifts = []
        prev = recent_embeddings[0]
        for emb in recent_embeddings[1:]:
            drift = 1.0 - cosine_similarity(prev, emb)
            drifts.append(drift)
            prev = emb

        # Add drift from last history embedding to current
        current_drift = 1.0 - cosine_similarity(recent_embeddings[-1], embedding)
        drifts.append(current_drift)

        # CUSUM computation
        # We track how much drift is BELOW the expected threshold
        # If cumulative below-threshold drift grows, agent is stagnating
        cusum_plus = 0.0  # Upward CUSUM (not used for stagnation)
        cusum_minus = 0.0  # Downward CUSUM (stagnation signal)
        drift_threshold = config.cusum_drift_threshold

        for d in drifts:
            deviation = d - drift_threshold
            cusum_minus = max(0.0, cusum_minus - deviation)
            cusum_plus = max(0.0, cusum_plus + deviation)

        # Update session state
        session.cusum_value = cusum_minus

        # Calculate statistics
        avg_drift = sum(drifts) / len(drifts) if drifts else 0
        recent_avg = sum(drifts[-3:]) / min(3, len(drifts))  # Last 3 steps
        drift_trend = recent_avg - avg_drift  # Negative = drift decreasing

        # Mirror-Loop Check: Decay toward zero after 6-7 steps
        # Check if the last 7 steps show strictly decreasing or consistently low drift
        mirror_loop_detected = False
        if len(drifts) >= 6:
            recent_drifts = drifts[-6:]
            # Criteria 1: Monotonic decrease to near zero
            is_decreasing = all(recent_drifts[i] >= recent_drifts[i+1] for i in range(len(recent_drifts)-1))
            is_near_zero = recent_drifts[-1] < 0.02
            
            # Criteria 2: Consistently tiny drift (collapsed state)
            is_collapsed = all(d < 0.02 for d in recent_drifts)
            
            if (is_decreasing and is_near_zero) or is_collapsed:
                mirror_loop_detected = True
                confidence = 0.95
                return DetectionSignal(
                    detector_name=self.name,
                    verdict=DetectorVerdict.LOOP_DETECTED,
                    loop_type=LoopType.CUSUM_STAGNATION,
                    confidence=confidence,
                    score=0.0, # Placeholder
                    threshold_used=0.02,
                    detail="Mirror-Loop detected: Embedding drift decayed to near-zero over last 6 steps.",
                    metadata={"drifts": recent_drifts, "pattern": "mirror_loop_decay"}
                )

        # Check for stagnation
        stagnation_limit = config.cusum_stagnation_limit
        is_stagnating = cusum_minus > stagnation_limit

        # Also check if recent drift is consistently low
        low_drift_count = sum(1 for d in drifts[-3:] if d < drift_threshold * 0.5)
        consistent_low = low_drift_count >= 2

        if is_stagnating and consistent_low:
            # Strong stagnation signal
            confidence = min(cusum_minus / (stagnation_limit * 2), 1.0)
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.CUSUM_STAGNATION,
                confidence=confidence,
                score=cusum_minus,
                threshold_used=stagnation_limit,
                detail=(
                    f"CUSUM stagnation: {cusum_minus:.4f} > {stagnation_limit:.4f}. "
                    f"Avg drift: {avg_drift:.4f}, recent: {recent_avg:.4f}. "
                    f"Agent stuck in same semantic neighborhood."
                ),
                metadata={
                    "cusum_minus": cusum_minus,
                    "cusum_plus": cusum_plus,
                    "avg_drift": avg_drift,
                    "recent_avg_drift": recent_avg,
                    "drift_trend": drift_trend,
                    "drifts": drifts,
                    "low_drift_count": low_drift_count,
                },
            )
        elif is_stagnating or consistent_low:
            # Early warning
            confidence = min(cusum_minus / (stagnation_limit * 3), 0.7)
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.CUSUM_STAGNATION,
                confidence=confidence,
                score=cusum_minus,
                threshold_used=stagnation_limit,
                detail=(
                    f"Drift decreasing: CUSUM={cusum_minus:.4f}, "
                    f"avg_drift={avg_drift:.4f}. Possible stagnation."
                ),
                metadata={
                    "cusum_minus": cusum_minus,
                    "avg_drift": avg_drift,
                    "drift_trend": drift_trend,
                },
            )

        return self._safe_signal(
            f"Healthy drift: CUSUM={cusum_minus:.4f}, avg={avg_drift:.4f}"
        )
