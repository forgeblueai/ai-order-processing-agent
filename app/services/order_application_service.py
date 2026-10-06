from __future__ import annotations

from uuid import UUID

from app.domain.order import OrderRecord
from app.ports.customer_response_drafter import CustomerResponseDrafter
from app.ports.order_repository import OrderRepository
from app.schemas.order import OrderItem, OrderStatus, ValidationIssue
from app.services.order_lifecycle import transition_order


class OrderNotFoundError(LookupError):
    """Raised when an application operation targets an unknown order."""


class OrderApplicationService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def create(self, *, subject: str = "", body: str = "") -> OrderRecord:
        order = OrderRecord.create(subject=subject, body=body)
        self._repository.save(order)
        return order

    def get(self, order_id: UUID) -> OrderRecord:
        order = self._repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"order not found: {order_id}")
        return order

    def list(self) -> list[OrderRecord]:
        return self._repository.list()

    def record_processing_result(
        self,
        order_id: UUID,
        *,
        items: list[OrderItem],
        issues: list[ValidationIssue],
        subtotal: float,
    ) -> OrderRecord:
        current = self.get(order_id)
        updated = current.with_processing_result(items=items, issues=issues, subtotal=subtotal)
        self._repository.save(updated)
        return updated

    def draft_customer_response(self, order_id: UUID, drafter: CustomerResponseDrafter) -> OrderRecord:
        current = self.get(order_id)
        validated_target = transition_order(current.status, OrderStatus.RESPONSE_DRAFTED)
        draft = drafter.draft(current).strip()
        if not draft:
            raise ValueError("customer response draft cannot be empty")
        updated = current.with_response_draft(draft).with_status(validated_target)
        self._repository.save(updated)
        return updated

    def mark_response_sent(self, order_id: UUID) -> OrderRecord:
        current = self.get(order_id)
        validated_target = transition_order(current.status, OrderStatus.RESPONSE_SENT)
        updated = current.with_response_sent().with_status(validated_target)
        self._repository.save(updated)
        return updated

    def transition(self, order_id: UUID, target: OrderStatus) -> OrderRecord:
        current = self.get(order_id)
        validated_target = transition_order(current.status, target)
        updated = current.with_status(validated_target)
        self._repository.save(updated)
        return updated
