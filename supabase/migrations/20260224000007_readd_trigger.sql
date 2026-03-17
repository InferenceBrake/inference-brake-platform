-- Re-add trigger that was dropped by simplify_auth migration
-- This trigger creates a user record with secure API key on Supabase Auth signup

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.raw_user_meta_data IS NOT NULL THEN
    INSERT INTO users (id, email, api_key, plan, daily_limit)
    VALUES (
      NEW.id,
      NEW.email,
      'ib_' || encode(gen_random_bytes(32), 'hex'),
      COALESCE(NEW.raw_user_meta_data->>'plan', 'hobby'),
      1000
    )
    ON CONFLICT (id) DO NOTHING;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
