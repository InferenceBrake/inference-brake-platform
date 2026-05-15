"""
InferenceBrake SDK test — follows the docs examples.

Usage:
    export INFERENCEBRAKE_API_KEY=ib_your_key_here
    uv run python test_docs.py
"""

import os
from inferencebrake import InferenceBrake

API_KEY = os.getenv("INFERENCEBRAKE_API_KEY", "ib_your_key")


def test_basic():
    print("\n=== Basic Usage ===")
    guard = InferenceBrake(api_key=API_KEY)

    reasoning_steps = [
        "I need to search for weather in NYC",
        "Let me call the weather API for NYC",
        "I should check the weather in New York City",
    ]

    for i, text in enumerate(reasoning_steps, 1):
        status = guard.check(reasoning=text, session_id="test-basic")
        dets = ", ".join(f"{k}:{v}" for k, v in status.detectors.items()) if status.detectors else "none"
        print(f"  Step {i}: action={status.action}, sim={status.similarity:.2%}, conf={status.confidence:.2f}, status={status.status}")
        print(f"         detectors: [{dets}]")

        if status.should_stop:
            print(f"  Loop detected: {status.message}")
            break

    # Print session history if available
    try:
        history = guard.get_session_history(session_id="test-basic", limit=10)
        steps = history.get("steps", [])
        print(f"\n  Session steps stored: {history.get('total', 0)}")
        for step in steps:
            det = step.get("loop_detected", False)
            print(f"    Step {step.get('step_number')}: loop={det}, sim={step.get('similarity', 0):.2%}")
    except Exception as e:
        print(f"\n  Session history error: {e}")

    return guard


def test_batch(guard: InferenceBrake):
    print("\n=== Batch Check ===")
    statuses = guard.check_batch(
        reasoning_list=["first step", "second step", "third step"],
        session_id="test-batch",
    )
    for i, s in enumerate(statuses, 1):
        print(f"  Step {i}: {s.action}")


def test_history(guard: InferenceBrake):
    print("\n=== Session History ===")
    try:
        history = guard.get_session_history(session_id="test-basic", limit=10)
        steps = history.get("steps", [])
        print(f"  Found {len(steps)} steps")
        for step in steps:
            print(f"  Step {step.get('step_number')}: {step.get('reasoning', '')[:60]}")
    except Exception as e:
        print(f"  History: {e}")


def test_config():
    print("\n=== Configuration ===")
    guard = InferenceBrake(api_key=API_KEY, timeout=10, auto_stop=False)
    status = guard.check(reasoning="config test", session_id="test-config")
    print(f"  Status: {status.status}")


if __name__ == "__main__":
    guard = test_basic()
    test_batch(guard)
    test_history(guard)
    test_config()
    print("\nDone.")
