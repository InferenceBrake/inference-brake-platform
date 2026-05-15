-- Fix handle_new_user trigger:
-- 1. Remove pgcrypto dependency (use gen_random_uuid instead)
-- 2. Remove raw_user_meta_data guard (can be null on signup)
-- 3. Backfill missing user rows for existing auth users

-- Fix the trigger function
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  INSERT INTO public.users (id, email, api_key, plan, daily_limit)
  VALUES (
    NEW.id,
    COALESCE(NEW.email, ''),
    'ib_' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''),
    COALESCE(NEW.raw_user_meta_data->>'plan', 'hobby'),
    10000
  )
  ON CONFLICT (id) DO NOTHING;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public;

-- Recreate trigger to ensure it uses the updated function
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- Backfill: create user rows for existing auth users who don't have one
INSERT INTO public.users (id, email, api_key, plan, daily_limit)
SELECT
  au.id,
  COALESCE(au.email, ''),
  'ib_' || replace(gen_random_uuid()::text, '-', '') || replace(gen_random_uuid()::text, '-', ''),
  'hobby',
  10000
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL
ON CONFLICT (id) DO NOTHING;
