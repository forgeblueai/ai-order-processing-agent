from typing import Any, Protocol

from app.ai.prompts import SYSTEM_PROMPT
from app.schemas.extraction import ExtractionResult
from app.schemas.order import OrderProcessRequest


class StructuredCompletionProvider(Protocol):
    """Minimal boundary implemented by any external LLM provider adapter."""

    def complete(self, *, system_prompt: str, user_text: str) -> dict[str, Any]: ...


class LLMOrderExtractor:
    """Converts provider output into trusted application data via strict validation."""

    def __init__(self, provider: StructuredCompletionProvider) -> None:
        self._provider = provider

    def extract(self, payload: OrderProcessRequest) -> ExtractionResult:
        raw = self._provider.complete(
            system_prompt=SYSTEM_PROMPT,
            user_text=f"Subject: {payload.subject}\nBody: {payload.body}",
        )
        return ExtractionResult.model_validate(raw)
