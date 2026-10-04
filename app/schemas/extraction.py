from typing import Literal

from pydantic import BaseModel, Field


class ExtractedItem(BaseModel):
    product_reference: str | None = None
    description: str | None = None
    quantity: int | None = Field(default=None, gt=0)
    confidence: float = Field(ge=0.0, le=1.0)


class ExtractionResult(BaseModel):
    intent: Literal["order_request", "unknown"]
    customer_name: str | None = None
    contact_name: str | None = None
    items: list[ExtractedItem] = Field(default_factory=list)
    requested_delivery_date: str | None = None
    notes: str | None = None
    requires_clarification: bool = False
    confidence: float = Field(ge=0.0, le=1.0)
