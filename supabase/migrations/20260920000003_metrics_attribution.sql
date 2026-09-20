-- Metrics attribution.
--
-- Records which model, tool/action, and prompt produced each check, plus the
-- detector votes and confidence, so analytics can attribute loops instead of
-- only counting them.

ALTER TABLE metrics ADD COLUMN IF NOT EXISTS model TEXT;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS action TEXT;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS prompt TEXT;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS confidence FLOAT;
ALTER TABLE metrics ADD COLUMN IF NOT EXISTS detectors JSONB;

CREATE INDEX IF NOT EXISTS idx_metrics_model ON metrics(user_id, model);
CREATE INDEX IF NOT EXISTS idx_metrics_action ON metrics(user_id, action);
CREATE INDEX IF NOT EXISTS idx_metrics_loop_created
  ON metrics(user_id, created_at DESC)
  WHERE loop_detected;

-- Extend analytics_summary with attribution breakdowns.
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
    ), '[]'::json),
    'by_model', COALESCE((
      SELECT json_agg(row_to_json(d))
      FROM (
        SELECT
          COALESCE(model, 'unknown') AS model,
          COUNT(*) AS checks,
          COUNT(*) FILTER (WHERE loop_detected) AS loops,
          ROUND(SUM(COALESCE(estimated_cost_saved, 0))::numeric, 6) AS saved
        FROM metrics
        WHERE user_id = p_user_id
        GROUP BY COALESCE(model, 'unknown')
        ORDER BY loops DESC, checks DESC
        LIMIT 10
      ) d
    ), '[]'::json),
    'by_action', COALESCE((
      SELECT json_agg(row_to_json(d))
      FROM (
        SELECT
          COALESCE(action, 'unknown') AS action,
          COUNT(*) AS checks,
          COUNT(*) FILTER (WHERE loop_detected) AS loops,
          ROUND(SUM(COALESCE(estimated_cost_saved, 0))::numeric, 6) AS saved
        FROM metrics
        WHERE user_id = p_user_id
        GROUP BY COALESCE(action, 'unknown')
        ORDER BY loops DESC, checks DESC
        LIMIT 10
      ) d
    ), '[]'::json),
    'by_prompt', COALESCE((
      SELECT json_agg(row_to_json(d))
      FROM (
        SELECT
          COALESCE(prompt, 'unlabeled') AS prompt,
          COUNT(*) AS checks,
          COUNT(*) FILTER (WHERE loop_detected) AS loops,
          ROUND(SUM(COALESCE(estimated_cost_saved, 0))::numeric, 6) AS saved
        FROM metrics
        WHERE user_id = p_user_id
          AND loop_detected
        GROUP BY COALESCE(prompt, 'unlabeled')
        ORDER BY loops DESC
        LIMIT 10
      ) d
    ), '[]'::json),
    'by_detector', COALESCE((
      SELECT json_agg(row_to_json(d) ORDER BY d.loops DESC)
      FROM (
        SELECT kv.key AS detector, COUNT(*) AS loops
        FROM metrics m
        CROSS JOIN LATERAL jsonb_each_text(m.detectors) AS kv(key, value)
        WHERE m.user_id = p_user_id
          AND m.loop_detected
          AND m.detectors IS NOT NULL
          AND kv.value = 'true'
        GROUP BY kv.key
      ) d
    ), '[]'::json),
    'recent_loops', COALESCE((
      SELECT json_agg(row_to_json(d) ORDER BY d.created_at DESC)
      FROM (
        SELECT
          session_id,
          model,
          action,
          prompt,
          confidence,
          ROUND(COALESCE(estimated_cost_saved, 0)::numeric, 6) AS saved,
          detectors,
          created_at
        FROM metrics
        WHERE user_id = p_user_id
          AND loop_detected
        ORDER BY created_at DESC
        LIMIT 20
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
