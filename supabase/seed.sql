-- Disable triggers temporarily to avoid errors during cleanup
SET session_replication_role = 'replica';

-- 1. Clean up your application tables
DELETE FROM public.reasoning_history;
DELETE FROM public.metrics;
DELETE FROM public.alerts;
DELETE FROM public.users WHERE email = 'dev@inferencebrake.local';

-- 2. Clean up the Auth system (This is where the bugs usually live)
DELETE FROM auth.identities WHERE user_id IN (SELECT id FROM auth.users WHERE email = 'dev@inferencebrake.local');
DELETE FROM auth.users WHERE email = 'dev@inferencebrake.local';

-- Re-enable triggers
SET session_replication_role = 'origin';