from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.ai.provider import LLMOrderExtractor
from app.schemas.order import OrderProcessRequest
from app.services.order_service import process_order


def test_real_qwen_extracts_order_through_application_boundary() -> None:
    extractor = LLMOrderExtractor(OllamaStructuredCompletionProvider.from_env())
    result = process_order(
        OrderProcessRequest(
            subject="Order Request - ABC Trading",
            body="Please send 50 F-200. Confirm availability and pricing.",
        ),
        extractor=extractor,
    )

    assert all(issue.type != "extraction_provider_unavailable" for issue in result.issues)
    assert len(result.items) == 1
    assert result.items[0].sku == "F-200"
    assert result.items[0].quantity == 50
    # Price must come from the trusted inventory service, never the model.
    assert result.items[0].unit_price == 120.0
    assert result.subtotal == 6000.0
