-- Drop the complex trigger for now
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP FUNCTION IF EXISTS handle_new_user();

-- Clean up RLS for development
DROP POLICY IF EXISTS "Anyone can insert users for signup" ON users;
DROP POLICY IF EXISTS "Users can view own API key" ON users;
DROP POLICY IF EXISTS "Service role full access users" ON users;

-- Simple policies for dev
CREATE POLICY "Public read users" ON users FOR SELECT USING (true);
CREATE POLICY "Public insert users" ON users FOR INSERT WITH CHECK (true);
CREATE POLICY "Public update users" ON users FOR UPDATE USING (true);
