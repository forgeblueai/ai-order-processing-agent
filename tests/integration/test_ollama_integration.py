import os

import pytest

from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.ai.provider import LLMOrderExtractor
from app.schemas.order import OrderProcessRequest
from app.services.order_service import process_order


pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_OLLAMA_INTEGRATION") != "1",
    reason="local Ollama integration test is opt-in",
)


def test_real_local_ollama_order_extraction() -> None:
    """Requires a running local Ollama server and the configured model."""
    extractor = LLMOrderExtractor(OllamaStructuredCompletionProvider.from_env())
    result = process_order(
        OrderProcessRequest(
            subject="Order Request - ABC Trading",
            body="Please send 50 F-200. Confirm availability and pricing.",
        ),
        extractor=extractor,
    )

    # A provider outage also routes to review, so explicitly verify real extraction occurred.
    assert all(issue.type != "extraction_provider_unavailable" for issue in result.issues)
    assert len(result.items) == 1
    assert result.items[0].sku == "F-200"
    assert result.items[0].quantity == 50
    assert result.items[0].unit_price == 120.0
    assert result.subtotal == 6000.0
