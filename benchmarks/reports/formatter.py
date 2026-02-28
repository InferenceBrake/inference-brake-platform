"""
Benchmark Report Generator.

Produces human-readable reports and machine-parseable JSON
from benchmark results.

Output formats:
    1. Console table (for CI/CD output)
    2. JSON (for dashboards and tracking)
    3. Markdown (for documentation)
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

from benchmarks.runner import BenchmarkMetrics


def format_console_report(metrics: BenchmarkMetrics) -> str:
    """Generate a formatted console report."""
    lines = []
    lines.append("")
    lines.append("=" * 60)
    lines.append("  INFERENCEBRAKE BENCHMARK RESULTS")
    lines.append("=" * 60)
    lines.append("")

    # Classification metrics
    lines.append("CLASSIFICATION METRICS")
    lines.append("-" * 40)
    lines.append(f"  Accuracy:     {metrics.accuracy:.1%}")
    lines.append(f"  Precision:    {metrics.precision:.1%}")
    lines.append(f"  Recall:       {metrics.recall:.1%}")
    lines.append(f"  F1 Score:     {metrics.f1:.1%}")
    lines.append(f"  FP Rate:      {metrics.false_positive_rate:.1%}")
    lines.append("")

    # Confusion matrix
    lines.append("CONFUSION MATRIX")
    lines.append("-" * 40)
    lines.append(f"  True Positives:   {metrics.true_positives:>5}")
    lines.append(f"  False Positives:  {metrics.false_positives:>5}")
    lines.append(f"  True Negatives:   {metrics.true_negatives:>5}")
    lines.append(f"  False Negatives:  {metrics.false_negatives:>5}")
    total = (
        metrics.true_positives
        + metrics.false_positives
        + metrics.true_negatives
        + metrics.false_negatives
    )
    lines.append(f"  Total Traces:     {total:>5}")
    lines.append("")

    # Latency
    lines.append("LATENCY (per trace)")
    lines.append("-" * 40)
    lines.append(f"  P50:          {metrics.latency_p50:.2f} ms")
    lines.append(f"  P95:          {metrics.latency_p95:.2f} ms")
    lines.append(f"  P99:          {metrics.latency_p99:.2f} ms")
    lines.append(f"  Mean:         {metrics.latency_mean:.2f} ms")
    lines.append("")

    # Detection timing
    if metrics.advance_warnings:
        lines.append("DETECTION TIMING")
        lines.append("-" * 40)
        lines.append(
            f"  Avg Advance Warning:  {metrics.avg_advance_warning:+.1f} steps"
        )
        lines.append(f"  (Positive = detected before onset)")
        lines.append("")

    # Per-source breakdown
    if metrics.source_results:
        lines.append("PER-SOURCE ACCURACY")
        lines.append("-" * 40)
        for cat, data in sorted(metrics.source_results.items()):
            acc = data["correct"] / data["total"] if data["total"] > 0 else 0
            lines.append(f"  {cat:<30s} {acc:.1%} ({data['correct']}/{data['total']})")
        lines.append("")

    # Per-detector breakdown
    if metrics.detector_results:
        lines.append("PER-DETECTOR PERFORMANCE")
        lines.append("-" * 40)
        for det, data in sorted(metrics.detector_results.items()):
            total_det = data["tp"] + data["fp"] + data["tn"] + data["fn"]
            if total_det == 0:
                continue
            det_acc = (data["tp"] + data["tn"]) / total_det
            det_prec = (
                data["tp"] / (data["tp"] + data["fp"])
                if (data["tp"] + data["fp"]) > 0
                else 0
            )
            det_recall = (
                data["tp"] / (data["tp"] + data["fn"])
                if (data["tp"] + data["fn"]) > 0
                else 0
            )
            lines.append(
                f"  {det:<12s}  Acc: {det_acc:.1%}  Prec: {det_prec:.1%}  Recall: {det_recall:.1%}  ({data['detections']} detections)"
            )
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


def format_json_report(metrics: BenchmarkMetrics) -> dict:
    """Generate a JSON-serializable report."""
    return {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "version": "0.1.0",
        "classification": {
            "accuracy": round(metrics.accuracy, 4),
            "precision": round(metrics.precision, 4),
            "recall": round(metrics.recall, 4),
            "f1_score": round(metrics.f1, 4),
            "false_positive_rate": round(metrics.false_positive_rate, 4),
        },
        "confusion_matrix": {
            "true_positives": metrics.true_positives,
            "false_positives": metrics.false_positives,
            "true_negatives": metrics.true_negatives,
            "false_negatives": metrics.false_negatives,
        },
        "latency": {
            "p50_ms": round(metrics.latency_p50, 2),
            "p95_ms": round(metrics.latency_p95, 2),
            "p99_ms": round(metrics.latency_p99, 2),
            "mean_ms": round(metrics.latency_mean, 2),
        },
        "detection_timing": {
            "avg_advance_warning_steps": round(metrics.avg_advance_warning, 2),
            "advance_warning_count": len(metrics.advance_warnings),
        },
        "per_source": {
            cat: {
                "accuracy": round(data["correct"] / data["total"], 4)
                if data["total"] > 0
                else 0,
                **data,
            }
            for cat, data in metrics.source_results.items()
        },
        "per_detector": metrics.detector_results,
    }


def format_markdown_report(metrics: BenchmarkMetrics) -> str:
    """Generate a markdown report."""
    lines = []
    lines.append("# InferenceBrake Benchmark Results")
    lines.append("")
    lines.append(f"*Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}*")
    lines.append("")

    lines.append("## Classification Metrics")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| Accuracy | {metrics.accuracy:.1%} |")
    lines.append(f"| Precision | {metrics.precision:.1%} |")
    lines.append(f"| Recall | {metrics.recall:.1%} |")
    lines.append(f"| F1 Score | {metrics.f1:.1%} |")
    lines.append(f"| False Positive Rate | {metrics.false_positive_rate:.1%} |")
    lines.append("")

    lines.append("## Latency")
    lines.append("")
    lines.append("| Percentile | Value |")
    lines.append("|------------|-------|")
    lines.append(f"| P50 | {metrics.latency_p50:.2f} ms |")
    lines.append(f"| P95 | {metrics.latency_p95:.2f} ms |")
    lines.append(f"| P99 | {metrics.latency_p99:.2f} ms |")
    lines.append(f"| Mean | {metrics.latency_mean:.2f} ms |")
    lines.append("")

    if metrics.source_results:
        lines.append("## Per-Source Breakdown")
        lines.append("")
        lines.append("| Source | Accuracy | TP | FP | TN | FN |")
        lines.append("|----------|----------|----|----|----|----|")
        for cat, data in sorted(metrics.source_results.items()):
            acc = data["correct"] / data["total"] if data["total"] > 0 else 0
            lines.append(
                f"| {cat} | {acc:.1%} | {data['tp']} | {data['fp']} | {data['tn']} | {data['fn']} |"
            )
        lines.append("")

    if metrics.detector_results:
        lines.append("## Per-Detector Performance")
        lines.append("")
        lines.append("| Detector | Accuracy | Precision | Recall | Detections |")
        lines.append("|----------|----------|-----------|--------|------------|")
        for det, data in sorted(metrics.detector_results.items()):
            total_det = data["tp"] + data["fp"] + data["tn"] + data["fn"]
            if total_det == 0:
                continue
            det_acc = (data["tp"] + data["tn"]) / total_det
            det_prec = (
                data["tp"] / (data["tp"] + data["fp"])
                if (data["tp"] + data["fp"]) > 0
                else 0
            )
            det_recall = (
                data["tp"] / (data["tp"] + data["fn"])
                if (data["tp"] + data["fn"]) > 0
                else 0
            )
            lines.append(
                f"| {det} | {det_acc:.1%} | {det_prec:.1%} | {det_recall:.1%} | {data['detections']} |"
            )
        lines.append("")

    return "\n".join(lines)


def save_report(
    metrics: BenchmarkMetrics,
    output_dir: str | Path = "benchmarks/reports",
    formats: list[str] | None = None,
) -> list[str]:
    """
    Save benchmark reports in multiple formats.

    Returns list of created file paths.
    """
    if formats is None:
        formats = ["console", "json", "markdown"]

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    created_files = []

    if "json" in formats:
        json_path = output_path / f"benchmark_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(format_json_report(metrics), f, indent=2)
        created_files.append(str(json_path))

    if "markdown" in formats:
        md_path = output_path / f"benchmark_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(format_markdown_report(metrics))
        created_files.append(str(md_path))

    if "console" in formats:
        txt_path = output_path / f"benchmark_{timestamp}.txt"
        with open(txt_path, "w") as f:
            f.write(format_console_report(metrics))
        created_files.append(str(txt_path))

    return created_files
