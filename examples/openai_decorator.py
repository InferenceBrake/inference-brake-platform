"""@guard_agent_loop around a raw completion call.

Uses a fake OpenAI-style response so it runs without the openai package. Replace
the marked line with your real call:

    return client.chat.completions.create(model="gpt-4o-mini", messages=[...])

Setup:
    uv run openai_decorator.py
"""

import os
import sys
import time
from types import SimpleNamespace

from dotenv import load_dotenv

from inferencebrake import LoopDetectedError, guard_agent_loop

load_dotenv()

api_key = os.getenv("INFERENCEBRAKE_API_KEY")
if not api_key:
    sys.exit("Set INFERENCEBRAKE_API_KEY in .env")


@guard_agent_loop(
    api_key=api_key,
    session_id=f"openai-demo-{int(time.time())}",
    model="gpt-4o-mini",
    prompt="fetch user balance",
    action=lambda result: "get_balance",
)
def call_model(prompt):
    # Replace with your real model call.
    return SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content="The service is unavailable, so I will retry the same call."
                )
            )
        ]
    )


def main():
    for step in range(1, 10):
        try:
            call_model("fetch the user balance for user_42")
        except LoopDetectedError as e:
            print(f"step {step}: halted by InferenceBrake -> {e}")
            return 0
        print(f"step {step}: ok")

    print("No loop detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
