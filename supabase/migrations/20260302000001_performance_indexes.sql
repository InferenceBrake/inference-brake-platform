-- Performance indexes for faster queries

-- Reasoning history: session lookups
CREATE INDEX IF NOT EXISTS idx_reasoning_history_session_user 
  ON reasoning_history(session_id, user_id);

CREATE INDEX IF NOT EXISTS idx_reasoning_history_created 
  ON reasoning_history(created_at DESC);

-- Metrics: user analytics queries
CREATE INDEX IF NOT EXISTS idx_metrics_user_session 
  ON metrics(user_id, session_id);

CREATE INDEX IF NOT EXISTS idx_metrics_created 
  ON metrics(created_at DESC);

-- Users: api key lookups
CREATE INDEX IF NOT EXISTS idx_users_api_key 
  ON users(api_key) WHERE api_key IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_users_test_key 
  ON users(test_mode_api_key) WHERE test_mode_api_key IS NOT NULL;

-- Composite for daily usage queries
CREATE INDEX IF NOT EXISTS idx_users_plan_limit 
  ON users(plan, subscription_status);
