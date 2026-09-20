"""
Token Repetition Detector.

Detects exact repeated token spans, both within a single response and against
recent steps. This is the failure mode Liquid AI's Antidoom targets at training
time ("a repeated span begins") and what OpenRouter's doom-loop detector catches
for repeated tool calls and text. Doing it here makes the signal available at
runtime, across any framework, next to the semantic detectors.

Method:
    - Longest repeated span (LRS) within the current reasoning, via O(n^2) DP
      over tokens. A span that repeats inside one response is the classic
      degenerate-repetition pattern.
    - Longest common span (LCS) between the current reasoning and each of the
      last N steps. Catches a phrase carried verbatim across turns.

The detector votes when the best span length reaches ``token_repeat_min_span``
tokens. Longer spans and more occurrences raise confidence.

Advantages:
    - No embeddings needed (pure string operations)
    - Catches exact repeats that semantic/edit-distance detectors can miss when
      surrounding text differs enough
    - Directly mirrors the training-time failure mode Antidoom describes
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

_WORD_RE = re.compile(r"[a-z0-9']+")


def _tokenize(text: str) -> list[str]:
    """Lowercase word tokens, punctuation stripped."""
    return _WORD_RE.findall(text.lower())


def _longest_repeated_span(tokens: list[str]) -> tuple[int, int, int]:
    """
    Longest repeated contiguous span within ``tokens``.

    Returns (length, start_index, occurrences). Occurrences counts
    non-overlapping repeats of the winning span.
    """
    n = len(tokens)
    if n < 2:
        return 0, -1, 0

    best_len = 0
    best_start = -1
    prev = [0] * (n + 1)

    for i in range(1, n + 1):
        curr = [0] * (n + 1)
        ti = tokens[i - 1]
        for j in range(1, i):
            if ti == tokens[j - 1]:
                length = prev[j - 1] + 1
                curr[j] = length
                if length > best_len:
                    best_len = length
                    best_start = i - length
        prev = curr

    if best_len == 0:
        return 0, -1, 0

    span = tokens[best_start:best_start + best_len]
    occurrences = 0
    i = 0
    while i <= n - best_len:
        if tokens[i:i + best_len] == span:
            occurrences += 1
            i += best_len
        else:
            i += 1

    return best_len, best_start, occurrences


def _longest_common_span(a: list[str], b: list[str]) -> int:
    """Length of the longest common contiguous span between two token lists."""
    if not a or not b:
        return 0
    if len(b) > len(a):
        a, b = b, a

    best = 0
    prev = [0] * (len(b) + 1)
    for i in range(1, len(a) + 1):
        curr = [0] * (len(b) + 1)
        ai = a[i - 1]
        for j in range(1, len(b) + 1):
            if ai == b[j - 1]:
                length = prev[j - 1] + 1
                curr[j] = length
                if length > best:
                    best = length
        prev = curr
    return best


class TokenRepeatDetector(BaseDetector):
    """Detects exact repeated token spans within and across steps."""

    name = "token_repeat"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        **kwargs,
    ) -> DetectionSignal:
        max_tokens = getattr(config, "token_repeat_max_tokens", 1500)
        tokens = _tokenize(reasoning)[:max_tokens]
        if len(tokens) < 3:
            return self._safe_signal("Too few tokens for repetition analysis")

        min_span = getattr(config, "token_repeat_min_span", 6)
        warn_span = getattr(config, "token_repeat_warn_span", 4)

        intra_len, start, occurrences = _longest_repeated_span(tokens)
        intra_ratio = intra_len / len(tokens) if tokens else 0.0

        window = getattr(config, "token_repeat_window", 5)
        cross_len = 0
        for prev_text in session.get_recent_reasoning(window):
            cross_len = max(cross_len, _longest_common_span(tokens, _tokenize(prev_text)[:max_tokens]))

        best_len = max(intra_len, cross_len)
        source = "intra" if intra_len >= cross_len else "cross"
        span_preview = ""
        if source == "intra" and start >= 0:
            span_preview = " ".join(tokens[start:start + intra_len])

        metadata = {
            "span_len": best_len,
            "span_preview": span_preview,
            "occurrences": occurrences,
            "intra_span": intra_len,
            "cross_span": cross_len,
            "intra_ratio": round(intra_ratio, 4),
            "token_count": len(tokens),
            "source": source,
        }

        if best_len >= min_span:
            confidence = min(
                0.55 + (best_len - min_span) * 0.05 + max(0, occurrences - 2) * 0.1,
                1.0,
            )
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.EXACT_REPETITION,
                confidence=confidence,
                score=float(best_len),
                threshold_used=float(min_span),
                detail=(
                    f"Repeated {best_len}-token span ({source}). "
                    f"Occurrences: {occurrences}. "
                    f"Span: '{span_preview[:80]}'"
                ),
                metadata=metadata,
            )

        if best_len >= warn_span:
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.WARNING,
                loop_type=LoopType.EXACT_REPETITION,
                confidence=min(0.3 + (best_len - warn_span) * 0.05, 0.6),
                score=float(best_len),
                threshold_used=float(warn_span),
                detail=f"Short repeated span ({best_len} tokens, {source})",
                metadata=metadata,
            )

        return self._safe_signal(
            f"No significant repetition (longest span {best_len} tokens)"
        )
