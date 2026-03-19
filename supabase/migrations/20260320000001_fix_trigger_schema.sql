-- Fix: Explicitly reference public.users schema in trigger
-- This prevents the trigger from accidentally using auth.users

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user();

CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.raw_user_meta_data IS NOT NULL THEN
    INSERT INTO public.users (id, email, api_key, plan, daily_limit)
    VALUES (
      NEW.id,
      NEW.email,
      'ib_' || encode(gen_random_bytes(32), 'hex'),
      COALESCE(NEW.raw_user_meta_data->>'plan', 'hobby'),
      10000
    )
    ON CONFLICT (id) DO NOTHING;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
