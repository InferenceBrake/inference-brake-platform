-- Migration: Use Supabase Auth as source of truth for users
-- This makes auth + API key work together

-- 1. Add auth_id column to link to Supabase Auth
ALTER TABLE users ADD COLUMN IF NOT EXISTS auth_id UUID UNIQUE;

-- 2. Update existing users to map their auth_id (if they have one)
-- For dev@inferencebrake.local, we'll leave auth_id null for now

-- 3. Create trigger to auto-create user record on Supabase Auth signup
-- This ensures every auth user has an API key

-- First, let's create a function to handle new user creation
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
  -- Check if user record already exists
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

-- 4. Create trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION handle_new_user();

-- 5. Allow users to read their own API key
CREATE POLICY "Users can view own API key"
  ON users FOR SELECT
  USING (auth.uid() = id);

-- 6. Allow service role full access (for edge function)
DROP POLICY IF EXISTS "Service role full access users" ON users;
CREATE POLICY "Service role full access users"
  ON users FOR ALL
  USING (true)
  WITH CHECK (true);
