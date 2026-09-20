"""Plain InferenceBrake guard around a hand-written agent loop.

Runs without an LLM: the agent reasons, calls a tool that always fails, and
retries. The guard halts it once the reasoning stops changing.

Setup:
    cp .env.example .env   # set INFERENCEBRAKE_API_KEY
    uv run raw_loop.py
"""

import os
import sys
import time

from dotenv import load_dotenv

from inferencebrake import (
    AuthenticationError,
    InferenceBrake,
    InferenceBrakeError,
    RateLimitError,
)

load_dotenv()

api_key = os.getenv("INFERENCEBRAKE_API_KEY")
if not api_key:
    sys.exit("Set INFERENCEBRAKE_API_KEY in .env")

guard = InferenceBrake(api_key=api_key, timeout=15)
session_id = f"raw-loop-{int(time.time())}"


def call_tool(user_id):
    """Replace with your real tool. This one always fails."""
    return f"ERROR: upstream service unavailable (HTTP 503) for {user_id}"


def agent_step():
    """One reasoning step. Replace with your real model call."""
    return "The service is unavailable, so I will retry the same call for user_42."


def main():
    print(f"session: {session_id}\n")

    for step in range(1, 12):
        reasoning = agent_step()

        try:
            status = guard.check(
                reasoning=reasoning,
                session_id=session_id,
                action="get_balance",
                model="gpt-4o-mini",
                prompt="fetch user balance",
            )
        except AuthenticationError:
            sys.exit("Invalid API key")
        except RateLimitError as e:
            sys.exit(f"Rate limited: {e}")
        except InferenceBrakeError as e:
            sys.exit(f"Request failed: {e}")

        print(
            f"step {step}: {status.action:7s} "
            f"conf={status.confidence:.2f} "
            f"saved=${status.estimated_cost_saved:.4f} "
            f"detectors=[{status.detector_triggered or 'none'}]"
        )

        if status.should_stop:
            print(f"\nLoop detected at step {step}: {status.message}")
            print(f"Estimated ${status.estimated_cost_saved:.4f} saved.")
            return 0

        # A real agent would call the tool here. The observation is identical
        # every time, which is exactly what drives the loop.
        observation = call_tool("user_42")
        assert observation

    print("\nNo loop detected in 12 steps.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
