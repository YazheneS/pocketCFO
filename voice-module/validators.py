"""
Strict validation for the voice module.

Everything that crosses a trust boundary goes through here:

* LLM output from the parser (``parser.py``)
* LLM / rule output from the categorizer (``categorizer.py``)
* client payloads on the Flask endpoints (``server.py``)

Two modes:

* lenient (default): recoverable problems (unknown category, out-of-range
  confidence, missing date, unknown payment mode...) are normalised and
  reported as *warnings*. Unrecoverable problems (no description, bad amount,
  bad type, unparseable date) reject the transaction.
* strict (``strict=True``): used right before saving. Any recoverable problem
  is an *error* too, so nothing is silently altered on its way into the DB.

The constants below mirror the CHECK constraints in database/schema.sql
(``categorized_transactions`` / ``category_override_rules``). Keep both in sync.
"""

from __future__ import annotations

import math
import re
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Iterable, Optional

import pytz

# ---------------------------------------------------------------------------
# Constants (mirrored in database/schema.sql)
# ---------------------------------------------------------------------------

ALLOWED_CATEGORIES = (
    "Revenue", "Inventory", "Utilities", "Rent", "Salaries", "Transport",
    "Marketing", "Maintenance", "Personal", "Food", "Other",
)
ALLOWED_TYPES = ("income", "expense")
ALLOWED_PAYMENT_MODES = ("cash", "upi", "card", "bank_transfer", "cheque", "unknown")
ALLOWED_CURRENCIES = ("INR", "USD", "EUR", "GBP", "AED")

DEFAULT_CURRENCY = "INR"
DEFAULT_CONFIDENCE = 0.5

MAX_DESCRIPTION_LEN = 500
MAX_KEYWORD_LEN = 100
MAX_TEXT_INPUT_LEN = 1000
MAX_BATCH_SIZE = 50
MAX_AMOUNT = Decimal("9999999999.99")  # NUMERIC(12, 2)
MIN_DATE = date(2000, 1, 1)
FUTURE_DATE_TOLERANCE_DAYS = 1  # timezone slack

_TZ = pytz.timezone("Asia/Kolkata")

_CATEGORY_LOOKUP = {c.lower(): c for c in ALLOWED_CATEGORIES}

_PAYMENT_SYNONYMS = {
    "gpay": "upi", "google pay": "upi", "phonepe": "upi", "paytm": "upi",
    "bhim": "upi", "upi": "upi",
    "credit card": "card", "debit card": "card", "card": "card",
    "neft": "bank_transfer", "imps": "bank_transfer", "rtgs": "bank_transfer",
    "netbanking": "bank_transfer", "net banking": "bank_transfer",
    "bank transfer": "bank_transfer", "bank_transfer": "bank_transfer",
    "bank": "bank_transfer",
    "cash": "cash", "cheque": "cheque", "check": "cheque",
    "unknown": "unknown", "": "unknown",
}

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
_AMOUNT_NOISE = re.compile(r"[,\s₹$€£]|rs\.?|inr", re.IGNORECASE)


class ValidationError(ValueError):
    """Raised when a payload cannot be accepted. ``errors`` lists every problem."""

    def __init__(self, errors: Iterable[str]):
        self.errors = list(errors)
        super().__init__("; ".join(self.errors))


# ---------------------------------------------------------------------------
# Field normalisers
# ---------------------------------------------------------------------------

def today_ist() -> date:
    return datetime.now(_TZ).date()


def clean_text(value: Any) -> str:
    """Strip control characters, collapse whitespace, trim."""
    if not isinstance(value, str):
        return ""
    return _WHITESPACE.sub(" ", _CONTROL_CHARS.sub("", value)).strip()


def normalize_category(value: Any) -> Optional[str]:
    """Map an LLM/user supplied category onto the allowed set, else None.

    Tolerates case, surrounding quotes/punctuation and trailing periods
    ("revenue.", ' "Food" ').
    """
    if not isinstance(value, str):
        return None
    key = value.strip().strip("\"'`.,:;!() \n\t").lower()
    return _CATEGORY_LOOKUP.get(key)


def normalize_confidence(value: Any, default: float = DEFAULT_CONFIDENCE):
    """Return (score, problem). Score is always a float in [0, 1]."""
    if isinstance(value, bool) or value is None:
        return default, "confidence_score missing or not a number"
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default, "confidence_score is not a number"
    if math.isnan(score) or math.isinf(score):
        return default, "confidence_score is not finite"
    if score < 0 or score > 1:
        return min(1.0, max(0.0, score)), "confidence_score outside 0-1 was clamped"
    return round(score, 2), None


def parse_amount(value: Any) -> Decimal:
    """Parse to a positive Decimal(2dp) or raise ValueError."""
    if isinstance(value, bool) or value is None:
        raise ValueError("amount is missing")
    if isinstance(value, (int, float, Decimal)):
        raw = value
    elif isinstance(value, str):
        cleaned = _AMOUNT_NOISE.sub("", value)
        if not cleaned:
            raise ValueError("amount is empty")
        raw = cleaned
    else:
        raise ValueError("amount must be a number")
    try:
        amount = Decimal(str(raw))
    except InvalidOperation:
        raise ValueError(f"amount {value!r} is not a valid number")
    if not amount.is_finite():
        raise ValueError("amount must be finite")
    amount = amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if amount <= 0:
        raise ValueError("amount must be greater than 0")
    if amount > MAX_AMOUNT:
        raise ValueError("amount is too large")
    return amount


def parse_date(value: Any) -> date:
    """Accept YYYY-MM-DD (or an ISO datetime prefix). Reject out-of-range dates."""
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        try:
            parsed = datetime.strptime(value.strip()[:10], "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"date {value!r} must be in YYYY-MM-DD format")
    else:
        raise ValueError("date must be a YYYY-MM-DD string")
    if parsed < MIN_DATE:
        raise ValueError(f"date {parsed.isoformat()} is before {MIN_DATE.isoformat()}")
    if parsed > today_ist() + timedelta(days=FUTURE_DATE_TOLERANCE_DAYS):
        raise ValueError(f"date {parsed.isoformat()} is in the future")
    return parsed


def normalize_payment_mode(value: Any) -> str:
    if not isinstance(value, str):
        return "unknown"
    return _PAYMENT_SYNONYMS.get(value.strip().lower(), "unknown")


def normalize_uuid(value: Any) -> str:
    """Return canonical lowercase UUID string or raise ValueError."""
    if not isinstance(value, str):
        raise ValueError("id must be a UUID string")
    try:
        return str(uuid.UUID(value.strip()))
    except ValueError:
        raise ValueError(f"{value!r} is not a valid UUID")


# ---------------------------------------------------------------------------
# Type / category consistency
# ---------------------------------------------------------------------------

def reconcile_type_and_category(tx_type: str, category: str):
    """Return (category, problem). Income -> Revenue/Other, Revenue -> income only."""
    if tx_type == "income" and category not in ("Revenue", "Other"):
        return "Revenue", f"income cannot have category {category!r}; set to Revenue"
    if tx_type == "expense" and category == "Revenue":
        return "Other", "expense cannot have category 'Revenue'; set to Other"
    return category, None


# ---------------------------------------------------------------------------
# Transaction validation
# ---------------------------------------------------------------------------

def validate_transaction(raw: Any, *, strict: bool = False, today: Optional[date] = None):
    """Validate one transaction dict.

    Returns ``(clean, warnings)``. ``clean`` contains ONLY whitelisted keys, so
    callers can never smuggle ``id``/``user_id``/arbitrary columns into the DB.
    Raises :class:`ValidationError` listing every unrecoverable problem.
    In strict mode warnings are raised as errors instead.
    """
    if not isinstance(raw, dict):
        raise ValidationError(["transaction must be an object"])

    errors: list[str] = []
    warnings: list[str] = []

    def problem(msg: str) -> None:
        (errors if strict else warnings).append(msg)

    # description
    description = clean_text(raw.get("description", raw.get("merchant")))
    if not description:
        errors.append("description is required")
    elif len(description) > MAX_DESCRIPTION_LEN:
        if strict:
            errors.append(f"description exceeds {MAX_DESCRIPTION_LEN} characters")
        else:
            description = description[:MAX_DESCRIPTION_LEN].rstrip()
            warnings.append(f"description truncated to {MAX_DESCRIPTION_LEN} characters")

    # amount
    amount: Optional[Decimal] = None
    try:
        amount = parse_amount(raw.get("amount"))
    except ValueError as e:
        errors.append(str(e))

    # type
    tx_type = raw.get("type")
    tx_type = tx_type.strip().lower() if isinstance(tx_type, str) else None
    if tx_type not in ALLOWED_TYPES:
        errors.append(f"type must be one of {', '.join(ALLOWED_TYPES)}")
        tx_type = None

    # date (accepts `transaction_date` or parser's `date`)
    raw_date = raw.get("transaction_date", raw.get("date"))
    parsed_date: Optional[date] = None
    if raw_date in (None, ""):
        problem("date missing; defaulted to today")
        parsed_date = today or today_ist()
    else:
        try:
            parsed_date = parse_date(raw_date)
        except ValueError as e:
            errors.append(str(e))

    # category
    category = normalize_category(raw.get("category"))
    if category is None:
        if raw.get("category") in (None, ""):
            # Not categorised yet (e.g. input to /categorize): fine in lenient mode.
            if strict:
                errors.append("category is required")
        else:
            problem(f"category {raw.get('category')!r} is not allowed; set to Other")
        category = "Other"
    elif raw.get("category") != category:
        problem(f"category {raw.get('category')!r} normalised to {category!r}")

    if tx_type:
        category, msg = reconcile_type_and_category(tx_type, category)
        if msg:
            problem(msg)

    # currency
    currency = raw.get("currency", DEFAULT_CURRENCY)
    currency = currency.strip().upper() if isinstance(currency, str) else None
    if currency not in ALLOWED_CURRENCIES:
        problem(f"currency {raw.get('currency')!r} is not supported; set to {DEFAULT_CURRENCY}")
        currency = DEFAULT_CURRENCY

    # payment mode
    payment_mode = normalize_payment_mode(raw.get("payment_mode", "unknown"))
    if (
        isinstance(raw.get("payment_mode"), str)
        and raw["payment_mode"].strip().lower() != payment_mode
        and raw["payment_mode"].strip() != ""
    ):
        problem(f"payment_mode {raw.get('payment_mode')!r} normalised to {payment_mode!r}")

    # confidence
    confidence, conf_problem = normalize_confidence(raw.get("confidence_score"))
    if raw.get("confidence_score") is None:
        if strict:
            errors.append("confidence_score is required")
    elif conf_problem:
        problem(conf_problem)

    if errors:
        raise ValidationError(errors)

    clean = {
        "description": description,
        "amount": float(amount),
        "type": tx_type,
        "category": category,
        "currency": currency,
        "date": parsed_date.isoformat(),
        "transaction_date": parsed_date.isoformat(),
        "payment_mode": payment_mode,
        "confidence_score": confidence,
        "is_personal": category == "Personal",
    }
    return clean, warnings


def validate_transactions(raws: Any, *, strict: bool = False, max_items: int = MAX_BATCH_SIZE):
    """Validate a batch. Returns ``(valid, rejected, warnings)``.

    ``rejected`` entries are ``{"index": i, "errors": [...]}``.
    Raises :class:`ValidationError` if the batch itself is malformed.
    """
    if not isinstance(raws, list) or not raws:
        raise ValidationError(["transactions must be a non-empty list"])
    if len(raws) > max_items:
        raise ValidationError([f"too many transactions (max {max_items})"])

    valid, rejected, warnings = [], [], []
    for i, raw in enumerate(raws):
        try:
            clean, warns = validate_transaction(raw, strict=strict)
            valid.append(clean)
            warnings.extend(f"#{i}: {w}" for w in warns)
        except ValidationError as e:
            rejected.append({"index": i, "errors": e.errors})
    return valid, rejected, warnings


def to_db_row(clean: dict) -> dict:
    """Project a validated transaction onto ``categorized_transactions`` columns."""
    return {
        "description": clean["description"],
        "amount": clean["amount"],
        "type": clean["type"],
        "category": clean["category"],
        "currency": clean["currency"],
        "transaction_date": clean["transaction_date"],
        "payment_mode": clean["payment_mode"],
        "confidence_score": clean["confidence_score"],
        "is_personal": clean["is_personal"],
    }


# ---------------------------------------------------------------------------
# Other payloads
# ---------------------------------------------------------------------------

def validate_text_input(value: Any) -> str:
    text = clean_text(value)
    if not text:
        raise ValidationError(["text is required"])
    if len(text) > MAX_TEXT_INPUT_LEN:
        raise ValidationError([f"text exceeds {MAX_TEXT_INPUT_LEN} characters"])
    return text


def validate_override_rule(keyword: Any, category: Any) -> tuple[str, str]:
    """Return a normalised (keyword, category) for category_override_rules."""
    errors = []
    kw = clean_text(keyword).lower() if isinstance(keyword, str) else ""
    if not kw:
        errors.append("keyword is required")
    elif len(kw) > MAX_KEYWORD_LEN:
        kw = kw[:MAX_KEYWORD_LEN].rstrip()  # long descriptions are used as keywords
    cat = normalize_category(category)
    if cat is None:
        errors.append(f"category must be one of {', '.join(ALLOWED_CATEGORIES)}")
    if errors:
        raise ValidationError(errors)
    return kw, cat


def validate_correction_payload(payload: Any) -> dict:
    """Validate the /correct-category body.

    ``transaction_id`` is optional (batch cards from /categorize aren't saved
    yet) but must be a UUID when present. At least one of ``transaction_id`` or
    ``keyword`` is needed so the request does something.
    """
    if not isinstance(payload, dict):
        raise ValidationError(["body must be a JSON object"])
    errors = []

    category = normalize_category(payload.get("new_category"))
    if category is None:
        errors.append(f"new_category must be one of {', '.join(ALLOWED_CATEGORIES)}")

    tx_id = None
    if payload.get("transaction_id") not in (None, ""):
        try:
            tx_id = normalize_uuid(payload["transaction_id"])
        except ValueError as e:
            errors.append(f"transaction_id: {e}")

    keyword = None
    if payload.get("keyword") not in (None, ""):
        try:
            keyword, _ = validate_override_rule(payload["keyword"], category or "Other")
        except ValidationError as e:
            errors.extend(e.errors)

    if not tx_id and not keyword and not errors:
        errors.append("transaction_id or keyword is required")
    if errors:
        raise ValidationError(errors)
    return {"transaction_id": tx_id, "new_category": category, "keyword": keyword}


def validate_query_filters(args) -> dict:
    """Validate GET /transactions style filters (category, type, limit, date)."""
    errors, out = [], {}
    if args.get("category"):
        cat = normalize_category(args["category"])
        if cat is None:
            errors.append("category filter is not allowed")
        out["category"] = cat
    if args.get("type"):
        t = args["type"].strip().lower()
        if t not in ALLOWED_TYPES:
            errors.append(f"type must be one of {', '.join(ALLOWED_TYPES)}")
        out["type"] = t
    if args.get("date"):
        try:
            out["date"] = datetime.strptime(args["date"].strip(), "%Y-%m-%d").date().isoformat()
        except ValueError:
            errors.append("date must be in YYYY-MM-DD format")
    try:
        limit = int(args.get("limit") or 50)
    except ValueError:
        errors.append("limit must be an integer")
        limit = 50
    if not 1 <= limit <= 200:
        errors.append("limit must be between 1 and 200")
    out["limit"] = limit
    if errors:
        raise ValidationError(errors)
    return out
