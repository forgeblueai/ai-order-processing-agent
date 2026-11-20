"""Fail-closed evidence checks for untrusted LLM-extracted order fields.

This is deliberately a narrow, conservative guard, not a second extractor.
Missing or invented source evidence sends the order to human review; no field is guessed.
"""

import re

from app.schemas.extraction import ExtractionResult


# Recognition only, NOT an alternative SKU/quantity extractor. When a customer
# explicitly supplies a SKU-shaped token that LLM output omits, fail closed.
# Restrict to dash-number codes; other catalog formats need a later extension.
_EXPLICIT_SKU_TOKEN = re.compile(
    r"(?<![\w-])([A-Za-z][A-Za-z0-9]{0,7}-[0-9]{1,6})(?![\w-])",
    flags=re.IGNORECASE,
)


def _explicit_skus(text: str) -> set[str]:
    return {match.group(1).upper() for match in _EXPLICIT_SKU_TOKEN.finditer(text)}


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

    # Presence-only coverage: do not invent a missing item or quantity.
    # Omitting an explicit SKU must not produce READY_FOR_APPROVAL.
    extracted_references = {
        item.product_reference.upper()
        for item in corrected
        if item.product_reference is not None
    }
    if _explicit_skus(source_text) - extracted_references:
        needs_review = True

    if not needs_review:
        return result
    return result.model_copy(update={"items": corrected, "requires_clarification": True})
