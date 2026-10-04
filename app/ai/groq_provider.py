import json
import os
from typing import Any

import httpx


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "openai/gpt-oss-20b"

# Groq strict mode requires every property to be required. Optional application
# fields are therefore represented as nullable rather than omitted.
ORDER_EXTRACTION_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": ["order_request", "unknown"]},
        "customer_name": {"type": ["string", "null"]},
        "contact_name": {"type": ["string", "null"]},
        "items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_reference": {"type": ["string", "null"]},
                    "description": {"type": ["string", "null"]},
                    "quantity": {"type": ["integer", "null"], "minimum": 1},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                },
                "required": ["product_reference", "description", "quantity", "confidence"],
                "additionalProperties": False,
            },
        },
        "requested_delivery_date": {"type": ["string", "null"]},
        "notes": {"type": ["string", "null"]},
        "requires_clarification": {"type": "boolean"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    },
    "required": [
        "intent", "customer_name", "contact_name", "items",
        "requested_delivery_date", "notes", "requires_clarification", "confidence",
    ],
    "additionalProperties": False,
}


class GroqStructuredCompletionProvider:
    """Groq adapter limited to structured extraction; it exposes no tools."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_GROQ_MODEL,
        client: httpx.Client | None = None,
    ) -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is required")
        self._api_key = api_key
        self._model = model
        self._client = client or httpx.Client(timeout=20.0)

    @classmethod
    def from_env(cls) -> "GroqStructuredCompletionProvider":
        return cls(
            api_key=os.environ.get("GROQ_API_KEY", ""),
            model=os.environ.get("GROQ_MODEL", DEFAULT_GROQ_MODEL),
        )

    def complete(self, *, system_prompt: str, user_text: str) -> dict[str, Any]:
        response = self._client.post(
            GROQ_API_URL,
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "order_extraction",
                        "strict": True,
                        "schema": ORDER_EXTRACTION_SCHEMA,
                    },
                },
            },
        )
        response.raise_for_status()
        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        return json.loads(content)
