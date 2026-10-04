import json

import httpx
import pytest

from app.ai.groq_provider import GroqStructuredCompletionProvider


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_groq_provider_uses_strict_schema_without_tools() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["Authorization"] == "Bearer test-key"
        body = json.loads(request.content)
        assert body["model"] == "openai/gpt-oss-20b"
        assert body["response_format"]["json_schema"]["strict"] is True
        assert body["response_format"]["json_schema"]["schema"]["additionalProperties"] is False
        assert "tools" not in body
        assert body["messages"][1]["role"] == "user"
        result = {
            "intent": "order_request", "customer_name": None, "contact_name": None,
            "items": [{"product_reference": "F-200", "description": None, "quantity": 50, "confidence": 0.98}],
            "requested_delivery_date": None, "notes": None,
            "requires_clarification": False, "confidence": 0.98,
        }
        return httpx.Response(200, json={"choices": [{"message": {"content": json.dumps(result)}}]})

    provider = GroqStructuredCompletionProvider(api_key="test-key", client=_client(handler))
    result = provider.complete(system_prompt="system", user_text="50 F-200")
    assert result["items"][0]["quantity"] == 50


def test_groq_provider_fails_closed_on_http_error() -> None:
    provider = GroqStructuredCompletionProvider(
        api_key="test-key",
        client=_client(lambda request: httpx.Response(429, json={"error": "rate limited"})),
    )
    with pytest.raises(httpx.HTTPStatusError):
        provider.complete(system_prompt="system", user_text="50 F-200")


def test_groq_provider_requires_api_key() -> None:
    with pytest.raises(ValueError, match="GROQ_API_KEY"):
        GroqStructuredCompletionProvider(api_key="")
