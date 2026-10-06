from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from app.db import Base
from app.domain.order import OrderRecord
from app.schemas.order import OrderStatus


def make_repository() -> tuple[SQLAlchemyOrderRepository, Session]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    return SQLAlchemyOrderRepository(session), session


def test_sqlalchemy_repository_round_trip_and_list() -> None:
    repository, session = make_repository()
    try:
        first = OrderRecord.create()
        second = OrderRecord.create()
        repository.save(first)
        repository.save(second)

        assert repository.get(first.id) == first
        assert {order.id for order in repository.list()} == {first.id, second.id}
    finally:
        session.close()


def test_sqlalchemy_repository_updates_existing_order_without_duplicate() -> None:
    repository, session = make_repository()
    try:
        order = OrderRecord.create()
        repository.save(order)
        updated = order.with_status(OrderStatus.EXTRACTED)
        repository.save(updated)

        stored = repository.get(order.id)
        assert stored is not None
        assert stored.id == order.id
        assert stored.status is OrderStatus.EXTRACTED
        assert len(repository.list()) == 1
    finally:
        session.close()
