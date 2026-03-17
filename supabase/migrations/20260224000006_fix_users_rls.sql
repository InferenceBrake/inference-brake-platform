-- Fix: Secure the users table with proper RLS policies
DROP POLICY IF EXISTS "Public read users" ON users;
DROP POLICY IF EXISTS "Public insert users" ON users;
DROP POLICY IF EXISTS "Public update users" ON users;

-- Users can only read their own row
CREATE POLICY "Users read own data" ON users FOR SELECT USING (auth.uid() = id);

-- Users can only insert their own row during signup
CREATE POLICY "Users insert own data" ON users FOR INSERT WITH CHECK (auth.uid() = id);

-- Users can only update their own row
CREATE POLICY "Users update own data" ON users FOR UPDATE USING (auth.uid() = id);
