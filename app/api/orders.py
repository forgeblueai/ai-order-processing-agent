from collections.abc import Generator
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai.extractor import OrderExtractor
from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.ai.provider import LLMOrderExtractor
from app.adapters.sqlalchemy_order_repository import SQLAlchemyOrderRepository
from app.db import SessionLocal
from app.ports.customer_response_drafter import DeterministicCustomerResponseDrafter
from app.schemas.order import OrderProcessRequest, OrderProcessResponse, OrderRecordResponse, OrderStatus
from app.services.order_application_service import OrderApplicationService, OrderNotFoundError
from app.services.order_lifecycle import InvalidOrderTransition
from app.services.order_service import process_order

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_extractor() -> OrderExtractor:
    return LLMOrderExtractor(OllamaStructuredCompletionProvider.from_env())


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def get_order_application_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> OrderApplicationService:
    return OrderApplicationService(SQLAlchemyOrderRepository(session))


@router.post("/process", response_model=OrderProcessResponse)
def process_order_endpoint(
    payload: OrderProcessRequest,
    extractor: Annotated[OrderExtractor, Depends(get_order_extractor)],
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderProcessResponse:
    record = orders.create(subject=payload.subject, body=payload.body)
    result = process_order(payload, extractor=extractor)
    orders.transition(record.id, OrderStatus.EXTRACTED)
    orders.transition(record.id, OrderStatus.VALIDATING)
    orders.record_processing_result(
        record.id,
        items=result.items,
        issues=result.issues,
        subtotal=result.subtotal,
    )
    orders.transition(record.id, result.status)
    return result.model_copy(update={"order_id": record.id})


@router.get("", response_model=list[OrderRecordResponse])
def list_orders(
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> list[OrderRecordResponse]:
    return [OrderRecordResponse.model_validate(order, from_attributes=True) for order in orders.list()]


@router.get("/{order_id}", response_model=OrderRecordResponse)
def get_order(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    try:
        return OrderRecordResponse.model_validate(orders.get(order_id), from_attributes=True)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="order not found") from exc


def _transition_http(order_id: UUID, target: OrderStatus, orders: OrderApplicationService) -> OrderRecordResponse:
    try:
        record = orders.transition(order_id, target)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="order not found") from exc
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail="invalid order transition") from exc
    return OrderRecordResponse.model_validate(record, from_attributes=True)


@router.post("/{order_id}/approve", response_model=OrderRecordResponse)
def approve_order(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    return _transition_http(order_id, OrderStatus.APPROVED, orders)


@router.post("/{order_id}/reject", response_model=OrderRecordResponse)
def reject_order(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    return _transition_http(order_id, OrderStatus.REJECTED, orders)


@router.post("/{order_id}/review", response_model=OrderRecordResponse)
def review_order(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    return _transition_http(order_id, OrderStatus.REVIEWED, orders)


@router.post("/{order_id}/ready", response_model=OrderRecordResponse)
def mark_order_ready(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    return _transition_http(order_id, OrderStatus.READY_FOR_APPROVAL, orders)


@router.post("/{order_id}/response/draft", response_model=OrderRecordResponse)
def draft_customer_response(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    try:
        record = orders.draft_customer_response(order_id, DeterministicCustomerResponseDrafter())
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="order not found") from exc
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail="invalid order transition") from exc
    return OrderRecordResponse.model_validate(record, from_attributes=True)


@router.post("/{order_id}/response/send", response_model=OrderRecordResponse)
def confirm_customer_response_sent(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    try:
        record = orders.mark_response_sent(order_id)
    except OrderNotFoundError as exc:
        raise HTTPException(status_code=404, detail="order not found") from exc
    except InvalidOrderTransition as exc:
        raise HTTPException(status_code=409, detail="invalid order transition") from exc
    return OrderRecordResponse.model_validate(record, from_attributes=True)


@router.post("/{order_id}/complete", response_model=OrderRecordResponse)
def complete_order(
    order_id: UUID,
    orders: Annotated[OrderApplicationService, Depends(get_order_application_service)],
) -> OrderRecordResponse:
    return _transition_http(order_id, OrderStatus.COMPLETED, orders)
