-- Replace dev-mode open policies with secure RLS + working auth trigger
-- Root cause: original version dropped trigger and opened RLS to public

-- Clean up any existing policies
DROP POLICY IF EXISTS "Anyone can insert users for signup" ON users;
DROP POLICY IF EXISTS "Users can view own API key" ON users;
DROP POLICY IF EXISTS "Service role full access users" ON users;
DROP POLICY IF EXISTS "Public read users" ON users;
DROP POLICY IF EXISTS "Public insert users" ON users;
DROP POLICY IF EXISTS "Public update users" ON users;
DROP POLICY IF EXISTS "Users read own data" ON users;
DROP POLICY IF EXISTS "Users insert own data" ON users;
DROP POLICY IF EXISTS "Users update own data" ON users;

-- Secure RLS: users can only access their own row
CREATE POLICY "Users read own data" ON users FOR SELECT USING (auth.uid() = id);
CREATE POLICY "Users insert own data" ON users FOR INSERT WITH CHECK (auth.uid() = id);
CREATE POLICY "Users update own data" ON users FOR UPDATE USING (auth.uid() = id);

-- Auth trigger: auto-create user record on signup
-- search_path must include extensions for gen_random_bytes
-- must reference public.users explicitly (auth.users also exists)
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
      'ib_' || encode(extensions.gen_random_bytes(32), 'hex'),
      COALESCE(NEW.raw_user_meta_data->>'plan', 'hobby'),
      10000
    )
    ON CONFLICT (id) DO NOTHING;
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER SET search_path = public, extensions;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();
