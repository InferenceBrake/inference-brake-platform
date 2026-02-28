#!/usr/bin/env python3
"""
InferenceBrake Benchmark CLI.

Run the full benchmark suite from the command line:

    python -m benchmarks.run_benchmarks
    python -m benchmarks.run_benchmarks --verbose
    python -m benchmarks.run_benchmarks --sweep              # threshold sweep
    python -m benchmarks.run_benchmarks --ablation           # detector ablation
    python -m benchmarks.run_benchmarks --collect            # Force data re-collection
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "packages" / "engine"))
sys.path.insert(0, str(project_root))

from benchmarks.runner import BenchmarkRunner
from benchmarks.collect_benchmark_data import BenchmarkDataCollector
from benchmarks.benchmark_format import BenchmarkTrace
from benchmarks.reports.formatter import (
    format_console_report,
    format_json_report,
    save_report,
)
from inferencebrake.types import PipelineConfig, ThresholdConfig


def load_traces(force_collect: bool = False) -> list[BenchmarkTrace]:
    """Load traces from disk or collect them if missing."""
    collector = BenchmarkDataCollector()
    data_file = collector.output_dir / "all_traces.json"

    if force_collect or not data_file.exists():
        print("[COLLECT] Data not found or forced collection. Running collector...")
        raw_traces = collector.collect_all()
    else:
        print(f"[LOAD] Loading benchmark data from {data_file}...")
        try:
            with open(data_file, "r", encoding="utf-8") as f:
                raw_traces = json.load(f)
        except Exception as e:
            print(f"[ERR] Error loading data: {e}. Re-collecting...")
            raw_traces = collector.collect_all()

    print(f"[CONVERT] Converting {len(raw_traces)} traces to benchmark format...")
    traces = []
    for d in raw_traces:
        try:
            traces.append(BenchmarkTrace.from_dict(d))
        except Exception as e:
            # Skip malformed traces
            continue
            
    print(f"[OK] Loaded {len(traces)} valid traces.")
    return traces


def run_standard_benchmark(args, traces):
    """Run the standard benchmark suite."""
    print(f"Looping traces:     {sum(1 for t in traces if t.label == 'loop')}")
    print(f"No-loop traces:     {sum(1 for t in traces if t.label != 'loop')}")

    config = PipelineConfig(
        thresholds=ThresholdConfig(
            similarity_threshold=args.threshold,
            voting_threshold=args.voting_threshold,
        ),
    )
    runner = BenchmarkRunner(config=config)

    print(f"\nRunning benchmark (threshold={args.threshold})...")
    t0 = time.time()
    metrics = runner.run(traces, verbose=args.verbose)
    elapsed = time.time() - t0

    report = format_console_report(metrics)
    print(report)
    print(f"Benchmark completed in {elapsed:.1f}s")

    if args.save:
        files = save_report(metrics, output_dir=args.output)
        print(f"\nReports saved:")
        for f in files:
            print(f"  {f}")

    if args.json:
        print("\nJSON Report:")
        print(json.dumps(format_json_report(metrics), indent=2))

    return metrics


def run_threshold_sweep(args, traces):
    """Run benchmarks across multiple thresholds."""
    print("Running threshold sweep...")
    
    runner = BenchmarkRunner()
    thresholds = [0.70, 0.75, 0.80, 0.82, 0.85, 0.87, 0.90, 0.92, 0.95]
    results = runner.run_threshold_sweep(
        traces=traces, thresholds=thresholds, verbose=args.verbose
    )

    print("\n" + "=" * 70)
    print("  THRESHOLD SWEEP RESULTS")
    print("=" * 70)
    print(
        f"  {'Threshold':>10s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s} | {'FPR':>6s}"
    )
    print("-" * 70)

    best_f1 = 0
    best_threshold = 0
    for threshold, metrics in results:
        f1 = metrics.f1
        print(
            f"  {threshold:>10.2f} | {metrics.accuracy:>8.1%} | {metrics.precision:>9.1%} | "
            f"{metrics.recall:>6.1%} | {f1:>6.1%} | {metrics.false_positive_rate:>6.1%}"
        )
        if f1 > best_f1:
            best_f1 = f1
            best_threshold = threshold

    print("-" * 70)
    print(f"  Best F1: {best_f1:.1%} at threshold {best_threshold}")
    print("=" * 70)


def run_ablation(args, traces):
    """Run detector ablation study."""
    print("Running detector ablation study...")
    
    runner = BenchmarkRunner()
    results = runner.run_detector_ablation(traces=traces, verbose=args.verbose)

    print("\n" + "=" * 70)
    print("  DETECTOR ABLATION STUDY")
    print("=" * 70)
    print(
        f"  {'Configuration':<25s} | {'Accuracy':>8s} | {'Precision':>9s} | {'Recall':>6s} | {'F1':>6s}"
    )
    print("-" * 70)

    baseline_f1 = results.get("full_pipeline", None)
    if baseline_f1:
        baseline_f1_val = baseline_f1.f1
    else:
        baseline_f1_val = 0.0

    for name, metrics in results.items():
        label = name.replace("_", " ").title()
        delta = ""
        if baseline_f1_val > 0 and name != "full_pipeline":
            d = metrics.f1 - baseline_f1_val
            delta = f"  ({d:+.1%})"
        print(
            f"  {label:<25s} | {metrics.accuracy:>8.1%} | {metrics.precision:>9.1%} | "
            f"{metrics.recall:>6.1%} | {metrics.f1:>6.1%}{delta}"
        )

    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(
        description="InferenceBrake Benchmark Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m benchmarks.run_benchmarks                    # Standard run with existing data
  python -m benchmarks.run_benchmarks --collect          # Force new data collection
  python -m benchmarks.run_benchmarks --sweep            # Find optimal threshold
  python -m benchmarks.run_benchmarks --ablation         # Detector contribution
  python -m benchmarks.run_benchmarks --save --json      # Save reports
        """,
    )
    # Removing 'traces' arg as it's controlled by collection now, 
    # but keeping it optional/ignored for backward compat if needed or maybe limit?
    # Actually, let's limit if specified.
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of traces to run (default: all)",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (default: 0.85)",
    )
    parser.add_argument(
        "--voting-threshold",
        type=float,
        default=0.5,
        help="Voting threshold (fraction of detectors needed, default: 0.5)",
    )
    parser.add_argument(
        "--collect",
        action="store_true",
        help="Force re-collection of benchmark data",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print progress during benchmark",
    )
    parser.add_argument(
        "--sweep",
        action="store_true",
        help="Run threshold sweep",
    )
    parser.add_argument(
        "--ablation",
        action="store_true",
        help="Run detector ablation study",
    )
    parser.add_argument(
        "--save",
        action="store_true",
        help="Save reports to benchmarks/reports/",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print JSON report",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="benchmarks/reports",
        help="Output directory for reports",
    )

    args = parser.parse_args()

    # Load data
    traces = load_traces(force_collect=args.collect)
    
    if args.limit:
        traces = traces[:args.limit]
        print(f"[LIMIT] Limiting to {len(traces)} traces.")

    if not traces:
        print("[ERR] No traces available. Exiting.")
        sys.exit(1)

    if args.sweep:
        run_threshold_sweep(args, traces)
    elif args.ablation:
        run_ablation(args, traces)
    else:
        run_standard_benchmark(args, traces)


if __name__ == "__main__":
    main()
