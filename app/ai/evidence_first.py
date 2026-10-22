"""Strict, evidence-first parsing for simple *fully specified* SKU orders.

This deliberately narrow parser abstains rather than guessing. The entire
customer body must match a simple explicit ordering grammar: no arbitrary
sentences, hidden instructions, dates, prices, partial matches or SKU aliases.

It is not an LLM replacement for free-form orders. Model-only benchmark v1
continues to exercise LLMOrderExtractor unchanged.
"""
from __future__ import annotations

import re

from app.ai.extractor import OrderExtractor
from app.ai.source_evidence import require_source_evidence
from app.schemas.extraction import ExtractedItem, ExtractionResult
from app.schemas.order import OrderProcessRequest

_SKU_SHAPE = r"[A-Za-z][A-Za-z0-9]{0,7}-[0-9]{1,6}"
_HEADER = re.compile(
    r"\s*(?:(?:please\s+)?(?:send|ship|supply)(?:\s+(?:us|me))?\s+"
    r"|(?:we|i)\s+(?:need|want)\s+)",
    re.IGNORECASE,
)
_ITEM = re.compile(
    rf"(?P<quantity>[1-9][0-9]{{0,5}})\s+(?P<sku>{_SKU_SHAPE})",
    re.IGNORECASE,
)
_JOIN = re.compile(r"\s*(?:,\s*(?:and\s+)?|and\s+)\s*", re.IGNORECASE)
_ANY_SKU = re.compile(rf"(?<![\w-]){_SKU_SHAPE}(?![\w-])", re.IGNORECASE)


def extract_explicit_sku_order(payload: OrderProcessRequest) -> ExtractionResult | None:
    """Return evidence-grounded extraction or None (abstain).

    The parsed content has to consume the *entire* order body. This prevents
    overreading unrelated numbers or ignoring non-order clauses, instructions,
    ambiguous qualifiers, and malicious appended text. No duplicate SKU lines
    or invented fallback quantities are permitted.
    """
    if _ANY_SKU.search(payload.subject):
        # A second SKU in the subject must not be silently omitted.
        return None
    body = payload.body.strip()
    if not body or "\n" in body or "\r" in body:
        return None
    head = _HEADER.match(body)
    if head is None:
        return None
    remainder = body[head.end():].strip()
    if remainder.endswith("."):
        remainder = remainder[:-1].rstrip()
    if not remainder:
        return None

    items: list[ExtractedItem] = []
    seen: set[str] = set()
    offset = 0
    while offset < len(remainder):
        match = _ITEM.match(remainder, offset)
        if match is None:
            return None
        sku = match.group("sku").upper()
        if sku in seen:
            # Multiple lines with same product may have conflicting semantics.
            return None
        seen.add(sku)
        items.append(ExtractedItem(
            product_reference=sku,
            quantity=int(match.group("quantity")),
            confidence=1.0,
        ))
        offset = match.end()
        if offset == len(remainder):
            break
        separator = _JOIN.match(remainder, offset)
        if separator is None or separator.end() <= offset:
            return None
        offset = separator.end()

    if not items or offset != len(remainder):
        return None
    result = ExtractionResult(
        intent="order_request",
        items=items,
        requires_clarification=False,
        confidence=1.0,
    )
    # Additional defense-in-depth, using the existing source evidence boundary.
    checked = require_source_evidence(
        result, source_text=f"{payload.subject}\n{payload.body}"
    )
    if checked.requires_clarification:
        return None
    return checked


class EvidenceFirstOrderExtractor:
    """Fast, bounded deterministic path; model fallback for unsupported text."""

    def __init__(self, fallback: OrderExtractor) -> None:
        self._fallback = fallback

    def extract(self, payload: OrderProcessRequest) -> ExtractionResult:
        explicit = extract_explicit_sku_order(payload)
        if explicit is not None:
            return explicit
        return self._fallback.extract(payload)
