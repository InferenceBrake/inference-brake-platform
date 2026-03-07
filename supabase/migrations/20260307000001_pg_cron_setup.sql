-- Enable pg_cron extension (requires superuser)
-- Note: pg_cron requires the database to be on Supabase Pro or above
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Grant usage on pg_cron to postgres role
GRANT USAGE ON SCHEMA cron TO postgres;

-- Schedule data retention cleanup to run daily at 3am UTC
-- Cron format: minute hour day-of-month month day-of-week
-- '0 3 * * *' = every day at 3:00 AM
SELECT cron.schedule(
    'data-retention-cleanup',
    '0 3 * * *',
    $$
    SELECT cleanup_old_sessions();
    $$
);

-- Alternative schedules:
-- Every hour: '0 * * * *'
-- Every day at midnight: '0 0 * * *'
-- Every Monday at 6am: '0 6 * * 1'
-- Every 15 minutes: '*/15 * * * *'
