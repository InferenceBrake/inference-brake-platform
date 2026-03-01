# InferenceBrake - Complete Deployment Guide

This guide covers setting up the development environment, running the research-backed benchmarking suite, and deploying the Supabase backend.

## Prerequisites

- **Python 3.10+** (Managed via `uv` recommended)
- **Node.js 18+** & **Bun** (for Supabase edge functions)
- **Supabase CLI** (`npm install -g supabase`)
- **Docker** (Required for local Supabase)

## Installation (Local Dev)

We use `uv` for Python package management.

1. **Install uv:**

    ```bash
    pip install uv
    # or
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```

2. **Sync Dependencies:**
    This installs the project, all extras (via the dev group), and development tools.

    ```bash
    uv sync
    ```

3. **Install Node Dependencies:**

    ```bash
    bun install
    ```

## Running Benchmarks

Validate the detection engine performance locally against synthetic traces.

```bash
# Run standard benchmark suite (50 traces per category)
uv run python -m benchmarks.run_benchmarks --traces 50 --verbose

# Run threshold sweep to optimize parameters
uv run python -m benchmarks.run_benchmarks --sweep

# Run detector ablation study (see which detector contributes most)
uv run python -m benchmarks.run_benchmarks --ablation
```

Reports are saved to `benchmarks/reports/` in JSON, Markdown, and TXT formats.

## Supabase Local Development

1. **Start Supabase:**

    ```bash
    supabase start
    ```

2. **Apply Migrations:**
    This creates the `users`, `reasoning_history` tables and the `detect_semantic_loop` RPC.

    ```bash
    supabase db reset
    ```

3. **Serve Edge Functions:**
    Runs the `check` function locally with hot-reload.

    ```bash
    supabase functions serve --no-verify-jwt
    ```

4. **Test the API:**

    ```bash
    curl -i --location --request POST 'http://127.0.0.1:54321/functions/v1/check' \
      --header 'Authorization: Bearer ib_test_key_123' \
      --header 'Content-Type: application/json' \
      --data '{"session_id": "test_1", "reasoning": "I should check the weather"}'
    ```

## Production Deployment

1. **Link to Supabase Project:**

    ```bash
    supabase link --project-ref your-project-id
    ```

2. **Push Database Schema:**

    ```bash
    supabase db push
    ```

3. **Deploy Edge Functions:**

    ```bash
    supabase functions deploy check --no-verify-jwt
    ```

4. **Set Secrets:**

    ```bash
    supabase secrets set SUPABASE_URL=... SUPABASE_SERVICE_ROLE_KEY=...
    ```

## Frontend Deployment

The `apps/web/` folder contains a SvelteKit application.

1. **Install & Build:**

    ```bash
    cd apps/web
    bun install
    bun run build
    ```

2. **Deploy to Vercel:**
    - Connect your GitHub repo to Vercel
    - Or run `vercel deploy`

3. **Environment Variables:**

    ```
    PUBLIC_SUPABASE_URL=https://your-project.supabase.co
    PUBLIC_SUPABASE_ANON_KEY=your-anon-key
    ```

## Authentication

The app uses Supabase Auth for user management:

1. Users sign up via `/register` (email/password)
2. On signup, a user record is created in the `users` table with an API key
3. Users can access `/dashboard` to see their session history
4. API key is stored in localStorage for SDK use

## Python SDK Distribution

To publish the SDK to PyPI:

1. **Build:**

    ```bash
    cd packages/python-sdk
    uv build
    ```

2. **Publish:**

    ```bash
    cd packages/python-sdk
    uv publish
    ```

---

## Business Model & Pricing

### Strategy: Open Core

- **Engine (Local):** Free, Open Source (MIT).
- **Platform (Hosted):** Paid SaaS for reliability, alerts, and advanced models.

### Pricing Tiers

- **Hobby (Free)**
  - Self-hosted or hosted API
  - All 7 detectors via default voting
  - 1,000 checks/day
  - 7-day history
  - Community support

- **Pro ($9/mo)**
  - Hosted API (no infra management)
  - 10k checks/day
  - Detector customization
  - Custom thresholds per detector
  - Auto-loop resolution hooks
  - Email/Webhook alerts
  - 90-day history retention

- **Enterprise (Coming Soon)**
  - Custom limits
  - Priority support
  - Custom integrations

---

## Monitoring & Observability

- **Local:** Check `supabase/functions/check` logs in the terminal.
- **Production:** Use the Supabase Dashboard > Edge Functions > Logs.
