from typing import Annotated

from fastapi import APIRouter, Depends

from app.ai.extractor import OrderExtractor
from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.ai.provider import LLMOrderExtractor
from app.schemas.order import OrderProcessRequest, OrderProcessResponse
from app.services.order_service import process_order

router = APIRouter(prefix="/orders", tags=["orders"])


def get_order_extractor() -> OrderExtractor:
    """Production dependency: zero-cost local LLM behind the extraction contract."""
    return LLMOrderExtractor(OllamaStructuredCompletionProvider.from_env())


@router.post("/process", response_model=OrderProcessResponse)
def process_order_endpoint(
    payload: OrderProcessRequest,
    extractor: Annotated[OrderExtractor, Depends(get_order_extractor)],
) -> OrderProcessResponse:
    return process_order(payload, extractor=extractor)
