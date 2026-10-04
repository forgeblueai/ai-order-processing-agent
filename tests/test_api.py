from fastapi.testclient import TestClient

from app.ai.extractor import RegexOrderExtractor
from app.api.orders import get_order_extractor
from app.main import app


app.dependency_overrides[get_order_extractor] = lambda: RegexOrderExtractor()
client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_order_with_enough_stock_is_ready_for_approval() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 50 F-200."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready_for_approval"
    assert data["subtotal"] == 6000.0
    assert data["issues"] == []


def test_insufficient_stock_requires_review() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order Request", "body": "We need 50 F-200 and 20 PV-10."},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "requires_review"
    assert data["subtotal"] == 7500.0
    assert data["issues"] == [
        {"sku": "PV-10", "type": "insufficient_stock", "requested": 20, "available": 15}
    ]


def test_unrecognized_order_is_sent_to_review() -> None:
    response = client.post(
        "/api/v1/orders/process",
        json={"subject": "Order", "body": "Please send our usual filters."},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "requires_review"


class FailingExtractor:
    def extract(self, payload):
        raise RuntimeError("provider details must not escape")


def test_provider_failure_fails_closed_at_http_boundary() -> None:
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
    assert data["issues"] == [
        {
            "sku": "unknown",
            "type": "extraction_provider_unavailable",
            "requested": None,
            "available": None,
        }
    ]
    assert "provider details must not escape" not in response.text
