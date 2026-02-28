"""
Multi-layer Detection Pipeline.

Orchestrates all detectors, manages session state, and produces
aggregated detection results using weighted voting.

Architecture:
    1. Pre-process: chunk long content, extract actions
    2. Fast detectors first: ngram, action (no API calls)
    3. Slow detectors: semantic, cusum (need embeddings)
    4. Aggregate: weighted voting across all signals
    5. Resolve: generate correction hints if loop detected

The pipeline supports short-circuit evaluation: if a fast
detector has high confidence, slow detectors can be skipped.

Voting system inspired by ensemble methods:
    - Each detector produces a signal with confidence [0, 1]
    - Signals are weighted by detector reliability
    - Final decision uses configurable threshold
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from inferencebrake.types import (
    DetectionResult,
    DetectionSignal,
    DetectorVerdict,
    LoopType,
    PipelineConfig,
    SessionState,
    StepRecord,
    ThresholdConfig,
)
from inferencebrake.detectors import BaseDetector
from inferencebrake.detectors.ngram import NgramDetector
from inferencebrake.detectors.semantic import SemanticDetector
from inferencebrake.detectors.cusum import CUSUMDetector
from inferencebrake.detectors.entropy import EntropyDetector
from inferencebrake.detectors.action import ActionDetector
from inferencebrake.detectors.compression import CompressionDetector
from inferencebrake.detectors.editdist import EditDistanceDecayDetector
from inferencebrake.content import LongContentHandler
from inferencebrake.resolution import LoopResolver


class DetectionPipeline:
    """
    Multi-layer loop detection pipeline.

    Usage:
        pipeline = DetectionPipeline()
        result = pipeline.check("session_123", "I should check the weather...")
        if result.should_stop:
            print(f"Loop detected: {result.loop_type}")
    """

    def __init__(
        self,
        config: PipelineConfig | None = None,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ):
        self.config = config or PipelineConfig()
        self._embedding_fn = embedding_fn
        self._sessions: dict[str, SessionState] = {}
        self._content_handler = LongContentHandler(
            chunk_size=self.config.chunk_size,
            overlap=self.config.chunk_overlap,
        )
        self._resolver = LoopResolver()

        # Initialize detectors
        self._detectors: dict[str, BaseDetector] = {}
        for name in self.config.enabled_detectors:
            if name == "ngram":
                self._detectors[name] = NgramDetector()
            elif name == "semantic":
                self._detectors[name] = SemanticDetector(embedding_fn=embedding_fn)
            elif name == "cusum":
                self._detectors[name] = CUSUMDetector()
            elif name == "entropy":
                self._detectors[name] = EntropyDetector()
            elif name == "action":
                self._detectors[name] = ActionDetector()
            elif name == "compression":
                self._detectors[name] = CompressionDetector()
            elif name == "editdist":
                self._detectors[name] = EditDistanceDecayDetector()

    def get_session(self, session_id: str) -> SessionState:
        """Get or create session state."""
        if session_id not in self._sessions:
            self._sessions[session_id] = SessionState(session_id=session_id)
        return self._sessions[session_id]

    def clear_session(self, session_id: str) -> None:
        """Remove session state."""
        self._sessions.pop(session_id, None)

    def check(
        self,
        session_id: str,
        reasoning: str,
        embedding: list[float] | None = None,
        actions: list[str] | None = None,
        metadata: dict | None = None,
    ) -> DetectionResult:
        """
        Run the full detection pipeline on a reasoning step.

        Args:
            session_id: Unique session identifier.
            reasoning: The reasoning text to check.
            embedding: Pre-computed embedding (optional).
            actions: Action/tool labels for this step (optional).
            metadata: Additional metadata to store.

        Returns:
            DetectionResult with aggregated verdict.
        """
        t0 = time.perf_counter()
        session = self.get_session(session_id)
        thresholds = self.config.thresholds

        # Pre-process: handle long content
        processed_reasoning = self._content_handler.process(reasoning)
        
        # Generate embedding if not provided but embedding_fn is available
        if embedding is None and hasattr(self, '_embedding_fn') and self._embedding_fn is not None:
            embedding = self._embedding_fn(processed_reasoning)

        # Count tokens (rough estimate: words * 1.3)
        token_count = int(len(reasoning.split()) * 1.3)

        # Run detectors
        signals: list[DetectionSignal] = []
        short_circuited = False

        # Phase 1: Fast detectors (no API calls, no embeddings)
        fast_detectors = ["ngram", "action", "compression", "editdist"]
        for name in fast_detectors:
            if name in self._detectors:
                detector = self._detectors[name]
                t_det = time.perf_counter()
                signal = detector.detect(
                    processed_reasoning,
                    session,
                    thresholds,
                    actions=actions,
                )
                signal.latency_ms = (time.perf_counter() - t_det) * 1000
                signals.append(signal)

                # Short-circuit disabled for benchmarking to get all detector signals
                # Only short-circuit if perfect confidence (1.0) and only for extreme cases
                if (
                    signal.verdict == DetectorVerdict.LOOP_DETECTED
                    and signal.confidence >= 1.0
                    and name == "ngram"  # Only ngram with perfect match
                ):
                    short_circuited = True

        # Phase 2: Slow detectors (need embeddings)
        if not short_circuited:
            slow_detectors = ["semantic", "cusum", "entropy"]
            for name in slow_detectors:
                if name in self._detectors:
                    detector = self._detectors[name]
                    t_det = time.perf_counter()
                    signal = detector.detect(
                        processed_reasoning,
                        session,
                        thresholds,
                        embedding=embedding,
                    )
                    signal.latency_ms = (time.perf_counter() - t_det) * 1000
                    signals.append(signal)

        # Aggregate signals
        result = self._aggregate(signals, session, thresholds)

        # Generate resolution hint if loop detected
        if result.should_stop and self.config.enable_resolution_hints:
            result.correction_hint = self._resolver.generate_hint(
                result.loop_type, session
            )

        # Record step in session history
        step = StepRecord(
            step_number=session.step_count + 1,
            reasoning=reasoning,
            embedding=embedding,
            actions=actions or [],
            token_count=token_count,
            metadata=metadata or {},
        )
        session.add_step(step)

        # Trim history if needed
        if len(session.steps) > self.config.max_history_steps:
            session.steps = session.steps[-self.config.max_history_steps :]

        # Finalize result
        result.total_latency_ms = (time.perf_counter() - t0) * 1000
        result.step_number = step.step_number
        result.session_id = session_id
        result.reasoning_preview = reasoning[:200]

        return result

    def _aggregate(
        self,
        signals: list[DetectionSignal],
        session: SessionState,
        config: ThresholdConfig,
    ) -> DetectionResult:
        """
        Aggregate detector signals using weighted voting.

        The voting system works as follows:
        1. Each LOOP_DETECTED signal contributes its confidence * weight
        2. Each WARNING signal contributes half its confidence * weight
        3. Total weighted score is compared against voting threshold
        """
        if not signals:
            return DetectionResult(
                should_stop=False,
                action="PROCEED",
                loop_detected=False,
                loop_type=LoopType.NONE,
                overall_confidence=0.0,
                signals=[],
                total_latency_ms=0.0,
                step_number=0,
                session_id="",
            )

        # Calculate weighted vote
        weights = self.config.detector_weights
        total_weight = 0.0
        weighted_score = 0.0
        strongest_signal: DetectionSignal | None = None
        strongest_weighted = 0.0

        for signal in signals:
            w = weights.get(signal.detector_name, 1.0)
            total_weight += w

            if signal.verdict == DetectorVerdict.LOOP_DETECTED:
                contribution = signal.confidence * w
            elif signal.verdict == DetectorVerdict.WARNING:
                contribution = signal.confidence * w * 0.5
            else:
                contribution = 0.0

            weighted_score += contribution

            if contribution > strongest_weighted:
                strongest_weighted = contribution
                strongest_signal = signal

        # Normalize
        vote_ratio = weighted_score / total_weight if total_weight > 0 else 0.0
        should_stop = vote_ratio >= config.voting_threshold

        # Determine primary loop type
        if strongest_signal and strongest_signal.verdict != DetectorVerdict.SAFE:
            loop_type = strongest_signal.loop_type
        else:
            loop_type = LoopType.NONE

        return DetectionResult(
            should_stop=should_stop,
            action="KILL" if should_stop else "PROCEED",
            loop_detected=should_stop,
            loop_type=loop_type,
            overall_confidence=min(vote_ratio, 1.0),
            signals=signals,
            total_latency_ms=0.0,
            step_number=0,
            session_id="",
        )

    def check_stream(
        self,
        session_id: str,
        token_buffer: str,
        check_interval: int = 500,
        embedding_fn: Callable[[str], list[float]] | None = None,
    ) -> DetectionResult | None:
        """
        Streaming detection: check periodically as tokens accumulate.

        Returns DetectionResult only when a check is performed
        (every check_interval tokens), otherwise None.
        """
        token_count = len(token_buffer.split())
        session = self.get_session(session_id)

        # Only check at intervals
        if token_count % check_interval != 0 or token_count == 0:
            return None

        # Generate embedding if function provided
        embedding = None
        if embedding_fn:
            chunk = self._content_handler.process(token_buffer)
            embedding = embedding_fn(chunk)

        return self.check(session_id, token_buffer, embedding=embedding)
