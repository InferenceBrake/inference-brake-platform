"""
N-gram Repetition Detector.

Inspired by DeRep (Liu et al., 2025 - arXiv:2504.12608):
    - 20-pattern repetition taxonomy
    - Rule-based detection achieves 91%+ accuracy
    - No ML required for the repetition detection layer

    Note: DeRep was developed for *code generation* repetition,
    not agent reasoning loops. The pattern taxonomy (rep-line,
    sim-line, rep-char, block, structural) transfers well
    conceptually, but the accuracy figures are not directly
    comparable to reasoning trace detection.

Detects:
    - Exact line/sentence repetition
    - N-gram overlap above threshold
    - Paraphrase patterns (same structure, swapped words)
    - Block-level repetition (multi-sentence repeats)

This is the fastest detector (no API calls, pure string ops).
Should run first in the pipeline as a fast reject filter.
"""

from __future__ import annotations

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


def _normalize(text: str) -> str:
    """Lowercase, collapse whitespace, strip punctuation for comparison."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", "", text)
    text = re.sub(r"\s+", " ", text)
    return text


def _extract_ngrams(text: str, n: int) -> list[tuple[str, ...]]:
    """Extract word-level n-grams from text."""
    words = _normalize(text).split()
    if len(words) < n:
        return [tuple(words)] if words else []
    return [tuple(words[i : i + n]) for i in range(len(words) - n + 1)]


def _extract_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    sentences = re.split(r"[.!?\n]+", text)
    return [s.strip() for s in sentences if s.strip() and len(s.strip()) > 10]


class NgramDetector(BaseDetector):
    """
    Multi-pattern repetition detector using n-gram analysis.

    Detection patterns (subset of DeRep's 20-pattern taxonomy):
        1. Exact sentence repetition (rep-line)
        2. N-gram overlap ratio (sim-line)
        3. Character-level substring repetition (rep-char)
        4. Block repetition (multi-sentence identical blocks)
        5. Structural repetition (same sentence template, different fillers)
    """

    name = "ngram"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        if session.step_count < config.min_steps_before_detection:
            return self._safe_signal("Not enough history")

        recent = session.get_recent_reasoning(config.ngram_window)
        if not recent:
            return self._safe_signal("No history")

        # Run all pattern checks and take the worst signal
        checks = [
            self._check_exact_repetition(reasoning, recent),
            self._check_ngram_overlap(
                reasoning, recent, config.ngram_size, config.ngram_overlap_threshold
            ),
            self._check_block_repetition(reasoning, recent),
            self._check_structural_repetition(reasoning, recent),
        ]

        # Return the check with highest confidence
        worst = max(checks, key=lambda s: s.confidence)
        return worst

    def _check_exact_repetition(
        self, reasoning: str, history: list[str]
    ) -> DetectionSignal:
        """Pattern 1: Exact sentence repetition (rep-line)."""
        current_sentences = set(_extract_sentences(reasoning))
        if not current_sentences:
            return self._safe_signal()

        for past in history:
            past_sentences = set(_extract_sentences(past))
            overlap = current_sentences & past_sentences
            if overlap:
                ratio = len(overlap) / max(len(current_sentences), 1)
                if ratio >= 0.5:
                    return DetectionSignal(
                        detector_name=self.name,
                        verdict=DetectorVerdict.LOOP_DETECTED,
                        loop_type=LoopType.EXACT_REPETITION,
                        confidence=min(ratio, 1.0),
                        score=ratio,
                        threshold_used=0.5,
                        detail=f"{len(overlap)} sentences repeated verbatim",
                        metadata={"repeated_sentences": list(overlap)[:3]},
                    )
                elif ratio >= 0.3:
                    return DetectionSignal(
                        detector_name=self.name,
                        verdict=DetectorVerdict.WARNING,
                        loop_type=LoopType.EXACT_REPETITION,
                        confidence=ratio * 0.8,
                        score=ratio,
                        threshold_used=0.3,
                        detail=f"{len(overlap)} sentences partially repeated",
                    )

        return self._safe_signal()

    def _check_ngram_overlap(
        self,
        reasoning: str,
        history: list[str],
        n: int,
        threshold: float,
    ) -> DetectionSignal:
        """Pattern 2: N-gram overlap ratio (sim-line)."""
        current_ngrams = Counter(_extract_ngrams(reasoning, n))
        if not current_ngrams:
            return self._safe_signal()

        max_overlap = 0.0
        for past in history:
            past_ngrams = Counter(_extract_ngrams(past, n))
            if not past_ngrams:
                continue

            # Jaccard-like overlap: intersection / union
            intersection = sum((current_ngrams & past_ngrams).values())
            union = sum((current_ngrams | past_ngrams).values())
            overlap = intersection / max(union, 1)
            max_overlap = max(max_overlap, overlap)

        if max_overlap >= threshold:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.NGRAM_REPETITION,
                confidence=min(max_overlap, 1.0),
                score=max_overlap,
                threshold_used=threshold,
                detail=f"{n}-gram overlap: {max_overlap:.1%} (threshold: {threshold:.1%})",
            )
        elif max_overlap >= threshold * 0.7:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.NGRAM_REPETITION,
                confidence=max_overlap * 0.7,
                score=max_overlap,
                threshold_used=threshold,
                detail=f"{n}-gram overlap approaching threshold: {max_overlap:.1%}",
            )

        return self._safe_signal(f"{n}-gram overlap: {max_overlap:.1%}")

    def _check_block_repetition(
        self, reasoning: str, history: list[str]
    ) -> DetectionSignal:
        """
        Pattern 4: Block repetition.
        Detects when multiple consecutive sentences are repeated as a block.
        """
        current_sentences = _extract_sentences(reasoning)
        if len(current_sentences) < 2:
            return self._safe_signal()

        # Build 2-sentence blocks from current
        current_blocks = set()
        for i in range(len(current_sentences) - 1):
            block = (
                _normalize(current_sentences[i])
                + " | "
                + _normalize(current_sentences[i + 1])
            )
            current_blocks.add(block)

        for past in history:
            past_sentences = _extract_sentences(past)
            for i in range(len(past_sentences) - 1):
                block = (
                    _normalize(past_sentences[i])
                    + " | "
                    + _normalize(past_sentences[i + 1])
                )
                if block in current_blocks:
                    return DetectionSignal(
                        detector_name=self.name,
                        verdict=DetectorVerdict.LOOP_DETECTED,
                        loop_type=LoopType.EXACT_REPETITION,
                        confidence=0.95,
                        score=1.0,
                        threshold_used=1.0,
                        detail="Multi-sentence block repeated verbatim",
                    )

        return self._safe_signal()

    def _check_structural_repetition(
        self, reasoning: str, history: list[str]
    ) -> DetectionSignal:
        """
        Pattern 5: Structural repetition.
        Detects when the sentence template is the same but fillers change.
        E.g.: "I should check the weather" -> "I should check the news"
              "Let me search for X" -> "Let me search for Y"
        
        Threshold raised to 0.5 with minimum 6 steps to reduce false positives
        on short traces with similar structure.
        """

        # Minimum step guard: only run structural pattern matching after 6 steps
        # to avoid false positives on short traces
        total_history_steps = len(history)
        if total_history_steps < 6:
            return self._safe_signal(f"History too short for structural check ({total_history_steps} < 6)")

        def _to_template(text: str) -> str:
            """Replace content words with placeholders, keep function words."""
            function_words = {
                "i",
                "me",
                "my",
                "we",
                "our",
                "you",
                "your",
                "it",
                "its",
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
                "let",
                "need",
                "want",
                "try",
                "should",
                "must",
            }
            words = _normalize(text).split()
            return " ".join(w if w in function_words else "_" for w in words)

        current_sentences = _extract_sentences(reasoning)
        current_templates = [_to_template(s) for s in current_sentences]

        template_matches = 0
        total_comparisons = 0

        for past in history:
            past_sentences = _extract_sentences(past)
            past_templates = [_to_template(s) for s in past_sentences]

            for ct in current_templates:
                for pt in past_templates:
                    total_comparisons += 1
                    if ct == pt and len(ct.split()) >= 4:
                        template_matches += 1

        if total_comparisons == 0:
            return self._safe_signal()

        match_ratio = template_matches / total_comparisons
        # Threshold raised from 0.3 to 0.5 to reduce false positives
        if match_ratio >= 0.5:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=min(match_ratio * 1.2, 1.0),
                score=match_ratio,
                threshold_used=0.5,
                detail=f"Structural repetition: {template_matches} template matches across steps",
            )
        elif match_ratio >= 0.25:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.PARAPHRASE_LOOP,
                confidence=match_ratio,
                score=match_ratio,
                threshold_used=0.15,
                detail=f"Possible paraphrase loop: {template_matches} template matches",
            )

        return self._safe_signal()
