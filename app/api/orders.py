from fastapi import APIRouter

from app.schemas.order import OrderProcessRequest, OrderProcessResponse
from app.services.order_service import process_order

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/process", response_model=OrderProcessResponse)
def process_order_endpoint(payload: OrderProcessRequest) -> OrderProcessResponse:
    return process_order(payload)
