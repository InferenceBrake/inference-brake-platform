"""
Edit Distance Decay Detector.

Tracks the normalized edit distance (Levenshtein) between consecutive
reasoning steps over time. When edit distance decays toward zero,
the agent is converging on a fixed point -- the "mirror loop" pattern.

This is the PRIMARY metric from the Mirror Loop paper
(DeVilling, 2025, arXiv:2510.21861), which found:

    "Mean informational change (delta I, measured via normalized edit
     distance) declined by 55% from early (0.193) to late (0.087)
     iterations in ungrounded runs, with consistent patterns across
     all three providers."

Key findings from the paper:
    - Edit distance decline is consistent across GPT-4o-mini, Claude 3
      Haiku, and Gemini 2.0 Flash (architecture-independent)
    - The decay is a structural property of autoregressive generation,
      not provider-specific alignment
    - A single grounding intervention at step 3 causes a +28% rebound
      in informational change
    - The pattern emerges after 6-7 steps of ungrounded reflection

This detector implements their "delta I" metric as a direct signal,
complementing the CUSUM detector (which uses embedding drift, a
related but different measure).

Advantages:
    - No embeddings needed (pure string operations)
    - Catches the TRAJECTORY toward fixation, not just the end state
    - Empirically validated across 3 model architectures
    - Detects "reformulation without progress" -- the core failure mode

Also incorporates ideas from:
    - REFRAIN (Sun et al., 2025, arXiv:2510.10103): Reflective
      redundancy detection via sliding-window analysis
"""

from __future__ import annotations

import re

from inferencebrake.detectors import BaseDetector
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


def _levenshtein_distance(s1: str, s2: str) -> int:
    """
    Compute Levenshtein edit distance between two strings.

    Uses the standard dynamic programming approach with O(min(m,n))
    space optimization (single-row DP).
    """
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))

    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Insertion, deletion, substitution
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]


def _normalized_edit_distance(text_a: str, text_b: str) -> float:
    """
    Normalized edit distance ∈ [0, 1].

    0.0 = identical texts
    1.0 = maximally different (no characters in common)

    This is the "delta I" metric from the Mirror Loop paper.
    """
    if not text_a and not text_b:
        return 0.0
    max_len = max(len(text_a), len(text_b))
    if max_len == 0:
        return 0.0

    # For very long texts, use word-level edit distance for performance
    # (character-level Levenshtein is O(n*m) and gets slow past ~3000 chars)
    if max_len > 3000:
        words_a = text_a.split()
        words_b = text_b.split()
        # Convert words to space-separated string for Levenshtein
        dist = _levenshtein_distance(' '.join(words_a), ' '.join(words_b))
        return min(dist / max(len(words_a), len(words_b), 1), 1.0)

    dist = _levenshtein_distance(text_a, text_b)
    return dist / max_len


class EditDistanceDecayDetector(BaseDetector):
    """
    Tracks normalized edit distance between consecutive steps.

    When the edit distance between successive reasoning steps
    monotonically decreases or stays near zero, the agent is
    approaching a semantic fixed point (the "mirror loop").

    This detector watches for two patterns:

    1. **Decay pattern**: Edit distance decreases over a window
       of N steps. This is the early warning -- the agent is
       converging even if it hasn't reached full repetition yet.

    2. **Stasis pattern**: Edit distance is consistently near
       zero for N steps. The agent is already at the fixed point.

    The detector maintains a sliding window of delta_I values
    and uses linear regression to detect the decay trend.
    """

    name = "editdist"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection:
            return self._safe_signal("Not enough history for edit distance analysis")

        # Normalize text for fair comparison
        current = _normalize(reasoning)

        # Get recent reasoning history
        window = min(
            getattr(config, "editdist_window", 6),
            session.step_count,
        )
        recent_texts = session.get_recent_reasoning(window)
        if not recent_texts:
            return self._safe_signal("No history available")

        recent_texts = [_normalize(t) for t in recent_texts]

        # Compute consecutive edit distances (delta_I series)
        # Include the distance from last history step to current
        delta_i_series = []
        for i in range(1, len(recent_texts)):
            d = _normalized_edit_distance(recent_texts[i - 1], recent_texts[i])
            delta_i_series.append(d)

        # Add current step's delta_I
        if recent_texts:
            current_delta = _normalized_edit_distance(recent_texts[-1], current)
            delta_i_series.append(current_delta)
        else:
            current_delta = 1.0

        if len(delta_i_series) < 3:
            return self._safe_signal(
                f"Need more steps for trend analysis (have {len(delta_i_series)})"
            )

        # Thresholds
        stasis_threshold = getattr(config, "editdist_stasis_threshold", 0.08)
        decay_rate_threshold = getattr(config, "editdist_decay_threshold", -0.03)

        # Analysis 1: Current delta_I (immediate signal)
        is_stasis = current_delta < stasis_threshold

        # Analysis 2: Trend detection (linear regression on delta_I series)
        trend = _compute_trend(delta_i_series)

        # Analysis 3: Check for consistent near-zero (stasis pattern)
        # Mirror Loop paper: "all below 0.087 in late iterations"
        recent_3 = delta_i_series[-3:]
        stasis_count = sum(1 for d in recent_3 if d < stasis_threshold)
        is_consistent_stasis = stasis_count >= 2

        # Analysis 4: Decay ratio -- how much has delta_I dropped from
        # its peak to current? (Paper found 55% decline)
        peak_delta = max(delta_i_series) if delta_i_series else 1.0
        if peak_delta > 0:
            decay_ratio = 1.0 - (current_delta / peak_delta)
        else:
            decay_ratio = 0.0

        # Decision logic
        # Strong signal: stasis + negative trend + high decay ratio
        if is_consistent_stasis and trend < decay_rate_threshold:
            confidence = min(
                0.5 + decay_ratio * 0.3 + abs(trend) * 2.0,
                1.0,
            )
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=confidence,
                score=current_delta,
                threshold_used=stasis_threshold,
                detail=(
                    f"Edit distance decay: current delta_I={current_delta:.3f} "
                    f"(threshold={stasis_threshold:.3f}). "
                    f"Trend: {trend:+.4f}/step. "
                    f"Decay from peak: {decay_ratio:.0%}. "
                    f"Agent approaching semantic fixed point (Mirror Loop)."
                ),
                metadata={
                    "current_delta_i": current_delta,
                    "delta_i_series": delta_i_series,
                    "trend": trend,
                    "decay_ratio": decay_ratio,
                    "stasis_count": stasis_count,
                    "peak_delta_i": peak_delta,
                },
            )

        # Warning: either stasis or strong negative trend
        if is_stasis or (trend < decay_rate_threshold and decay_ratio > 0.4):
            confidence = min(
                abs(trend) * 3.0 + (1.0 - current_delta) * 0.2,
                0.7,
            )
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=confidence,
                score=current_delta,
                threshold_used=stasis_threshold,
                detail=(
                    f"Edit distance declining: delta_I={current_delta:.3f}, "
                    f"trend={trend:+.4f}/step, decay={decay_ratio:.0%}. "
                    f"Possible convergence toward fixed point."
                ),
                metadata={
                    "current_delta_i": current_delta,
                    "trend": trend,
                    "decay_ratio": decay_ratio,
                },
            )

        return self._safe_signal(
            f"Edit distance healthy: delta_I={current_delta:.3f}, "
            f"trend={trend:+.4f}/step"
        )


def _normalize(text: str) -> str:
    """Normalize whitespace and case for fair comparison."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _compute_trend(values: list[float]) -> float:
    """Simple linear regression slope."""
    n = len(values)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2
    y_mean = sum(values) / n
    numerator = sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values))
    denominator = sum((i - x_mean) ** 2 for i in range(n))
    return numerator / denominator if denominator > 0 else 0.0
