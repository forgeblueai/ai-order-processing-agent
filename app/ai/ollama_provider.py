import json
import os
from typing import Any

import httpx

from app.schemas.extraction import ExtractionResult


DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:8b"


class OllamaStructuredCompletionProvider:
    """Zero-cost local provider. It exposes no tools and requires no API key."""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_OLLAMA_URL,
        model: str = DEFAULT_OLLAMA_MODEL,
        think: bool = False,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._think = think
        self._client = client or httpx.Client(timeout=60.0)

    @classmethod
    def from_env(cls) -> "OllamaStructuredCompletionProvider":
        think_setting = os.environ.get("OLLAMA_THINK", "false").strip().lower()
        if think_setting not in {"true", "false"}:
            raise ValueError("OLLAMA_THINK must be true or false")
        return cls(
            base_url=os.environ.get("OLLAMA_URL", DEFAULT_OLLAMA_URL),
            model=os.environ.get("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            think=think_setting == "true",
        )

    def complete(self, *, system_prompt: str, user_text: str) -> dict[str, Any]:
        response = self._client.post(
            f"{self._base_url}/api/chat",
            json={
                "model": self._model,
                "stream": False,
                # Bounded deterministic extraction profile for local Qwen3:
                # no intermediate reasoning trace, greedy decoding, fixed seed.
                # The benchmark corpus/scorer/threshold remain untouched.
                "think": self._think,
                "options": {"temperature": 0, "seed": 42},
                "format": ExtractionResult.model_json_schema(),
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_text},
                ],
            },
        )
        response.raise_for_status()
        payload = response.json()
        return json.loads(payload["message"]["content"])
