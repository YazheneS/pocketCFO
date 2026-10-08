import os
import json
from groq import Groq
from dotenv import load_dotenv
from datetime import datetime
import pytz
import re

from validators import ValidationError, validate_text_input, validate_transactions, MAX_BATCH_SIZE

load_dotenv()

def _extract_json_array(raw: str):
    """Pull a JSON value out of an LLM reply (strips fences / chatter)."""
    raw = re.sub(r"```(?:json)?", "", raw).strip()
    start, end = raw.find("["), raw.rfind("]") + 1
    if start != -1 and end > start:
        raw = raw[start:end]
    return json.loads(raw)


def validate_parser_output(result) -> dict:
    """Strictly validate whatever the LLM produced.

    Returns ``{"transactions": [...], "rejected": [...], "warnings": [...]}``.
    Only schema-conformant transactions are returned; everything else is listed
    in ``rejected`` with the reasons, never silently passed on.
    """
    if isinstance(result, dict):
        result = [result]
    if not isinstance(result, list) or not result:
        return {"transactions": [], "rejected": [], "warnings": ["no transactions found"]}
    if len(result) > MAX_BATCH_SIZE:
        extra = len(result) - MAX_BATCH_SIZE
        result = result[:MAX_BATCH_SIZE]
        truncated = [f"{extra} transactions beyond the limit of {MAX_BATCH_SIZE} were ignored"]
    else:
        truncated = []
    valid, rejected, warnings = validate_transactions(result, max_items=MAX_BATCH_SIZE)
    return {"transactions": valid, "rejected": rejected, "warnings": truncated + warnings}


def parse_transaction_detailed(text: str) -> dict:
    """Parse free text into validated transactions plus rejection details."""
    empty = {"transactions": [], "rejected": [], "warnings": []}
    raw = ""
    try:
        text = validate_text_input(text)
    except ValidationError as e:
        return {**empty, "warnings": e.errors}

    try:
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("ERROR: GROQ_API_KEY not found")
            return {**empty, "warnings": ["GROQ_API_KEY not configured"]}

        client = Groq(api_key=api_key)

        today = datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%Y-%m-%d')

        prompt = f"""You are a financial transaction parser.
Extract ALL transactions from the text below.
Return ONLY a raw JSON array. No markdown. No backticks. No explanation.

Each item must have:
{{
  "description": "short description",
  "amount": 200,
  "type": "expense or income",
  "category": "Inventory or Revenue or Utilities or Rent or Personal or Transport or Salaries or Marketing or Maintenance or Food or Other",
  "currency": "INR",
  "date": "{today}",
  "payment_mode": "unknown",
  "confidence_score": 0.85
}}

CRITICAL RULES for type and category:
- If text contains: sold, selling, received, earned, got paid, income, sale, profit, got money
  -> type = 'income' AND category = 'Revenue'

- If text contains: bought, purchasing, paid, spent, cost, bill, rent, salary, expense
  -> type = 'expense'

- 'sold juice' = income, Revenue
- 'sold cakes' = income, Revenue  
- 'sold anything' = income, Revenue
- NEVER put sold/received items as Food or Inventory

Rules:
- "bought/purchased/paid" = expense
- "sold/received/earned/got" = income
- Convert word amounts: "fifty" = 50, "hundred" = 100
- If multiple transactions in one sentence, return multiple objects

Text: {text}

Return ONLY the JSON array starting with [ and ending with ]"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            messages=[{"role": "user", "content": prompt}]
        )
        raw = (response.choices[0].message.content or "").strip()
        print(f"[PARSE] Groq response length: {len(raw)} chars")

        return validate_parser_output(_extract_json_array(raw))

    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Raw response was: {raw}")
        return {**empty, "warnings": ["model returned invalid JSON"]}
    except Exception as e:
        print(f"Parse error: {e}")
        return {**empty, "warnings": ["parsing failed"]}


def parse_transaction(text: str) -> list[dict]:
    """Backwards-compatible wrapper: validated transactions only."""
    return parse_transaction_detailed(text)["transactions"]
