from typing import Protocol

from app.domain.order import OrderRecord


class CustomerResponseDrafter(Protocol):
    """Drafts customer-facing text only; it has no send or lifecycle capability."""

    def draft(self, order: OrderRecord) -> str: ...


class DeterministicCustomerResponseDrafter:
    """Zero-cost safe fallback used when no generative provider is configured."""

    def draft(self, order: OrderRecord) -> str:
        lines = [f"- {item.quantity} × {item.sku} at ${item.unit_price:.2f} each" for item in order.items]
        item_summary = "\n".join(lines) or "- No validated line items"
        return (
            "Thank you for your order request.\n\n"
            "Validated order summary:\n"
            f"{item_summary}\n\n"
            f"Order subtotal: ${order.subtotal:.2f}.\n"
            "This draft requires human confirmation before it is sent."
        )
