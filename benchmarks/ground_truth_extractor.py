from app.schemas.extraction import ExtractedItem, ExtractionResult


class GroundTruthExtractor:
    """Deterministic benchmark control proving scorer correctness without claiming model quality."""

    def __init__(self, corpus: list[dict]) -> None:
        self._cases = {(case["subject"], case["body"]): case for case in corpus}

    def extract(self, payload):
        case = self._cases[(payload.subject, payload.body)]
        expected = case["expected"]
        items = [
            ExtractedItem(
                product_reference=item["sku"],
                quantity=item["quantity"],
                confidence=1.0,
            )
            for item in expected["items"]
        ]
        requires_clarification = any(item["sku"] is None for item in expected["items"])
        return ExtractionResult(
            intent="order_request",
            items=items,
            requires_clarification=requires_clarification,
            confidence=1.0,
        )
