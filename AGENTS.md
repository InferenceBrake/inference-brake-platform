# AGENTS.md - OpenCode Agent Instructions

This file tells opencode how to work with this project.

Role: You are a senior software engineer. Your communication style is minimalist, technical, and objective.

## Instructions for all Documentation and Commits

1. Tone and Vocabulary
    - No Fluff: Remove all adjectives like "seamless," "powerful," "comprehensive," or "revolutionary."
    - No Hype: Never use phrases like "Let's build," "Unlock the potential," "Built with love," or "Next steps to success."
    - Neutral Voice: Write in the imperative mood for instructions (e.g., "Install dependencies" instead of "You can easily install the dependencies").
    - Directness: If a feature is a work-in-progress, state "Status: Incomplete" rather than "Exciting updates coming soon."

2. Visual Style (Emoji Policy)
    - Strict Prohibition: Never use "fluff" emojis: 🚀, ✨, 🙌, 🔥, 💡, 💎.
    - Avoid use of special quotes “marks” or „‟ and ― bars, — em dash,  – en dash etc. Humans don't type those.
    - Allowed Symbols: Use ONLY functional status indicators:
        - ✅ (Pass / Complete)
        - ❌ (Fail / Error)
        - 🔴 (Critical / Stop)
        - 🟢 (Active / Running)
    - Diagrams: Use standard ASCII/Unicode box-drawing characters (├──, └──, │) for directory trees.

3. Git Commit Standards
    - Format: Action: Subject (e.g., Fix: authentication bypass in login.py).
    - Content: Describe what changed and why. Never summarize the "journey" or "excitement" of the code change.
    - Length: Keep the first line under 50 characters.

**Constraint: I will penalize any response that uses marketing-speak or unnecessary emojis. Focus 100% on technical accuracy and 0% on presentation fluff.**

## Project Overview

InferenceBrake is a multi-detector loop detection system for AI agents. It detects when AI agents get stuck in reasoning loops and stops them before they burn through budget.

## Tech Stack

- **Frontend/Web**: Bun + SvelteKit (TypeScript)
- **Backend/Edge Functions**: Deno (Supabase Edge Functions)
- **Python Engine**: `uv` for package management
- **Database**: Supabase (PostgreSQL + pgvector)
- **Embeddings**: Supabase AI (gte-small, 384 dims) - FREE

## Commands

### Root / Monorepo

```bash
# Install all dependencies (runs bun install for all workspaces)
bun install

# Run tests
bun run test

# Start local Supabase
bunx supabase start
```

### Python / Engine

```bash
# Install dependencies
cd packages/engine && uv sync

# Run a Python script
cd packages/engine && uv run python path/to/script.py
```

### Benchmarks

```bash
# Run benchmarks
uv run python -m benchmarks.run_benchmarks
```

### Web / Frontend (SvelteKit)

```bash
# Install dependencies
cd apps/web && bun install

# Run dev server
cd apps/web && bun run dev

# Build for production
cd apps/web && bun run build
```

### Supabase Edge Functions

```bash
# Deploy edge function
cd supabase/functions && bunx supabase functions deploy check

# Run migrations
bunx supabase db push
```

## Project Structure

```
inferencebrake/
├── apps/
│   ├── web/                      # SvelteKit frontend (Vercel)
│   │   ├── src/
│   │   │   ├── routes/
│   │   │   │   ├── +layout.svelte
│   │   │   │   ├── +page.svelte
│   │   │   │   ├── login/
│   │   │   │   ├── register/
│   │   │   │   └── dashboard/
│   │   │   ├── app.css
│   │   │   └── lib/
│   │   │       └── supabase.ts
│   │   ├── package.json
│   │   └── vite.config.ts
│   │
│   └── functions/                # Supabase Edge Functions (Deno)
│       ├── check/
│       ├── stripe-checkout/
│       └── stripe-webhook/
│
├── packages/
│   ├── engine/                   # Python detection engine
│   │   ├── pyproject.toml
│   │   └── inferencebrake/
│   │       ├── pipeline.py
│   │       ├── types.py
│   │       └── detectors/
│   │
│   ├── python-sdk/              # PyPI package
│   │   ├── pyproject.toml
│   │   └── inferencebrake_sdk.py
│   │
│   ├── js-sdk/                  # NPM package
│   │   ├── package.json
│   │   └── index.js
│   │
│   └── core/                    # Shared types (optional)
│
├── supabase/                    # Database config
│   ├── migrations/
│   ├── config.toml
│   └── functions/               # Supabase Edge Functions (Deno)
│       ├── check/
│       ├── stripe-checkout/
│       ├── stripe-webhook/
│       ├── stripe-cancel/
│       ├── account-delete/
│       ├── generate-test-key/
│       └── health/
│
├── tests/                       # Integration tests (Bun)
│   ├── basicTest.ts
│   └── rateLimitTest.ts
│
├── benchmarks/                  # Benchmarking suite
├── benchmark_data/             # Test data
├── package.json                # Root with workspaces
└── pyproject.toml              # Root Python config (legacy)
```

## Key Files

- `packages/engine/inferencebrake/pipeline.py` - Main detection orchestration
- `packages/engine/inferencebrake/types.py` - Config and threshold settings
- `supabase/functions/check/index.ts` - Edge function entry point
- `supabase/migrations/` - SQL schema and RPC functions
- `apps/web/src/routes/+page.svelte` - Landing page
- `apps/web/src/routes/dashboard/+page.svelte` - User dashboard
- `packages/js-sdk/index.js` - JavaScript SDK
- `packages/python-sdk/inferencebrake_sdk.py` - Python SDK

## Running Tests

```bash
# Integration tests (requires Supabase)
bun run test

# Python benchmarks
uv run python -m benchmarks.run_benchmarks
```

## Building & Deploying

```bash
# Build web (SvelteKit with Vercel adapter)
cd apps/web && bun run build

# Deploy to Vercel (auto-deploys on git push)
# Ensure environment variables are set in Vercel:
# - PUBLIC_SUPABASE_URL
# - PUBLIC_SUPABASE_ANON_KEY
```

## Publishing Packages

```bash
# Publish Python SDK to PyPI
cd packages/python-sdk
uv publish

# Publish JS SDK to NPM
cd packages/js-sdk
npm publish
```

## Landing Page Structure

The landing page (`apps/web/src/routes/+page.svelte`) uses a split hero layout:

- **Left (solution)**: Headline, description, CTA buttons
- **Right (problem)**: Real Reddit stories as clickable cards linking to source posts

The detector cards in the "7 Detection Methods" section should link to relevant research papers.

## Adding New Detectors

1. Create detector in `packages/engine/inferencebrake/detectors/`
2. Inherit from `BaseDetector`
3. Implement `detect()` method returning `DetectionSignal`
4. Add to `PipelineConfig.enabled_detectors`
5. Add weights in `PipelineConfig.detector_weights`
6. Add thresholds in `ThresholdConfig`

## OpenCode Notes

- Use `frontend-design` skill for UI decisions
- This project uses SvelteKit for the frontend
- Use Svelte 5 runes ($state, $derived, $effect) in .svelte files
- Python dependencies managed via `pyproject.toml` and `uv`
- Benchmarks can take a long time - use smaller subsets for testing
