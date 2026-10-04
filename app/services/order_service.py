import re

from app.schemas.order import (
    OrderItem,
    OrderProcessRequest,
    OrderProcessResponse,
    OrderStatus,
    ValidationIssue,
)
from app.services.inventory_service import get_product

# Sprint 1 placeholder. Sprint 2 replaces this extraction boundary with an LLM
# that returns a strict structured schema. Business rules remain deterministic.
ITEM_PATTERN = re.compile(r"(?P<quantity>\\d+)\\s*(?:x|×)?\\s*(?P<sku>F-200|PV-10|P-500)", re.IGNORECASE)


def _extract_items(text: str) -> list[tuple[str, int]]:
    return [
        (match.group("sku").upper(), int(match.group("quantity")))
        for match in ITEM_PATTERN.finditer(text)
    ]


def process_order(payload: OrderProcessRequest) -> OrderProcessResponse:
    extracted = _extract_items(f"{payload.subject}\n{payload.body}")
    items: list[OrderItem] = []
    issues: list[ValidationIssue] = []

    if not extracted:
        issues.append(ValidationIssue(sku="unknown", type="no_supported_items_detected"))

    for sku, quantity in extracted:
        product = get_product(sku)
        if product is None:
            issues.append(ValidationIssue(sku=sku, type="unknown_product", requested=quantity))
            continue

        items.append(
            OrderItem(
                sku=product.sku,
                quantity=quantity,
                unit_price=product.unit_price,
                available_stock=product.stock,
            )
        )
        if quantity > product.stock:
            issues.append(
                ValidationIssue(
                    sku=sku,
                    type="insufficient_stock",
                    requested=quantity,
                    available=product.stock,
                )
            )

    subtotal = sum(item.quantity * item.unit_price for item in items)
    status = OrderStatus.REQUIRES_REVIEW if issues else OrderStatus.READY_FOR_APPROVAL
    return OrderProcessResponse(status=status, items=items, issues=issues, subtotal=subtotal)
