import os
import sys

import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
os.environ.setdefault("SUPABASE_URL", "http://localhost")
os.environ.setdefault("SUPABASE_KEY", "anon")

import server
import validators as v

TX = {"description": "sold cakes", "amount": 500, "type": "income", "category": "Revenue",
      "date": v.today_ist().isoformat(), "confidence_score": 0.9}
UUID = "123e4567-e89b-12d3-a456-426614174000"
AUTH = {"Authorization": "Bearer tok"}


class FakeQuery:
    def __init__(self, log, data):
        self.log, self.data = log, data
    def __getattr__(self, name):
        def call(*a, **k):
            self.log.append((name, a, k))
            return self
        return call
    def execute(self):
        class R: pass
        r = R(); r.data = self.data
        return r


def first_call(sb, name):
    """Positional args of the first recorded query-builder call called `name`."""
    return next(e[1] for e in sb.log if e[0] == name and len(e) == 3)


class FakeSb:
    def __init__(self, data=None):
        self.log, self.data = [], data
        self.postgrest = type("P", (), {"auth": lambda s, t: self.log.append(("auth", t))})()
    def table(self, name):
        self.log.append(("table", name))
        data = self.data(name) if callable(self.data) else self.data
        return FakeQuery(self.log, data)


@pytest.fixture
def client():
    server.app.config["TESTING"] = True
    return server.app.test_client()


def use(monkeypatch, sb):
    monkeypatch.setattr(server, "create_client", lambda *a, **k: sb)


def test_save_rejects_invalid_and_saves_nothing(client, monkeypatch):
    sb = FakeSb([]); use(monkeypatch, sb)
    r = client.post("/save-transactions", json={"transactions": [TX, {**TX, "amount": -1}]}, headers=AUTH)
    assert r.status_code == 400 and r.get_json()["rejected"][0]["index"] == 1
    assert not any(e[0] == "insert" for e in sb.log)


def test_save_is_strict_no_silent_fixes(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    r = client.post("/save-transactions", json={"transactions": [{**TX, "category": "Gadgets"}]}, headers=AUTH)
    assert r.status_code == 400


def test_save_works_without_auth(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    assert client.post("/save-transactions", json={"transactions": [TX]}).status_code != 401


def test_save_whitelists_columns(client, monkeypatch):
    sb = FakeSb([{"id": UUID}]); use(monkeypatch, sb)
    r = client.post("/save-transactions", json={"transactions": [{**TX, "user_id": "evil", "id": "x"}]}, headers=AUTH)
    assert r.status_code == 200 and r.get_json()["count"] == 1
    assert next(e[1] for e in sb.log if e[0] == "table") == "transactions"
    row = first_call(sb, "insert")[0][0]
    assert row["user_id"] == server.DEMO_USER_ID
    assert "id" not in row and "date" not in row and "currency" not in row


def test_save_fails_loudly_on_partial_insert(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    assert client.post("/save-transactions", json={"transactions": [TX]}, headers=AUTH).status_code == 500


def test_categorize_rejects_garbage(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    assert client.post("/categorize", json={"transactions": "x"}).status_code == 400
    r = client.post("/categorize", json={"transactions": [{"description": "x", "amount": 0, "type": "expense"}]})
    assert r.status_code == 400


def test_categorize_returns_valid_contract(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    r = client.post("/categorize", json={"transactions": [
        {"description": "bought flour", "amount": "200", "type": "expense"},
        {"description": "bad", "amount": "nope", "type": "expense"}]})
    body = r.get_json()
    assert body["count"] == 1 and len(body["rejected"]) == 1
    t = body["transactions"][0]
    assert t["category"] == "Inventory" and t["amount"] == 200.0 and 0 <= t["confidence_score"] <= 1


def test_correct_category_validation_and_auth(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    assert client.post("/correct-category", json={"new_category": "Nope", "keyword": "x"}, headers=AUTH).status_code == 400
    assert client.post("/correct-category", json={"new_category": "Food", "keyword": "x"}).status_code != 401


def test_correct_category_unknown_transaction_404(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    r = client.post("/correct-category", json={"new_category": "Food", "transaction_id": UUID}, headers=AUTH)
    assert r.status_code == 404


def test_correct_category_keyword_only_saves_rule(client, monkeypatch):
    sb = FakeSb([]); use(monkeypatch, sb)
    r = client.post("/correct-category", json={"new_category": "Food", "keyword": " Tea Stall ", "transaction_id": ""}, headers=AUTH)
    body = r.get_json()
    assert r.status_code == 200 and body["rule_saved"] and not body["updated"]
    payload = first_call(sb, "upsert")[0]
    assert payload == {"keyword": "tea stall", "correct_category": "Food"}


def test_parse_validates_text(client):
    assert client.post("/parse", json={"text": ""}).status_code == 400
    assert client.post("/parse", json={"text": "x" * 5000}).status_code == 400


def test_parse_endpoint_exposes_rejections(client, monkeypatch):
    import parser as p
    monkeypatch.setattr(p, "parse_transaction_detailed",
                        lambda t: {"transactions": [], "rejected": [{"index": 0, "errors": ["bad"]}], "warnings": []})
    body = client.post("/parse", json={"text": "sold tea"}).get_json()
    assert body["rejected"] and body["count"] == 0


def test_list_filters_validated(client, monkeypatch):
    use(monkeypatch, FakeSb([]))
    assert client.get("/transactions?limit=9999", headers=AUTH).status_code == 400
    assert client.get("/transactions?type=x", headers=AUTH).status_code == 400
    assert client.get("/transactions", headers=AUTH).status_code == 200
    assert client.get("/transactions").status_code == 200
