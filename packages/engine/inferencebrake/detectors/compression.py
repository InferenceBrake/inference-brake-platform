"""
Normalized Compression Distance (NCD) Detector.

Uses information-theoretic compression to detect repetitive reasoning
without requiring embeddings. Two texts that compress well together
(relative to individually) are informationally similar.

Theory:
    NCD(x,y) = (C(x+y) - min(C(x), C(y))) / max(C(x), C(y))

    Where C(x) is the compressed length of x. NCD ∈ [0, 1+ε]:
        0.0 = identical information content
        1.0 = maximally different information content

    This is a universal similarity metric derived from Kolmogorov
    complexity (Li et al., 2004; Cilibrasi & Vitányi, 2005).

Advantages over embedding similarity:
    - Zero cost: no model inference needed
    - Catches structural repetition that n-gram overlap misses
    - Works on any text length without chunking
    - Language-agnostic (works on code, logs, JSON, etc.)

Advantages over n-gram overlap:
    - Captures long-range dependencies (repeated paragraphs, blocks)
    - Handles insertions/deletions gracefully
    - Not sensitive to word order within repeated segments

Related work:
    - Li et al. (2004): "The Similarity Metric" -- foundational NCD paper
    - Cilibrasi & Vitányi (2005): "Clustering by Compression"
    - Bennett et al. (1998): "Information Distance" -- theoretical basis
    - DeRep (Liu et al., 2025): block-level repetition detection
      (NCD naturally captures this pattern class)
"""

from __future__ import annotations

import re
import zlib

from inferencebrake.detectors import BaseDetector
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


def _compressed_size(text: str) -> int:
    """Get compressed size of text using zlib (fast, good ratio)."""
    return len(zlib.compress(text.encode("utf-8"), level=6))


def _ncd(text_a: str, text_b: str) -> float:
    """
    Normalized Compression Distance between two texts.

    Returns value in [0, ~1]:
        0.0 = identical information content
        1.0 = maximally different
    """
    if not text_a or not text_b:
        return 1.0

    c_a = _compressed_size(text_a)
    c_b = _compressed_size(text_b)
    c_ab = _compressed_size(text_a + text_b)

    denominator = max(c_a, c_b)
    if denominator == 0:
        return 0.0

    ncd = (c_ab - min(c_a, c_b)) / denominator
    return max(0.0, min(ncd, 1.0))


def _ncd_similarity(text_a: str, text_b: str) -> float:
    """Convert NCD distance to similarity (1 - NCD)."""
    return 1.0 - _ncd(text_a, text_b)


class CompressionDetector(BaseDetector):
    """
    Compression-based repetition detector.

    Compares the current reasoning step against recent history
    using Normalized Compression Distance. When NCD is low
    (high compression similarity), the agent is producing
    informationally redundant content.

    This detector is:
        - Fast: ~0.1ms per comparison (zlib is C-optimized)
        - Free: no model inference, no API calls
        - Robust: catches structural repetition, block copies,
          and paraphrases that share information content

    Detection strategy:
        1. Pairwise NCD against recent steps (like semantic detector)
        2. Cumulative NCD: compress current step against concatenated
           recent history -- if the step adds no new information to
           the history, it compresses away almost entirely
    """

    name = "compression"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection:
            return self._safe_signal("Not enough history for compression analysis")

        # Normalize whitespace for fair comparison
        current = _normalize(reasoning)
        if len(current) < 20:
            return self._safe_signal("Text too short for compression analysis")

        # Get recent reasoning history
        window = min(
            getattr(config, "compression_window", 5),
            session.step_count,
        )
        recent_texts = session.get_recent_reasoning(window)
        if not recent_texts:
            return self._safe_signal("No history available")

        recent_texts = [_normalize(t) for t in recent_texts]

        # Strategy 1: Pairwise NCD against each recent step
        pairwise_sims = []
        for prev_text in recent_texts:
            if len(prev_text) < 20:
                continue
            sim = _ncd_similarity(current, prev_text)
            pairwise_sims.append(sim)

        max_pairwise = max(pairwise_sims) if pairwise_sims else 0.0

        # Strategy 2: Cumulative NCD -- does this step add information
        # to the recent history as a whole?
        history_concat = "\n".join(recent_texts)
        if len(history_concat) >= 20:
            # Measure how much new information the current step adds
            c_history = _compressed_size(history_concat)
            c_combined = _compressed_size(history_concat + "\n" + current)
            c_current = _compressed_size(current)

            # Information gain: how much the combined compressed size
            # grows relative to just the current step's compressed size.
            # If gain ≈ 0, the current step is fully redundant.
            if c_current > 0:
                info_gain = (c_combined - c_history) / c_current
            else:
                info_gain = 1.0
        else:
            info_gain = 1.0

        # Thresholds
        ncd_threshold = getattr(config, "compression_threshold", 0.80)

        # Decision logic
        is_pairwise_high = max_pairwise >= ncd_threshold
        is_redundant = info_gain < 0.3  # Less than 30% new information

        if is_pairwise_high and is_redundant:
            confidence = min(
                (max_pairwise - ncd_threshold) / (1.0 - ncd_threshold) + 0.5,
                1.0,
            )
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=confidence,
                score=max_pairwise,
                threshold_used=ncd_threshold,
                detail=(
                    f"Compression similarity {max_pairwise:.3f} >= {ncd_threshold:.3f}. "
                    f"Information gain: {info_gain:.1%}. "
                    f"Step is informationally redundant with recent history."
                ),
                metadata={
                    "max_pairwise_ncd_sim": max_pairwise,
                    "all_pairwise_sims": pairwise_sims,
                    "info_gain": info_gain,
                    "window": window,
                },
            )

        if is_pairwise_high or is_redundant:
            confidence = min(max_pairwise * 0.6 + (1.0 - info_gain) * 0.3, 0.7)
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=confidence,
                score=max_pairwise,
                threshold_used=ncd_threshold,
                detail=(
                    f"Compression warning: similarity={max_pairwise:.3f}, "
                    f"info_gain={info_gain:.1%}. Possible redundancy."
                ),
                metadata={
                    "max_pairwise_ncd_sim": max_pairwise,
                    "info_gain": info_gain,
                },
            )

        return self._safe_signal(
            f"Compression healthy: sim={max_pairwise:.3f}, gain={info_gain:.1%}"
        )


def _normalize(text: str) -> str:
    """Normalize whitespace and case for fair compression comparison."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return text
