-- Analytics summary for a user.
-- Aggregates the metrics table into totals plus a daily series. Totals reflect
-- retained metrics only (see cleanup_old_sessions), so hobby users are limited
-- to their 7-day window.

CREATE OR REPLACE FUNCTION analytics_summary(
  p_user_id UUID,
  p_days INTEGER DEFAULT 30
)
RETURNS JSON
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
  result JSON;
BEGIN
  SELECT json_build_object(
    'total_checks', COALESCE(COUNT(*), 0),
    'loops_blocked', COALESCE(COUNT(*) FILTER (WHERE loop_detected), 0),
    'estimated_usd_saved',
      COALESCE(ROUND(SUM(COALESCE(estimated_cost_saved, 0))::numeric, 6), 0),
    'avg_similarity', COALESCE(ROUND(AVG(similarity)::numeric, 4), 0),
    'first_check_at', MIN(created_at),
    'last_check_at', MAX(created_at),
    'daily', COALESCE((
      SELECT json_agg(row_to_json(d) ORDER BY d.date)
      FROM (
        SELECT
          DATE(created_at) AS date,
          COUNT(*) AS checks,
          COUNT(*) FILTER (WHERE loop_detected) AS loops,
          ROUND(SUM(COALESCE(estimated_cost_saved, 0))::numeric, 6) AS saved
        FROM metrics
        WHERE user_id = p_user_id
          AND created_at >= NOW() - (p_days || ' days')::interval
        GROUP BY DATE(created_at)
      ) d
    ), '[]'::json)
  )
  INTO result
  FROM metrics
  WHERE user_id = p_user_id;

  RETURN result;
END;
$$;

GRANT EXECUTE ON FUNCTION analytics_summary(UUID, INTEGER) TO service_role;
