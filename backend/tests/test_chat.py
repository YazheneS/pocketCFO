import asyncio

from backend.app.routes import chat as chat_route


def test_common_finance_questions_load_transaction_context(monkeypatch):
    fetched = []
    transactions = [{
        "description": "Office rent",
        "amount": "1200.00",
        "type": "expense",
        "category": "Rent",
        "transaction_date": "2026-10-01",
    }]

    async def get_context(context):
        fetched.append(context.user_id)
        return transactions

    class GroqResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"choices": [{"message": {"content": "Your revenue is recorded."}}]}

    requests = []

    def post(url, **kwargs):
        requests.append(kwargs)
        return GroqResponse()

    monkeypatch.setenv("GROQ_API_KEY", "test-key")
    monkeypatch.setattr(chat_route, "get_transaction_context", get_context)
    monkeypatch.setattr(chat_route.requests, "post", post)

    response = asyncio.run(chat_route.chat(
        chat_route.ChatRequest(message="What are my expenses?"),
        chat_route.AuthenticatedContext(client=None, user_id="demo-user"),
    ))

    assert response.response == "Your revenue is recorded."
    assert fetched == ["demo-user"]
    assert "Office rent" in requests[0]["json"]["messages"][1]["content"]


def test_financial_terms_trigger_transaction_lookup():
    assert chat_route.is_transaction_question("Show my revenue")
    assert chat_route.is_transaction_question("How much did I spend on rent?")
    assert chat_route.is_transaction_question("Tell me about my last purchase")