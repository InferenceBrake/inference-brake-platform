"""
Core types for the InferenceBrake detection engine.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class LoopType(Enum):
    """Classification of detected loop patterns."""

    NONE = "none"
    EXACT_REPETITION = "exact_repetition"  # Verbatim text repeat
    NGRAM_REPETITION = "ngram_repetition"  # N-gram overlap above threshold
    SEMANTIC_SIMILARITY = "semantic_similarity"  # Embedding cosine similarity
    CUSUM_STAGNATION = "cusum_stagnation"  # Cumulative drift below threshold
    ENTROPY_COLLAPSE = "entropy_collapse"  # Output distribution collapsed
    ACTION_REPETITION = "action_repetition"  # Same tool/action repeated
    STRUCTURAL_LOOP = "structural_loop"  # Cyclic pattern in action sequence
    PARAPHRASE_LOOP = "paraphrase_loop"  # Same idea rephrased repeatedly
    PROMPT_ECHO = "prompt_echo"  # Model echoing/copying the prompt


class DetectorVerdict(Enum):
    """Individual detector's verdict."""

    SAFE = "safe"
    WARNING = "warning"
    LOOP_DETECTED = "loop_detected"


@dataclass
class DetectionSignal:
    """Signal from a single detector."""

    detector_name: str
    verdict: DetectorVerdict
    loop_type: LoopType
    confidence: float  # 0.0 to 1.0 - how confident the detector is
    score: float  # Raw score (e.g., similarity value, n-gram overlap)
    threshold_used: float  # What threshold triggered this
    detail: str = ""  # Human-readable explanation
    metadata: dict[str, Any] = field(default_factory=dict)
    latency_ms: float = 0.0  # How long this detector took


@dataclass
class DetectionResult:
    """
    Aggregated result from the full detection pipeline.

    This is the primary output consumers interact with.
    """

    should_stop: bool
    action: str  # "KILL" or "PROCEED"
    loop_detected: bool
    loop_type: LoopType
    overall_confidence: float  # Weighted confidence across detectors
    signals: list[DetectionSignal]  # Individual detector signals
    total_latency_ms: float
    step_number: int
    session_id: str
    reasoning_preview: str = ""  # First 200 chars of the reasoning
    correction_hint: str = ""  # Suggested hint to break the loop
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def status(self) -> str:
        if self.should_stop:
            return "danger"
        if any(s.verdict == DetectorVerdict.WARNING for s in self.signals):
            return "warning"
        return "safe"

    @property
    def max_similarity(self) -> float:
        """Backward-compatible: return highest similarity score."""
        sim_signals = [
            s for s in self.signals if s.loop_type == LoopType.SEMANTIC_SIMILARITY
        ]
        return max((s.score for s in sim_signals), default=0.0)


@dataclass
class StepRecord:
    """A single reasoning step stored in session history."""

    step_number: int
    reasoning: str
    embedding: Optional[list[float]] = None
    actions: list[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    token_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SessionState:
    """
    In-memory state for a reasoning session.

    Tracks history, embeddings, and running statistics
    needed by all detectors.
    """

    session_id: str
    steps: list[StepRecord] = field(default_factory=list)
    cusum_value: float = 0.0
    entropy_history: list[float] = field(default_factory=list)
    action_sequence: list[str] = field(default_factory=list)
    total_tokens: int = 0
    created_at: float = field(default_factory=time.time)

    @property
    def step_count(self) -> int:
        return len(self.steps)

    def add_step(self, step: StepRecord) -> None:
        self.steps.append(step)
        self.total_tokens += step.token_count
        self.action_sequence.extend(step.actions)

    def get_recent_steps(self, n: int) -> list[StepRecord]:
        return self.steps[-n:] if n < len(self.steps) else self.steps

    def get_recent_reasoning(self, n: int) -> list[str]:
        return [s.reasoning for s in self.get_recent_steps(n)]

    def get_recent_embeddings(self, n: int) -> list[list[float]]:
        steps = self.get_recent_steps(n)
        return [s.embedding for s in steps if s.embedding is not None]


@dataclass
class ThresholdConfig:
    """
    Configurable thresholds for detection.

    Supports adaptive adjustment based on task type
    and user sensitivity preference.
    """

    # Semantic similarity
    similarity_threshold: float = 0.85
    similarity_window: int = 10  # How many past steps to compare

    # N-gram repetition
    ngram_size: int = 3
    ngram_overlap_threshold: float = 0.50
    ngram_window: int = 5

    # CUSUM drift
    cusum_drift_threshold: float = 0.05
    cusum_stagnation_limit: float = 0.1
    cusum_window: int = 10

    # Entropy
    entropy_collapse_threshold: float = 0.3
    entropy_window: int = 5

    # Action repetition
    action_repeat_limit: int = 3
    action_cycle_min_length: int = 2
    action_cycle_max_length: int = 5

    # Compression (NCD) - fast, no embeddings needed
    compression_threshold: float = 0.80  # NCD similarity threshold
    compression_window: int = 5

    # Edit Distance Decay - fast, no embeddings needed
    editdist_stasis_threshold: float = 0.08  # delta_I below this = stasis
    editdist_decay_threshold: float = -0.03  # negative trend = decay
    editdist_window: int = 6

    # Pipeline
    min_steps_before_detection: int = 2  # Don't flag until N steps
    voting_threshold: float = 0.5  # Fraction of detectors needed

    # Sensitivity presets
    @classmethod
    def strict(cls) -> "ThresholdConfig":
        return cls(
            similarity_threshold=0.75,
            ngram_overlap_threshold=0.40,
            cusum_stagnation_limit=0.15,
            entropy_collapse_threshold=0.35,
            action_repeat_limit=2,
            compression_threshold=0.75,
            editdist_stasis_threshold=0.12,
            editdist_decay_threshold=-0.02,
            voting_threshold=0.3,
        )

    @classmethod
    def balanced(cls) -> "ThresholdConfig":
        return cls()  # defaults

    @classmethod
    def lenient(cls) -> "ThresholdConfig":
        return cls(
            similarity_threshold=0.92,
            ngram_overlap_threshold=0.65,
            cusum_stagnation_limit=0.05,
            entropy_collapse_threshold=0.20,
            action_repeat_limit=5,
            compression_threshold=0.85,
            editdist_stasis_threshold=0.05,
            editdist_decay_threshold=-0.04,
            voting_threshold=0.7,
        )

    @classmethod
    def for_task(
        cls, task_type: str, sensitivity: str = "balanced"
    ) -> "ThresholdConfig":
        """
        Create thresholds adapted to task type.

        Informed by Kaiser et al. (2026): different task types have
        inherently different verbalization overhead and repetition patterns.
        """
        base = {
            "strict": cls.strict,
            "balanced": cls.balanced,
            "lenient": cls.lenient,
        }.get(sensitivity, cls.balanced)()

        adjustments = {
            "code_generation": {
                "similarity_threshold": 0.05,
                "ngram_overlap_threshold": 0.10,
            },
            "creative_writing": {
                "similarity_threshold": 0.03,
                "ngram_overlap_threshold": 0.05,
            },
            "research": {"similarity_threshold": 0.02, "ngram_overlap_threshold": 0.03},
            "customer_service": {
                "similarity_threshold": -0.05,
                "ngram_overlap_threshold": -0.05,
            },
        }

        if task_type in adjustments:
            for attr, delta in adjustments[task_type].items():
                current = getattr(base, attr)
                setattr(base, attr, max(0.50, min(0.98, current + delta)))

        return base


@dataclass
class PipelineConfig:
    """Configuration for the detection pipeline."""

    thresholds: ThresholdConfig = field(default_factory=ThresholdConfig)
    enabled_detectors: list[str] = field(
        default_factory=lambda: [
            "ngram", "semantic", "cusum", "entropy", "action",
            "compression", "editdist",  # Fast, no embeddings needed
        ]
    )
    # Weights for voting (detector_name -> weight)
    detector_weights: dict[str, float] = field(
        default_factory=lambda: {
            "ngram": 1.0,
            "semantic": 1.5,  # Semantic gets higher weight (needs embeddings)
            "cusum": 1.2,
            "entropy": 0.8,
            "action": 1.0,
            "compression": 1.0,  # NCD - fast, no embeddings
            "editdist": 1.0,  # Edit distance decay - fast, no embeddings
        }
    )
    enable_resolution_hints: bool = True
    max_history_steps: int = 100  # Max steps to keep in memory per session
    chunk_size: int = 2000  # Token chunk size for long content
    chunk_overlap: int = 200  # Overlap between chunks
