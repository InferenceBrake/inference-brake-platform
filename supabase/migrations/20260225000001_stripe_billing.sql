-- Add Stripe fields to users table for subscription management

-- Add Stripe-related columns
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status TEXT DEFAULT 'inactive'; -- active, past_due, canceled
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_current_period_end TIMESTAMPTZ;
ALTER TABLE users ADD COLUMN IF NOT EXISTS test_mode_api_key TEXT;

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription ON users(subscription_status);

-- Update daily_limit based on plan
CREATE OR REPLACE FUNCTION get_plan_limits(user_plan TEXT)
RETURNS TABLE(daily_limit INTEGER, name TEXT) AS $$
BEGIN
  RETURN QUERY
  SELECT
    CASE
      WHEN user_plan = 'pro' THEN 10000
      WHEN user_plan = 'enterprise' THEN 999999
      ELSE 1000  -- hobby
    END AS daily_limit,
    CASE
      WHEN user_plan = 'pro' THEN 'Pro'
      WHEN user_plan = 'enterprise' THEN 'Enterprise'
      ELSE 'Hobby'
    END AS name;
END;
$$ LANGUAGE plpgsql;

-- Function to regenerate API key
CREATE OR REPLACE FUNCTION regenerate_api_key(user_uuid UUID)
RETURNS TEXT AS $$
DECLARE
  new_key TEXT;
BEGIN
  new_key := 'ib_' || encode(gen_random_bytes(32), 'hex');
  
  UPDATE users
  SET api_key = new_key, updated_at = NOW()
  WHERE id = user_uuid;
  
  RETURN new_key;
END;
$$ LANGUAGE plpgsql;

GRANT EXECUTE ON FUNCTION regenerate_api_key(UUID) TO service_role;
