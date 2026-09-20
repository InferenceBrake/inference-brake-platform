-- Monthly quota support.
--
-- Enforcement moves to a monthly counter (checks_this_month / monthly_limit).
-- The daily counter is retained for display and burst visibility. Both counters
-- are reset by pg_cron. Previously reset_daily_checks was never scheduled, so
-- the daily counter never reset.

ALTER TABLE users ADD COLUMN IF NOT EXISTS checks_this_month INTEGER NOT NULL DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS monthly_limit INTEGER;

-- Backfill monthly_limit from plan.
UPDATE users
SET monthly_limit = CASE plan
  WHEN 'pro' THEN 500000
  WHEN 'growth' THEN 100000
  ELSE 5000
END
WHERE monthly_limit IS NULL;

-- Increment both counters in one place.
CREATE OR REPLACE FUNCTION increment_usage(user_uuid UUID)
RETURNS void AS $$
BEGIN
  UPDATE users
  SET checks_today = checks_today + 1,
      checks_this_month = checks_this_month + 1
  WHERE id = user_uuid;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION increment_usage(UUID) TO service_role;

-- Monthly reset.
CREATE OR REPLACE FUNCTION reset_monthly_checks()
RETURNS void AS $$
BEGIN
  UPDATE users SET checks_this_month = 0;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION reset_monthly_checks() TO service_role;

-- Schedule the daily and monthly resets when pg_cron is available.
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pg_cron') THEN
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'daily-usage-reset') THEN
      PERFORM cron.unschedule('daily-usage-reset');
    END IF;
    IF EXISTS (SELECT 1 FROM cron.job WHERE jobname = 'monthly-usage-reset') THEN
      PERFORM cron.unschedule('monthly-usage-reset');
    END IF;
    PERFORM cron.schedule('daily-usage-reset', '0 0 * * *', 'SELECT reset_daily_checks();');
    PERFORM cron.schedule('monthly-usage-reset', '0 0 1 * *', 'SELECT reset_monthly_checks();');
  END IF;
END;
$$;

CREATE INDEX IF NOT EXISTS idx_users_checks_month ON users(checks_this_month);

-- New users get a monthly limit based on plan.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_plan TEXT := COALESCE(NEW.raw_user_meta_data->>'plan', 'hobby');
BEGIN
  INSERT INTO public.users (id, email, api_key, plan, daily_limit, monthly_limit)
  VALUES (
    NEW.id,
    COALESCE(NEW.email, ''),
    'ib_' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''),
    new_plan,
    1000,
    CASE new_plan
      WHEN 'pro' THEN 500000
      WHEN 'growth' THEN 100000
      ELSE 5000
    END
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
