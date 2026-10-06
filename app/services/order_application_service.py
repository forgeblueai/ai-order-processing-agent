from uuid import UUID

from app.domain.order import OrderRecord
from app.ports.order_repository import OrderRepository
from app.schemas.order import OrderStatus
from app.services.order_lifecycle import transition_order


class OrderNotFoundError(LookupError):
    """Raised when an application operation targets an unknown order."""


class OrderApplicationService:
    def __init__(self, repository: OrderRepository) -> None:
        self._repository = repository

    def create(self) -> OrderRecord:
        order = OrderRecord.create()
        self._repository.save(order)
        return order

    def get(self, order_id: UUID) -> OrderRecord:
        order = self._repository.get(order_id)
        if order is None:
            raise OrderNotFoundError(f"order not found: {order_id}")
        return order

    def transition(self, order_id: UUID, target: OrderStatus) -> OrderRecord:
        current = self.get(order_id)
        validated_target = transition_order(current.status, target)
        updated = current.with_status(validated_target)
        self._repository.save(updated)
        return updated
