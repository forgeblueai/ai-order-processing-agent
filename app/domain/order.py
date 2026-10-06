from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas.order import OrderStatus


@dataclass(frozen=True, slots=True)
class OrderRecord:
    id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime

    @classmethod
    def create(cls) -> "OrderRecord":
        now = datetime.now(UTC)
        return cls(id=uuid4(), status=OrderStatus.RECEIVED, created_at=now, updated_at=now)

    def with_status(self, status: OrderStatus) -> "OrderRecord":
        return OrderRecord(
            id=self.id,
            status=status,
            created_at=self.created_at,
            updated_at=datetime.now(UTC),
        )
