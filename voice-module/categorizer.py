import os
from groq import Groq
import re
from typing import List, Tuple, Optional

from validators import (
    ALLOWED_CATEGORIES,
    normalize_category,
    normalize_confidence,
    reconcile_type_and_category,
    validate_override_rule,
    ValidationError,
)

CATEGORY_RULES = {
    "Revenue": ["sold", "received", "earned", "sale", "payment received", "got paid", "income", "profit"],
    "Personal": ["myself", "personal", "family", "groceries for home", "medical", "clothes", "shoes", "movie", "outing", "personal use"],
    "Inventory": ["bought", "purchased", "flour", "rice", "vegetables", "stock", "supplies", "raw material", "ingredients", "wholesale"],
    "Utilities": ["electricity", "wifi", "internet", "water bill", "gas bill", "phone bill", "recharge", "broadband", "EB bill"],
    "Rent": ["rent", "shop rent", "office rent", "lease", "rental"],
    "Salaries": ["salary", "paid staff", "paid employee", "wages", "paid worker", "delivery boy", "helper", "staff payment"],
    "Transport": ["uber", "auto", "petrol", "fuel", "travel", "cab", "bus", "transport", "delivery charge", "shipping"],
    "Marketing": ["ad", "advertisement", "promotion", "poster", "pamphlet", "social media", "banner", "flyer"],
    "Maintenance": ["repair", "fixed", "maintenance", "service", "cleaning", "paint", "plumber", "electrician"],
    "Food": ["lunch", "dinner", "breakfast", "tea", "coffee", "snacks", "hotel", "restaurant", "meals", "food"],
    "Other": []
}


def get_category_from_gemini(description: str) -> str:
    """LLM fallback. The reply is validated against the allowed category set."""
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Other"
        client = Groq(api_key=api_key)
        safe_desc = (description or "").replace("'", " ")[:500]
        prompt = (
            "Categorize this business transaction into EXACTLY one of these categories: "
            + ", ".join(ALLOWED_CATEGORIES)
            + ". Transaction: '" + safe_desc + "'. "
            "Reply with ONLY the category name, nothing else. No explanation."
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        text = (resp.choices[0].message.content or "").strip()
        # Strict: anything that is not exactly an allowed category becomes "Other".
        return normalize_category(text) or "Other"
    except Exception:
        return "Other"


def get_category_from_rules(description: str, tx_type: Optional[str] = None) -> Tuple[str, float]:
    """Return (category, confidence). ``tx_type`` ('income'/'expense') keeps the
    result consistent: income is Revenue, expenses are never Revenue."""
    tx_type = tx_type.lower() if isinstance(tx_type, str) else None
    if tx_type == "income":
        return ("Revenue", 0.90)
    if not description:
        return ("Other", 0.50)
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if not keywords:
            continue
        if category == "Revenue" and tx_type == "expense":
            continue
        for kw in keywords:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, desc):
                return (category, 0.90)
    # No rule match -> try the LLM fallback
    try:
        res = normalize_category(get_category_from_gemini(description)) or "Other"
        if tx_type == "expense" and res == "Revenue":
            res = "Other"
        return (res, 0.75 if res != "Other" else 0.50)
    except Exception:
        return ("Other", 0.50)


def validate_categorization(tx: dict) -> dict:
    """Enforce the categorizer's output contract on one transaction (in place):
    category in the allowed set, confidence a float in [0, 1], and category
    consistent with income/expense."""
    category = normalize_category(tx.get("category")) or "Other"
    tx_type = tx.get("type")
    if isinstance(tx_type, str) and tx_type.lower() in ("income", "expense"):
        category, _ = reconcile_type_and_category(tx_type.lower(), category)
    score, _ = normalize_confidence(tx.get("confidence_score"), default=0.5)
    tx["category"] = category
    tx["confidence_score"] = score
    tx["is_personal"] = category == "Personal"
    return tx


def apply_categorization(transactions: List[dict]) -> List[dict]:
    updated = []
    for tx in transactions:
        if not isinstance(tx, dict):
            continue
        desc = tx.get("description", "")
        cat, score = get_category_from_rules(desc, tx.get("type"))
        tx["category"] = cat
        tx["confidence_score"] = float(score)
        updated.append(validate_categorization(tx))
    return updated


def check_category_corrections(description: str, supabase_client) -> Optional[str]:
    """Return a user-defined override category for ``description`` if one matches.

    Rows with an invalid category are ignored (never trusted blindly from the DB).
    Longest matching keyword wins so specific rules beat generic ones.
    """
    try:
        resp = supabase_client.table('category_override_rules').select('keyword,correct_category').execute()
        rows = resp.get('data') if isinstance(resp, dict) else getattr(resp, 'data', None)
        if not rows:
            return None
        desc = (description or "").lower()
        best_kw, best_cat = "", None
        for r in rows:
            keyword = (r.get('keyword') or '').strip().lower()
            correct = normalize_category(r.get('correct_category'))
            if keyword and correct and keyword in desc and len(keyword) > len(best_kw):
                best_kw, best_cat = keyword, correct
        return best_cat
    except Exception:
        return None


def save_correction(keyword: str, category: str, supabase_client):
    """Validate then upsert an override rule. Raises ValidationError on bad input."""
    keyword, category = validate_override_rule(keyword, category)
    # user_id is filled by the column default auth.uid(); unique on (user_id, keyword)
    supabase_client.table('category_override_rules').upsert(
        {"keyword": keyword, "correct_category": category},
        on_conflict="user_id,keyword",
    ).execute()
