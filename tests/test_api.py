from fastapi.testclient import TestClient

from app.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.ai.extractor import RegexOrderExtractor
from app.api.orders import get_order_application_service, get_order_extractor
from app.main import app
from app.services.order_application_service import OrderApplicationService


repository = InMemoryOrderRepository()
app.dependency_overrides[get_order_extractor] = lambda: RegexOrderExtractor()
app.dependency_overrides[get_order_application_service] = lambda: OrderApplicationService(repository)
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_processed_order_is_persisted_and_can_be_approved() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 50 F-200."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready_for_approval"
    assert data["subtotal"] == 6000.0
    assert data["issues"] == []
    order_id = data["order_id"]

    stored = client.get(f"/api/v1/orders/{order_id}")
    assert stored.status_code == 200
    assert stored.json()["status"] == "ready_for_approval"

    approved = client.post(f"/api/v1/orders/{order_id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_review_order_cannot_bypass_human_review_to_approval() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 20 PV-10."},
    )
    order_id = response.json()["order_id"]
    assert response.json()["status"] == "requires_review"

    approved = client.post(f"/api/v1/orders/{order_id}/approve")
    assert approved.status_code == 409
    assert approved.json()["detail"] == "invalid order transition"

    stored = client.get(f"/api/v1/orders/{order_id}")
    assert stored.json()["status"] == "requires_review"


def test_orders_can_be_listed_and_unknown_order_is_404() -> None:
    listed = client.get("/api/v1/orders")
    assert listed.status_code == 200
    assert isinstance(listed.json(), list)

    missing = client.get("/api/v1/orders/00000000-0000-0000-0000-000000000000")
    assert missing.status_code == 404


def test_reject_ready_order_is_persisted() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 1 P-500."},
    )
    order_id = response.json()["order_id"]
    rejected = client.post(f"/api/v1/orders/{order_id}/reject")
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"


class FailingExtractor:
    def extract(self, payload):
        raise RuntimeError("provider details must not escape")


def test_provider_failure_fails_closed_and_is_persisted_for_review() -> None:
    app.dependency_overrides[get_order_extractor] = lambda: FailingExtractor()
    try:
        response = client.post(
            "/api/v1/orders/process",
            json={"subject": "Order Request", "body": "We need 50 F-200."},
        )
    finally:
        app.dependency_overrides[get_order_extractor] = lambda: RegexOrderExtractor()

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requires_review"
    assert data["items"] == []
    assert data["subtotal"] == 0.0
    assert data["issues"][0]["type"] == "extraction_provider_unavailable"
    assert "provider details must not escape" not in response.text
    stored = client.get(f"/api/v1/orders/{data['order_id']}")
    assert stored.json()["status"] == "requires_review"


def test_review_path_reaches_ready_then_approved_then_completed() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 20 PV-10."},
    )
    data = response.json()
    order_id = data["order_id"]
    assert data["status"] == "requires_review"

    detail = client.get(f"/api/v1/orders/{order_id}").json()
    assert detail["subject"] == "Order Request"
    assert detail["body"] == "We need 20 PV-10."
    assert detail["subtotal"] == 1500.0
    assert detail["issues"][0]["type"] == "insufficient_stock"

    assert client.post(f"/api/v1/orders/{order_id}/review").json()["status"] == "reviewed"
    assert client.post(f"/api/v1/orders/{order_id}/ready").json()["status"] == "ready_for_approval"
    assert client.post(f"/api/v1/orders/{order_id}/approve").json()["status"] == "approved"

    blocked = client.post(f"/api/v1/orders/{order_id}/complete")
    assert blocked.status_code == 409

    drafted = client.post(f"/api/v1/orders/{order_id}/response/draft")
    assert drafted.status_code == 200
    assert drafted.json()["status"] == "response_drafted"
    assert "PV-10" in drafted.json()["response_draft"]
    assert drafted.json()["response_sent_at"] is None

    sent = client.post(f"/api/v1/orders/{order_id}/response/send")
    assert sent.status_code == 200
    assert sent.json()["status"] == "response_sent"
    assert sent.json()["response_sent_at"] is not None

    assert client.post(f"/api/v1/orders/{order_id}/complete").json()["status"] == "completed"

    final = client.get(f"/api/v1/orders/{order_id}").json()
    assert final["status"] == "completed"
    assert final["response_draft"] is not None
    assert final["response_sent_at"] is not None
    assert final["items"][0]["unit_price"] == 75.0
    assert final["subtotal"] == 1500.0
