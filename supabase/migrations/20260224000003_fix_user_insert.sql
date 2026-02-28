-- Emergency fix: Allow public insert for user registration
-- The trigger runs as superuser but let's make sure inserts work

-- Allow anyone to insert (for signup)
CREATE POLICY "Anyone can insert users for signup"
  ON users FOR INSERT
  WITH CHECK (true);

-- Allow service role full access
DROP POLICY IF EXISTS "Service role full access users" ON users;
CREATE POLICY "Service role full access users"
  ON users FOR ALL
  USING (true)
  WITH CHECK (true);
