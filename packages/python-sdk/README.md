# InferenceBrake Python SDK

Loop detection for AI agents. Detect and stop runaway reasoning loops before they burn your token budget.

InferenceBrake runs your agent's reasoning step through five detectors (semantic similarity, action repetition, n-gram overlap, edit distance, and compression distance) and returns a `KILL`/`PROCEED` decision. When a loop is detected it also returns an estimated dollar amount saved by halting it.

- Docs: https://inferencebrake.dev/docs
- Dashboard / API keys: https://inferencebrake.dev

## Install

```bash
pip install inferencebrake
```

With the LangChain callback:

```bash
pip install inferencebrake[langchain]
```

## Quickstart

```python
from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="ib_your_key")

status = guard.check(
    reasoning="Let me search for the weather in NYC",
    session_id="agent-session-123",
)

print(status.action)                 # "PROCEED" or "KILL"
print(status.similarity)             # 0.0 - 1.0
print(status.should_stop)            # True when action == "KILL"
print(status.estimated_cost_saved)   # estimated USD saved on a KILL
```

Wrap an agent loop:

```python
from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="ib_your_key")

for step in agent.run():
    status = guard.check(reasoning=step["reasoning"], session_id="my-agent")

    if status.should_stop:
        print(f"Loop detected: {status.message}")
        break
```

## Options

```python
guard = InferenceBrake(
    api_key="ib_your_key",
    timeout=10,        # request timeout in seconds
    auto_stop=False,   # raise InferenceBrakeError on a detected loop
    supabase_url=None, # override the API base URL (self-hosting)
)
```

Environment variable `INFERENCEBRAKE_URL` overrides the default API base URL.

## LangChain

```python
from inferencebrake import InferenceBrakeCallbackHandler

handler = InferenceBrakeCallbackHandler(api_key="ib_your_key")
agent = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])
```

## CrewAI

```python
from inferencebrake import create_crewai_callback

callback = create_crewai_callback(
    api_key="ib_your_key",
    on_loop_detected=lambda status: print(f"Loop detected: {status.message}"),
)
agent.callbacks = [callback]
```

## Batch and history

```python
results = guard.check_batch([step1, step2, step3], session_id="my-agent")
history = guard.get_session_history("my-agent", limit=50)
```

## Errors

```python
from inferencebrake import AuthenticationError, RateLimitError, InferenceBrakeError

try:
    status = guard.check(reasoning="...", session_id="...")
except AuthenticationError:
    ...  # invalid API key (HTTP 401)
except RateLimitError:
    ...  # daily quota exceeded (HTTP 429)
except InferenceBrakeError:
    ...  # any other API or transport error
```

## CLI

```bash
inferencebrake --api-key ib_your_key --session demo --reasoning "check this step"
```

## License

MIT
