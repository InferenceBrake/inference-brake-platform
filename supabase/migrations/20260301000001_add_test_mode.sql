-- Add test_mode flag to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS test_mode BOOLEAN DEFAULT FALSE;

-- Create index for test_mode queries
CREATE INDEX IF NOT EXISTS idx_users_test_mode ON users(test_mode);
