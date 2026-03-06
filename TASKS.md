# TASKS.md - InferenceBrake Autonomous Development Roadmap

This file serves as an autonomous backlog for AI agents to continuously improve InferenceBrake into a production-ready product.

## How to Use

AI agents should:

1. Pick highest priority tasks from **TODO** sections
2. Implement features following existing code patterns
3. Run benchmarks/tests after changes
4. Update this file as tasks complete
5. Report results in commit messages

---

## MVP - Must Have (Priority 0)

### Landing Page

- [x] Make detector cards clickable with links to relevant papers/research

### Authentication & User Management

- [x] Fix Firefox scroll restoration bug (marked with FIXME in app.html)
- [x] Add password reset functionality
- [x] Add email verification flow (via Supabase Auth)
- [x] Add user profile page (dashboard shows email/plan)
- [x] Add logout confirmation

### Payments & Billing (Stripe)

- [x] Create Stripe account (setup required)
- [x] Add Stripe fields to users table (stripe_customer_id, stripe_subscription_id, plan, subscription_status)
- [x] Create Stripe products (Hobby $0, Pro $9)
- [x] Implement subscription checkout (Stripe Checkout Session) - demo mode works without Stripe
- [x] Add Stripe webhook edge function (handle invoice.paid, customer.subscription.deleted, etc.)
- [x] Add daily_limit based on plan (hobby: 100, pro: 10000)
- [x] Add rate limiting check before processing requests

### API Key Management

- [x] Add secure API key generation (ib_ prefix + 64 char random)
- [x] Add "Regenerate API Key" button in dashboard
- [x] Add API key display (show/hide toggle)
- [x] Add API key usage stats (requests today)
- [x] Add "Copy API Key" button
- [x] Add test mode keys (sandbox - doesn't count against limit)

### Dashboard

- [x] Add session detail view (click session → see all steps)
- [x] Add loop visualization (show when each detector fired)
- [x] Add date range filter for sessions
- [x] Add export to CSV functionality
- [x] Add delete session functionality
- [x] Add current plan display with upgrade button
- [x] Add usage meter (X of Y checks today) with auto-refresh

### API & SDK

- [x] Verify Node.js SDK works with latest edge function
- [x] Add TypeScript types to Node.js SDK
- [x] Add rate limit headers to API responses (X-RateLimit-Remaining, X-RateLimit-Reset)

### Testing

- [x] Add unit tests for edge function
- [x] Add edge function benchmark test
- [ ] Add E2E tests for auth flow (register → login → dashboard)
- [x] Add E2E tests for API (check endpoint)

---

## Production Ready (Priority 1)

### Reliability

- [x] Add retry logic to SDKs (exponential backoff)
- [x] Add timeout handling (default 10s, configurable)
- [x] Add circuit breaker pattern for API calls
- [x] Add offline detection and queueing

### Performance

- [ ] Benchmark edge function cold start time
- [ ] Add caching for embeddings (skip if recent session)
- [x] Optimize SQL queries (add composite indexes)
- [ ] Benchmark vs competitors (Portkey, Helicone)

### Monitoring

- [x] Add health check endpoint (/health)
- [x] Add error tracking (Sentry integration)
- [ ] Add analytics dashboard for admin
- [ ] Add uptime monitoring

### Data

- [x] Add data retention policies (auto-delete old sessions)
- [x] Add GDPR export functionality
- [x] Add account deletion (with confirmation)

---

## Integrations (Priority 2)

### Framework Integrations

- [x] Add LangChain callback handler
- [x] Add CrewAI integration example
- [ ] Add LlamaIndex integration
- [ ] Add AutoGen integration example

### Platform Integrations

- [x] Add Slack webhook alerts
- [ ] Add Discord webhook alerts
- [ ] Add PagerDuty integration
- [ ] Add Zapier/NMake webhook support

### SDKs

- [ ] Add Go SDK
- [ ] Add Ruby SDK
- [ ] Add PHP SDK

---

## Developer Experience (Priority 2)

### Documentation

- [ ] Add API reference docs (OpenAPI spec)
- [ ] Add integration guides (LangChain, CrewAI, etc.)
- [ ] Add troubleshooting guide
- [ ] Add video tutorials

### Tools

- [ ] Add CLI tool for local testing
- [ ] Add playground page in dashboard
- [ ] Add curl/SDK code generator in dashboard
- [ ] Add webhook tester in dashboard

---

## Enterprise Features (Priority 3)

### Security

- [ ] Add SSO/SAML support
- [ ] Add IP allowlist
- [ ] Add audit logs
- [ ] Add API key rotation

### Compliance

- [ ] Add SOC 2 documentation
- [ ] Add HIPAA compliance mode
- [ ] Add data residency options (EU, US, etc.)

### Scaling

- [ ] Add multi-region support
- [ ] Add dedicated infrastructure tier
- [ ] Add custom model support (use your own embeddings)

---

## Benchmarking Tasks (Run Regularly)

### Detection Accuracy

```bash
# Run full benchmark suite
cd engine && uv run python -m benchmarks.run_benchmarks --traces 100
```

### Latency

```bash
# Measure P50, P95, P99 latency
# Target: P95 < 500ms
```

### Cost Analysis

```bash
# Calculate cost per 1M checks
```

---

## Experiment Ideas (Exploration Phase)

### New Detectors

- [ ] Experiment with different embedding models (e5, bge)
- [ ] Add LLM-based detector (use GPT-4 for loop判断)
- [ ] Add visual loop detector (screenshots)
- [ ] Add audio pattern detector (voice agents)

### Advanced Features

- [ ] Add loop prediction (predict next step will loop)
- [ ] Add recovery suggestions (how to escape loop)
- [ ] Add loop severity scoring
- [ ] Add agent "personality" detection

### Research

- [ ] Survey: How do top AI agents handle loops?
- [ ] Paper: Multi-detector loop detection in production
- [ ] Blog: How we built InferenceBrake for <$1/mo

---

## Reporting Template

When completing a task, document:

```
## Completed: [Task Name]

**Date**: YYYY-MM-DD
**Time Spent**: X hours
**Changes Made**:
- [list of files changed]

**Testing**:
- [ ] Unit tests pass
- [ ] Manual verification
- [ ] Performance impact: [none/low/medium/high]

**Notes**:
[Any learnings, tradeoffs, or follow-ups needed]
```

---

## Prioritization Guidelines

| Priority | Criteria |
|----------|----------|
| **P0** | Blocks first paying customer |
| **P1** | Blocks production use |
| **P2** | Improves DX or enables integrations |
| **P3** | Nice to have, competitive advantage |

---

## Quick Start for AI Agent

1. **Check for regressions**: Run `bun run tests/basicTest.ts`
2. **Build web**: `cd web && bun run build`
3. **Deploy edge**: `supabase functions deploy check`
4. **Verify**: Test locally with curl or SDK

---

*Last Updated: 2026-03-05*
*Version: 0.2.1*
