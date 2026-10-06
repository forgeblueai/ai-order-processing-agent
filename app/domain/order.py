from dataclasses import dataclass, replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.schemas.order import OrderItem, OrderStatus, ValidationIssue


@dataclass(frozen=True, slots=True)
class OrderRecord:
    id: UUID
    status: OrderStatus
    created_at: datetime
    updated_at: datetime
    subject: str = ""
    body: str = ""
    items: tuple[OrderItem, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()
    subtotal: float = 0.0

    @classmethod
    def create(cls, *, subject: str = "", body: str = "") -> "OrderRecord":
        now = datetime.now(UTC)
        return cls(id=uuid4(), status=OrderStatus.RECEIVED, created_at=now, updated_at=now, subject=subject, body=body)

    def with_status(self, status: OrderStatus) -> "OrderRecord":
        return replace(self, status=status, updated_at=datetime.now(UTC))

    def with_processing_result(
        self,
        *,
        items: list[OrderItem],
        issues: list[ValidationIssue],
        subtotal: float,
    ) -> "OrderRecord":
        return replace(
            self,
            items=tuple(items),
            issues=tuple(issues),
            subtotal=subtotal,
            updated_at=datetime.now(UTC),
        )
