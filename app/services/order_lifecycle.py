from collections.abc import Mapping

from app.schemas.order import OrderStatus


class InvalidOrderTransition(ValueError):
    """Raised when a requested lifecycle transition violates the order state machine."""


_ALLOWED_TRANSITIONS: Mapping[OrderStatus, frozenset[OrderStatus]] = {
    OrderStatus.RECEIVED: frozenset({OrderStatus.EXTRACTED, OrderStatus.REQUIRES_REVIEW, OrderStatus.FAILED}),
    OrderStatus.EXTRACTED: frozenset({OrderStatus.VALIDATING, OrderStatus.REQUIRES_REVIEW, OrderStatus.FAILED}),
    OrderStatus.VALIDATING: frozenset({OrderStatus.READY_FOR_APPROVAL, OrderStatus.REQUIRES_REVIEW, OrderStatus.FAILED}),
    OrderStatus.READY_FOR_APPROVAL: frozenset({OrderStatus.APPROVED, OrderStatus.REJECTED}),
    OrderStatus.REQUIRES_REVIEW: frozenset({OrderStatus.REVIEWED, OrderStatus.REJECTED}),
    OrderStatus.REVIEWED: frozenset({OrderStatus.READY_FOR_APPROVAL, OrderStatus.REJECTED}),
    OrderStatus.APPROVED: frozenset({OrderStatus.COMPLETED}),
    OrderStatus.REJECTED: frozenset(),
    OrderStatus.COMPLETED: frozenset(),
    OrderStatus.FAILED: frozenset(),
}


def transition_order(current: OrderStatus, target: OrderStatus) -> OrderStatus:
    """Return the target state only when the deterministic lifecycle permits it."""
    if target not in _ALLOWED_TRANSITIONS[current]:
        raise InvalidOrderTransition(f"invalid order transition: {current.value} -> {target.value}")
    return target
