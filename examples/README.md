# InferenceBrake Examples

Runnable integrations for the [InferenceBrake](https://inferencebrake.dev) loop detector.

Each example is self-contained and runs without an LLM provider, using a scripted or fake model so you can see detection fire immediately. Swap the marked line for your real model call.

## Setup

```bash
cd examples
cp .env.example .env        # add your API key (https://inferencebrake.dev)
uv run raw_loop.py
```

Or with pip:

```bash
pip install inferencebrake
export INFERENCEBRAKE_API_KEY=ib_your_key
python raw_loop.py
```

## Examples

| File | What it shows |
| --- | --- |
| `raw_loop.py` | Plain `InferenceBrake` guard around a hand-written agent loop |
| `langchain_example.py` | `InferenceBrakeCallbackHandler` on a LangChain chain |
| `crewai_example.py` | `create_crewai_callback` on agent steps |
| `openai_decorator.py` | `@guard_agent_loop` around a raw completion call |
| `escalation_example.py` | Escalate to a stronger model before stopping |
| `node_example.js` | JS SDK `guarded` wrapper |

Each example prints the decision, the detectors that fired, and the estimated dollars saved, then exits non-zero if the guard never fired.

## Notes

- Detection needs a few steps: the first call always returns `PROCEED` because there is no history yet.
- `model`, `action`, and `prompt` are optional. Pass them to get per-model / per-tool / per-prompt attribution in the analytics dashboard.
- The LangChain example needs `inferencebrake[langchain]`.
