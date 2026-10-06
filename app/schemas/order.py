from enum import StrEnum

from pydantic import BaseModel, Field


class OrderStatus(StrEnum):
    RECEIVED = "received"
    EXTRACTED = "extracted"
    VALIDATING = "validating"
    READY_FOR_APPROVAL = "ready_for_approval"
    REQUIRES_REVIEW = "requires_review"
    REVIEWED = "reviewed"
    APPROVED = "approved"
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
    status: OrderStatus
    items: list[OrderItem]
    issues: list[ValidationIssue] = []
    subtotal: float = Field(ge=0)
