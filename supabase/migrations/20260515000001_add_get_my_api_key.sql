-- Function for authenticated users to retrieve their own API key
-- Falls back to generating one if the user row is missing

CREATE OR REPLACE FUNCTION get_my_api_key()
RETURNS TEXT
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, extensions
AS $$
DECLARE
  user_key TEXT;
BEGIN
  -- Try to get existing key
  SELECT api_key INTO user_key FROM users WHERE id = auth.uid();

  -- If no row exists, create one with a new key
  IF NOT FOUND THEN
    user_key := 'ib_' || encode(extensions.gen_random_bytes(32), 'hex');
    INSERT INTO users (id, email, api_key, plan, daily_limit)
    VALUES (auth.uid(), '', user_key, 'hobby', 10000)
    ON CONFLICT (id) DO UPDATE SET api_key = EXCLUDED.api_key
    RETURNING api_key INTO user_key;
  END IF;

  -- If row exists but key is null/empty, generate one
  IF user_key IS NULL OR user_key = '' THEN
    user_key := 'ib_' || encode(extensions.gen_random_bytes(32), 'hex');
    UPDATE users SET api_key = user_key, updated_at = NOW() WHERE id = auth.uid();
  END IF;

  RETURN user_key;
END;
$$;

GRANT EXECUTE ON FUNCTION get_my_api_key TO authenticated;
