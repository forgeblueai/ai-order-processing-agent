import json
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, String, Text, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db import Base
from app.domain.order import OrderRecord
from app.schemas.order import OrderItem, OrderStatus, ValidationIssue


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    subject: Mapped[str] = mapped_column(String(500), nullable=False, default="")
    body: Mapped[str] = mapped_column(Text, nullable=False, default="")
    items_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    issues_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    subtotal: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    response_draft: Mapped[str | None] = mapped_column(Text, nullable=True)
    response_sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SQLAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, order: OrderRecord) -> None:
        model = self._session.get(OrderModel, str(order.id))
        values = {
            "status": order.status.value,
            "subject": order.subject,
            "body": order.body,
            "items_json": json.dumps([item.model_dump(mode="json") for item in order.items]),
            "issues_json": json.dumps([issue.model_dump(mode="json") for issue in order.issues]),
            "subtotal": order.subtotal,
            "response_draft": order.response_draft,
            "response_sent_at": order.response_sent_at,
            "updated_at": order.updated_at,
        }
        if model is None:
            model = OrderModel(id=str(order.id), created_at=order.created_at, **values)
            self._session.add(model)
        else:
            for key, value in values.items():
                setattr(model, key, value)
        self._session.commit()

    def get(self, order_id: UUID) -> OrderRecord | None:
        model = self._session.get(OrderModel, str(order_id))
        return self._to_domain(model) if model else None

    def list(self) -> list[OrderRecord]:
        models = self._session.scalars(select(OrderModel).order_by(OrderModel.created_at)).all()
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _as_utc(value: datetime) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    @classmethod
    def _to_domain(cls, model: OrderModel) -> OrderRecord:
        return OrderRecord(
            id=UUID(model.id),
            status=OrderStatus(model.status),
            subject=model.subject,
            body=model.body,
            items=tuple(OrderItem.model_validate(item) for item in json.loads(model.items_json)),
            issues=tuple(ValidationIssue.model_validate(issue) for issue in json.loads(model.issues_json)),
            subtotal=model.subtotal,
            response_draft=model.response_draft,
            response_sent_at=cls._as_utc(model.response_sent_at) if model.response_sent_at else None,
            created_at=cls._as_utc(model.created_at),
            updated_at=cls._as_utc(model.updated_at),
        )
