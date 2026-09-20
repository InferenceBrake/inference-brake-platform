"""CrewAI-style step callback.

Runs without CrewAI: the callback is duck-typed, so it works anywhere you can
call a step hook (CrewAI's on_agent_action, AutoGen step listeners, or your own
loop).

Setup:
    uv run crewai_example.py
"""

import os
import sys
import time

from dotenv import load_dotenv

from inferencebrake import LoopDetectedError, create_crewai_callback

load_dotenv()

api_key = os.getenv("INFERENCEBRAKE_API_KEY")
if not api_key:
    sys.exit("Set INFERENCEBRAKE_API_KEY in .env")


def main():
    callback = create_crewai_callback(
        api_key=api_key,
        session_id=f"crewai-demo-{int(time.time())}",
        model="gpt-4o-mini",
    )

    for step in range(1, 10):
        try:
            callback.step(
                "The service is unavailable, retrying the same call",
                action="get_balance",
            )
        except LoopDetectedError as e:
            print(f"step {step}: halted by InferenceBrake -> {e}")
            return 0
        print(f"step {step}: ok")

    print("No loop detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
