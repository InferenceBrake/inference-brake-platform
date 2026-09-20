-- Stripe webhook idempotency.
--
-- Stripe can deliver the same event more than once. Record processed event ids
-- and ignore duplicates so plan updates are applied exactly once.

CREATE TABLE IF NOT EXISTS stripe_events (
  event_id TEXT PRIMARY KEY,
  event_type TEXT,
  processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE stripe_events ENABLE ROW LEVEL SECURITY;
-- No policies: only the service role (edge function) reads or writes this table.

CREATE OR REPLACE FUNCTION cleanup_stripe_events()
RETURNS void AS $$
BEGIN
  DELETE FROM stripe_events WHERE processed_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'stripe-events-cleanup') THEN
      PERFORM cron.unschedule('stripe-events-cleanup');
    END IF;
    PERFORM cron.schedule('stripe-events-cleanup', '30 3 * * *', 'SELECT cleanup_stripe_events();');
  END IF;
END;
$$;
