# InferenceBrake JavaScript SDK

Loop detection for AI agents. Detect and stop runaway reasoning loops before they burn your token budget.

Runs your agent's reasoning step through five detectors (semantic similarity, action repetition, n-gram overlap, edit distance, compression distance) and returns a `KILL`/`PROCEED` decision. On a detected loop it also returns an estimated dollar amount saved by halting it.

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

const status = await guard.check('Let me search for the weather in NYC', 'agent-session-123');

console.log(status.action);              // 'PROCEED' or 'KILL'
console.log(status.similarity);          // 0.0 - 1.0
console.log(status.shouldStop);          // true when action === 'KILL'
console.log(status.estimatedCostSaved);  // estimated USD saved on a KILL
```

ES modules:

```js
import { InferenceBrake } from 'inferencebrake';
```

Wrap an agent loop:

```js
const { InferenceBrake } = require('inferencebrake');

const guard = new InferenceBrake({ apiKey: 'ib_your_key' });

for (const step of await agent.run()) {
  const status = await guard.check(step.reasoning, 'my-agent');

  if (status.shouldStop) {
    console.log(`Loop detected: ${status.message}`);
    break;
  }
}
```

## Options

```js
const guard = new InferenceBrake({
  apiKey: 'ib_your_key',
  supabaseUrl: undefined,       // override API base URL (self-hosting)
  timeout: 10000,               // request timeout in ms
  autoStop: false,              // throw on a detected loop
  maxRetries: 3,                // retries on transient errors
  retryDelay: 1000,             // initial retry delay in ms
  retryBackoff: 2,              // exponential backoff multiplier
  circuitBreakerThreshold: 5,   // consecutive failures before opening
  circuitBreakerTimeout: 30000, // ms before a half-open attempt
});
```

Environment variable `INFERENCEBRAKE_URL` overrides the default API base URL.

## Errors

```js
const {
  InferenceBrakeError,
  AuthenticationError,
  RateLimitError,
  CircuitBreakerError,
} = require('inferencebrake');

try {
  await guard.check(reasoning, sessionId);
} catch (e) {
  if (e instanceof AuthenticationError) { /* invalid API key (401) */ }
  else if (e instanceof RateLimitError) { /* daily quota exceeded (429) */ }
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
