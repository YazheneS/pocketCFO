import os
import base64
import binascii
import json
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from categorizer import apply_categorization, check_category_corrections, save_correction
from supabase import create_client
from validators import (
    ValidationError,
    to_db_row,
    validate_correction_payload,
    validate_query_filters,
    validate_text_input,
    validate_transaction,
    validate_transactions,
)

app = Flask(__name__)
CORS(app)


def _bearer_token():
    header = request.headers.get("Authorization", "")
    if header.lower().startswith("bearer "):
        return header[7:].strip() or None
    return None


def get_supabase(require_user: bool = False):
    """Return a Supabase client (login is not enforced; ``require_user`` is ignored)."""
    # Authentication is disabled: every request uses the plain client and the
    # shared demo user configured in database/migrations/003_disable_auth.sql.
    return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


def _rows(resp):
    if isinstance(resp, dict):
        return resp.get("data") or []
    return getattr(resp, "data", None) or []


@app.errorhandler(PermissionError)
def _unauthorized(e):
    return jsonify({"success": False, "error": str(e)}), 401


def _bad_request(e: ValidationError):
    return jsonify({"success": False, "error": "; ".join(e.errors), "errors": e.errors}), 400


@app.route("/categorize", methods=["POST"])
def categorize():
    try:
        payload = request.get_json(silent=True) or {}
        try:
            transactions, rejected, warnings = validate_transactions(payload.get("transactions"))
        except ValidationError as e:
            return _bad_request(e)
        if not transactions:
            return jsonify({"success": False, "error": "no valid transactions",
                            "rejected": rejected}), 400

        supabase = get_supabase()

        to_categorize = []
        updated = []
        for tx in transactions:
            corrected = None
            if supabase is not None:
                try:
                    corrected = check_category_corrections(tx["description"], supabase)
                except Exception:
                    corrected = None
            if corrected:
                tx["category"] = corrected
                tx["confidence_score"] = 1.0
                updated.append(tx)
            else:
                to_categorize.append(tx)

        if to_categorize:
            updated.extend(apply_categorization(to_categorize))

        # Final contract check on everything we are about to hand back.
        final, final_rejected, final_warnings = validate_transactions(updated)
        rejected += final_rejected
        warnings += final_warnings
        return jsonify({"success": True, "transactions": final, "count": len(final),
                        "rejected": rejected, "warnings": warnings})
    except Exception as e:
        app.logger.exception("categorize failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/save-transactions", methods=["POST"])
def save_transactions():
    """All-or-nothing save. Strict validation: nothing is altered or dropped."""
    try:
        payload = request.get_json(silent=True) or {}
        try:
            valid, rejected, _ = validate_transactions(payload.get("transactions"), strict=True)
        except ValidationError as e:
            return _bad_request(e)
        if rejected:
            return jsonify({"success": False, "error": "validation failed; nothing was saved",
                            "rejected": rejected}), 400

        supabase = get_supabase(require_user=True)
        rows = [to_db_row(tx) for tx in valid]  # whitelist: no id/user_id from the client
        resp = supabase.table('categorized_transactions').insert(rows).execute()
        ids = [r.get('id') for r in _rows(resp) if r.get('id')]
        if len(ids) != len(rows):
            app.logger.error("save-transactions: inserted %s of %s rows", len(ids), len(rows))
            return jsonify({"success": False, "error": "save did not complete"}), 500

        return jsonify({"success": True, "saved": True, "count": len(ids), "ids": ids})
    except PermissionError:
        raise
    except Exception as e:
        app.logger.exception("save-transactions failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/correct-category", methods=["POST"])
def correct_category():
    try:
        try:
            data = validate_correction_payload(request.get_json(silent=True))
        except ValidationError as e:
            return _bad_request(e)

        supabase = get_supabase(require_user=True)
        updated = False
        if data["transaction_id"]:
            resp = (supabase.table('categorized_transactions')
                    .update({"category": data["new_category"],
                             "is_personal": data["new_category"] == "Personal"})
                    .eq('id', data["transaction_id"]).execute())
            if not _rows(resp):  # RLS hides other users' rows, so this is also an ownership check
                return jsonify({"success": False, "error": "transaction not found"}), 404
            updated = True

        rule_saved = False
        if data["keyword"]:
            try:
                save_correction(data["keyword"], data["new_category"], supabase)
                rule_saved = True
            except Exception:
                app.logger.exception("could not save override rule")

        return jsonify({"success": True, "updated": updated, "rule_saved": rule_saved})
    except PermissionError:
        raise
    except Exception as e:
        app.logger.exception("correct-category failed")
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        try:
            f = validate_query_filters(request.args)
        except ValidationError as e:
            return _bad_request(e)

        supabase = get_supabase(require_user=True)
        query = supabase.table('categorized_transactions').select('*').order('created_at', desc=True)
        if f.get("category"):
            query = query.eq('category', f["category"])
        if f.get("type"):
            query = query.eq('type', f["type"])
        query = query.limit(f["limit"])

        rows = _rows(query.execute())
        return jsonify({"success": True, "transactions": rows, "count": len(rows)})
    except PermissionError:
        raise
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


@app.route("/categories/summary", methods=["GET"])
def categories_summary():
    try:
        supabase = get_supabase(require_user=True)
        rows = _rows(supabase.table('categorized_transactions').select('category,amount').execute())

        summary = {}
        for r in rows:
            cat = r.get('category') or 'Other'
            summary[cat] = summary.get(cat, 0) + _to_float(r.get('amount'))

        return jsonify({"success": True, "summary": summary})
    except PermissionError:
        raise
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/summary", methods=["GET"])
def overall_summary():
    try:
        try:
            f = validate_query_filters(request.args)
        except ValidationError as e:
            return _bad_request(e)

        supabase = get_supabase(require_user=True)
        query = supabase.table('categorized_transactions').select('type,amount')
        if f.get("date"):
            query = query.eq('transaction_date', f["date"])
        rows = _rows(query.execute())

        total_revenue = 0.0
        total_expenses = 0.0
        for r in rows:
            val = _to_float(r.get('amount'))
            ttype = (r.get('type') or '').lower()
            if ttype == 'income':
                total_revenue += val
            elif ttype == 'expense':
                total_expenses += val
        return jsonify({
            "success": True,
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": total_revenue - total_expenses,
                "transaction_count": len(rows)
            }
        })
    except PermissionError:
        raise
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "PocketCFO API is running"})


@app.route("/auth/config", methods=["GET"])
def auth_config():
    """Return only the Supabase browser configuration, never a service key."""
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        return jsonify({"success": False, "message": "Supabase is not configured"}), 503

    try:
        encoded_payload = supabase_key.split(".")[1]
        encoded_payload += "=" * (-len(encoded_payload) % 4)
        role = json.loads(
            base64.urlsafe_b64decode(encoded_payload).decode("utf-8")
        ).get("role")
    except (IndexError, ValueError, UnicodeDecodeError, binascii.Error):
        role = None

    if role != "anon":
        return jsonify({
            "success": False,
            "message": "A public Supabase anon key is required for browser authentication",
        }), 500

    return jsonify({
        "success": True,
        "supabase_url": supabase_url,
        "supabase_anon_key": supabase_key,
    })


@app.route("/", methods=["GET"])
def serve_index():
    return send_from_directory(os.path.dirname(__file__), 'index.html')


@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    if os.path.isfile(os.path.join(os.path.dirname(__file__), path)):
        return send_from_directory(os.path.dirname(__file__), path)
    return send_from_directory(os.path.dirname(__file__), 'index.html')


@app.route("/parse", methods=["POST"])
def parse():
    try:
        payload = request.get_json(silent=True) or {}
        try:
            text = validate_text_input(payload.get("text"))
        except ValidationError as e:
            return _bad_request(e)

        from parser import parse_transaction_detailed
        result = parse_transaction_detailed(text)

        return jsonify({
            "success": True,
            "parsed": result["transactions"],
            "count": len(result["transactions"]),
            "rejected": result["rejected"],
            "warnings": result["warnings"],
        })
    except Exception as e:
        app.logger.exception("parse failed")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
