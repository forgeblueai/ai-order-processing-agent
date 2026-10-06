from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from app.db import Base
from app.domain.order import OrderRecord
from app.schemas.order import OrderItem, OrderStatus, ValidationIssue


def make_repository() -> tuple[SQLAlchemyOrderRepository, Session]:
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = Session(engine, expire_on_commit=False)
    return SQLAlchemyOrderRepository(session), session


def test_sqlalchemy_repository_round_trip_preserves_complete_order() -> None:
    repository, session = make_repository()
    try:
        order = OrderRecord.create(subject="Order Request", body="We need 50 F-200.")
        processed = order.with_processing_result(
            items=[OrderItem(sku="F-200", quantity=50, unit_price=120.0, available_stock=80)],
            issues=[],
            subtotal=6000.0,
        )
        repository.save(processed)

        stored = repository.get(order.id)
        assert stored == processed
        assert stored.created_at.tzinfo is not None
        assert stored.updated_at.tzinfo is not None
        assert stored.subject == "Order Request"
        assert stored.items[0].unit_price == 120.0
        assert stored.subtotal == 6000.0
    finally:
        session.close()


def test_sqlalchemy_repository_preserves_validation_issues() -> None:
    repository, session = make_repository()
    try:
        order = OrderRecord.create(subject="Order", body="20 PV-10")
        processed = order.with_processing_result(
            items=[OrderItem(sku="PV-10", quantity=20, unit_price=75.0, available_stock=15)],
            issues=[ValidationIssue(sku="PV-10", type="insufficient_stock", requested=20, available=15)],
            subtotal=1500.0,
        )
        repository.save(processed)
        stored = repository.get(order.id)
        assert stored is not None
        assert stored.issues[0].type == "insufficient_stock"
    finally:
        session.close()
