import pytest

from app.schemas.order import OrderStatus
from app.services.order_lifecycle import InvalidOrderTransition, transition_order


def test_happy_path_reaches_completed_only_through_approval() -> None:
    state = OrderStatus.RECEIVED
    for target in (
        OrderStatus.EXTRACTED,
        OrderStatus.VALIDATING,
        OrderStatus.READY_FOR_APPROVAL,
        OrderStatus.APPROVED,
        OrderStatus.COMPLETED,
    ):
        state = transition_order(state, target)
    assert state is OrderStatus.COMPLETED


def test_review_path_must_return_to_ready_before_approval() -> None:
    state = transition_order(OrderStatus.VALIDATING, OrderStatus.REQUIRES_REVIEW)
    state = transition_order(state, OrderStatus.REVIEWED)
    state = transition_order(state, OrderStatus.READY_FOR_APPROVAL)
    assert transition_order(state, OrderStatus.APPROVED) is OrderStatus.APPROVED


def test_review_cannot_skip_human_decision_and_approve_directly() -> None:
    with pytest.raises(InvalidOrderTransition):
        transition_order(OrderStatus.REQUIRES_REVIEW, OrderStatus.APPROVED)


def test_ready_order_cannot_complete_without_approval() -> None:
    with pytest.raises(InvalidOrderTransition):
        transition_order(OrderStatus.READY_FOR_APPROVAL, OrderStatus.COMPLETED)


def test_terminal_states_cannot_transition() -> None:
    for state in (OrderStatus.REJECTED, OrderStatus.COMPLETED, OrderStatus.FAILED):
        with pytest.raises(InvalidOrderTransition):
            transition_order(state, OrderStatus.RECEIVED)
