-- Lifetime usage totals.
--
-- analytics_summary and the dashboard computed dollars-saved from the metrics
-- table, which data retention deletes. A free user's "total saved" therefore
-- reset every 7 days. usage_totals accumulates counters independent of
-- retention, updated by a trigger on metrics insert.

CREATE TABLE IF NOT EXISTS usage_totals (
  user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
  total_checks BIGINT NOT NULL DEFAULT 0,
  total_loops BIGINT NOT NULL DEFAULT 0,
  total_saved NUMERIC NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE usage_totals ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own totals" ON usage_totals;
CREATE POLICY "Users can view own totals"
  ON usage_totals FOR SELECT
  USING (auth.uid() = user_id);

-- Accumulate on every metrics insert.
CREATE OR REPLACE FUNCTION record_metric_totals()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO usage_totals (user_id, total_checks, total_loops, total_saved, updated_at)
  VALUES (
    NEW.user_id,
    1,
    CASE WHEN NEW.loop_detected THEN 1 ELSE 0 END,
    COALESCE(NEW.estimated_cost_saved, 0),
    NOW()
  )
  ON CONFLICT (user_id) DO UPDATE
  SET total_checks = usage_totals.total_checks + 1,
      total_loops = usage_totals.total_loops + CASE WHEN NEW.loop_detected THEN 1 ELSE 0 END,
      total_saved = usage_totals.total_saved + COALESCE(NEW.estimated_cost_saved, 0),
      updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

DROP TRIGGER IF EXISTS metrics_record_totals ON metrics;
CREATE TRIGGER metrics_record_totals
  AFTER INSERT ON metrics
  FOR EACH ROW EXECUTE FUNCTION record_metric_totals();

-- Backfill from whatever metrics are still retained.
INSERT INTO usage_totals (user_id, total_checks, total_loops, total_saved, updated_at)
SELECT
  user_id,
  COUNT(*),
  COUNT(*) FILTER (WHERE loop_detected),
  COALESCE(SUM(estimated_cost_saved), 0),
  NOW()
FROM metrics
GROUP BY user_id
ON CONFLICT (user_id) DO UPDATE
SET total_checks = EXCLUDED.total_checks,
    total_loops = EXCLUDED.total_loops,
    total_saved = EXCLUDED.total_saved,
    updated_at = NOW();

-- Lifetime totals as the headline figures; keep window figures for the series.
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
  life usage_totals%ROWTYPE;
BEGIN
  SELECT * INTO life FROM usage_totals WHERE user_id = p_user_id;

  SELECT json_build_object(
    'total_checks', COALESCE(life.total_checks, 0),
    'loops_blocked', COALESCE(life.total_loops, 0),
    'estimated_usd_saved', COALESCE(ROUND(life.total_saved::numeric, 6), 0),
    'window_days', p_days,
    'window_checks', COALESCE(COUNT(*), 0),
    'window_loops', COALESCE(COUNT(*) FILTER (WHERE loop_detected), 0),
    'window_usd_saved',
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
