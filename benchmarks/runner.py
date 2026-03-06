"""
Benchmark Runner.

Executes the detection pipeline against benchmark traces
and computes comprehensive metrics.

Metrics computed:
    - Classification: Precision, Recall, F1, Accuracy
    - Latency: P50, P95, P99, mean
    - Per-detector statistics
"""

from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Optional

import numpy as np

# Add engine to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "packages" / "engine"))

from inferencebrake.pipeline import DetectionPipeline
from inferencebrake.types import (
    DetectionResult,
    PipelineConfig,
    ThresholdConfig,
)
from benchmarks.benchmark_format import BenchmarkTrace, LoopType

try:
    from sentence_transformers import SentenceTransformer
    HAS_EMBEDDINGS = True
except ImportError:
    HAS_EMBEDDINGS = False


@dataclass
class StepResult:
    """Result of running the pipeline on one step."""
    trace_id: str
    step_number: int
    predicted: bool  # True = loop detected
    confidence: float
    latency_ms: float
    signals: dict  # detector_name -> verdict


@dataclass
class TraceResult:
    """Aggregated result for one trace."""
    trace_id: str
    source: str
    is_loop_gt: bool  # Ground truth
    loop_detected: bool  # Pipeline result
    detection_step: int | None
    step_results: list[StepResult]
    total_latency_ms: float


@dataclass
class BenchmarkMetrics:
    """Complete benchmark metrics."""
    # Classification metrics
    true_positives: int = 0
    false_positives: int = 0
    true_negatives: int = 0
    false_negatives: int = 0

    # Latency
    latencies_ms: list[float] = field(default_factory=list)

    # Detection timing
    advance_warnings: list[int] = field(default_factory=list)

    # Per-category/source results
    source_results: dict[str, dict] = field(default_factory=dict)

    # Per-detector results
    detector_results: dict[str, dict] = field(default_factory=dict)

    # Trace-level results
    trace_results: list[TraceResult] = field(default_factory=list)

    @property
    def precision(self) -> float:
        denom = self.true_positives + self.false_positives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def recall(self) -> float:
        denom = self.true_positives + self.false_negatives
        return self.true_positives / denom if denom > 0 else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0

    @property
    def accuracy(self) -> float:
        total = (
            self.true_positives
            + self.false_positives
            + self.true_negatives
            + self.false_negatives
        )
        return (self.true_positives + self.true_negatives) / total if total > 0 else 0.0

    @property
    def false_positive_rate(self) -> float:
        denom = self.false_positives + self.true_negatives
        return self.false_positives / denom if denom > 0 else 0.0

    @property
    def latency_p50(self) -> float:
        return float(np.percentile(self.latencies_ms, 50)) if self.latencies_ms else 0.0

    @property
    def latency_p95(self) -> float:
        return float(np.percentile(self.latencies_ms, 95)) if self.latencies_ms else 0.0

    @property
    def latency_p99(self) -> float:
        return float(np.percentile(self.latencies_ms, 99)) if self.latencies_ms else 0.0

    @property
    def latency_mean(self) -> float:
        return float(np.mean(self.latencies_ms)) if self.latencies_ms else 0.0


    @property
    def avg_advance_warning(self) -> float:
        return float(np.mean(self.advance_warnings)) if self.advance_warnings else 0.0


class BenchmarkRunner:
    """
    Run the detection pipeline against benchmark traces.
    """

    def __init__(self, config: PipelineConfig | None = None):
        self.config = config or PipelineConfig()
        
        # Load embedding model
        self.embedding_model = None
        if HAS_EMBEDDINGS:
            print("[INIT] Loading embedding model (Thenlper/gte-small)...")
            try:
                self.embedding_model = SentenceTransformer("Thenlper/gte-small")
            except Exception as e:
                print(f"[ERR] Failed to load embedding model: {e}")
                print("   (Ensure sentence-transformers is installed: pip install sentence-transformers)")
        else:
            print("[WARN] sentence-transformers not installed. Embeddings will be zeroed.")

        # Define embedding function for pipeline
        def embedding_fn(text: str) -> List[float]:
            if self.embedding_model:
                return self.embedding_model.encode(text).tolist()
            return [0.0] * 384  # Fallback for testing without model

        self.pipeline = DetectionPipeline(config=self.config, embedding_fn=embedding_fn)

    def run(
        self,
        traces: List[BenchmarkTrace],
        verbose: bool = False,
    ) -> BenchmarkMetrics:
        """
        Run the full benchmark.
        """
        metrics = BenchmarkMetrics()
        total = len(traces)

        print(f"[RUN] Running benchmark on {total} traces...")

        for idx, trace in enumerate(traces):
            if verbose and (idx + 1) % 10 == 0:
                print(f"  [{idx + 1}/{total}] Processing {trace.id}...")

            trace_result = self._run_trace(trace)
            metrics.trace_results.append(trace_result)

            # Ground truth: label="loop" means positive
            # Some datasets might use different labels, standardized in BenchmarkTrace
            is_loop_gt = (trace.label == "loop")

            # Classify
            if is_loop_gt:
                if trace_result.loop_detected:
                    metrics.true_positives += 1
                else:
                    metrics.false_negatives += 1
            else:
                if trace_result.loop_detected:
                    metrics.false_positives += 1
                else:
                    metrics.true_negatives += 1

            # Collect latencies
            metrics.latencies_ms.append(trace_result.total_latency_ms)

            # Per-source tracking
            source = trace.source
            if source not in metrics.source_results:
                metrics.source_results[source] = {
                    "total": 0, "correct": 0,
                    "tp": 0, "fp": 0, "tn": 0, "fn": 0,
                }
            
            s_metrics = metrics.source_results[source]
            s_metrics["total"] += 1
            
            match = (is_loop_gt == trace_result.loop_detected)
            if match:
                s_metrics["correct"] += 1
            
            if is_loop_gt and trace_result.loop_detected:
                s_metrics["tp"] += 1
            elif not is_loop_gt and trace_result.loop_detected:
                s_metrics["fp"] += 1
            elif not is_loop_gt and not trace_result.loop_detected:
                s_metrics["tn"] += 1
            else:
                s_metrics["fn"] += 1

            # Per-detector tracking (aggregate stats per trace)
            # Determine which detectors fired at least once in this trace
            detectors_fired = set()
            all_detectors_seen = set()
            
            for sr in trace_result.step_results:
                for det_name, verdict in sr.signals.items():
                    all_detectors_seen.add(det_name)
                    if verdict == "loop_detected":
                        detectors_fired.add(det_name)

            # Update metrics per detector
            for det_name in all_detectors_seen:
                if det_name not in metrics.detector_results:
                    metrics.detector_results[det_name] = {
                        "tp": 0, "fp": 0, "tn": 0, "fn": 0, "detections": 0
                    }
                dr = metrics.detector_results[det_name]
                
                fired = det_name in detectors_fired
                if fired:
                    dr["detections"] += 1
                    if is_loop_gt:
                        dr["tp"] += 1
                    else:
                        dr["fp"] += 1
                else:
                    if is_loop_gt:
                        dr["fn"] += 1
                    else:
                        dr["tn"] += 1

            # Clear session state
            self.pipeline.clear_session(trace.id)

        return metrics

    def _run_trace(self, trace: BenchmarkTrace) -> TraceResult:
        """Run the pipeline on all steps of a trace."""
        step_results = []
        loop_detected = False
        detection_step = None
        total_latency = 0.0

        # We assume the trace is a sequence. The pipeline manages history.
        for step in trace.steps:
            t0 = time.perf_counter()
            
            # Extract actions from step if available
            actions = None
            if step.action:
                actions = [step.action]

            # Extract pre-computed embedding from step metadata if available
            precomputed_emb = step.metadata.get("embedding") if step.metadata else None

            # Run pipeline - use pre-computed embedding if available
            result = self.pipeline.check(
                session_id=trace.id,
                reasoning=step.reasoning,
                actions=actions,
                embedding=precomputed_emb,
            )
            
            latency = (time.perf_counter() - t0) * 1000
            total_latency += latency

            # Extract per-detector signals
            signals = {}
            for sig in result.signals:
                signals[sig.detector_name] = sig.verdict.value

            step_results.append(StepResult(
                trace_id=trace.id,
                step_number=step.step_number,
                predicted=result.should_stop,
                confidence=result.overall_confidence,
                latency_ms=latency,
                signals=signals,
            ))

            if result.should_stop and not loop_detected:
                loop_detected = True
                detection_step = step.step_number
                # In a real scenario, we might stop processing here.
                # For benchmarking, we continue but mark it detected.

        return TraceResult(
            trace_id=trace.id,
            source=trace.source,
            is_loop_gt=(trace.label == "loop"),
            loop_detected=loop_detected,
            detection_step=detection_step,
            step_results=step_results,
            total_latency_ms=total_latency,
        )

    def run_threshold_sweep(
        self,
        traces: List[BenchmarkTrace],
        thresholds: List[float] | None = None,
        verbose: bool = False,
    ) -> List[tuple[float, BenchmarkMetrics]]:
        """Run benchmarks across multiple thresholds."""
        if thresholds is None:
            thresholds = [0.75, 0.80, 0.85, 0.90, 0.95]

        results = []
        
        # Helper to preserve model
        def embedding_fn(text):
            if self.embedding_model:
                return self.embedding_model.encode(text).tolist()
            return [0.0] * 384

        for threshold in thresholds:
            if verbose:
                print(f"\n--- Threshold: {threshold} ---")
            
            # Update config
            config = PipelineConfig(
                thresholds=ThresholdConfig(similarity_threshold=threshold)
            )
            
            # Re-init pipeline with new config and preserved embedding function
            self.pipeline = DetectionPipeline(config=config, embedding_fn=embedding_fn)
            
            metrics = self.run(traces, verbose=False) # less verbose inner loop
            results.append((threshold, metrics))

        return results

    def run_detector_ablation(
        self,
        traces: List[BenchmarkTrace],
        verbose: bool = False,
    ) -> Dict[str, BenchmarkMetrics]:
        """Run benchmarks with individual detectors disabled."""
        all_detectors = ["ngram", "semantic", "cusum", "entropy", "action", "compression", "editdist"]
        results = {}

        # Helper for embedding fn
        def embedding_fn(text):
            if self.embedding_model:
                return self.embedding_model.encode(text).tolist()
            return [0.0] * 384

        # Full pipeline
        if verbose:
            print("\n--- Full Pipeline ---")
        config = PipelineConfig(enabled_detectors=all_detectors)
        self.pipeline = DetectionPipeline(config=config, embedding_fn=embedding_fn)
        results["full_pipeline"] = self.run(traces, verbose=False)

        # Remove one at a time
        for det in all_detectors:
            if verbose:
                print(f"\n--- Without {det} ---")
            subset = [d for d in all_detectors if d != det]
            config = PipelineConfig(enabled_detectors=subset)
            self.pipeline = DetectionPipeline(config=config, embedding_fn=embedding_fn)
            results[f"without_{det}"] = self.run(traces, verbose=False)

        return results
