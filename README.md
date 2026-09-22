# InferenceBrake

> Kill runaway AI agents before they kill your budget

**Multi-detector loop detection for AI agents using Supabase's free embedding model (gte-small)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cost: $0](https://img.shields.io/badge/Cost-$0_embeddings-green.svg)](https://supabase.com)
[![Detectors](https://img.shields.io/badge/Detectors-8-brightgreen.svg)]()

---

## The Problem

Runaway AI agents rapidly consume API credits through loops:

```
Step 1: "I should check the weather in NYC..."
Step 2: "Let me get NYC weather data..."
Step 3: "I need to fetch weather for New York..."
Step 247: [Your OpenAI bill: $4,732.50]
```

**Real stories from the community:**

- "$700 in a single night" - r/SaaS
- "$30,000 in an agent loop" - r/AI_Agents
- "$1,400 in 6 hours" - r/Python
- "Burnt all monthly credits" - r/cursor
- "340,000 credits burned on broken fixes" - [Bolt.new doom loop](https://nocrash.io/blog/bolt-new-doom-loop)

**Why existing solutions fail:**

- ❌ **Budget limits** (Portkey, Helicone) - React AFTER burning money
- ❌ **Code loop detection** (AgentCircuit) - Only catch `while True:` loops
- ❌ **OpenRouter doom-loop detection** - Exact repeats only, scoped to OpenRouter's own Agent SDK
- ❌ **Antidoom** ([Liquid AI](https://github.com/Liquid4All/antidoom)) - Training-time only; does not help an agent already stuck in production
- ❌ **Post-deploy monitoring** (NoCrash) - Catches broken output after the run, not the loop during it
- ❌ **Manual monitoring** - Too slow, too late

**InferenceBrake detects semantic loops in reasoning:**

- ✅ Analyzes **reasoning content**, not just code patterns
- ✅ Uses **cosine similarity** on embeddings to detect repetition
- ✅ **FREE** embeddings via Supabase (gte-small, 384 dims)
- ✅ Stops execution **before** budget burn
- ✅ Works with any framework (LangChain, CrewAI, AutoGPT, custom)
- ✅ **8 detectors**: Semantic, Token Repeat, Action, N-gram, CUSUM, Entropy, Compression, Edit Distance

---

## Demo

A real OpenRouter agent is given one tool that always fails. The agent retries the same call and its reasoning converges. InferenceBrake detects the loop and halts it at step 10.

![InferenceBrake detecting a real agent loop](demo.gif)

[Watch the full recording on asciinema](https://asciinema.org/a/tlLRb0bXAfIu0otq)

Two raw editor clips of the failure mode, captured from real sessions with no inference involved:

- [OpenCode doom loop](apps/web/static/opencode-doomloop.mp4)
- [VS Code doom loop](apps/web/static/vscode-doomloop.mp4)

Try the hosted detector at https://inferencebrake.dev.

---

## Quick Start

### 1. Deploy Supabase Edge Function

```bash
# Clone repo
git clone https://github.com/InferenceBrake/inference-brake-platform
cd inference-brake-platform

# Install Supabase CLI
npm install -g supabase

# Link to your project
supabase link --project-ref YOUR_PROJECT_REF

# Deploy edge function
supabase functions deploy check

# Set environment variables
supabase secrets set SUPABASE_URL=https://YOUR_PROJECT.supabase.co
supabase secrets set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
```

### 2. Setup Database

```sql
-- Apply migrations with the Supabase CLI:
--   supabase db push
-- Migrations live in supabase/migrations/
```

### 3. Install SDK & Use

```bash
pip install inferencebrake
```

```python
from inferencebrake import InferenceBrake

# Initialize with your Supabase URL
guard = InferenceBrake(
    api_key="ib_your_key",
    supabase_url="https://yourproject.supabase.co"
)

# Monitor your agent
for step in agent.run():
    status = guard.check(step.reasoning, session_id="agent-1")
    
    if status.should_stop:
        print(f"Loop detected! Similarity: {status.similarity}")
        break
```

---

## How It Works

### Architecture

```
┌─────────────┐
│ Your Agent  │
└──────┬──────┘
       │ POST /functions/v1/check
       ↓
┌─────────────────────────────────┐
│ Supabase Edge Function (Deno)  │
│ 1. Auth & rate limit            │
│ 2. Generate embedding (FREE)    │
│ 3. Cosine similarity check      │
│ 4. Return KILL/PROCEED          │
└──────┬──────────────────────────┘
       │
       ↓
┌─────────────────────────────────┐
│ Postgres + pgvector             │
│ - Session history               │
│ - Embeddings (384 dims)         │
│ - User data & metrics           │
└─────────────────────────────────┘
```

### The Algorithm

```python
# 1. Generate embedding (Supabase gte-small model - FREE!)
embedding = await model.run(reasoning, {
    mean_pool: true,
    normalize: true
})

# 2. Compare with recent steps via SQL RPC
similarity = cosine_similarity(embedding, history_embeddings)

# 3. Decision
if similarity >= 0.85:
    return "KILL"  # Loop detected!
else:
    return "PROCEED"  # Safe to continue
```

### Why This is Better

| Feature | Portkey/Helicone | AgentCircuit | InferenceBrake |
|---------|------------------|--------------|----------------|
| **Detects** | Token/$ limits | Code loops | Semantic loops |
| **When** | After burn | During code | During reasoning |
| **Embedding cost** | N/A | N/A | **$0** (Supabase free) |
| **Framework** | Any | Python | Any (REST API) |

---

## Benchmark Status

The system uses 8 complementary detectors:

| Detector | Type | Best For |
|----------|------|----------|
| **Semantic** | Embedding similarity | Paraphrased repetition |
| **Token Repeat** | Exact repeated spans | Verbatim loops (the Antidoom / OpenRouter failure mode) |
| **Action** | Tool call patterns | Repeated actions |
| **N-gram** | Text overlap | Phrase repetition |
| **CUSUM** | Embedding drift | Early stagnation warning |
| **Entropy** | Vocabulary collapse | Information decay |
| **Compression (NCD)** | Information theory | Structural similarity |
| **Edit Distance** | Levenshtein decay | Mirror loop detection |

The hosted API runs 6 of these (semantic, token repeat, action, n-gram, edit distance, compression); CUSUM and entropy are in the Python engine.

### Token-repeat detector (Antidoom benchmark)

Prompts from [LiquidAI/antidoom-mix-v1.0](https://huggingface.co/datasets/LiquidAI/antidoom-mix-v1.0) plus repetition-inducing prompts, completed by a model at low temperature. Ground truth is a conservative repeated-span length (>=16 tokens) computed independently of the detector.

| Span threshold | Precision | Recall | F1 | False-positive rate |
| --- | --- | --- | --- | --- |
| 6 | 0.36 | 1.00 | 0.53 | 0.33 |
| 10 | 0.50 | 1.00 | 0.67 | 0.19 |
| 12 | 0.67 | 1.00 | 0.80 | 0.10 |

Sample: 25 completions, 4 severe. The default span threshold is 10: full recall on severe loops with far fewer false positives than 6. Reproduce with `uv run --project packages/engine python benchmarks/antidoom_benchmark.py --limit 20 --induce 8`. Raw results in `benchmarks/reports/antidoom_benchmark.json`.

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for running benchmarks.

---

## How InferenceBrake compares

"Doom loop" is used for several different failure modes. They are not the same problem, and no single tool covers all of them.

| Approach | When it acts | What it catches | Scope |
|----------|--------------|-----------------|-------|
| [OpenRouter doom-loop detection](https://openrouter.ai/docs/agent-sdk/call-model/doom-loop-detection) | Runtime | Exact repeats of tool calls, server tools, and text | OpenRouter's Agent SDK only |
| [Antidoom](https://github.com/Liquid4All/antidoom) (Liquid AI) | Training time | Reduces a model's tendency to repeat | Models you fine-tune |
| [NoCrash](https://nocrash.io/blog/bolt-new-doom-loop) | After deploy | Broken output that reaches users | Live app monitoring |
| [Unblocked](https://getunblocked.com/blog/ai-agent-doom-loop/) | Between sessions | Repeated mistakes caused by missing institutional context | Context/memory layer |
| **InferenceBrake** | **Runtime** | **Semantic loops plus exact token repeats** | **Any framework, any model** |

InferenceBrake is the only runtime option that is framework-agnostic and detects rephrased reasoning. The others are complementary: Antidoom reduces how often a model loops, Unblocked reduces repeated mistakes across sessions, and NoCrash catches breakage after the run. InferenceBrake stops the loop while it is happening.

---

## Integrations

Runnable examples for every integration live in [InferenceBrake/inferencebrake-examples](https://github.com/InferenceBrake/inferencebrake-examples).

### LangChain

```python
from inferencebrake import InferenceBrakeCallbackHandler

handler = InferenceBrakeCallbackHandler(
    api_key="ib_key",
    supabase_url="https://xxx.supabase.co"
)

agent = initialize_agent(tools, llm, callbacks=[handler])
```

### CrewAI

```python
from inferencebrake import create_crewai_callback

callback = create_crewai_callback(
    api_key="ib_key",
    supabase_url="https://xxx.supabase.co"
)

agent.callbacks = [callback]
```

### REST API (Any Language)

```bash
curl -X POST https://yourproject.supabase.co/functions/v1/check \
  -H "Authorization: Bearer ib_your_key" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "agent-123",
    "reasoning": "I should check the weather..."
  }'

# Response
{
  "action": "PROCEED",
  "loop_detected": false,
  "similarity": 0.42,
  "action_repeat_count": 0,
  "ngram_overlap": 0.1,
  "detectors": {
    "semantic": false,
    "action": false,
    "ngram": false
  },
  "confidence": 0.18,
  "status": "safe",
  "message": "Reasoning sound"
}
```

---

## Pricing

**Plans scale with the number of agent steps you monitor.**

| Plan | Price | Checks | Features |
|------|-------|--------|----------|
| **Free** | **$0** | 5,000/month | All 6 detectors, 7-day history |
| **Growth** | **$49/mo** | 100,000/month | Slack + webhook alerts, dollars-saved dashboard, 30-day history |
| **Pro** | **$199/mo** | 500,000/month | Custom thresholds, priority latency, 90-day history |

All plans use Supabase's free gte-small model (no embedding costs!)

---

## Tech Stack

- **Edge Function**: Deno (Supabase) - TypeScript
- **Database**: Postgres + pgvector
- **Embeddings**: Supabase AI (gte-small, 384 dims) - **FREE**
- **Frontend**: SvelteKit (Bun) - Neobrutalist UI with light/dark theming
- **Auth**: Supabase Auth
- **Payments**: Stripe (subscriptions)
- **Cost**: ~$0/mo for hobby tier (Supabase free tier)

### Why Supabase Embeddings?

- ✅ **$0 cost** (included in free tier)
- ✅ **Fast** (no external API calls)
- ✅ **384 dims** (vs OpenAI's 1536) = faster queries

### Multi-Detector Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     INFERENCEBRAKE ENGINE                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  FAST (No Embeddings)        │  SLOW (Needs Embeddings)         │
│  ─────────────────────       │  ──────────────────────          │
│  ┌──────────────┐            │  ┌──────────────┐                │
│  │   NGRAM      │            │  │   SEMANTIC   │                │
│  │  DETECTOR    │            │  │  DETECTOR    │                │
│  └──────────────┘            │  └──────────────┘                │
│  ┌──────────────┐            │  ┌──────────────┐                │
│  │   ACTION     │            │  │    CUSUM     │                │
│  │  DETECTOR    │            │  │  DETECTOR    │                │
│  └──────────────┘            │  └──────────────┘                │
│  ┌──────────────┐            │  ┌──────────────┐                │
│  │ COMPRESSION  │            │  │    ENTROPY   │                │
│  │  (NCD)       │            │  │  DETECTOR    │                │
│  └──────────────┘            │  └──────────────┘                │
│  ┌──────────────┐            │                                  │
│  │  EDIT DIST   │            │                                  │
│  │  DECAY       │            │                                  │
│  └──────────────┘            │                                  │
│         │                    │                                  │
│         └────────┬───────────┘                                  │
│                  ▼                                              │
│  ┌─────────────────────────────────────────────────────┐        │
│  │              WEIGHTED VOTING SYSTEM                 │        │
│  │           Threshold: 0.5 (configurable)             │        │
│  └──────────────────────┬──────────────────────────────┘        │
│                         │                                       │
│                         ▼                                       │
│  ┌─────────────────────────────────────────────────────┐        │
│  │                   RESPONSE                          │        │
│  │  { action: "KILL" | "PROCEED",                      │        │
│  │    confidence: 0.0-1.0,                             │        │
│  │    loop_type: "semantic" | "action" | ... }         │        │
│  └─────────────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## Documentation

### Python SDK

```python
# Initialize
guard = InferenceBrake(
    api_key="ib_key",
    supabase_url="https://xxx.supabase.co",
    timeout=10,
    auto_stop=False  # Raise exception on loop
)

# Check single step
status = guard.check(
    reasoning="text",
    session_id="sess-1",
    threshold=0.85  # Optional custom threshold
)

# Batch check
statuses = guard.check_batch(
    reasoning_list=["step1", "step2", "step3"],
    session_id="sess-1"
)

# Get session history
history = guard.get_session_history(
    session_id="sess-1",
    limit=50
)
```

### CheckStatus Object

```python
status.action          # "KILL" or "PROCEED"
status.loop_detected   # boolean
status.similarity      # float (0.0 - 1.0)
status.status          # "safe", "warning", or "danger"
status.message         # human-readable message
status.should_stop     # convenience property
```

### JavaScript/Node.js SDK

```javascript
const { InferenceBrake } = require('inferencebrake');

const guard = new InferenceBrake({
  apiKey: 'ib_your_key',
  supabaseUrl: 'https://xxx.supabase.co',
  
  // Resilience options (all optional)
  timeout: 10000,              // Request timeout in ms (default: 10000)
  maxRetries: 3,                // Max retry attempts (default: 3)
  retryDelay: 1000,             // Initial retry delay in ms (default: 1000)
  retryBackoff: 2,              // Exponential backoff multiplier (default: 2)
  circuitBreakerThreshold: 5,   // Failures before opening circuit (default: 5)
  circuitBreakerTimeout: 30000, // Circuit reset timeout in ms (default: 30000)
});

// Check single step
const status = await guard.check(
  'reasoning text',
  'session-1'
);

if (status.shouldStop) {
  console.log('Loop detected!', status.message);
}

// Check offline queue status
console.log('Queued requests:', guard.getQueueSize());
console.log('Online:', guard.isOnline());
```

**SDK Features:**
- Automatic retry with exponential backoff
- Circuit breaker pattern for fault tolerance
- Offline detection and request queueing
- Configurable timeouts

---

## Development

### Local Setup

```bash
# Clone repo
git clone https://github.com/InferenceBrake/inference-brake-platform
cd inference-brake-platform

# Install dependencies (uses bun for web, uv for Python)
cd apps/web && bun install && cd ../..
cd packages/engine && uv sync && cd ../..

# Start Supabase locally
supabase start

# Run web dev server
cd apps/web && bun run dev

# In another terminal, serve edge functions
supabase functions serve check --no-verify-jwt

# Run the engine test suite
cd packages/engine && uv run pytest -q
```

### Environment Variables

```bash
# apps/web/.env (use VITE_ prefix for client-side vars)
VITE_PUBLIC_SUPABASE_URL=http://localhost:54321
VITE_PUBLIC_SUPABASE_ANON_KEY=your-anon-key

# Supabase edge function secrets (supabase secrets set ...)
STRIPE_SECRET_KEY=sk_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_GROWTH_PRICE_ID=price_...
STRIPE_PRO_PRICE_ID=price_...
PUBLIC_SITE_URL=https://inferencebrake.dev

# Email loop alerts (optional; alerts are skipped when unset)
RESEND_API_KEY=re_...
ALERT_FROM_EMAIL=alerts@inferencebrake.dev

# Optional: Sentry error tracking
SENTRY_ORG=your-org
SENTRY_PROJECT=your-project
VITE_PUBLIC_SENTRY_DSN=https://xxx@sentry.io/xxx
```

---

## Project Structure

```
inferencebrake/
├── apps/
│   ├── web/                    # SvelteKit frontend (Vercel)
│   │   ├── src/
│   │   │   └── routes/
│   │   └── package.json
│
├── packages/
│   ├── engine/                 # Python detection engine
│   │   └── inferencebrake/
│   ├── python-sdk/            # PyPI package
│   └── js-sdk/                # NPM package (index.js, index.d.ts)
│
├── supabase/
│   ├── migrations/
│   ├── config.toml
│   └── functions/             # Supabase Edge Functions
│       ├── check/
│       ├── stripe-checkout/
│       ├── stripe-webhook/
│       ├── stripe-cancel/
│       ├── account-delete/
│       ├── generate-test-key/
│       └── health/
│
├── tests/                     # Integration tests (Bun)
└── benchmarks/                # Benchmarking suite
```

---

## Roadmap

### Completed

- [x] Core loop detection (8 detectors in the engine; 6 live in the hosted API)
- [x] Supabase Edge Function
- [x] Python SDK with LangChain & CrewAI integrations
- [x] Node.js SDK with retry/circuit-breaker/offline queue
- [x] SvelteKit landing page
- [x] User authentication (signup/login)
- [x] Dashboard with session history
- [x] SQL migrations & RPC functions
- [x] Health check endpoint
- [x] Error tracking (Sentry)
- [x] Test mode API keys
- [x] Data retention policies
- [x] GDPR data export
- [x] Slack webhook alerts
- [x] Waitlist for beta users

### In Progress

- [ ] Beta launch & user feedback
- [ ] Threshold customization UI

### Planned

- [ ] Pro plan with payments (Stripe)
- [ ] Webhook configuration UI
- [ ] Self-hosted deployment guide

---

## Contributing

We welcome contributions! Areas we need help:

- [ ] Go SDK
- [ ] More framework integrations
- [ ] Better visualization dashboards
- [ ] Documentation improvements

Open an issue or a pull request - all contributions are reviewed.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Community & Support

- **Discord**: [discord.gg/inferencebrake](https://discord.gg/inferencebrake)
- **Twitter**: [@inferencebrake](https://twitter.com/inferencebrake)
- **Email**: <support@inferencebrake.dev>
- **Docs**: [docs.inferencebrake.dev](https://docs.inferencebrake.dev)

---

## Acknowledgments

Built with:

- [Supabase](https://supabase.com) - Free embeddings + database
- [pgvector](https://github.com/pgvector/pgvector) - Vector similarity
- [Vercel](https://vercel.com) - Frontend hosting

Inspired by:

- Portkey (budget limits)
- Helicone (observability)
- AgentCircuit (code loop detection)

---

## Get Started

```bash
# 1. Sign up at https://inferencebrake.dev (free plan available)
# 2. Get your API key from the dashboard
# 3. Install SDK
pip install inferencebrake

# 4. Start protecting your agents
from inferencebrake import InferenceBrake
guard = InferenceBrake(api_key="ib_key", supabase_url="...")
```

**No credit card required. 5,000 checks/month on the Free plan.**

[Get Started Free](https://inferencebrake.dev) · [View Demo](https://inferencebrake.dev/demo) · [Read Docs](https://docs.inferencebrake.dev)
