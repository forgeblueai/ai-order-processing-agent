from app.ai.extractor import OrderExtractor, RegexOrderExtractor
from app.schemas.order import (
    OrderItem,
    OrderProcessRequest,
    OrderProcessResponse,
    OrderStatus,
    ValidationIssue,
)
from app.services.inventory_service import get_product

LOW_CONFIDENCE_THRESHOLD = 0.80
DEFAULT_EXTRACTOR: OrderExtractor = RegexOrderExtractor()


def process_order(payload: OrderProcessRequest, extractor: OrderExtractor = DEFAULT_EXTRACTOR) -> OrderProcessResponse:
    try:
        extraction = extractor.extract(payload)
    except Exception:
        # External/local model failures must never bypass review or expose provider details.
        return OrderProcessResponse(
            status=OrderStatus.REQUIRES_REVIEW,
            items=[],
            issues=[ValidationIssue(sku="unknown", type="extraction_provider_unavailable")],
            subtotal=0,
        )

    items: list[OrderItem] = []
    issues: list[ValidationIssue] = []

    if extraction.requires_clarification or not extraction.items:
        issues.append(ValidationIssue(sku="unknown", type="requires_clarification"))
    if extraction.confidence < LOW_CONFIDENCE_THRESHOLD:
        issues.append(ValidationIssue(sku="unknown", type="low_extraction_confidence"))

    for extracted_item in extraction.items:
        sku = extracted_item.product_reference
        quantity = extracted_item.quantity
        if extracted_item.confidence < LOW_CONFIDENCE_THRESHOLD:
            issues.append(ValidationIssue(sku=sku or "unknown", type="low_item_confidence", requested=quantity))
        if not sku:
            issues.append(ValidationIssue(sku="unknown", type="missing_product_reference", requested=quantity))
            continue
        if quantity is None:
            issues.append(ValidationIssue(sku=sku, type="missing_quantity"))
            continue
        product = get_product(sku)
        if product is None:
            issues.append(ValidationIssue(sku=sku, type="unknown_product", requested=quantity))
            continue
        items.append(OrderItem(sku=product.sku, quantity=quantity, unit_price=product.unit_price, available_stock=product.stock))
        if quantity > product.stock:
            issues.append(ValidationIssue(sku=sku, type="insufficient_stock", requested=quantity, available=product.stock))

    subtotal = sum(item.quantity * item.unit_price for item in items)
    status = OrderStatus.REQUIRES_REVIEW if issues else OrderStatus.READY_FOR_APPROVAL
    return OrderProcessResponse(status=status, items=items, issues=issues, subtotal=subtotal)
