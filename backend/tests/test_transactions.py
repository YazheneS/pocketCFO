from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.app.routes import transactions
from backend.app.utils.supabase_client import AuthenticatedContext


def test_delete_transaction_accepts_uuid_path_parameter():
    transaction_id = "6fa49330-3c5c-4c5b-a4c3-1424cb81e89e"

    class FakeService:
        fetched_id = None
        deleted_id = None

        async def get_transaction_by_id(self, user_id, requested_id):
            self.fetched_id = requested_id
            return object()

        async def delete_transaction(self, user_id, requested_id):
            self.deleted_id = requested_id

    service = FakeService()
    app = FastAPI()
    app.include_router(transactions.router)
    app.dependency_overrides[transactions.get_authenticated_context_dependency] = (
        lambda: AuthenticatedContext(client=object(), user_id="demo-user")
    )
    app.dependency_overrides[transactions.get_transaction_service] = lambda: service

    response = TestClient(app).delete(f"/transactions/{transaction_id}")

    assert response.status_code == 200
    assert service.fetched_id == transaction_id
    assert service.deleted_id == transaction_id