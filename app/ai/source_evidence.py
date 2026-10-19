"""Fail-closed evidence checks for untrusted LLM-extracted order fields.

This is deliberately a narrow, conservative guard, not a second extractor.
Missing source evidence sends the order to human review; no field is guessed.
"""

import re

from app.schemas.extraction import ExtractionResult


def _mentioned_reference(text: str, reference: str) -> list[re.Match[str]]:
    pattern = rf"(?<![\w-]){re.escape(reference)}(?![\w-])"
    return list(re.finditer(pattern, text, flags=re.IGNORECASE))


def _quantity_near_reference(text: str, reference: str, quantity: int) -> bool:
    # Prices cannot be order quantities, even when immediately beside an SKU.
    without_prices = re.sub(r"\$\s*\d+(?:\.\d+)?", " ", text)
    value_pattern = re.compile(rf"(?<![\w.]){quantity}(?![\w.])")
    for match in _mentioned_reference(without_prices, reference):
        before = without_prices[max(0, match.start() - 32):match.start()]
        after = without_prices[match.end():match.end() + 32]
        if value_pattern.search(before) or value_pattern.search(after):
            return True
    return False


def require_source_evidence(result: ExtractionResult, *, source_text: str) -> ExtractionResult:
    """Null unsupported identifier/quantity fields; force review on any correction.

    Lexical checking deliberately errs toward review for spelled-out quantities,
    long-distance references, and unusual order layouts. The original result
    schema and business confidence thresholds remain unchanged.
    """
    corrected = []
    needs_review = False
    for item in result.items:
        reference = item.product_reference
        quantity = item.quantity
        if reference is not None and not _mentioned_reference(source_text, reference):
            reference = None
            needs_review = True
        if reference is not None and quantity is not None and not _quantity_near_reference(
            source_text, reference, quantity
        ):
            quantity = None
            needs_review = True
        corrected.append(item.model_copy(update={"product_reference": reference, "quantity": quantity}))

    if not needs_review:
        return result
    return result.model_copy(update={"items": corrected, "requires_clarification": True})
