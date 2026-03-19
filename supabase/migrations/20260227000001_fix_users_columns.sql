-- Ensure users table has required columns (fix for production if missing)
ALTER TABLE users ADD COLUMN IF NOT EXISTS api_key TEXT UNIQUE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS test_mode_api_key TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS test_mode BOOLEAN DEFAULT FALSE;
