-- ============================================================
-- Categorization tables used by voice-module/server.py
--   * categorized_transactions : voice/text transactions after categorization
--   * category_override_rules  : per-user "always categorize X as Y" corrections
--
-- Idempotent: safe to run more than once. Requires Supabase (auth.users, auth.uid()).
-- Allowed values mirror voice-module/validators.py - keep both in sync.
-- ============================================================

-- Shared updated_at trigger function
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = CURRENT_TIMESTAMP;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------
-- categorized_transactions
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS categorized_transactions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

  -- Filled from the caller's JWT, so the API never trusts a client-sent user_id
  user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,

  description TEXT NOT NULL
    CHECK (char_length(description) > 0 AND char_length(description) <= 500),
  amount NUMERIC(12, 2) NOT NULL CHECK (amount > 0),
  type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
  category TEXT NOT NULL CHECK (category IN (
    'Revenue', 'Inventory', 'Utilities', 'Rent', 'Salaries', 'Transport',
    'Marketing', 'Maintenance', 'Personal', 'Food', 'Other'
  )),
  currency TEXT NOT NULL DEFAULT 'INR'
    CHECK (currency IN ('INR', 'USD', 'EUR', 'GBP', 'AED')),
  transaction_date DATE NOT NULL,
  payment_mode TEXT NOT NULL DEFAULT 'unknown'
    CHECK (payment_mode IN ('cash', 'upi', 'card', 'bank_transfer', 'cheque', 'unknown')),
  confidence_score NUMERIC(3, 2) NOT NULL DEFAULT 0.50
    CHECK (confidence_score >= 0 AND confidence_score <= 1),
  is_personal BOOLEAN NOT NULL DEFAULT FALSE,

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- Income is Revenue (or Other); Revenue is never an expense
  CONSTRAINT categorized_type_category_consistent CHECK (
    (type = 'income' AND category IN ('Revenue', 'Other'))
    OR (type = 'expense' AND category <> 'Revenue')
  ),
  CONSTRAINT categorized_personal_flag_consistent CHECK (
    is_personal = (category = 'Personal')
  )
);

CREATE INDEX IF NOT EXISTS idx_categorized_tx_user_created
  ON categorized_transactions(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_categorized_tx_user_date
  ON categorized_transactions(user_id, transaction_date DESC);
CREATE INDEX IF NOT EXISTS idx_categorized_tx_user_category
  ON categorized_transactions(user_id, category);
CREATE INDEX IF NOT EXISTS idx_categorized_tx_user_type
  ON categorized_transactions(user_id, type);

DROP TRIGGER IF EXISTS set_categorized_transactions_updated_at ON categorized_transactions;
CREATE TRIGGER set_categorized_transactions_updated_at
  BEFORE UPDATE ON categorized_transactions
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE categorized_transactions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "categorized_tx_select_own" ON categorized_transactions;
CREATE POLICY "categorized_tx_select_own" ON categorized_transactions
  FOR SELECT TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "categorized_tx_insert_own" ON categorized_transactions;
CREATE POLICY "categorized_tx_insert_own" ON categorized_transactions
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "categorized_tx_update_own" ON categorized_transactions;
CREATE POLICY "categorized_tx_update_own" ON categorized_transactions
  FOR UPDATE TO authenticated
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "categorized_tx_delete_own" ON categorized_transactions;
CREATE POLICY "categorized_tx_delete_own" ON categorized_transactions
  FOR DELETE TO authenticated USING (auth.uid() = user_id);

REVOKE ALL ON categorized_transactions FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON categorized_transactions TO authenticated;

-- ------------------------------------------------------------
-- category_override_rules
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS category_override_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,

  -- Stored lower-cased and trimmed (the server normalizes before writing)
  keyword TEXT NOT NULL
    CHECK (char_length(keyword) BETWEEN 1 AND 100 AND keyword = lower(btrim(keyword))),
  correct_category TEXT NOT NULL CHECK (correct_category IN (
    'Revenue', 'Inventory', 'Utilities', 'Rent', 'Salaries', 'Transport',
    'Marketing', 'Maintenance', 'Personal', 'Food', 'Other'
  )),

  created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,

  -- One rule per keyword per user; the API upserts on this pair
  CONSTRAINT category_override_rules_user_keyword_key UNIQUE (user_id, keyword)
);

DROP TRIGGER IF EXISTS set_category_override_rules_updated_at ON category_override_rules;
CREATE TRIGGER set_category_override_rules_updated_at
  BEFORE UPDATE ON category_override_rules
  FOR EACH ROW EXECUTE FUNCTION set_updated_at();

ALTER TABLE category_override_rules ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "override_rules_select_own" ON category_override_rules;
CREATE POLICY "override_rules_select_own" ON category_override_rules
  FOR SELECT TO authenticated USING (auth.uid() = user_id);

DROP POLICY IF EXISTS "override_rules_insert_own" ON category_override_rules;
CREATE POLICY "override_rules_insert_own" ON category_override_rules
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "override_rules_update_own" ON category_override_rules;
CREATE POLICY "override_rules_update_own" ON category_override_rules
  FOR UPDATE TO authenticated
  USING (auth.uid() = user_id) WITH CHECK (auth.uid() = user_id);

DROP POLICY IF EXISTS "override_rules_delete_own" ON category_override_rules;
CREATE POLICY "override_rules_delete_own" ON category_override_rules
  FOR DELETE TO authenticated USING (auth.uid() = user_id);

REVOKE ALL ON category_override_rules FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON category_override_rules TO authenticated;
