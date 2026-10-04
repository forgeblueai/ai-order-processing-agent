import re
from typing import Protocol

from app.schemas.extraction import ExtractedItem, ExtractionResult
from app.schemas.order import OrderProcessRequest


class OrderExtractor(Protocol):
    def extract(self, payload: OrderProcessRequest) -> ExtractionResult: ...


class RegexOrderExtractor:
    """Deterministic fallback used until an external LLM provider is configured."""

    _item_pattern = re.compile(
        r"(?P<quantity>\d+)\s*(?:x|×)?\s*(?P<sku>F-200|PV-10|P-500)",
        re.IGNORECASE,
    )

    def extract(self, payload: OrderProcessRequest) -> ExtractionResult:
        text = f"{payload.subject}\n{payload.body}"
        items = [
            ExtractedItem(
                product_reference=match.group("sku").upper(),
                quantity=int(match.group("quantity")),
                confidence=1.0,
            )
            for match in self._item_pattern.finditer(text)
        ]
        return ExtractionResult(
            intent="order_request" if items else "unknown",
            items=items,
            requires_clarification=not items,
            confidence=1.0 if items else 0.0,
        )
