-- RLS bypass for local development
-- Allow anonymous read access when using local Supabase

-- Drop existing policies and create more permissive ones for development
DROP POLICY IF EXISTS "Users can view own history" ON reasoning_history;
DROP POLICY IF EXISTS "Users can view own metrics" ON metrics;
DROP POLICY IF EXISTS "Users can view own alerts" ON alerts;

-- Allow anyone to read (for dev/demo purposes)
-- In production, you'd want to restrict this back
CREATE POLICY "Anyone can view history for dev"
  ON reasoning_history FOR SELECT
  USING (true);

CREATE POLICY "Anyone can view metrics for dev"
  ON metrics FOR SELECT
  USING (true);

CREATE POLICY "Anyone can view alerts for dev"
  ON alerts FOR SELECT
  USING (true);

-- Also allow inserts from service role
CREATE POLICY "Service role can insert history"
  ON reasoning_history FOR INSERT
  WITH CHECK (true);

CREATE POLICY "Service role can insert metrics"
  ON metrics FOR INSERT
  WITH CHECK (true);
