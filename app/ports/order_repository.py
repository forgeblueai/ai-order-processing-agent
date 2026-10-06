from typing import Protocol
from uuid import UUID

from app.domain.order import OrderRecord


class OrderRepository(Protocol):
    def save(self, order: OrderRecord) -> None: ...

    def get(self, order_id: UUID) -> OrderRecord | None: ...

    def list(self) -> list[OrderRecord]: ...
