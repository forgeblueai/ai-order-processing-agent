from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db import Base
from app.domain.order import OrderRecord
from app.schemas.order import OrderStatus


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class SQLAlchemyOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def save(self, order: OrderRecord) -> None:
        model = self._session.get(OrderModel, str(order.id))
        if model is None:
            model = OrderModel(
                id=str(order.id), status=order.status.value,
                created_at=order.created_at, updated_at=order.updated_at,
            )
            self._session.add(model)
        else:
            model.status = order.status.value
            model.updated_at = order.updated_at
        self._session.commit()

    def get(self, order_id: UUID) -> OrderRecord | None:
        model = self._session.get(OrderModel, str(order_id))
        return self._to_domain(model) if model else None

    def list(self) -> list[OrderRecord]:
        models = self._session.scalars(select(OrderModel).order_by(OrderModel.created_at)).all()
        return [self._to_domain(model) for model in models]

    @staticmethod
    def _to_domain(model: OrderModel) -> OrderRecord:
        return OrderRecord(
            id=UUID(model.id), status=OrderStatus(model.status),
            created_at=model.created_at, updated_at=model.updated_at,
        )
