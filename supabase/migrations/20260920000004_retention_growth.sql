-- Include the growth plan in data retention.
--
-- cleanup_old_sessions only pruned hobby (7 days) and pro (90 days), so growth
-- data was never deleted despite the advertised 30-day retention. This keeps
-- growth at 30 days.

CREATE OR REPLACE FUNCTION cleanup_old_sessions()
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
  deleted_count int := 0;
BEGIN
  DELETE FROM reasoning_history
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'hobby')
    AND created_at < NOW() - INTERVAL '7 days';

  DELETE FROM reasoning_history
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'growth')
    AND created_at < NOW() - INTERVAL '30 days';

  DELETE FROM reasoning_history
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'pro')
    AND created_at < NOW() - INTERVAL '90 days';

  DELETE FROM metrics
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'hobby')
    AND created_at < NOW() - INTERVAL '7 days';

  DELETE FROM metrics
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'growth')
    AND created_at < NOW() - INTERVAL '30 days';

  DELETE FROM metrics
  WHERE user_id IN (SELECT id FROM users WHERE plan = 'pro')
    AND created_at < NOW() - INTERVAL '90 days';

  GET DIAGNOSTICS deleted_count = ROW_COUNT;
  RAISE NOTICE 'Data retention cleanup completed. Deleted % old records', deleted_count;
END;
$$;
