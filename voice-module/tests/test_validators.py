import os
import sys
from datetime import timedelta

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import validators as v
import parser as tx_parser
import categorizer


def good(**over):
    base = {"description": "sold cakes", "amount": 500, "type": "income",
            "category": "Revenue", "date": v.today_ist().isoformat(),
            "confidence_score": 0.9}
    base.update(over)
    return base


# ---- amount -----------------------------------------------------------
@pytest.mark.parametrize("raw", [0, -5, "abc", "", None, True, float("nan"), float("inf"), 10**12, [1], {"a": 1}])
def test_bad_amounts_rejected(raw):
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(amount=raw))


@pytest.mark.parametrize("raw,expected", [(200, 200.0), ("₹1,250.5", 1250.5), ("Rs. 99", 99.0), (10.005, 10.01)])
def test_amounts_normalised(raw, expected):
    clean, _ = v.validate_transaction(good(amount=raw))
    assert clean["amount"] == expected


# ---- type / category --------------------------------------------------
def test_bad_type_rejected():
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(type="refund"))


def test_unknown_category_becomes_other_with_warning():
    clean, warns = v.validate_transaction(good(type="expense", category="Gadgets"))
    assert clean["category"] == "Other" and warns


def test_unknown_category_rejected_in_strict():
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(type="expense", category="Gadgets"), strict=True)


def test_category_case_and_punctuation_normalised():
    assert v.normalize_category(' "revenue." ') == "Revenue"
    assert v.normalize_category("Gadgets") is None
    assert v.normalize_category(None) is None


def test_income_forced_to_revenue_expense_never_revenue():
    clean, _ = v.validate_transaction(good(category="Food"))
    assert clean["category"] == "Revenue"
    clean, _ = v.validate_transaction(good(type="expense", category="Revenue"))
    assert clean["category"] == "Other"
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(type="expense", category="Revenue"), strict=True)


# ---- date -------------------------------------------------------------
def test_date_validation():
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(date="31/12/2025"))
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(date="1990-01-01"))
    future = (v.today_ist() + timedelta(days=30)).isoformat()
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(date=future))


def test_missing_date_defaults_lenient_but_fails_strict():
    raw = good()
    del raw["date"]
    clean, warns = v.validate_transaction(raw)
    assert clean["transaction_date"] == v.today_ist().isoformat() and warns
    with pytest.raises(v.ValidationError):
        v.validate_transaction(raw, strict=True)


# ---- misc fields ------------------------------------------------------
def test_confidence_clamped_and_defaulted():
    clean, warns = v.validate_transaction(good(confidence_score=7))
    assert clean["confidence_score"] == 1.0 and warns
    clean, _ = v.validate_transaction(good(confidence_score="high"))
    assert clean["confidence_score"] == 0.5


def test_description_cleaned_and_required():
    clean, _ = v.validate_transaction(good(description="  sold \x00 cakes \n today "))
    assert clean["description"] == "sold cakes today"
    with pytest.raises(v.ValidationError):
        v.validate_transaction(good(description="   "))


def test_payment_mode_and_currency_normalised():
    clean, _ = v.validate_transaction(good(payment_mode="GPay", currency="usd"))
    assert clean["payment_mode"] == "upi" and clean["currency"] == "USD"
    clean, warns = v.validate_transaction(good(payment_mode="barter", currency="XYZ"))
    assert clean["payment_mode"] == "unknown" and clean["currency"] == "INR" and warns


def test_extra_keys_dropped_and_db_row_whitelisted():
    clean, _ = v.validate_transaction(good(id="x", user_id="evil", role="admin"))
    row = v.to_db_row(clean)
    assert set(row) == {"description", "amount", "type", "category", "currency",
                        "transaction_date", "payment_mode", "confidence_score", "is_personal"}


def test_personal_flag_derived():
    clean, _ = v.validate_transaction(good(type="expense", category="Personal"))
    assert clean["is_personal"] is True


# ---- batches ----------------------------------------------------------
def test_batch_splits_valid_and_rejected():
    valid, rejected, _ = v.validate_transactions([good(), good(amount=-1), "junk"])
    assert len(valid) == 1 and [r["index"] for r in rejected] == [1, 2]


def test_batch_limits():
    for bad in (None, [], "x", [good()] * (v.MAX_BATCH_SIZE + 1)):
        with pytest.raises(v.ValidationError):
            v.validate_transactions(bad)


# ---- other payloads ---------------------------------------------------
def test_correction_payload():
    ok = v.validate_correction_payload({"new_category": "food", "keyword": "  Tea Stall "})
    assert ok == {"transaction_id": None, "new_category": "Food", "keyword": "tea stall"}
    for bad in ({}, {"new_category": "Nope", "keyword": "x"},
                {"new_category": "Food"}, {"new_category": "Food", "transaction_id": "not-a-uuid"}, []):
        with pytest.raises(v.ValidationError):
            v.validate_correction_payload(bad)


def test_text_input():
    assert v.validate_text_input("  sold tea ") == "sold tea"
    for bad in ("", "   ", None, "x" * (v.MAX_TEXT_INPUT_LEN + 1)):
        with pytest.raises(v.ValidationError):
            v.validate_text_input(bad)


def test_query_filters():
    assert v.validate_query_filters({"limit": "10", "type": "Income"})["type"] == "income"
    for bad in ({"limit": "0"}, {"limit": "abc"}, {"type": "x"}, {"category": "x"}, {"date": "05-10-2026"}):
        with pytest.raises(v.ValidationError):
            v.validate_query_filters(bad)


# ---- parser output ----------------------------------------------------
def test_parser_output_validation():
    out = tx_parser.validate_parser_output([good(), {"description": "x", "amount": "free", "type": "expense"}, 5])
    assert len(out["transactions"]) == 1 and len(out["rejected"]) == 2
    assert tx_parser.validate_parser_output([])["transactions"] == []
    assert len(tx_parser.validate_parser_output(good())["transactions"]) == 1  # bare object


def test_parser_json_extraction():
    assert tx_parser._extract_json_array('```json\n[{"a": 1}]\n```')[0] == {"a": 1}
    assert tx_parser._extract_json_array('Sure! [{"a": 1}] hope it helps')[0] == {"a": 1}


# ---- categorizer output -----------------------------------------------
def test_categorizer_expense_never_revenue():
    cat, _ = categorizer.get_category_from_rules("paid supplier, payment received slip", "expense")
    assert cat != "Revenue"


def test_categorizer_income_is_revenue():
    assert categorizer.get_category_from_rules("customer paid for lunch", "income")[0] == "Revenue"


def test_apply_categorization_enforces_contract():
    txs = [{"description": "bought flour", "amount": 10, "type": "expense", "confidence_score": "bad"}]
    out = categorizer.apply_categorization(txs)[0]
    assert out["category"] in v.ALLOWED_CATEGORIES and 0 <= out["confidence_score"] <= 1


def test_llm_fallback_output_is_validated(monkeypatch):
    class R:  # fake Groq reply with chatter instead of a bare category
        choices = [type("C", (), {"message": type("M", (), {"content": "I think it is Gadgets"})()})()]
    class Client:
        def __init__(self, *a, **k):
            self.chat = type("Ch", (), {"completions": type("Co", (), {"create": staticmethod(lambda **k: R)})()})()
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setattr(categorizer, "Groq", Client)
    assert categorizer.get_category_from_gemini("whatever") == "Other"


def test_override_rules_ignore_invalid_rows_and_prefer_longest():
    class Resp: data = [{"keyword": "tea", "correct_category": "Food"},
                        {"keyword": "tea stall", "correct_category": "Personal"},
                        {"keyword": "tea stall rent", "correct_category": "Bogus"}]
    class Q:
        def select(self, *a): return self
        def execute(self): return Resp
    class Sb:
        def table(self, n): return Q()
    assert categorizer.check_category_corrections("Tea Stall rent", Sb()) == "Personal"
