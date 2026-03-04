-- Data retention function
-- Deletes reasoning_history older than retention period based on user plan
-- Run daily via cron or pg_cron

CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  deleted_count int := 0;
BEGIN
  -- Delete hobby plan data older than 7 days
  DELETE FROM reasoning_history
  WHERE user_id IN (
    SELECT id FROM users WHERE plan = 'hobby'
  )
  AND created_at < NOW() - INTERVAL '7 days';
  
  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  
  -- Delete pro plan data older than 90 days
  DELETE FROM reasoning_history
  WHERE user_id IN (
    SELECT id FROM users WHERE plan = 'pro'
  )
  AND created_at < NOW() - INTERVAL '90 days';
  
  -- Clean up metrics older than respective retention periods
  DELETE FROM metrics
  WHERE user_id IN (
    SELECT id FROM users WHERE plan = 'hobby'
  )
  AND created_at < NOW() - INTERVAL '7 days';
  
  DELETE FROM metrics
  WHERE user_id IN (
    SELECT id FROM users WHERE plan = 'pro'
  )
  AND created_at < NOW() - INTERVAL '90 days';
  
  RAISE NOTICE 'Data retention cleanup completed. Deleted % old records', deleted_count;
END;
$$;

-- Create index for faster cleanup queries
CREATE INDEX IF NOT EXISTS idx_reasoning_history_user_created 
  ON reasoning_history(user_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_metrics_user_created 
  ON metrics(user_id, created_at DESC);
