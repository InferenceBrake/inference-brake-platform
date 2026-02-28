"""
Action / Tool Repetition Detector.

Detects when an agent calls the same tools or actions repeatedly
in patterns that indicate a loop. Goes beyond simple "same action
N times" to detect cyclic patterns.

Inspired by:
    - SMR (Lee et al., 2025, arXiv:2505.23059): State machine reasoning
      with explicit {Refine, Rerank, Stop} actions. Models reasoning
      as a state machine, achieving 74.4% token reduction.
    - GRU-Mem (Sheng et al., 2026, arXiv:2602.10560): RL-trained
      exit gates - memory only updates on new evidence, exits when
      sufficient evidence collected.

Detection patterns:
    1. Direct repeat: A, A, A, A (same action N times)
    2. Short cycle: A, B, A, B, A, B
    3. Long cycle: A, B, C, A, B, C
    4. Stutter cycle: A, A, B, A, A, B
"""

from __future__ import annotations

from inferencebrake.detectors import BaseDetector
from inferencebrake.types import (
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    SessionState,
    ThresholdConfig,
)


def _find_direct_repeat(actions: list[str], min_count: int) -> tuple[str, int] | None:
    """
    Find an action repeated consecutively >= min_count times.
    Returns (action, count) or None.
    """
    if not actions:
        return None
    current = actions[-1]
    count = 0
    for a in reversed(actions):
        if a == current:
            count += 1
        else:
            break
    if count >= min_count:
        return current, count
    return None


def _find_cycle(
    actions: list[str], min_len: int, max_len: int
) -> tuple[list[str], int] | None:
    """
    Find a repeating cycle of length [min_len, max_len] at the end
    of the action sequence.

    Returns (cycle_pattern, repeat_count) or None.

    Example: [A, B, C, A, B, C, A, B, C] -> ([A, B, C], 3)
    """
    if len(actions) < min_len * 2:
        return None

    for cycle_len in range(min_len, max_len + 1):
        if len(actions) < cycle_len * 2:
            continue

        candidate = actions[-cycle_len:]
        repeats = 1
        pos = len(actions) - cycle_len

        while pos >= cycle_len:
            window = actions[pos - cycle_len : pos]
            if window == candidate:
                repeats += 1
                pos -= cycle_len
            else:
                break

        if repeats >= 2:
            return candidate, repeats

    return None


def _find_stutter_cycle(
    actions: list[str], max_cycle: int
) -> tuple[list[str], int] | None:
    """
    Find cycles with internal repeats (stuttering).
    E.g., A, A, B, A, A, B -> stutter cycle [A, A, B] x 2

    This catches cases where direct repeat detection misses
    because the repetition has sub-patterns.
    """
    # Normalize consecutive duplicates
    if not actions:
        return None
    compressed = [actions[0]]
    counts = [1]
    for a in actions[1:]:
        if a == compressed[-1]:
            counts[-1] += 1
        else:
            compressed.append(a)
            counts.append(1)

    # Check if the compressed sequence has a cycle
    result = _find_cycle(compressed, 2, max_cycle)
    if result and result[1] >= 2:
        # Reconstruct the full pattern
        cycle, reps = result
        return cycle, reps

    return None


class ActionDetector(BaseDetector):
    """
    Detects repetitive action/tool call patterns.

    Works with action labels extracted from agent traces.
    Actions can be tool names, function calls, or any
    categorical labels from the agent's execution.
    """

    name = "action"

    def detect(
        self,
        reasoning: str,
        session: SessionState,
        config: ThresholdConfig,
        actions: list[str] | None = None,
        **kwargs,
    ) -> DetectionSignal:
        # Merge any new actions into session state
        if actions:
            session.action_sequence.extend(actions)

        seq = session.action_sequence
        if len(seq) < config.action_repeat_limit:
            return self._safe_signal("Not enough actions")

        # Check 1: Direct repeat (A, A, A, A)
        repeat = _find_direct_repeat(seq, config.action_repeat_limit)
        if repeat:
            action, count = repeat
            confidence = min((count - config.action_repeat_limit + 1) / 3, 1.0)
            return DetectionSignal(
                detector_name=self.name,
                verdict=DetectorVerdict.LOOP_DETECTED,
                loop_type=LoopType.ACTION_REPETITION,
                confidence=confidence,
                score=count,
                threshold_used=config.action_repeat_limit,
                detail=f"Action '{action}' repeated {count} times consecutively",
                metadata={"action": action, "count": count, "pattern": "direct_repeat"},
            )

        # Check 2: Short cycle (A, B, A, B)
        cycle = _find_cycle(
            seq, config.action_cycle_min_length, config.action_cycle_max_length
        )
        if cycle:
            pattern, repeats = cycle
            if repeats >= 2:
                confidence = min((repeats - 1) / 3, 1.0)
                pattern_str = " -> ".join(pattern)
                return DetectionSignal(
                    detector_name=self.name,
                    verdict=DetectorVerdict.LOOP_DETECTED,
                    loop_type=LoopType.STRUCTURAL_LOOP,
                    confidence=confidence,
                    score=repeats,
                    threshold_used=2,
                    detail=f"Cyclic pattern [{pattern_str}] repeated {repeats} times",
                    metadata={
                        "cycle": pattern,
                        "repeats": repeats,
                        "pattern": "cycle",
                    },
                )

        # Check 3: Stutter cycle (A, A, B, A, A, B)
        stutter = _find_stutter_cycle(seq, config.action_cycle_max_length)
        if stutter:
            pattern, repeats = stutter
            if repeats >= 2:
                confidence = min((repeats - 1) / 4, 0.8)
                pattern_str = " -> ".join(pattern)
                return DetectionSignal(
                    detector_name=self.name,
                    verdict=DetectorVerdict.WARNING,
                    loop_type=LoopType.STRUCTURAL_LOOP,
                    confidence=confidence,
                    score=repeats,
                    threshold_used=2,
                    detail=f"Stutter cycle [{pattern_str}] repeated {repeats} times",
                    metadata={
                        "cycle": pattern,
                        "repeats": repeats,
                        "pattern": "stutter_cycle",
                    },
                )

        # No pattern detected
        return self._safe_signal(f"No action loops ({len(seq)} actions recorded)")
