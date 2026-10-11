"""Negative-access matrix for every order route.

All credentials in this test module are non-production, deterministic fixtures.
"""

import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from app.api.orders import get_order_application_service
from app.main import app

_TEST_KEYS = {
    role: f"test-only-{role}-key-not-for-production-0000000000000000"
    for role in ("operator", "reviewer", "approver", "sender")
}
_ROUTES = [
    ("POST", "/api/v1/orders/process", "operator"),
    ("GET", "/api/v1/orders", "operator"),
    ("GET", "/api/v1/orders/00000000-0000-0000-0000-000000000001", "operator"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/approve", "approver"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/reject", "approver"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/review", "reviewer"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/ready", "reviewer"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/response/draft", "sender"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/response/send", "sender"),
    ("POST", "/api/v1/orders/00000000-0000-0000-0000-000000000001/complete", "sender"),
]


@pytest.fixture
def configured_auth(monkeypatch):
    digests = {hashlib.sha256(key.encode()).hexdigest(): [role] for role, key in _TEST_KEYS.items()}
    monkeypatch.setenv("ORDER_API_KEY_HASHES_JSON", json.dumps(digests))
    return _TEST_KEYS


def _request(client, method, path, token=None):
    headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
    kwargs = {"headers": headers}
    if method == "POST" and path.endswith("/process"):
        kwargs["json"] = {"subject": "Test", "body": "Please send 2 F-200."}
    return client.request(method, path, **kwargs)


@pytest.mark.parametrize("method,path,role", _ROUTES)
def test_anonymous_request_denied_before_order_access(configured_auth, method, path, role):
    class UnreachableService:
        def __getattribute__(self, name):
            raise AssertionError("order service must not be used by anonymous caller")

    existing_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_order_application_service] = lambda: UnreachableService()
    try:
        response = _request(TestClient(app), method, path)
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)


@pytest.mark.parametrize("method,path,role", _ROUTES)
def test_wrong_role_cannot_access_or_mutate(configured_auth, method, path, role):
    other_role = next(candidate for candidate in _TEST_KEYS if candidate != role)

    class UnreachableService:
        def __getattribute__(self, name):
            raise AssertionError("wrong role must never access the database")

    existing_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_order_application_service] = lambda: UnreachableService()
    try:
        response = _request(TestClient(app), method, path, configured_auth[other_role])
        assert response.status_code == 403
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)


def test_missing_configuration_fails_closed(monkeypatch):
    monkeypatch.delenv("ORDER_API_KEY_HASHES_JSON", raising=False)
    response = _request(TestClient(app), "GET", "/api/v1/orders", _TEST_KEYS["operator"])
    assert response.status_code == 503
    assert "authentication unavailable" in response.json()["detail"]


@pytest.mark.parametrize("bad_value", ["", "not json", "{}", '{"abcd":["operator"]}', '{"f":["admin"]}'])
def test_malformed_auth_config_fails_closed(monkeypatch, bad_value):
    monkeypatch.setenv("ORDER_API_KEY_HASHES_JSON", bad_value)
    response = _request(TestClient(app), "GET", "/api/v1/orders", _TEST_KEYS["operator"])
    assert response.status_code == 503


def test_invalid_bearer_is_unauthorized(configured_auth):
    response = _request(TestClient(app), "GET", "/api/v1/orders", "wrong-token-value-000000000000000000000000000")
    assert response.status_code == 401


def test_valid_operator_can_list_empty_orders(configured_auth):
    class EmptyService:
        def list(self):
            return []

    existing_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_order_application_service] = lambda: EmptyService()
    try:
        response = _request(TestClient(app), "GET", "/api/v1/orders", configured_auth["operator"])
        assert response.status_code == 200
        assert response.json() == []
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)


def test_public_health_stays_available_without_auth(monkeypatch):
    monkeypatch.delenv("ORDER_API_KEY_HASHES_JSON", raising=False)
    response = TestClient(app).get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_denied_approve_and_send_do_not_change_stored_state(configured_auth):
    from app.adapters.in_memory_order_repository import InMemoryOrderRepository
    from app.schemas.order import OrderStatus
    from app.services.order_application_service import OrderApplicationService

    orders = OrderApplicationService(InMemoryOrderRepository())
    record = orders.create(subject="Sensitive customer", body="We need 2 F-200.")
    initial_status = orders.get(record.id).status
    existing_overrides = dict(app.dependency_overrides)
    app.dependency_overrides[get_order_application_service] = lambda: orders
    try:
        api = TestClient(app)
        denied_approval = _request(
            api, "POST", f"/api/v1/orders/{record.id}/approve", configured_auth["operator"]
        )
        denied_send = _request(
            api, "POST", f"/api/v1/orders/{record.id}/response/send", configured_auth["approver"]
        )
        assert denied_approval.status_code == 403
        assert denied_send.status_code == 403
        assert orders.get(record.id).status == initial_status == OrderStatus.RECEIVED
    finally:
        app.dependency_overrides.clear()
        app.dependency_overrides.update(existing_overrides)
