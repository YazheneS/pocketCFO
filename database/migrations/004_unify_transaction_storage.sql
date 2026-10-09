-- Move data created by the former voice-module table into the canonical table
-- used by the FastAPI transaction API and chatbot. Safe to rerun.
BEGIN;

UPDATE transactions
SET user_id = '00000000-0000-0000-0000-000000000001';

INSERT INTO transactions (
  id,
  user_id,
  description,
  amount,
  type,
  category,
  transaction_date,
  is_personal,
  created_at,
  updated_at
)
SELECT
  id,
  '00000000-0000-0000-0000-000000000001',
  description,
  amount,
  type,
  category,
  transaction_date,
  is_personal,
  created_at,
  updated_at
FROM categorized_transactions
ON CONFLICT (id) DO NOTHING;

COMMIT;