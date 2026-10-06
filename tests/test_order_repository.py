from app.adapters.in_memory_order_repository import InMemoryOrderRepository
from app.domain.order import OrderRecord
from app.schemas.order import OrderStatus
from app.services.order_lifecycle import transition_order


def test_new_order_has_stable_identity_and_received_state() -> None:
    order = OrderRecord.create()
    assert order.id is not None
    assert order.status is OrderStatus.RECEIVED
    assert order.created_at.tzinfo is not None
    assert order.updated_at == order.created_at


def test_repository_round_trip_preserves_order() -> None:
    repository = InMemoryOrderRepository()
    order = OrderRecord.create()
    repository.save(order)
    assert repository.get(order.id) == order


def test_missing_order_returns_none() -> None:
    repository = InMemoryOrderRepository()
    missing_id = OrderRecord.create().id
    assert repository.get(missing_id) is None


def test_persisted_transition_keeps_identity_and_creation_time() -> None:
    repository = InMemoryOrderRepository()
    order = OrderRecord.create()
    repository.save(order)

    target = transition_order(order.status, OrderStatus.EXTRACTED)
    updated = order.with_status(target)
    repository.save(updated)

    stored = repository.get(order.id)
    assert stored is not None
    assert stored.id == order.id
    assert stored.created_at == order.created_at
    assert stored.status is OrderStatus.EXTRACTED
    assert stored.updated_at >= order.updated_at
