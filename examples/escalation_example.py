"""Escalate to a stronger model before stopping.

Instead of halting on the first loop, hand the agent a chance to recover on a
stronger model, then stop if it still loops. The SDK does not pick models; the
`escalate` hook does.

Setup:
    uv run escalation_example.py
"""

import os
import sys
import time

from dotenv import load_dotenv

from inferencebrake import LoopDetectedError, guard_agent_loop

load_dotenv()

api_key = os.getenv("INFERENCEBRAKE_API_KEY")
if not api_key:
    sys.exit("Set INFERENCEBRAKE_API_KEY in .env")

attempts = []


def switch_model(model):
    attempts.append(model)
    print(f"  escalating to {model} (attempt {len(attempts)})")


@guard_agent_loop(
    api_key=api_key,
    session_id=f"escalation-demo-{int(time.time())}",
    escalate=lambda status, attempt: switch_model("claude-opus"),
    max_escalations=2,
)
def call_model(prompt):
    # Replace with your real model call. `switch_model` would change the model
    # used for the next attempt.
    return "The service is unavailable, so I will retry the same call."


def main():
    for step in range(1, 10):
        try:
            call_model("fetch the user balance")
        except LoopDetectedError as e:
            print(f"step {step}: stopped after {len(attempts)} escalation(s) -> {e}")
            return 0
        print(f"step {step}: continuing")

    print("No loop detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
