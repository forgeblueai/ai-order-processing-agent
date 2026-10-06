from uuid import uuid4

import pytest

from app.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.schemas.order import OrderStatus
from app.services.order_application_service import OrderApplicationService, OrderNotFoundError
from app.services.order_lifecycle import InvalidOrderTransition


def test_create_persists_received_order() -> None:
    repository = InMemoryOrderRepository()
    service = OrderApplicationService(repository)

    created = service.create()

    assert created.status is OrderStatus.RECEIVED
    assert repository.get(created.id) == created


def test_get_returns_persisted_order() -> None:
    repository = InMemoryOrderRepository()
    service = OrderApplicationService(repository)
    created = service.create()

    assert service.get(created.id) == created


def test_get_unknown_order_raises_domain_safe_error() -> None:
    service = OrderApplicationService(InMemoryOrderRepository())

    with pytest.raises(OrderNotFoundError):
        service.get(uuid4())


def test_valid_transition_is_persisted() -> None:
    repository = InMemoryOrderRepository()
    service = OrderApplicationService(repository)
    created = service.create()

    updated = service.transition(created.id, OrderStatus.EXTRACTED)

    assert updated.status is OrderStatus.EXTRACTED
    assert repository.get(created.id) == updated


def test_invalid_transition_never_mutates_persisted_order() -> None:
    repository = InMemoryOrderRepository()
    service = OrderApplicationService(repository)
    created = service.create()
    before = repository.get(created.id)

    with pytest.raises(InvalidOrderTransition):
        service.transition(created.id, OrderStatus.APPROVED)

    assert repository.get(created.id) == before
    assert repository.get(created.id).status is OrderStatus.RECEIVED
