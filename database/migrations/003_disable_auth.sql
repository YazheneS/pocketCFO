-- 003_disable_auth.sql
-- Run once in the Supabase SQL editor.
-- Removes the dependency on Supabase Auth: all rows belong to one shared demo
-- user, so the app works with any login. Idempotent.
-- WARNING: with RLS off, anyone holding the anon key can read/write these
-- tables. Fine for a demo / college project, not for real financial data.

-- 1. Drop foreign keys to auth.users (the demo user does not exist there)
ALTER TABLE transactions            DROP CONSTRAINT IF EXISTS transactions_user_id_fkey;
ALTER TABLE categorized_transactions DROP CONSTRAINT IF EXISTS categorized_transactions_user_id_fkey;
ALTER TABLE category_override_rules  DROP CONSTRAINT IF EXISTS category_override_rules_user_id_fkey;

-- 2. Default every row to the shared demo user (matches DEMO_USER_ID in the backend)
ALTER TABLE transactions            ALTER COLUMN user_id SET DEFAULT '00000000-0000-0000-0000-000000000001';
ALTER TABLE categorized_transactions ALTER COLUMN user_id SET DEFAULT '00000000-0000-0000-0000-000000000001';
ALTER TABLE category_override_rules  ALTER COLUMN user_id SET DEFAULT '00000000-0000-0000-0000-000000000001';

-- 3. Turn off row level security so the anon key can read/write
ALTER TABLE transactions            DISABLE ROW LEVEL SECURITY;
ALTER TABLE categorized_transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE category_override_rules  DISABLE ROW LEVEL SECURITY;

-- 4. Make sure the anon role may use the tables
GRANT SELECT, INSERT, UPDATE, DELETE ON transactions, categorized_transactions, category_override_rules TO anon;
