import os
from groq import Groq
import re
from typing import List, Tuple, Optional

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
    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return "Other"
        client = Groq(api_key=api_key)
        prompt = (
            "Categorize this business transaction into EXACTLY one of these categories: Revenue, Inventory, Utilities, "
            "Rent, Salaries, Transport, Marketing, Maintenance, Personal, Food, Other. Transaction: '" + description + "'. "
            "Reply with ONLY the category name, nothing else. No explanation."
        )
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        text = resp.choices[0].message.content.strip()

        if not text:
            return "Other"
        category = text.strip()
        valid = list(CATEGORY_RULES.keys())
        if category not in valid:
            return "Other"
        return category
    except Exception:
        return "Other"


def get_category_from_rules(description: str) -> Tuple[str, float]:
    if not description:
        return ("Other", 0.50)
    desc = description.lower()
    for category, keywords in CATEGORY_RULES.items():
        if not keywords:
            continue
        for kw in keywords:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, desc):
                return (category, 0.90)
    # No rule match -> try Gemini
    try:
        res = get_category_from_gemini(description)
        if res:
            return (res, 0.75)
        return ("Other", 0.50)
    except Exception:
        return ("Other", 0.50)


def apply_categorization(transactions: List[dict]) -> List[dict]:
    updated = []
    for tx in transactions:
        desc = tx.get("description", "")
        cat, score = get_category_from_rules(desc)
        tx["category"] = cat
        tx["confidence_score"] = float(score)
        updated.append(tx)
    return updated


def check_category_corrections(description: str, supabase_client) -> Optional[str]:
    try:
        resp = supabase_client.table('category_override_rules').select('*').execute()
        # resp may be dict-like or have .data
        rows = None
        if isinstance(resp, dict):
            rows = resp.get('data')
        else:
            rows = getattr(resp, 'data', None) or getattr(resp, 'json', lambda: None)()
        if not rows:
            return None
        desc = (description or "").lower()
        for r in rows:
            keyword = (r.get('keyword') or '').lower()
            correct = r.get('correct_category')
            if keyword and keyword in desc:
                return correct
        return None
    except Exception:
        return None


def save_correction(keyword: str, category: str, supabase_client):
    try:
        supabase_client.table('category_override_rules').insert({
            "keyword": keyword,
            "correct_category": category
        }).execute()
    except Exception as e:
        print("Failed to save correction:", e)
