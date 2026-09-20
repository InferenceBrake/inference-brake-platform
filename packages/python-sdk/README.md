# InferenceBrake Python SDK

Loop detection for AI agents. Detect and stop runaway reasoning loops before they burn your token budget.

InferenceBrake runs each agent step through five detectors (semantic similarity, action repetition, n-gram overlap, edit distance, and compression distance) and returns a `KILL`/`PROCEED` decision. On a detected loop it returns an estimated dollar amount saved by halting the run.

Framework-agnostic: LangChain, CrewAI, AutoGen, and raw OpenAI/Anthropic loops all use the same guard. Detection is semantic, so it catches reasoning that repeats the same idea in different words, not just exact repeats.

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
    action="web_search",   # optional, enables action repetition detection
    model="gpt-4o-mini",   # optional, recorded for attribution
    prompt="weather task", # optional, recorded for attribution
)

status.should_stop            # True when a loop was detected
status.score                  # detection confidence, 0.0 - 1.0
status.detector_triggered     # e.g. "semantic, action, compression"
status.estimated_cost_saved   # estimated USD saved on a halt
```

## Framework adapters

### LangChain

`InferenceBrakeCallbackHandler` subclasses `BaseCallbackHandler` and checks the completion in `on_llm_end`.

```python
from inferencebrake import InferenceBrakeCallbackHandler

handler = InferenceBrakeCallbackHandler(api_key="ib_your_key")
agent = AgentExecutor(agent=agent, tools=tools, callbacks=[handler])
```

On a detected loop it raises `LoopDetectedError` (alias `DoomLoopException`).

### CrewAI / AutoGen / custom step loops

The callback is duck-typed, so it works anywhere you can call a step hook.

```python
from inferencebrake import create_crewai_callback

callback = create_crewai_callback(
    api_key="ib_your_key",
    on_loop_detected=lambda status: print(status.message),
)

agent.callbacks = [callback]          # CrewAI on_agent_action
callback.step(reasoning, action="get_balance")  # or call directly
```

## Raw OpenAI / Anthropic loops

Decorate the function that performs one model call or one agent step.

```python
from inferencebrake import guard_agent_loop

@guard_agent_loop(api_key="ib_your_key", session_id="agent-1")
def call_model(prompt):
    return client.chat.completions.create(model="gpt-4o", messages=[...])
```

The result is read from `choices[0].message.content` by default. Override with `extract`, and pull an action identity with `action`:

```python
@guard_agent_loop(
    api_key="ib_your_key",
    session_id=lambda *a, **k: current_run_id(),
    extract=lambda r: r["reasoning"],
    action=lambda r: r["tool"],
    loop_key=lambda a: a.strip().lower(),  # normalize cosmetic differences
    on_loop=lambda status: metrics.record(status),
)
def step(task):
    ...
```

Async functions are supported.

## Fail-open

By default the guard **fails open**: if the API is unreachable, times out, or returns a 5xx, it logs a warning and returns a safe `Status` with `degraded=True` instead of breaking your agent. Auth (401) and rate limit (429) errors still raise.

```python
guard = InferenceBrake(api_key="ib_your_key", fail_open=True)
status = guard.check("...", "session")
if status.degraded:
    ...  # detection was skipped this step
```

Set `fail_open=False` to raise `InferenceBrakeError` instead.

## Escalation

Instead of stopping on the first loop, give the agent a chance to recover on a stronger model, then stop if it still loops. `escalate` is your hook; the SDK does not pick models.

```python
from inferencebrake import guard_agent_loop

@guard_agent_loop(
    api_key="ib_your_key",
    session_id="agent-1",
    escalate=lambda status, attempt: switch_model("claude-opus"),  # 1st, 2nd...
    max_escalations=2,
)
def call_model(prompt):
    ...
```

Order of precedence on detection:

1. `escalate(status, attempt)` while under `max_escalations`
2. `on_loop(status)`
3. raise `LoopDetectedError` when `auto_stop`

`LoopPolicy` exposes the same behavior directly, and `steering_message(status)` returns a ready-to-inject nudge:

```python
from inferencebrake import LoopPolicy, steering_message

policy = LoopPolicy(max_escalations=2, escalate=on_escalate, auto_stop=True)
policy.handle(status)
nudge = steering_message(status)
```

## Options

```python
guard = InferenceBrake(
    api_key="ib_your_key",
    timeout=10,        # request timeout in seconds
    auto_stop=False,   # raise LoopDetectedError on a detected loop
    fail_open=True,    # do not break the host agent on transport errors
    supabase_url=None, # override the API base URL (self-hosting)
)
```

Environment variable `INFERENCEBRAKE_URL` overrides the default API base URL.

## Response

`check()` returns a `CheckStatus` (alias `Status`):

| Field | Description |
| --- | --- |
| `should_stop` | `True` when the decision is `KILL` |
| `action` | `"KILL"` or `"PROCEED"` |
| `score` / `confidence` | Detection confidence, `0.0` - `1.0` |
| `similarity` | Max semantic similarity to recent steps |
| `detector_triggered` | Names of the detectors that fired |
| `detectors` | Per-detector boolean votes |
| `estimated_cost_saved` | Estimated USD saved on a halt |
| `degraded` | `True` when the API was unreachable and the guard failed open |

## Batch and history

```python
results = guard.check_batch([step1, step2, step3], session_id="my-agent")
history = guard.get_session_history("my-agent", limit=50)
```

## Analytics

`GET /functions/v1/analytics-summary` returns usage and dollars-saved totals plus a daily series for the account behind the API key.

```bash
curl -H "Authorization: Bearer ib_your_key" \
  "https://<project>.supabase.co/functions/v1/analytics-summary?days=30"
```

```json
{
  "plan": "growth",
  "total_checks": 78,
  "loops_blocked": 9,
  "estimated_usd_saved": 0.0146,
  "avg_similarity": 0.7739,
  "daily": [{ "date": "2026-09-19", "checks": 47, "loops": 8, "saved": 0.0107 }],
  "by_model": [{ "model": "gpt-4o-mini", "checks": 3, "loops": 1, "saved": 0.0019 }],
  "by_action": [{ "action": "get_balance", "checks": 3, "loops": 1, "saved": 0.0019 }],
  "by_detector": [{ "detector": "token_repeat", "loops": 1 }],
  "recent_loops": [{ "session_id": "agent-1", "model": "gpt-4o-mini", "action": "get_balance", "confidence": 0.85, "saved": 0.0019, "detectors": { "semantic": true } }]
}
```

Attribution (`by_model`, `by_action`, `by_prompt`, `by_detector`, `recent_loops`) comes from the `model`, `action`, and `prompt` you pass to `check()`. Totals reflect retained metrics, so the window is bounded by your plan's retention.

## Errors

```python
from inferencebrake import (
    InferenceBrakeError,
    AuthenticationError,
    RateLimitError,
    LoopDetectedError,
)

try:
    guard.check("...", "session")
except AuthenticationError:
    ...  # invalid API key (401)
except RateLimitError:
    ...  # daily quota exceeded (429)
except LoopDetectedError:
    ...  # loop detected with auto_stop=True
except InferenceBrakeError:
    ...  # any other API error
```

## CLI

```bash
inferencebrake --api-key ib_your_key --session demo --reasoning "check this step"
```

## License

MIT