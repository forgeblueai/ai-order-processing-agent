from uuid import UUID

from app.domain.order import OrderRecord


class InMemoryOrderRepository:
    """Zero-cost persistence adapter for tests and local development."""

    def __init__(self) -> None:
        self._orders: dict[UUID, OrderRecord] = {}

    def save(self, order: OrderRecord) -> None:
        self._orders[order.id] = order

    def get(self, order_id: UUID) -> OrderRecord | None:
        return self._orders.get(order_id)
