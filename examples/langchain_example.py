"""LangChain chain guarded by InferenceBrake.

Uses langchain-core's FakeListLLM so it runs without an API key. Replace the LLM
with your real one and the handler works the same.

Setup:
    uv run --extra langchain langchain_example.py
"""

import os
import sys
import time

from dotenv import load_dotenv

from inferencebrake import InferenceBrakeCallbackHandler, LoopDetectedError

load_dotenv()

api_key = os.getenv("INFERENCEBRAKE_API_KEY")
if not api_key:
    sys.exit("Set INFERENCEBRAKE_API_KEY in .env")

try:
    from langchain_core.language_models.fake import FakeListLLM
    from langchain_core.prompts import PromptTemplate
except ImportError:
    sys.exit("Install with: pip install 'inferencebrake[langchain]'")


def main():
    llm = FakeListLLM(
        responses=["The service is unavailable, I will retry the same call."] * 10
    )
    prompt = PromptTemplate.from_template("{input}")
    chain = prompt | llm

    handler = InferenceBrakeCallbackHandler(
        api_key=api_key,
        session_id=f"langchain-demo-{int(time.time())}",
        model="fake-llm",
    )

    for step in range(1, 8):
        try:
            chain.invoke({"input": "fetch the user balance"}, config={"callbacks": [handler]})
        except LoopDetectedError as e:
            print(f"step {step}: halted by InferenceBrake -> {e}")
            print(f"detectors: {handler.last_status.detector_triggered or 'none'}")
            return 0
        print(f"step {step}: ok")

    print("No loop detected")
    return 1


if __name__ == "__main__":
    sys.exit(main())
