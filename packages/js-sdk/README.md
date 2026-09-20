# InferenceBrake JavaScript SDK

Loop detection for AI agents. Detect and stop runaway reasoning loops before they burn your token budget.

Runs each agent step through six detectors (semantic similarity, token repetition, action repetition, n-gram overlap, edit distance, compression distance) and returns a `KILL`/`PROCEED` decision. On a detected loop it returns an estimated dollar amount saved by halting it.

Framework-agnostic: LangChain.js, raw OpenAI/Anthropic, or any custom loop. Detection is semantic, so it catches reasoning that repeats the same idea in different words, not just exact repeats.

- Docs: https://inferencebrake.dev/docs
- Dashboard / API keys: https://inferencebrake.dev

## Install

```bash
npm install inferencebrake
```

Requires Node.js 18+ (uses `fetch` and `AbortSignal.timeout`). Works in modern browsers.

## Quickstart

```js
const { InferenceBrake } = require('inferencebrake');

const guard = new InferenceBrake({ apiKey: 'ib_your_key' });

const status = await guard.check('Let me search for the weather in NYC', 'agent-session-123', {
  action: 'web_search', // optional, enables action repetition detection
});

status.shouldStop            // true when a loop was detected
status.score                 // detection confidence, 0.0 - 1.0
status.detectorTriggered     // e.g. "semantic, token_repeat, compression"
status.estimatedCostSaved    // estimated USD saved on a halt
```

ES modules:

```js
import { InferenceBrake } from 'inferencebrake';
```

## Options

```js
const guard = new InferenceBrake({
  apiKey: 'ib_your_key',
  supabaseUrl: undefined,       // override API base URL (self-hosting)
  timeout: 10000,               // request timeout in ms
  autoStop: false,              // throw LoopDetectedError on a detected loop
  failOpen: true,               // do not break the host agent on transport errors
  maxRetries: 3,                // retries on transient errors
  retryDelay: 1000,             // initial retry delay in ms
  retryBackoff: 2,              // exponential backoff multiplier
  circuitBreakerThreshold: 5,   // consecutive failures before opening
  circuitBreakerTimeout: 30000, // ms before a half-open attempt
});
```

Environment variable `INFERENCEBRAKE_URL` overrides the default API base URL.

## Fail-open

By default the guard **fails open**: on a network error or 5xx it logs a warning and returns a safe `CheckStatus` with `degraded: true` instead of breaking your agent. Auth (401) and rate limit (429) errors still throw.

```js
const status = await guard.check('...', 'session');
if (status.degraded) {
  // detection was skipped this step
}
```

Set `failOpen: false` to throw instead.

## Escalation

Give the agent a chance to recover on a stronger model, then stop if it still loops. `escalate` is your hook; the SDK does not pick models.

```js
const { guarded } = require('inferencebrake');

const callModel = guarded(async (prompt) => {
  return openai.chat.completions.create({ model: 'gpt-4o-mini', messages: [...] });
}, {
  apiKey: 'ib_your_key',
  sessionId: 'agent-1',
  escalate: (status, attempt) => switchModel('gpt-4o'), // 1st, 2nd...
  maxEscalations: 2,
});
```

Order of precedence on detection:

1. `escalate(status, attempt)` while under `maxEscalations`
2. `onLoop(status)`
3. throw `LoopDetectedError` when `autoStop`

`LoopPolicy` exposes the same behavior directly, and `steeringMessage(status)` returns a ready-to-inject nudge:

```js
const { LoopPolicy, steeringMessage } = require('inferencebrake');

const policy = new LoopPolicy({ maxEscalations: 2, escalate: onEscalate });
policy.handle(status);
const nudge = steeringMessage(status);
```

## LangChain.js

```js
const { InferenceBrakeCallbackHandler } = require('inferencebrake');

const handler = new InferenceBrakeCallbackHandler({ apiKey: 'ib_your_key' });
const result = await chain.invoke(input, { callbacks: [handler] });
```

The handler implements `handleLLMStart`, `handleLLMEnd`, and `handleLLMError`, and raises `LoopDetectedError` on a detected loop.

## Errors

```js
const {
  InferenceBrakeError,
  AuthenticationError,
  RateLimitError,
  CircuitBreakerError,
  LoopDetectedError,
} = require('inferencebrake');

try {
  await guard.check(reasoning, sessionId);
} catch (e) {
  if (e instanceof AuthenticationError) { /* invalid API key (401) */ }
  else if (e instanceof RateLimitError) { /* monthly quota exceeded (429) */ }
  else if (e instanceof LoopDetectedError) { /* loop detected with autoStop */ }
  else if (e instanceof CircuitBreakerError) { /* too many failures */ }
}
```

## Batch and history

```js
const results = await guard.checkBatch([step1, step2, step3], 'my-agent');
const history = await guard.getSessionHistory('my-agent', 50);
```

## License

MIT
