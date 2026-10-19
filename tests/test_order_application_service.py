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


@pytest.mark.parametrize(
    "issue_type",
    ["requires_clarification", "missing_quantity", "missing_product_reference",
     "insufficient_stock", "extraction_provider_unavailable", "unknown_product"],
)
def test_review_acknowledgement_does_not_resolve_validation_issue(issue_type) -> None:
    from app.schemas.order import ValidationIssue

    repo = InMemoryOrderRepository()
    service = OrderApplicationService(repo)
    order = service.create(subject="Synthetic review", body="20 PV-10")
    service.transition(order.id, OrderStatus.EXTRACTED)
    service.transition(order.id, OrderStatus.VALIDATING)
    service.record_processing_result(
        order.id,
        items=[],
        issues=[ValidationIssue(sku="PV-10", type=issue_type)],
        subtotal=0.0,
    )
    service.transition(order.id, OrderStatus.REQUIRES_REVIEW)
    reviewed = service.transition(order.id, OrderStatus.REVIEWED)

    with pytest.raises(InvalidOrderTransition, match="unresolved validation issues"):
        service.transition(order.id, OrderStatus.READY_FOR_APPROVAL)

    # Failed transition must not alter stored issues or status.
    assert repo.get(order.id) == reviewed
    assert service.get(order.id).status == OrderStatus.REVIEWED
    assert service.transition(order.id, OrderStatus.REJECTED).status == OrderStatus.REJECTED
