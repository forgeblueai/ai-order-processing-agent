from uuid import uuid4

from sqlalchemy import inspect

from app.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from app.db import SessionLocal, engine
from app.domain.order import OrderRecord
from app.schemas.order import OrderItem, OrderStatus, ValidationIssue
from app.services.order_application_service import OrderApplicationService
from app.services.order_lifecycle import InvalidOrderTransition


def test_migrated_postgres_repository_and_lifecycle() -> None:
    columns = {column["name"] for column in inspect(engine).get_columns("orders")}
    assert {"id", "status", "subject", "body", "items_json", "issues_json", "subtotal", "created_at", "updated_at"} <= columns

    session = SessionLocal()
    try:
        repository = SQLAlchemyOrderRepository(session)
        service = OrderApplicationService(repository)
        order = service.create(subject="Postgres integration", body="50 F-200")
        service.transition(order.id, OrderStatus.EXTRACTED)
        service.transition(order.id, OrderStatus.VALIDATING)
        service.record_processing_result(
            order.id,
            items=[OrderItem(sku="F-200", quantity=50, unit_price=120.0, available_stock=80)],
            issues=[],
            subtotal=6000.0,
        )
        ready = service.transition(order.id, OrderStatus.READY_FOR_APPROVAL)
        stored = service.get(order.id)
        assert ready.status is OrderStatus.READY_FOR_APPROVAL
        assert stored.subject == "Postgres integration"
        assert stored.items[0].unit_price == 120.0
        assert stored.subtotal == 6000.0

        try:
            service.transition(order.id, OrderStatus.COMPLETED)
        except InvalidOrderTransition:
            pass
        else:
            raise AssertionError("invalid lifecycle transition unexpectedly succeeded")
        assert service.get(order.id).status is OrderStatus.READY_FOR_APPROVAL
    finally:
        session.close()
