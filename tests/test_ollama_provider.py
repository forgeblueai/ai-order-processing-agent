import json

import httpx
import pytest

from app.ai.ollama_provider import OllamaStructuredCompletionProvider
from app.schemas.extraction import ExtractionResult


def _client(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_ollama_provider_is_local_keyless_tool_free_and_schema_constrained() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "http://127.0.0.1:11434/api/chat"
        assert "authorization" not in request.headers
        body = json.loads(request.content)
        assert body["model"] == "qwen3:8b"
        assert body["stream"] is False
        assert body["think"] is False
        assert body["options"] == {"temperature": 0, "seed": 42}
        assert body["format"] == ExtractionResult.model_json_schema()
        assert body["format"]["title"] == "ExtractionResult"
        assert set(body["format"]["required"]) == {"intent", "confidence"}
        assert "tools" not in body
        assert body["messages"][0]["role"] == "system"
        assert body["messages"][1]["role"] == "user"
        result = {
            "intent": "order_request", "customer_name": None, "contact_name": None,
            "items": [{"product_reference": "F-200", "description": None, "quantity": 50, "confidence": 0.95}],
            "requested_delivery_date": None, "notes": None,
            "requires_clarification": False, "confidence": 0.95,
        }
        return httpx.Response(200, json={"message": {"content": json.dumps(result)}})

    provider = OllamaStructuredCompletionProvider(client=_client(handler))
    result = provider.complete(system_prompt="system", user_text="50 F-200")
    assert result["items"][0]["quantity"] == 50


def test_ollama_provider_fails_closed_when_local_runtime_is_unavailable() -> None:
    provider = OllamaStructuredCompletionProvider(
        client=_client(lambda request: httpx.Response(503, json={"error": "unavailable"}))
    )
    with pytest.raises(httpx.HTTPStatusError):
        provider.complete(system_prompt="system", user_text="50 F-200")


def test_ollama_provider_supports_explicit_thinking_evaluation_profile() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        data = json.loads(request.content)
        assert data["think"] is True
        assert data["options"] == {"temperature": 0, "seed": 42}
        assert "tools" not in data
        return httpx.Response(200, json={"message": {"content": json.dumps({
            "intent": "order_request", "confidence": 0.90, "items": []
        })}})

    provider = OllamaStructuredCompletionProvider(
        model="qwen3:1.7b", think=True, client=_client(handler)
    )
    assert provider.complete(system_prompt="system", user_text="message")["intent"] == "order_request"


def test_ollama_thinking_env_is_opt_in_and_rejects_unknown_values(monkeypatch) -> None:
    monkeypatch.delenv("OLLAMA_THINK", raising=False)
    assert OllamaStructuredCompletionProvider.from_env()._think is False

    monkeypatch.setenv("OLLAMA_THINK", "TRUE")
    assert OllamaStructuredCompletionProvider.from_env()._think is True

    monkeypatch.setenv("OLLAMA_THINK", "yes")
    with pytest.raises(ValueError, match="OLLAMA_THINK"):
        OllamaStructuredCompletionProvider.from_env()
