from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    VALIDATING = "validating"
    READY_FOR_APPROVAL = "ready_for_approval"
    REQUIRES_REVIEW = "requires_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
    RESPONSE_DRAFTED = "response_drafted"
    RESPONSE_SENT = "response_sent"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


class OrderProcessRequest(BaseModel):
    subject: str = Field(min_length=1, max_length=500)
    body: str = Field(min_length=1, max_length=20_000)


class OrderItem(BaseModel):
    sku: str
    quantity: int = Field(gt=0)
    unit_price: float = Field(ge=0)
    available_stock: int = Field(ge=0)


class ValidationIssue(BaseModel):
    sku: str
    type: str
    requested: int | None = None
    available: int | None = None


class OrderProcessResponse(BaseModel):
    order_id: UUID | None = None
    status: OrderStatus
    items: list[OrderItem]
    issues: list[ValidationIssue] = Field(default_factory=list)
    subtotal: float = Field(ge=0)


class OrderRecordResponse(BaseModel):
    id: UUID
    status: OrderStatus
    subject: str
    body: str
    items: list[OrderItem]
    issues: list[ValidationIssue]
    subtotal: float = Field(ge=0)
    response_draft: str | None = None
    response_sent_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
