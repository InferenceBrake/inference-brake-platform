"""
Entropy / Confidence Monitor.

Detects loops by monitoring the "information content" of each
reasoning step. When entropy collapses (agent becomes very
repetitive/predictable), it signals a loop.

IMPORTANT LIMITATION:
    The referenced papers (Sun 2026, Conformal Thinking) define
    "token-level entropy" as the logprob distribution over the LLM's
    vocabulary at generation time. That signal requires access to the
    model's output distribution (logprobs from the API).

    This detector receives already-generated text as a string. It
    approximates entropy via vocabulary diversity, sentence structure
    variation, and information density. This is a weaker signal than
    true generation entropy, and the accuracy figures from the papers
    (e.g., Sun's 60.7% -> 84.0%) do NOT apply to this text-based
    approximation.

    The detector is still useful as a complementary signal for
    detecting repetitive/low-information output, but should not be
    relied on as a primary detector.

Related work:
    - Reinforcement Inference (Sun, 2026, arXiv:2602.08520):
      Token-level entropy as a control signal. Requires logprobs.
    - Conformal Thinking (Wang et al., 2026, arXiv:2602.03814):
      Distribution-free risk control for reasoning budgets.
    - Kaiser et al. (2026, arXiv:2602.09805): Deterministic
      trace-quality measures (grounding, repetition, prompt-copying)
      separate degenerate looping from verbose-but-engaged reasoning.

This detector computes text-level entropy metrics (not token logits,
since we don't have access to the model's output distribution).
Uses vocabulary diversity, sentence structure variation, and
information density as proxy signals.
"""

from __future__ import annotations

import math
import re
from collections import Counter

from inferencebrake.detectors import BaseDetector
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


def _word_entropy(text: str) -> float:
    """
    Shannon entropy of the word distribution in text.
    Higher = more diverse vocabulary = more information.
    Lower = repetitive vocabulary = less information.
    """
    words = re.findall(r"\w+", text.lower())
    if len(words) < 2:
        return 0.0
    counts = Counter(words)
    total = len(words)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    # Normalize by max possible entropy for this text length
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return entropy / max_entropy if max_entropy > 0 else 0.0


def _vocabulary_diversity(text: str) -> float:
    """Type-token ratio: unique words / total words."""
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    return len(set(words)) / len(words)


def _structural_entropy(text: str) -> float:
    """
    Measures diversity of sentence structures.
    Uses sentence length distribution as a proxy.
    """
    sentences = re.split(r"[.!?\n]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) < 2:
        return 1.0  # Single sentence = can't measure structure
    lengths = [len(s.split()) for s in sentences]
    counts = Counter(lengths)
    total = len(lengths)
    entropy = 0.0
    for count in counts.values():
        p = count / total
        if p > 0:
            entropy -= p * math.log2(p)
    max_entropy = math.log2(len(counts)) if len(counts) > 1 else 1.0
    return entropy / max_entropy if max_entropy > 0 else 0.0


def _information_density(text: str) -> float:
    """
    Ratio of content words to total words.
    Low density = filler-heavy text = possible stalling.

    Inspired by Kaiser et al. (2026): grounding metric
    measures whether reasoning is anchored to the problem.
    """
    function_words = {
        "i",
        "me",
        "my",
        "we",
        "our",
        "you",
        "your",
        "he",
        "she",
        "it",
        "the",
        "a",
        "an",
        "this",
        "that",
        "these",
        "those",
        "is",
        "am",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "shall",
        "should",
        "may",
        "might",
        "can",
        "could",
        "and",
        "but",
        "or",
        "nor",
        "for",
        "so",
        "yet",
        "in",
        "on",
        "at",
        "to",
        "from",
        "by",
        "with",
        "of",
        "about",
        "if",
        "then",
        "else",
        "when",
        "while",
        "not",
        "no",
        "very",
        "really",
        "just",
        "also",
        "well",
        "now",
    }
    words = re.findall(r"\w+", text.lower())
    if not words:
        return 0.0
    content_words = [w for w in words if w not in function_words]
    return len(content_words) / len(words)


class EntropyDetector(BaseDetector):
    """
    Text-level entropy and information content monitor.

    Tracks multiple entropy-like signals across reasoning steps:
        1. Word entropy: vocabulary diversity within a step
        2. Cross-step entropy: how much new information each step adds
        3. Structural entropy: sentence structure variation
        4. Information density: content word ratio

    When these signals collapse (decreasing entropy trend),
    the agent is likely looping or stalling.
    """

    name = "entropy"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection:
            return self._safe_signal("Not enough history")

        # Compute entropy signals for current step
        current_word_ent = _word_entropy(reasoning)
        current_vocab_div = _vocabulary_diversity(reasoning)
        current_struct_ent = _structural_entropy(reasoning)
        current_info_density = _information_density(reasoning)

        # Composite entropy score (weighted average)
        current_score = (
            current_word_ent * 0.3
            + current_vocab_div * 0.2
            + current_struct_ent * 0.2
            + current_info_density * 0.3
        )

        # Track in session
        session.entropy_history.append(current_score)

        # Need at least 3 data points to detect a trend
        if len(session.entropy_history) < 3:
            return self._safe_signal(f"Entropy: {current_score:.3f}")

        # Get recent entropy history
        window = min(config.entropy_window, len(session.entropy_history))
        recent = session.entropy_history[-window:]

        # Compute trend: is entropy consistently decreasing?
        avg_entropy = sum(recent) / len(recent)
        entropy_trend = self._compute_trend(recent)

        # Cross-step vocabulary novelty: how many new words vs previous step
        novelty = self._compute_novelty(reasoning, session, config)

        # Decision logic
        collapse_threshold = config.entropy_collapse_threshold

        # Check for entropy collapse
        is_collapsed = current_score < collapse_threshold
        is_declining = entropy_trend < -0.05  # Negative trend
        is_low_novelty = novelty < 0.2  # Less than 20% new words
        is_stale = avg_entropy < collapse_threshold * 1.2

        # Strong signal: collapsed AND declining AND low novelty
        if is_collapsed and (is_declining or is_low_novelty):
            confidence = min(
                (collapse_threshold - current_score) / collapse_threshold + 0.5,
                1.0,
            )
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.ENTROPY_COLLAPSE,
                confidence=confidence,
                score=current_score,
                threshold_used=collapse_threshold,
                detail=(
                    f"Entropy collapsed: {current_score:.3f} < {collapse_threshold:.3f}. "
                    f"Trend: {entropy_trend:+.3f}, novelty: {novelty:.1%}. "
                    f"Agent producing low-information content."
                ),
                metadata={
                    "current_entropy": current_score,
                    "avg_entropy": avg_entropy,
                    "entropy_trend": entropy_trend,
                    "word_entropy": current_word_ent,
                    "vocab_diversity": current_vocab_div,
                    "structural_entropy": current_struct_ent,
                    "info_density": current_info_density,
                    "novelty": novelty,
                    "history": recent,
                },
            )

        # Warning: declining but not yet collapsed
        if (is_declining and is_stale) or (is_low_novelty and is_stale):
            confidence = min(abs(entropy_trend) * 3 + (1 - novelty) * 0.3, 0.7)
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.ENTROPY_COLLAPSE,
                confidence=confidence,
                score=current_score,
                threshold_used=collapse_threshold,
                detail=(
                    f"Entropy declining: {current_score:.3f}, "
                    f"trend: {entropy_trend:+.3f}, novelty: {novelty:.1%}"
                ),
                metadata={
                    "current_entropy": current_score,
                    "entropy_trend": entropy_trend,
                    "novelty": novelty,
                },
            )

        return self._safe_signal(
            f"Entropy healthy: {current_score:.3f}, trend: {entropy_trend:+.3f}"
        )

    @staticmethod
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

    @staticmethod
    def _compute_novelty(
        reasoning: str, session: SessionState, config: ThresholdConfig
    ) -> float:
        """
        Compute vocabulary novelty: fraction of words in current
        step that didn't appear in the previous step.
        """
        recent = session.get_recent_reasoning(1)
        if not recent:
            return 1.0
        prev_words = set(re.findall(r"\w+", recent[0].lower()))
        curr_words = set(re.findall(r"\w+", reasoning.lower()))
        if not curr_words:
            return 0.0
        new_words = curr_words - prev_words
        return len(new_words) / len(curr_words)
