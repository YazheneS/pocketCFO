import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, request, jsonify
from flask_cors import CORS

from categorizer import apply_categorization, check_category_corrections, save_correction
from supabase import create_client

app = Flask(__name__)
CORS(app)

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))


@app.route("/categorize", methods=["POST"])
def categorize():
    try:
        payload = request.get_json() or {}
        transactions = payload.get("transactions")
        if not transactions or not isinstance(transactions, list):
            return jsonify({"success": False, "error": "transactions missing or empty"}), 400

        to_categorize = []
        updated = []
        for tx in transactions:
            desc = tx.get("description", "")
            corrected = None
            try:
                corrected = check_category_corrections(desc, supabase)
            except Exception:
                corrected = None
            if corrected:
                tx["category"] = corrected
                tx["confidence_score"] = 1.0
                updated.append(tx)
            else:
                to_categorize.append(tx)

        if to_categorize:
            processed = apply_categorization(to_categorize)
            updated.extend(processed)

        return jsonify({"success": True, "transactions": updated, "count": len(updated)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/save-transactions", methods=["POST"])
def save_transactions():
    try:
        payload = request.get_json() or {}
        transactions = payload.get("transactions")
        if not transactions or not isinstance(transactions, list):
            return jsonify({"success": False, "error": "transactions missing or empty"}), 400

        # Attempt batch insert
        try:
            resp = supabase.table('categorized_transactions').insert(transactions).execute()
            # normalize response
            if isinstance(resp, dict):
                rows = resp.get('data') or []
            else:
                rows = getattr(resp, 'data', None) or []
            ids = [r.get('id') for r in rows if r.get('id')]
        except Exception:
            # Fallback to individual inserts
            ids = []
            for tx in transactions:
                try:
                    r = supabase.table('categorized_transactions').insert(tx).execute()
                    if isinstance(r, dict):
                        d = r.get('data') or []
                        if d and isinstance(d, list):
                            ids.append(d[0].get('id'))
                    else:
                        data = getattr(r, 'data', None) or []
                        if data and isinstance(data, list):
                            ids.append(data[0].get('id'))
                except Exception:
                    continue

        return jsonify({"success": True, "saved": True, "count": len(ids), "ids": ids})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/correct-category", methods=["POST"])
def correct_category():
    try:
        payload = request.get_json() or {}
        transaction_id = payload.get("transaction_id")
        new_category = payload.get("new_category")
        keyword = payload.get("keyword")
        if not transaction_id or not new_category:
            return jsonify({"success": False, "error": "transaction_id and new_category required"}), 400

        supabase.table('categorized_transactions').update({"category": new_category}).eq('id', transaction_id).execute()
        # Save override rule for future
        try:
            if keyword:
                save_correction(keyword, new_category, supabase)
        except Exception:
            pass

        return jsonify({"success": True, "updated": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/transactions", methods=["GET"])
def get_transactions():
    try:
        category = request.args.get('category')
        ttype = request.args.get('type')
        limit = int(request.args.get('limit') or 50)

        query = supabase.table('categorized_transactions').select('*').order('created_at', {'ascending': False})
        if category:
            query = query.eq('category', category)
        if ttype:
            query = query.eq('type', ttype)
        if limit:
            query = query.limit(limit)

        resp = query.execute()
        if isinstance(resp, dict):
            rows = resp.get('data') or []
        else:
            rows = getattr(resp, 'data', None) or []

        return jsonify({"success": True, "transactions": rows, "count": len(rows)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/categories/summary", methods=["GET"])
def categories_summary():
    try:
        resp = supabase.table('categorized_transactions').select('*').execute()
        if isinstance(resp, dict):
            rows = resp.get('data') or []
        else:
            rows = getattr(resp, 'data', None) or []

        summary = {}
        for r in rows:
            cat = r.get('category') or 'Other'
            amt = r.get('amount') or 0
            try:
                val = float(amt)
            except Exception:
                try:
                    val = float(str(amt))
                except Exception:
                    val = 0
            summary[cat] = summary.get(cat, 0) + val

        return jsonify({"success": True, "summary": summary})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/summary", methods=["GET"])
def overall_summary():
    try:
        date_filter = request.args.get('date')
        query = supabase.table('categorized_transactions').select('*')
        if date_filter:
            query = query.eq('date', date_filter)
        resp = query.execute()
        if isinstance(resp, dict):
            rows = resp.get('data') or []
        else:
            rows = getattr(resp, 'data', None) or []

        total_revenue = 0.0
        total_expenses = 0.0
        for r in rows:
            amt = r.get('amount') or 0
            try:
                val = float(amt)
            except Exception:
                try:
                    val = float(str(amt))
                except Exception:
                    val = 0
            ttype = (r.get('type') or '').lower()
            if ttype == 'income':
                total_revenue += val
            elif ttype == 'expense':
                total_expenses += val
        net_profit = total_revenue - total_expenses
        return jsonify({
            "success": True,
            "summary": {
                "total_revenue": total_revenue,
                "total_expenses": total_expenses,
                "net_profit": net_profit,
                "transaction_count": len(rows)
            }
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "message": "PocketCFO API is running"})


@app.route("/parse", methods=["POST"])
def parse():
    try:
        payload = request.get_json() or {}
        text = payload.get("text", "").strip()
        if not text:
            return jsonify({"success": False, "error": "text is required"}), 400

        from parser import parse_transaction
        parsed = parse_transaction(text)

        return jsonify({
            "success": True,
            "parsed": parsed,
            "count": len(parsed)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5000)), debug=True)
