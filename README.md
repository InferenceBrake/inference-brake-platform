# InferenceBrake

> Kill runaway AI agents before they kill your budget

**Multi-detector loop detection for AI agents using Supabase's free embedding model (gte-small)**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Cost: $0](https://img.shields.io/badge/Cost-$0_embeddings-green.svg)](https://supabase.com)
[![Detectors](https://img.shields.io/badge/Detectors-7-brightgreen.svg)]()

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

**Why existing solutions fail:**

- ❌ **Budget limits** (Portkey, Helicone) - React AFTER burning money
- ❌ **Code loop detection** (AgentCircuit) - Only catch `while True:` loops
- ❌ **Manual monitoring** - Too slow, too late

**InferenceBrake detects semantic loops in reasoning:**

- ✅ Analyzes **reasoning content**, not just code patterns
- ✅ Uses **cosine similarity** on embeddings to detect repetition
- ✅ **FREE** embeddings via Supabase (gte-small, 384 dims)
- ✅ Stops execution **before** budget burn
- ✅ Works with any framework (LangChain, CrewAI, AutoGPT, custom)
- ✅ **7 detectors**: Semantic, Action, N-gram, CUSUM, Entropy, Compression, Edit Distance

---

## Quick Start

### 1. Deploy Supabase Edge Function

```bash
# Clone repo
git clone https://github.com/yourusername/inferencebrake
cd inferencebrake

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
-- Run in Supabase SQL Editor
-- See supabase-schema.sql for complete schema
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

The system uses 7 complementary detectors:

| Detector | Type | Best For |
|----------|------|----------|
| **Semantic** | Embedding similarity | Paraphrased repetition |
| **Action** | Tool call patterns | Repeated actions |
| **N-gram** | Text overlap | Phrase repetition |
| **CUSUM** | Embedding drift | Early stagnation warning |
| **Entropy** | Vocabulary collapse | Information decay |
| **Compression (NCD)** | Information theory | Structural similarity |
| **Edit Distance** | Levenshtein decay | Mirror loop detection |

See [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for running benchmarks.

---

## Integrations

### LangChain

```python
from inferencebrake import InferenceBrakeCallback

callback = InferenceBrakeCallback(
    api_key="ib_key",
    supabase_url="https://xxx.supabase.co"
)

agent = initialize_agent(tools, llm, callbacks=[callback])
```

### CrewAI

```python
from inferencebrake import InferenceBrake

guard = InferenceBrake(api_key="ib_key", supabase_url="...")

def after_task(task):
    status = guard.check(task.output, session_id=crew.id)
    if status.should_stop:
        crew.stop()
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

| Plan | Price | Checks/Day | Features |
|------|-------|------------|----------|
| **Hobby** | **$0** | 100 | Free embeddings, 7-day history |
| **Pro** | $9/mo | 10,000 | Webhooks, 90-day history, dashboard |
| **Enterprise** | Coming Soon | Custom | Priority support |

**All plans use Supabase's free gte-small model (no OpenAI costs!)**

---

## Tech Stack

- **Edge Function**: Deno (Supabase) - TypeScript
- **Database**: Postgres + pgvector
- **Embeddings**: Supabase AI (gte-small, 384 dims) - **FREE**
- **Frontend**: SvelteKit (Bun) - Dark industrial design
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

---

## Development

### Local Setup

```bash
# Clone repo
git clone https://github.com/yourusername/inferencebrake
cd inferencebrake

# Install dependencies (uses bun for web, uv for Python)
cd web && bun install && cd ..
cd engine && uv sync && cd ..

# Start Supabase locally
supabase start

# Run web dev server
cd web && bun run dev

# In another terminal, serve edge functions
supabase functions serve check --no-verify-jwt
```

### Environment Variables

```bash
# apps/web/.env
PUBLIC_SUPABASE_URL=http://localhost:54321
PUBLIC_SUPABASE_ANON_KEY=your-anon-key
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
│   └── functions/              # Supabase Edge Functions (Deno)
│       ├── check/
│       └── stripe-checkout/
│
├── packages/
│   ├── engine/                 # Python detection engine
│   │   └── inferencebrake/
│   │       ├── pipeline.py
│   │       ├── types.py
│   │       └── detectors/
│   ├── python-sdk/            # PyPI package
│   └── js-sdk/                # NPM package
│
├── supabase/                   # Database config
│   ├── migrations/
│   └── config.toml
│
├── tests/                      # Integration tests (Bun)
├── benchmarks/                 # Benchmarking suite
└── benchmark_data/             # Test data
```

---

## Roadmap

### ✅ Completed

- [x] Core loop detection (7 detectors)
- [x] Supabase Edge Function
- [x] Python SDK
- [x] Node.js SDK
- [x] SvelteKit landing page
- [x] User authentication (signup/login)
- [x] Dashboard with session history
- [x] SQL migrations & RPC functions

### In Progress

- [ ] Live demo page
- [ ] Webhook alerts
- [ ] User settings (thresholds, sensitivity)

### Planned

- [ ] Self-hosted deployment guide
- [ ] LangChain integration
- [ ] CrewAI integration
- [ ] Team features

---

## Contributing

We welcome contributions! Areas we need help:

- [ ] Node.js/TypeScript SDK
- [ ] Go SDK
- [ ] More framework integrations
- [ ] Better visualization dashboards
- [ ] Documentation improvements
- [ ] Test coverage

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

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
# 1. Sign up for Supabase (free tier)
# 2. Deploy edge function (1 command)
# 3. Install SDK
pip install inferencebrake

# 4. Start protecting your agents
from inferencebrake import InferenceBrake
guard = InferenceBrake(api_key="ib_key", supabase_url="...")
```

**No credit card required. Free forever for hobby projects.**

[Get Started Free](https://inferencebrake.dev) · [View Demo](https://inferencebrake.dev/demo) · [Read Docs](https://docs.inferencebrake.dev)
